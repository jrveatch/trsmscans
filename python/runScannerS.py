import subprocess
import multiprocessing
import os
import shutil
import math

def runScannerS(ininame,npoints,model="TRSMBroken"):

    # output .tsv name
    tsvname = model + ".tsv"

    # maximum number of points for a single process
    max_points = 1000

    # default number of processes
    num_processes = 1

    # if npoints is larger than the max, round to nearest
    # multiple of max_points and figure out how many processes
    # to run
    if npoints > max_points:
        if npoints % max_points:
            print("Can only run with multiples of",max_points,"per process, rounding up")
        num_processes = math.ceil(npoints/max_points)
        points_per_job = max_points
    else:
        points_per_job = npoints

    # TODO: Should we put some limit on num_processes?

    # create list of directories
    directories = [f"dir_{i}" for i in range(num_processes)]

    # define process
    process = [model, "--config", "../"+ininame, "scan", "-n", str(points_per_job)]

    print(process)

    # if only one process needed, just use subprocess
    if num_processes == 1:
        directory = "dir_0"
        print(f"Running process in directory '{directory}'.")
        os.makedirs(directory, exist_ok=True)
        os.chdir(directory)
        subprocess.run(process)
        shutil.move(tsvname,"../"+tsvname)
        os.chdir("..")
        shutil.rmtree(directory)
        print("Finished running process. Continuing...")

    # otherwise use multiprocessing
    else:
        # create a pool of processes
        with multiprocessing.Pool(processes=num_processes) as pool:
            # map the run_process function to each directory
            pool.starmap(run_process, [(process, directory) for directory in directories])
        
            # wait for all processes to finish
            pool.close()
            pool.join()

            print("All processes finished. Continuing...")

            # combine the outputs into a single file
            concatenate_files(directories,"TRSMBroken.tsv",points_per_job)

    return

def run_process(process, directory):
    print(f"Running process in directory '{directory}'.")
    # create temporary directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    # change to the temporary directory
    os.chdir(directory)
    # call the process with arguments and suppress output
    with open(os.devnull, 'w') as devnull:
        subprocess.run(process, stdout=devnull, stderr=subprocess.STDOUT)
    print(f"Process in directory '{directory}' finished.")

def concatenate_files(directories,filename,points_per_job):
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
                else:
                    # skip the header line
                    next(infile)
                for line in infile:
                    # replace the index with a unique value
                    parts = line.strip().split('\t')
                    parts[0] = str(int(parts[0]) + dir_number * points_per_job)
                    outfile.write('\t'.join(parts) + '\n')
            # delete the temporary directory
            shutil.rmtree(directory)


if __name__ == "__main__":
    runScannerS("TRSMBroken_baseline.ini",1000)