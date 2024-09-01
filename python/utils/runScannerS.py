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
def runScannerS(ininame: str,
                npoints: int,
                modelname: str,
                use_multiprocessing: bool) -> int:

    # if only one process needed, use subprocess
    if not use_multiprocessing:
        return run_single_process(ininame=ininame,
                                  npoints=npoints,
                                  modelname=modelname)

    # otherwise use multiprocessing
    else:
        return run_parallel_processes(ininame=ininame,
                                      npoints=npoints,
                                      modelname=modelname)

# run job as a single process
def run_single_process(ininame: str,
                       npoints: int,
                       modelname: str) -> int:

    # simple information message
    print(f"Running ScannerS as a single process with",npoints,"points.")

    # complain and exit if .ini doesn't exist
    # TODO: Change this to a try/except
    if not os.path.exists(ininame):
        print(ininame,"doesn't exist. Exiting.")
        quit()

    # define process
    process = [modelname, "--config", ininame, "scan", "-n", str(npoints)]

    # run the process
    try:
        run_subprocess(process,modelname)
    except TimeoutError:
        raise

    # simple information message
    print("Finished running process")

    # return number of points used
    return npoints

# run multiple processes in parallel
def run_parallel_processes(ininame: str,
                           npoints: int,
                           modelname: str,
                           njobs=-1) -> int:

    # complain and exit if .ini doesn't exist
    if not os.path.exists(ininame):
        print(ininame,"doesn't exist. Exiting.")
        quit()

    # get number of available CPUs
    ncpu = mp.cpu_count()

    # if there is only 1 CPU available, run a single process
    if ncpu == 1:
        print("Only 1 CPU available, running as a single process")
        return run_single_process(ininame=ininame,
                                  npoints=npoints,
                                  modelname=modelname)

    # set number of workers to 80% of the available cores
    nworkers = int(ncpu * 0.8)

    # by default set nprocesses to nworkers
    if njobs < 1:
        num_processes = nworkers
    # if the number of requested jobs is greater than the number
    # of workers, limit number of processes to number of workers
    elif njobs > nworkers:
        num_processes = nworkers
    # otherwise set the number of processes to the requested number of jobs
    else:
        num_processes = njobs

    # minimum number of points per job
    min_points = 10

    # get number of points per job, rounded up
    points_per_job = math.ceil(npoints/num_processes)

    # if points_per_job is less than min_points, reduce the number of jobs
    if points_per_job < min_points:
        num_processes = math.ceil(npoints/min_points) - 1
        points_per_job = min_points

    # if fewer than 2 processes are needed, run a single process
    if num_processes < 2:
        print("Only 1 process needed, running as a single process")
        return run_single_process(ininame=ininame,
                                  npoints=npoints,
                                  modelname=modelname)

    # print out some information
    print("Running test job with",min_points,"points")

    # define test process with 10 points
    test_process = [modelname, "--config", ininame, "scan", "-n", str(min_points)]

    # run test process
    try:
        run_subprocess(test_process,modelname)
    except TimeoutError:
        raise

    # print out some information
    print("Test job was successful")

    # reset npoints to reflect how many are actually used
    npoints = points_per_job * num_processes

    # print out some information
    print("Running",npoints,"points as",num_processes,"processes with",points_per_job,"points each")

    # create list of directories
    directories = [f"dir_{i}" for i in range(num_processes)]

    # define process
    process = [modelname, "--config", ininame, "scan", "-n", str(points_per_job)]

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
    concatenate_files(directories,modelname+".tsv")

    # return number of points that are actually used
    return npoints

# run a process for multiprocessing
def run_process(process: list[str],
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
    subprocess.run(process, stdout=log, stderr=log)

    # get Terminal for nicer outputs
    term = Terminal()

    # increment the counter and print out how many processes are finished
    counter.value += 1
    print(term.move_up() + f"{counter.value}/{num_processes} processes finished")

# run a python subprocess for a single job
def run_subprocess(process: list[str],
                   modelname: str) -> None:

    # output file name
    outfile = modelname + ".tsv"

    # log file
    log = open("ScannerS.log", "w")

    # time in seconds at which process will be killed if nothing is printed out
    timeout = 20

    # launch process
    process = subprocess.Popen(process, stdout=log, stderr=log)

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
                      filename: str) -> None:

    # loop over temporary directories
    for directory in directories:

        # write/append .tsv from directory to output file
        tsvutils.save_tsv_output(inputfile=directory+"/"+filename,
                                 outputfile=filename)

        # delete the temporary directory
        shutil.rmtree(directory)

if __name__ == "__main__":

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    argparser.add_argument("-n", "--npoints", default=200, type=int, help="Number of points")
    argparser.add_argument("-j", "--njobs", default=4, type=int, help="Number of jobs")
    args = argparser.parse_args()

    # get baseline .ini from data directory
    ininame = os.environ['DATADIR'] + "models/" + args.model + "_baseline.ini"

    # run ScannerS using baseline .ini
    runScannerS(ininame=ininame,
                modelname=args.model,
                npoints=args.npoints,
                njobs=args.njobs)
