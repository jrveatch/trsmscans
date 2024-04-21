import numpy as np
import matplotlib.pyplot as plt
import random as random

import parse

def main():
    decay = "SbbHtautau"
    xmass = "1000"
    smass = "300"
    niter = 2

    prescan = "output/prescan/X"+xmass+"_S"+smass+"/TRSMBroken_prescan.tsv"
    trialfile_0 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0000.tsv"
    trialfile_1 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0001.tsv"
    trialfile_2 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0002.tsv"
    trialfile_3 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0003.tsv"
    trialfile_4 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0004.tsv"
    trialfile_5 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0005.tsv"
    trialfile_6 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0006.tsv"
    trialfile_7 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0007.tsv"

    filename = prescan
    #second_file = trialfile

    files = [prescan, trialfile_0, trialfile_1, trialfile_2, trialfile_3, trialfile_4, trialfile_5, trialfile_6, trialfile_7]
    
    #plot_multiple(files, smass, decay)
    #plt.show()
    

    # get arrays object
    parser = parse.Parse(filename,HMass=125,SMass=float(smass))
    #parser1 = parse.Parse(second_file,HMass=125,SMass=float(smass))

    thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
    #thetahS, thetahX, thetaSX, vs, vx = parser1.getvars()

    xb = parser.getxb(decay) # y-axis when plotting
    #xb = parser1.getxb(decay)

    
    plot_and_save(thetahS, thetahX, "thetahS", "thetahX", xmass, smass)
    plot_and_save(thetahS, thetaSX, "thetahS", "thetaSX", xmass, smass)
    plot_and_save(thetahS, vs, "thetahS", "vs", xmass, smass)
    plot_and_save(thetahS, vx, "thetahS", "vx", xmass, smass)
    plot_and_save(thetahX, thetaSX, "thetahX", "thetaSX", xmass, smass)
    plot_and_save(thetahX, vs, "thetahX", "vs", xmass, smass)
    plot_and_save(thetahX, vx, "thetahX", "vx", xmass, smass)
    plot_and_save(thetaSX, vs, "thetaSX", "vs", xmass, smass)
    plot_and_save(thetaSX, vx, "thetaSX", "vx", xmass, smass)
    plot_and_save(thetahS, xb, "thetahS", "xb", xmass, smass)
    plot_and_save(thetahX, xb, "thetahX", "xb", xmass, smass)
    plot_and_save(thetaSX, xb, "thetaSX", "xb", xmass, smass)
    plot_and_save(vs, xb, "vs", "xb", xmass, smass)
    plot_and_save(vx, xb, "vx", "xb", xmass, smass)
    plt.show()
    
    


    # OK !!!!! Possible problem - 'plot_and_save' function works, however, all graphs do not plot at the same time !!!!
    # OK ^^ plt.show() should be the last thing in order to show them at once --- this might depend on preference
    #### ^^ This was fixed by having the plt.show() at the end of all the function's call rather than at the end of the function
    # Figure out how to compare different files 

#Function that will plot the given arrays and save them as a png
def plot_and_save(array1, array2, array1_name, array2_name, xmass, smass, size=30):
    x = array1_name
    y = array2_name
    
    decay = "SbbHtautau"
    xmass = xmass
    smass = smass

    #create color
    r = random.random()
    g = random.random()
    b = random.random()

    color = (r, g, b)

    plt.figure()
    plt.scatter(array1, array2, size, c=color)
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(x + " vs " + y)

    #Create Directory
    output_dir = "output/plots/" + decay + "/X"+xmass+"_S"+smass+"/"
    mkdir_p(output_dir)

    name = str(x + " vs " + y + ".png")

    plt.savefig(output_dir + name)
    #plt.show()

def plot_multiple(file_array, smass, decay):

    #file_array = [file1, file2]

    for df in file_array:

        parser = parse.Parse(df,HMass=125,SMass=float(smass))

        thetahS, thetahX, thetaSX, vs, vx = parser.getmaxpoint()

        xb = parser.getxb(decay)

        #create color
        r = random.random()
        g = random.random()
        b = random.random()

        color = (r, g, b)

        plt.scatter(thetahS, vs, s=30, c=color)
        

#Create a function that will determine if the directory is already made, else it will create it
def mkdir_p(mypath):
    '''Creates a directory. equivalent to using mkdir -p on the command line'''

    from errno import EEXIST
    from os import makedirs,path

    try:
        makedirs(mypath)
    except OSError as exc: # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else: raise

if __name__ == '__main__':
    main()
