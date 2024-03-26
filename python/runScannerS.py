import subprocess
import multiprocessing
import os
import shutil

def runScannerS(ininame,npoints,num_processes):

    # TODO: Check num_processes and automate getting cores

    directories = [f"dir_{i}" for i in range(num_processes)]

    process = ["../../ScannerS/build/TRSMBroken", "--config", "../"+ininame, "scan", "-n", str(npoints)]

    print(process)

    # Create a pool of processes
    with multiprocessing.Pool(processes=num_processes) as pool:
        # Map the run_process function to each directory
        pool.starmap(run_process, [(process, directory) for directory in directories])
        
        # Wait for all processes to finish
        pool.close()
        pool.join()

    print("All processes finished. Continuing...")

    concatenate_files(directories,"TRSMBroken.tsv")

    return

def run_process(process, directory):
    print(f"Running process in directory '{directory}'.")
    # create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    # Change directory to the specified directory
    os.chdir(directory)
    # Call the process with arguments and suppress output
    with open(os.devnull, 'w') as devnull:
        subprocess.run(process, stdout=devnull, stderr=subprocess.STDOUT)
    print(f"Process in directory '{directory}' finished.")

def concatenate_files(directories,filename):
    header_written = False
    with open(filename,"w") as outfile:
        for directory in directories:
            with open(directory+"/"+filename,"r") as infile:
                if not header_written:
                    header = infile.readline()
                    outfile.write(header)
                    header_written = True
                else:
                    # skip the header line
                    next(infile)
                for line in infile:
                    outfile.write(line)
            shutil.rmtree(directory)
                

if __name__ == "__main__":
    runScannerS("TRSMBroken_baseline.ini",100,5)