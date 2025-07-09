#!/usr/bin/env python3

# standard libraries
import argparse
import logging
import math
import multiprocessing as mp
from multiprocessing.managers import ValueProxy
import os
import shutil
import subprocess
import time
from typing import List

# third-party libraries
from blessings import Terminal

# local modules
from utils.config_loader import ConfigLoader
from utils.cpu_utils import get_n_cpus
from utils.env_utils import data_dir
from utils.tsv_utils import save_tsv_output

# get logger
logger = logging.getLogger(__name__)

# get configurations
config_loader = ConfigLoader("RunConfig.yml")
try:
    # minimum number of points per job
    min_points_per_job: int = config_loader.get('ScannerS', 'min_points_per_job')
    # time in seconds at which process will be killed if nothing is printed out
    timeout: float = config_loader.get('ScannerS', 'timeout')
except Exception as e:
    logger.exception(e)
    raise

# method to run ScannerS
def run_scannerS(ini_name: str,
                 num_points: int,
                 model_name: str,
                 use_multiprocessing: bool = True,
                 run_test_job: bool = True) -> int:

    # raise exception if .ini doesn't exist
    if not os.path.exists(ini_name):
        raise FileNotFoundError(f"The requested .ini file {ini_name} doesn't exist. Exiting.")

    # initialize number of processes to 1
    num_processes = 1

    # get number of available CPUs
    num_cpu = get_n_cpus()

    # use num_points unless modified for parallel processes
    points_per_process = num_points

    # if multiprocessing flag isn't set, run as a single process
    if not use_multiprocessing:
        logger.debug(f"Multiprocessing set to False, running as a single process with {num_points} points.")

    # if there is only 1 CPU available, run as a single process
    if num_cpu == 1:
        logger.debug(f"Only 1 CPU available, running as a single process with {num_points} points.")
        use_multiprocessing = False

    # run as a single process if only one is needed
    if num_points <= min_points_per_job:
        logger.debug(f"Only 1 process needed, running as a single process with {num_points} points.")
        use_multiprocessing = False

    # if using multiprocessing, run a test job and then calculate number of jobs and points per job
    if use_multiprocessing:

        # set points_to_run
        points_to_run = num_points

        # run test process if requested
        if run_test_job:
            logger.debug(f"Running a test job with {min_points_per_job} points")
            test_process_args = get_process_args(model_name=model_name,
                                                 ini_name=ini_name,
                                                 num_points=min_points_per_job)
            logger.debug("Running test job to check if ScannerS works with the given configuration")
            run_timed_process(process_args=test_process_args,
                              model_name=model_name)
            points_to_run -= min_points_per_job
            logger.debug("Test job was successful")

        # set number of processes to the number of allowed CPUs
        num_processes = num_cpu

        # get number of points per job, rounded up
        points_per_process = math.ceil(points_to_run/num_processes)

        # if points_per_process is less than min_points_per_job, reduce the number of jobs
        if points_per_process <= min_points_per_job:
            num_processes = math.ceil(points_to_run/min_points_per_job)
            points_per_process = min_points_per_job

        # reset points_to_run to reflect how many are actually used
        points_to_run = points_per_process * num_processes

        # print out some information
        logger.info(f"Running {num_processes} processes")
        logger.debug(f"Running {points_to_run} points as {num_processes} processes with {points_per_process} points each")

        num_points = points_to_run
        if run_test_job:
            num_points += min_points_per_job

        # create list of directories
        directories = [f"dir_{i}" for i in range(num_processes)]

        # define process
        process_args = get_process_args(model_name=model_name,
                                        ini_name=ini_name,
                                        num_points=points_per_process)

        # create a shared counter and a lock
        counter: ValueProxy = mp.Manager().Value("i",0)
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

    else:
        logger.info("Running as a single process")

        # define test process
        process_args = get_process_args(model_name=model_name,
                                        ini_name=ini_name,
                                        num_points=num_points)

        # run test process
        run_timed_process(process_args=process_args,
                          model_name=model_name)

    # return number of points that are actually used, including test job points
    return num_points

