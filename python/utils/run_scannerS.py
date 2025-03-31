#!/usr/bin/env python3

# standard libraries
import argparse
import logging
import math
import multiprocessing as mp
import os
import shutil
import subprocess
import time
from typing import List

# third-party libraries
from blessings import Terminal

# local modules
from utils.config_loader import ConfigLoader
from utils.env_utils import data_dir
from utils.tsv_utils import save_tsv_output

# get logger
logger = logging.getLogger(__name__)

config_loader = ConfigLoader(config_file_name="ScannerS.yml")
# get configurations from config file
try:
    # fraction of cpus to use when parallel processing
    frac_cpu: float = config_loader.get('ScannerS', 'frac_cpu')
    # minimum number of points per job
    min_points_per_job: int = config_loader.get('ScannerS', 'min_points_per_job')
    # time in seconds at which process will be killed if nothing is printed out
    timeout: float = config_loader.get('ScannerS', 'timeout')
except KeyError as e:
    logger.error(e)
    raise
except Exception as e:
    logger.error(e)
    raise

# get logger
logger = logging.getLogger(__name__)

# method to run ScannerS
def run_scannerS(ini_name: str,
                 num_points: int,
                 model_name: str,
                 use_multiprocessing: bool = True) -> int:

    # raise exception if .ini doesn't exist
    if not os.path.exists(ini_name):
        raise FileNotFoundError(f"The requested .ini file {ini_name} doesn't exist. Exiting.")

    # initialize number of processes to 1
    num_processes = 1

    # get number of available CPUs
    num_cpu = mp.cpu_count()

    # make sure the minimum number of points are used
    if num_points < min_points_per_job:
        logger.debug(f"A minimum of {min_points_per_job} is required to run, adjusting...")
        num_points = min_points_per_job

    # use num_points unless modified for parallel processes
    points_per_process = num_points

    # if multiprocessing flag isn't set, run as a single process
    if not use_multiprocessing:
        logger.debug(f"Multiprocessing set to False, running as a single process with {num_points} points.")

    # if there is only 1 CPU available, run as a single process
    if num_cpu == 1:
        logger.debug(f"Only 1 CPU available, running as a single process with {num_points} points.")
        use_multiprocessing = False

    # if fewer than 2 processes are needed, run as a single process
    if num_points <= 2 * min_points_per_job:
        logger.debug(f"Only 1 process needed, running as a single process with {num_points} points.")
        use_multiprocessing = False

    # if using multiprocessing, run a test job and then calculate number of jobs and points per job
    if use_multiprocessing:

        # print out some information
        logger.debug(f"Running a test job with {min_points_per_job} points")

        # define test process with 10 points
        test_process_args = [model_name, "--config", ini_name, "scan", "-n", str(min_points_per_job)]

        # run test process
        try:
            run_test_process(test_process_args,model_name)
        except TimeoutError:
            raise

        # print out some information
        logger.debug("Test job was successful")

        # number of points left to run after test job
        points_to_run = num_points - min_points_per_job

        # set number of processes to 80% of the available cores rounded down
        num_processes = int(num_cpu * frac_cpu)

        # get number of points per job, rounded up
        points_per_process = math.ceil(points_to_run/num_processes)

        # if points_per_process is less than min_points_per_job, reduce the number of jobs
        if points_per_process < min_points_per_job:
            num_processes = math.ceil(points_to_run/min_points_per_job)
            points_per_process = min_points_per_job

        # reset points_to_run to reflect how many are actually used
        points_to_run = points_per_process * num_processes

        # print out some information
        logger.info(f"Running {num_processes} processes")
        logger.debug(f"Running {points_to_run} points as {num_processes} processes with {points_per_process} points each")

        num_points = points_to_run + min_points_per_job
    
    else:
        logger.info("Running as a single process")
        
    # create list of directories
    directories = [f"dir_{i}" for i in range(num_processes)]

    # define process
    process_args = [model_name, "--config", ini_name, "scan", "-n", str(points_per_process)]

    # create a shared counter and a lock
    counter = mp.Manager().Value("i",0)
    lock = mp.Manager().Lock()

    # print empty job completion counter
    print(f"{counter.value}/{num_processes} processes finished")

    # create a pool of processes
    with mp.Pool(processes=num_processes) as pool:

        # map the run_process function to each directory
        pool.starmap(run_process, [(process_args, directory, num_processes, counter, lock) for directory in directories])

        # wait for all processes to finish
        pool.close()
        pool.join()

    # success message
    logger.info("All processes finished. Merging outputs...")

    # combine the outputs into a single file
    concatenate_files(directories=directories,
                      file_name=model_name+".tsv")

    # return number of points that are actually used, including test job points
    return num_points

