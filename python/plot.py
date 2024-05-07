import numpy as np
import matplotlib.pyplot as plt
import random as random
import os as os
import os.path
import parse
import argparse
import pandas as pd

# Main Function
def main(decay, xmass, smass):

    # Iterate through all files in the given directory
    all_files = iterate_directory(decay, xmass, smass)

    # CHECK IF PRESCAN EXISTS -- If it does, make it the first file to plot
    prescan = "output/prescan/X"+xmass+"_S"+smass+"/TRSMBroken_prescan.tsv"
    if ((os.path.exists(prescan))):
        all_files.insert(0, prescan)

    '''
    Note: Reason why there is no if-else is due to testing variables, I will create the if-else after assuring that functions work as desired
    '''
    
    # Using Iterate Directory - Plot all files and variables
    plot_multiple_chat(all_files, smass, decay, xmass)



'''
The way this function works is that it will plot all of the points for one combination and then move on from combination to combination 

^^ This is different from my original idea of plotting each combination as we go through each file 

Pros -- Code works !!!
Cons -- the code runs slower than original approach as it is plotting through each file almost manually

'''
#Plot multiple function with the help of AI -- find a way to make the process more efficient and faster !!
def plot_multiple_chat(file_array, smass, decay, xmass):

    array_of_colors = ["brown", "red", "orangered", "sienna", "saddlebrown", "darkorange", "gold", "darkolivegreen", "green", "teal", "steelblue", "blue", "blueviolet", "purple", "hotpink"]
    
    # Create Directory
    output_dir = "output/plots/" + decay + "/X" + xmass + "_S" + smass + "/"
    mkdir_p(output_dir)

    op = (0.8 / len(file_array))


    for i in range(15):
        opac = op + 0.19
        plt.figure()  # Create a new figure for each variable combination
        for df in file_array:
            print(df)
            parser = parse.Parse(df, HMass=125, SMass=float(smass))
            thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
            xb = parser.getxb(decay)

            var_array = [[thetahS, thetahX], [thetahS, thetaSX], [thetahS, vs], [thetahS, vx], [thetahX, thetaSX],
                         [thetahX, vs], [thetahX, vx], [thetaSX, vs], [thetaSX, vx], [vs, vx], [thetahS, xb],
                         [thetahX, xb], [thetaSX, xb], [vs, xb], [vx, xb]]
            var_names = [["thetahS", "thetahX"], ["thetahS", "thetaSX"], ["thetahS", "vs"], ["thetahS", "vx"],
                         ["thetahX", "thetaSX"], ["thetahX", "vs"], ["thetahX", "vx"], ["thetaSX", "vs"], ["thetaSX", "vx"],
                         ["vs", "vx"], ["thetahS", "xb"], ["thetahX", "xb"], ["thetaSX", "xb"], ["vs", "xb"], ["vx", "xb"]]

            plt.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac, label=f"{df}: {var_names[i][0]} vs {var_names[i][1]}")
            opac += op
            #array_of_colors.reverse()

        plt.xlabel(var_names[i][0])
        plt.ylabel(var_names[i][1])
        plt.title(f"{var_names[i][0]} vs {var_names[i][1]}")
        #plt.legend()
        plt.savefig(output_dir + f"{var_names[i][0]}_vs..._{var_names[i][1]}.png")
        plt.close()


