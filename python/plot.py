import numpy as np
import matplotlib.pyplot as plt
import random as random
import os as os
import os.path
from itertools import combinations
from pathlib import Path
import parse

def main():
    decay = "SbbHtautau"
    xmass = "1000"
    smass = "300"
    niter = 2


    # CHECK IF PRESCAN EXISTS -- If it does, make it the first file to plot
    prescan = "output/prescan/X"+xmass+"_S"+smass+"/TRSMBroken_prescan.tsv"
    if ((os.path.exists(prescan)) == False):
        mkdir_p(prescan)
    filename = prescan
    parser = parse.Parse(filename,HMass=125,SMass=float(smass))
    thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
    xb = parser.getxb(decay) # y-axis when plotting

    '''
    Note: Reason why there is no if-else is due to testing variables, I will create the if-else after assuring that functions work as desired
    '''

    
    trialfile_0 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0000.tsv"
    trialfile_1 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0001.tsv"
    trialfile_2 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0002.tsv"
    trialfile_3 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0003.tsv"
    trialfile_4 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0004.tsv"
    trialfile_5 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0005.tsv"
    trialfile_6 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0006.tsv"
    trialfile_7 = "output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/TRSMBroken_0007.tsv"
    

    #second_file = trialfile

    files = [prescan, trialfile_0, trialfile_1, trialfile_2, trialfile_3, trialfile_4, trialfile_5, trialfile_6, trialfile_7]
    
    #var_array = [[thetahS, thetahX], [thetahS, thetaSX], [thetahS, vs], [thetahS, vx], [thetahX, thetaSX], [thetahX, vs], [thetahX, vx], [thetaSX, vs], [thetaSX, vx]]

    #plot_multiple(files, smass, decay, xmass)
    #plt.show()
    

    # get arrays object
    #parser1 = parse.Parse(second_file,HMass=125,SMass=float(smass))

    #thetahS, thetahX, thetaSX, vs, vx = parser1.getvars()

    #xb = parser1.getxb(decay)

    
    #** Using Iterate Directory
    array_files = iterate_directory(decay, xmass, smass)
    plot_multiple(array_files, smass, decay, xmass)
    

    '''
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
    '''
    


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

    #name = str(x + " vs " + y + ".png")

    plt.savefig(output_dir + name)
    #plt.show()

#ef iterate_variables():



def plot_multiple(file_array, smass, decay, xmass):

    array_of_colors = []
    #variable_array = [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4]]

    count = 15

    while(count < 0):
        r = random.random()
        g = random.random()
        b = random.random()

        color = (r, g, b)

        array_of_colors.append(color)

    plt.figure()
    op = 0.05
    for df in file_array:

        print(df)

        parser = parse.Parse(df,HMass=125,SMass=float(smass))

        thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
        xb = parser.getxb(decay)

        plt.scatter(thetahS, xb, s=15, c="darkblue", alpha=op)
            
        op +=0.05
    
    #Create Directory
    output_dir = "output/plots/" + decay + "/X"+xmass+"_S"+smass+"/"
    mkdir_p(output_dir)

    plt.xlabel("thetahS")
    plt.ylabel("xb")
    plt.title("thetahS vs xb")
    name = "thetahS vs xb - X1000_S300.png"

    plt.savefig(output_dir + name)
    #plt.show()



def iterate_directory(decay, xmass, smass):

    file_array = []

    directory = "./output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/"

    for file in os.listdir(directory):

        file_name = file

        if ".tsv" in file_name:
            file_array.append(directory + file)

    file_array.sort()
    return file_array


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

def plot_multiple_dup(file_array, smass, decay):

    array_of_colors = []
    #variable_array = [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4]]

    count = 15

    while(count < 0):
        r = random.random()
        g = random.random()
        b = random.random()

        color = (r, g, b)

        array_of_colors.append(color)

    for i in range(9):
        for i in range(2):

            plt.figure()
            op = 0.05
            for df in file_array:

                parser = parse.Parse(df,HMass=125,SMass=float(smass))

                thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
                xb = parser.getxb(decay)

                plt.scatter(thetahS, thetahX, s=15, c="red", alpha=op)
                    
                op +=0.05
            
            
            #plt.show()

if __name__ == '__main__':
    main()
