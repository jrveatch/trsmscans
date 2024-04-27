import subprocess
import multiprocessing as mp
import os
import shutil
import time
import math

def runScannerS(ininame,npoints,model="TRSMBroken",njobs=-1):

    # if only one process needed, just use subprocess
    if njobs == 1:
        return runSingleProcess(ininame,npoints,model)

    # otherwise use multiprocessing
    else:
        return runParallelProcesses(ininame,npoints,model,njobs)

def runSingleProcess(ininame,npoints,model="TRSMBroken"):

    # simple information message
    print(f"Running ScannerS as a single process.")

    # define process
    process = [model, "--config", ininame, "scan", "-n", str(npoints)]

    # run the process
    result = run_subprocess(process,model)

    # pass failed job error up the line
    if result < 0:
        return result

    # simple information message
    print("Finished running process. Continuing...")

    # return number of points used
    return npoints

def runParallelProcesses(ininame,npoints,model="TRSMBroken",njobs=-1):

    # get number of available CPUs
    ncpu = mp.cpu_count()

    # if there is only 1 CPU available, run a single process
    if ncpu == 1:
        print("Only 1 CPU available, running as a single process")
        return runSingleProcess(ininame,npoints,model)

    # set number of workers to 80% of the available cores
    nworkers = int(ncpu * 0.8)

    # by default set nprocesses to nworkers
    if njobs < 1:
        num_processes = nworkers
    # if the number of requested jobs is greater than the number
    # of workers, limit number of processes to number of workers
    elif njobs > nworkers:
        num_processes = nworkers
    # otherwise set the number of processes to the requested
    # number of jobs
    else:
        num_processes = njobs

    # get number of points per job, rounded up
    points_per_job = math.ceil(npoints/num_processes)

    # minimum number of points per job
    min_points = 10

    # if points_per_job is less than min_points, reduce the number of jobs
    if points_per_job < min_points:
        num_processes = math.ceil(npoints/min_points)
        points_per_job = min_points

    # if there is only 1 CPU available, run a single process
    if num_processes == 1:
        print("Only 1 process needed, running as a single process")
        return runSingleProcess(ininame,npoints,model)

    # define test process with 10 points
    test_process = [model, "--config", ininame, "scan", "-n", "10"]

    # run test process
    test_result = run_subprocess(test_process,model)

    # if test_result indicates a timeout, complain and exit
    if test_result < 0:
        print("Test job timed out. Exiting")
        return test_result

    # reset npoints to reflect how many are actually used
    npoints = points_per_job * num_processes

    # print out some information
    print("Running",num_processes,"process with",points_per_job,"points each")

    # create list of directories
    directories = [f"dir_{i}" for i in range(num_processes)]

    # define process
    process = [model, "--config", "../"+ininame, "scan", "-n", str(points_per_job)]

    # create a pool of processes
    with mp.Pool(processes=num_processes) as pool:

        # map the run_process function to each directory
        pool.starmap(run_process, [(process, directory) for directory in directories])

        # wait for all processes to finish
        pool.close()
        pool.join()

    # success message
    print("All processes finished. Merging outputs...")

    # combine the outputs into a single file
    concatenate_files(directories,model+".tsv",points_per_job)

    # return number of points that are actually used
    return npoints

def run_process(process, directory):

    # simple information message
    print(f"Running process in directory '{directory}'.")

    # create temporary directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # change to the temporary directory
    os.chdir(directory)

    # run the process with arguments and suppress output
    subprocess.run(process, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # simple information message
    print(f"Process in directory '{directory}' finished.")

def run_subprocess(process,model="TRSMBroken"):

    # output file name
    outfile = model + ".tsv"

    # launch process
    process = subprocess.Popen(process, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    # time in seconds at which process will be killed if nothing is printed out
    timeout = 10

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

                # complain
                print("No output after",timeout,"seconds. Exiting!")

                # kill process
                process.kill()

                # exit
                return -1

            # only need to check timeout once
            check_timeout = False

        # wait 1 second before checking again
        time.sleep(1)

    # successful run
    return 0

def concatenate_files(directories,filename,points_per_job):

    # flag indicating whether header has already been written
    header_written = False

    # open output file
    with open(filename,"w") as outfile:

        # loop over temporary directories
        for dir_number, directory in enumerate(directories):

            # open .tsv file in the directory
            with open(directory+"/"+filename,"r") as infile:

                # if the header has not already been written, write it
                if not header_written:
                    header = infile.readline()
                    outfile.write(header)
                    header_written = True

                # if header has already been written, skip it in future files
                else:
                    # skip the header line
                    next(infile)

                # loop over all non-header lines in file
                for line in infile:

                    # replace the index with a unique value
                    parts = line.strip().split('\t')
                    parts[0] = str(int(parts[0]) + dir_number * points_per_job)
                    outfile.write('\t'.join(parts) + '\n')

            # delete the temporary directory
            shutil.rmtree(directory)

if __name__ == "__main__":
    runScannerS(ininame="TRSMBroken_baseline.ini",npoints=200,njobs=4)