#### Original plot multiple function 
def plot_multiple(file_array, smass, decay, xmass):

    array_of_colors = ["brown", "red", "orangered", "sienna", "saddlebrown", "darkorange", "gold", "darkolivegreen", "green", "teal", "steelblue", "blue", "blueviolet", "purple", "hotpink"]

    #Create Directory
    output_dir = "output/plots/" + decay + "/X"+xmass+"_S"+smass+"/"
    mkdir_p(output_dir)

    counter = 0
    plots = []

    op = (0.8 / len(file_array))
    opac = op + 0.19
    
    for df in file_array:

        print(df)

        parser = parse.Parse(df,HMass=125,SMass=float(smass))

        thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
        xb = parser.getxb(decay)
        
        var_array = [[thetahS, thetahX], [thetahS, thetaSX], [thetahS, vs], [thetahS, vx], [thetahX, thetaSX], [thetahX, vs], [thetahX, vx], [thetaSX, vs], [thetaSX, vx], [vs, vx], [thetahS, xb], [thetahX, xb], [thetaSX, xb], [vs, xb], [vx,xb]]
        var_names = [["thetahS", "thetahX"], ["thetahS", "thetaSX"], ["thetahS", "vs"], ["thetahS", "vx"], ["thetahX", "thetaSX"], ["thetahX", "vs"], ["thetahX", "vx"], ["thetaSX", "vs"], ["thetaSX", "vx"], ["vs", "vx"], ["thetahS", "xb"], ["thetahX", "xb"], ["thetaSX", "xb"], ["vs", "xb"], ["vx", "xb"]]
        
        for i in range(len(var_array)):
            plt.figure()  # Create a new figure for each variable combination
            plt.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac)
            plt.xlabel(var_names[i][0])
            plt.ylabel(var_names[i][1])
            plt.title(f"{var_names[i][0]} v s {var_names[i][1]}")
            plt.savefig(output_dir + f"{var_names[i][0]}_v_s_{var_names[i][1]}.png")
            plt.close()

        
        if counter == 0:
            for i in range(len(var_array)):

                
                #print("**")
                fig = plt.figure()
                scatter = plt.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac)
                axis = fig.add_subplot(111)
                axis.add_collection(scatter)
                

                plt.figure()
                plt.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac)
                scatter = plt.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac)
                plt.xlabel(var_names[i][0])
                plt.ylabel(var_names[i][1])
                plt.title(f'{var_names[i][0]} vs. {var_names[i][1]}')
                plt.savefig(output_dir + f'{var_names[i][0]} testy {var_names[i][1]}.png')
                plots.append(scatter)
                #plt.show()
                plt.close()
                
              
        else:

            for i in range(len(var_array)):
                plt.figure()  # Create a new figure
                plt.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac)
                plt.xlabel(var_names[i][0])
                plt.ylabel(var_names[i][1])
                plt.savefig(output_dir + f'{var_names[i][0]} testy {var_names[i][1]}.png')
                plt.close()

            
            for i in range(len(var_array)):
                plot = plots[i]
                plot.figure()
                plot.axes.scatter(var_array[i][0], var_array[i][1], s=15, c=array_of_colors[i], alpha=opac)
                plot.axes.xlabel(var_names[i][0])
                plot.axes.ylabel(var_names[i][1])
                plot.savefig(output_dir + f'{var_names[i][0]} testy {var_names[i][1]}.png')
                #plt.show()
                plot.axes.close()
        
        counter += 1
        opac += op

#Function that iterates through a directory to find all tsv files pertaining to the input
def iterate_directory(decay, xmass, smass):

    # Empty array that will hold the files found
    file_array = []

    # Directory for the scan outputs
    directory = "./output/scan/"+decay+"/X"+xmass+"_S"+smass+"/files/"

    # Iterate through the directory
    for file in os.listdir(directory):

        file_name = file

        # Check if the file is a .tsv file, if it is, append to the list
        if ".tsv" in file_name:
            file_array.append(directory + file)

    #Sort the array so files are in order
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

#Function that will plot the given arrays and save them as a png ---- original function (will be deleted soon)
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

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-D", "--Decay", required=True, type=str)
    argparser.add_argument("-X", "--XMass", required=True, type=str)
    argparser.add_argument("-S", "--SMass", required=True, type=str)
    args = vars(argparser.parse_args())

    decay = args["Decay"]
    xmass = args["XMass"]
    smass = args["SMass"]

    main(decay, xmass, smass)