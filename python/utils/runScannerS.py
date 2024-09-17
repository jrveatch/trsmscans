#!/usr/bin/env python3

import subprocess
import multiprocessing as mp
import os
import shutil
import time
import math
from blessings import Terminal
from utils import tsvutils
import argparse

# method to run ScannerS
def runScannerS(ini_name: str,
                num_points: int,
                model_name: str,
                use_multiprocessing: bool) -> int:

    # raise exception if .ini doesn't exist
    if not os.path.exists(ini_name):
        raise FileNotFoundError(ini_name,"doesn't exist. Exiting.")

    # if only one process needed, use subprocess
    if not use_multiprocessing:
        return run_single_process(ini_name = ini_name,
                                  num_points = num_points,
                                  model_name = model_name)

    # otherwise use multiprocessing
    else:
        return run_parallel_processes(ini_name = ini_name,
                                      num_points = num_points,
                                      model_name = model_name)

# run job as a single process
def run_single_process(ini_name: str,
                       num_points: int,
                       model_name: str) -> int:

    # simple information message
    print(f"Running ScannerS as a single process with {num_points} points.")

    # define process
    process_args = [model_name, "--config", ini_name, "scan", "-n", str(num_points)]

    directory = "dir_0"

    # create temporary directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # change to the temporary directory
    os.chdir(directory)

    # run the process
    try:
        run_subprocess(process_args,model_name)
    except TimeoutError:
        raise

    # Move the results to the temporary directory
    output_file = model_name + ".tsv"
    tsvutils.save_tsv_output(output_file, "../" + output_file)

    os.chdir("..")
    shutil.rmtree(directory)

    # simple information message
    print("Finished running process")

    # return number of points used
    return num_points

# run multiple processes in parallel
def run_parallel_processes(ini_name: str,
                           num_points: int,
                           model_name: str) -> int:

    # get number of available CPUs
    num_cpu = mp.cpu_count()

    # minimum number of points per job
    min_points = 10

    # if there is only 1 CPU available, run a single process
    if num_cpu == 1:
        print("Only 1 CPU available, running as a single process")
        return run_single_process(ini_name = ini_name,
                                  num_points = num_points,
                                  model_name = model_name)

    # if fewer than 2 processes are needed, run a single process
    if num_points < 2 * min_points:
        print("Only 1 process needed, running as a single process")
        return run_single_process(ini_name = ini_name,
                                  num_points = num_points,
                                  model_name = model_name)

    # print out some information
    print(f"Running test job with {min_points} points")

    # define test process with 10 points
    test_process_args = [model_name, "--config", ini_name, "scan", "-n", str(min_points)]

    # run test process
    try:
        run_subprocess(test_process_args,model_name)
    except TimeoutError:
        raise

    # print out some information
    print("Test job was successful")

    # set number of processes to 80% of the available cores rounded down
    num_processes = int(num_cpu * 0.8)

    # get number of points per job, rounded up
    points_per_process = math.ceil(num_points/num_processes)

    # if points_per_process is less than min_points, reduce the number of jobs
    if points_per_process < min_points:
        num_processes = math.ceil(num_points/min_points) - 1
        points_per_process = min_points

    # reset num_points to reflect how many are actually used
    num_points = points_per_process * num_processes

    # print out some information
    print(f"Running {num_points} points as {num_processes} processes with {points_per_process} points each")

    # create list of directories
    directories = [f"dir_{i}" for i in range(num_processes)]

    # define process
    process = [model_name, "--config", ini_name, "scan", "-n", str(points_per_process)]

    # create a manager and a shared counter to track the number of finished processes
    manager = mp.Manager()
    counter = manager.Value("i",0)

    # print empty job completion counter
    print(f"{counter.value}/{num_processes} processes finished")

    # create a pool of processes
    with mp.Pool(processes=num_processes) as pool:

        # map the run_process function to each directory
        pool.starmap(run_process, [(process, directory, counter, num_processes) for directory in directories])

        # wait for all processes to finish
        pool.close()
        pool.join()

    # success message
    print("All processes finished. Merging outputs...")

    # combine the outputs into a single file
    concatenate_files(directories=directories,
                      file_name=model_name+".tsv")

    # return number of points that are actually used, including test job points
    return num_points + min_points

# run a process for multiprocessing
def run_process(process_args: list[str],
                directory: str,
                counter,
                num_processes: int) -> None:

    # create temporary directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # change to the temporary directory
    os.chdir(directory)

    # log file
    log = open("ScannerS.log", "w")

    # run the process with arguments and suppress output
    subprocess.run(process_args, stdout=log, stderr=log)

    # get Terminal for nicer outputs
    term = Terminal()

    # increment the counter and print out how many processes are finished
    counter.value += 1
    print(term.move_up() + f"{counter.value}/{num_processes} processes finished")

# run a python subprocess for a single job
def run_subprocess(process_args: list[str],
                   model_name: str) -> None:

    # output file name
    outfile = model_name + ".tsv"

    # log file
    log = open("ScannerS.log", "w")

    # time in seconds at which process will be killed if nothing is printed out
    timeout = 20

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
def concatenate_files(directories: list[str],
                      file_name: str) -> None:

    # loop over temporary directories
    for directory in directories:

        # write/append .tsv from directory to output file
        tsvutils.save_tsv_output(input_file=directory+"/"+file_name,
                                 output_file=file_name)

        # delete the temporary directory
        shutil.rmtree(directory)
        # this is a possible fix, but it is likely unstable
        #shutil.rmtree(directory, ignore_errors=True)

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-n", "--npoints", default=200, type=int, help="Number of points")
    args = arg_parser.parse_args()

    # get baseline .ini from data directory
    ini_name = os.environ['DATADIR'] + "models/" + args.model + "_baseline.ini"

    # run ScannerS using baseline .ini
    runScannerS(ini_name = ini_name,
                model_name = args.model,
                num_points = args.npoints)
