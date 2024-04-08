import subprocess
import multiprocessing as mp
import os
import shutil
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

    # TODO: Make this a separate function that uses Popen and checks output file and terminates if it stalls out. Use process.poll() to check if it is still running
    # run the process with arguments and suppress output
    subprocess.run(process, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

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