def run_scannerS_single_point(ini_name: str,
                              model_name: str) -> None:
    """Runs ScannerS for a single parameter point using the given model configuration.

    Args:
        ini_name (str): Path to the `.ini` configuration file.
        model_name (str): Name of the model to be scanned.
    """

    # raise exception if .ini doesn't exist
    if not os.path.exists(ini_name):
        raise FileNotFoundError(f"The requested .ini file '{ini_name}' doesn't exist. Exiting.")

    # define process
    process_args = get_process_args(model_name=model_name,
                                    ini_name=ini_name,
                                    num_points=1)

    # run timed process
    run_timed_process(process_args=process_args,
                      model_name=model_name)

# run a process for multiprocessing
def run_process(process_args: List[str],
                directory: str,
                num_processes: int,
                counter,
                lock) -> None:

    # create temporary directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # run the process with arguments and suppress output
    with open("ScannerS.log", "w") as log:
        subprocess.run(process_args, stdout=log, stderr=log, cwd=directory)

    # increment the counter and print out how many processes are finished
    with lock:
        counter.value += 1
        print(Terminal().move_up() + f"{counter.value}/{num_processes} processes finished")

# run a python test process as a single job
def run_timed_process(process_args: List[str],
                      model_name: str) -> None:

    # output file name
    outfile = model_name + ".tsv"

    # launch the process with arguments and redirect output to a log file
    with open("ScannerS.log", "w") as log:
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

    # clean up artifact files
    remove_artifact_files()

# concatenate outputs from parallel processes into a single .tsv file
def concatenate_files(directories: List[str],
                      file_name: str) -> None:

    try:
        # Loop over directories and concatenate their .tsv files
        for directory in directories:
            input_file = os.path.join(directory, file_name)

            # Check if the file exists before attempting to concatenate
            if os.path.exists(input_file):
                save_tsv_output(input_file=input_file, output_file=file_name)
            else:
                logger.warning(f"Missing expected file: {input_file}")

        logger.debug(f"Successfully concatenated all files into {file_name}")

    except Exception as e:
        logger.exception(f"Error during file concatenation: {e}")
        return  # Do not proceed with deleting directories

    # If everything worked, proceed to delete directories
    logger.debug("Removing temp directories")
    for directory in directories:
        remove_temp_dir(directory)
    logger.debug("Successfully removed temp directories")

# if rmtree fails due to non-empty directory, try a few more times
# this seems necessary on lxplus and maybe some other systems
def remove_temp_dir(directory, retries=5, delay=1):
    for attempt in range(retries):
        try:
            shutil.rmtree(directory)
            logger.verbose(f"Successfully removed: {directory}")
        except OSError as e:
            if 'Directory not empty' in str(e):
                logger.verbose(f"Attempt {attempt + 1}: Directory not empty, retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
            else:
                raise  # Raise if it's another type of error
        else:
            return
    logger.exception(f"Failed to remove {directory} after {retries} retries.")

def remove_artifact_files() -> None:
    """Remove artifact files that are not needed after the scan."""
    artifact_files = ["HS_analyses.txt",
                      "HS_correlations.txt",
                      "Key.dat", "STXS_analyses.txt",
                      "STXS_correlations.txt",]
    for file in artifact_files:
        if os.path.exists(file):
            os.remove(file)
            logger.debug(f"Removed artifact file: {file}")
        else:
            logger.debug(f"Artifact file {file} does not exist, skipping removal.")

def get_process_args(model_name: str,
                     ini_name: str,
                     num_points: int) -> List[str]:
    args = [model_name, "--config", ini_name, "scan", "-n", str(num_points)]
    return args

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-n", "--num_points", default=200, type=int, help="Number of points")
    arg_parser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    args = arg_parser.parse_args()

    # get baseline .ini from data directory
    ini_name = os.path.join(data_dir(), "models", f"{args.model}_baseline.ini")

    # run ScannerS using baseline .ini
    run_scannerS(ini_name = ini_name,
                 model_name = args.model,
                 num_points = args.num_points,
                 use_multiprocessing = args.use_multiprocessing)