# run a process for multiprocessing
def run_process(process_args: List[str],
                directory: str,
                num_processes: int,
                counter,
                lock) -> None:

    # create temporary directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # get original directory
    original_dir = os.getcwd()

    # change to the temporary directory
    os.chdir(directory)

    # log file
    log = open("ScannerS.log", "w")

    # run the process with arguments and suppress output
    subprocess.run(process_args, stdout=log, stderr=log)

    # change back to the original directory
    os.chdir(original_dir)

    # increment the counter and print out how many processes are finished
    with lock:
        counter.value += 1
        print(Terminal().move_up() + f"{counter.value}/{num_processes} processes finished")

# run a python test process as a single job
def run_test_process(process_args: List[str],
                     model_name: str) -> None:

    # output file name
    outfile = model_name + ".tsv"

    # log file
    log = open("ScannerS.log", "w")

    # launch process
    process = subprocess.Popen(process_args, stdout=log, stderr=log)

    # get start time
    start_time = time.time()

    # flag to check timeout
    check_timeout = True

    # check output while the process is still running
    while process.poll() is None:

        # check timeout once if it hasn't been checked before
        if check_timeout and time.time() - start_time >= timeout:

            # if output file is empty, complain, kill process and exit
            if os.path.exists(outfile) and not os.path.getsize(outfile):

                # kill process
                process.kill()

                # make exception message
                msg = f"No output after {timeout} seconds. Run directory should be cleaned up."

                # raise timeout exception
                raise TimeoutError(msg)

            # only need to check timeout once
            check_timeout = False

        # wait 1 second before checking again
        time.sleep(1)

    # successful run
    return

# concatenate outputs from parallel processes into a single .tsv file
def concatenate_files(directories: List[str],
                      file_name: str) -> None:

    # loop over temporary directories
    for directory in directories:

        # write/append .tsv from directory to output file
        save_tsv_output(input_file = directory + "/" + file_name,
                        output_file = file_name)

        # delete the temporary directory
        remove_temp_dir(directory)

# if rmtree fails due to non-empty directory, try a few more times
# this seems necessary on lxplus and maybe some other systems
def remove_temp_dir(directory, retries=5, delay=1):
    for attempt in range(retries):
        try:
            shutil.rmtree(directory)
            logger.debug(f"Successfully removed: {directory}")
            return
        except OSError as e:
            if 'Directory not empty' in str(e):
                logger.debug(f"Attempt {attempt + 1}: Directory not empty, retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
            else:
                raise  # Raise if it's another type of error
    logger.error(f"Failed to remove {directory} after {retries} retries.")

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-n", "--num_points", default=200, type=int, help="Number of points")
    arg_parser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    args = arg_parser.parse_args()

    # get baseline .ini from data directory
    ini_name = data_dir() + "models/" + args.model + "_baseline.ini"

    # run ScannerS using baseline .ini
    run_scannerS(ini_name = ini_name,
                 model_name = args.model,
                 num_points = args.num_points,
                 use_multiprocessing = args.use_multiprocessing)
