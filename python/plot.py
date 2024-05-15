import numpy as np
import matplotlib.pyplot as plt
import random as random
import os as os
import os.path
import parse
import argparse
from masses import Masses

# Main Function
def main(decay, xmass, smass):

    # Iterate through all files in the given directory
    all_files = iterate_directory(decay, xmass, smass)

    # CHECK IF PRESCAN EXISTS -- If it does, make it the first file to plot
    prescan = "output/prescan/X"+xmass+"_S"+smass+"/TRSMBroken_prescan.tsv"
    if ((os.path.exists(prescan))):
        all_files.insert(0, prescan)

    # Using Iterate Directory - Plot all files and variables
    plot(all_files, smass, decay, xmass)

#Plot multiple function with the help of AI -- find a way to make the process more efficient and faster !!
def plot(file_array, smass, decay, xmass):

    #Create a masses object
    masses = Masses(mX=float(xmass),mS=float(smass), mH=125)
    
    # Create Directory
    output_dir = "output/plots/" + decay + "/X" + xmass + "_S" + smass + "/" 
    mkdir_p(output_dir) #pass directory to the make directory function

    #Initialize variable 2D-lists to store each variable list from all files
    thetahS_list = []
    thetahX_list = []
    thetaSX_list = []
    vs_list = []
    vx_list = []
    xb_list = []

    #Initialize list that will hold all the maximum points for each file iteration
    maxpoint_list = []

    #Iterate through each file
    for file in file_array:

        #Retrieve the variables from the list
        parser = parse.Parse(filename=file, masses=masses, decay=decay) 
        thetahS, thetahX, thetaSX, vs, vx = parser.getvars()
        xb = parser.getxb(decay)

        #Retrive maximum point based on the file's variables
        maxpoint = parser.getmaxpoint()
        
        #Append each variable list from the file to its 2D-Variable array
        thetahS_list.append(thetahS)
        thetahX_list.append(thetahX)
        thetaSX_list.append(thetaSX)
        vs_list.append(vs)
        vx_list.append(vx)
        xb_list.append(xb)

        #Append the maximum point in to its respective list
        maxpoint_list.append(maxpoint)

    #Create a list containing all of the variable lists
    var_list = [thetahS_list, thetahX_list, thetaSX_list, vs_list, vx_list, xb_list]
    var_names = ["thetahS", "thetahX", "thetaSX", "vs", "vx", "xb"] #List with all the variable names
    point_vars = ["tHS", "tHX", "tSX", "vs", "vx", "xb"] #List with all the variable names based on the Point class

    # Define default start and end colors using RGB values directly
    start_rgb = (0, 0, 1)  # Blue
    end_rgb = (1, 0, 0)    # Red

    #Iterate through the list of all variables to plot each variable combination from each file
    for v in range(len(var_list)-1):

        var1 = var_list[v] #Get the first variable 2D-list from the all variable list
        
        for j in range(v+1, len(var_list)):

            var2 = var_list[j] #Get the second variable 2D-List from the all variable list

            #Set the opacity to be between values 0.19 and 1 depending on amount of files
            op = (0.8 / len(file_array))
            opac = op + 0.19

            #Create a new scatter figure
            plt.figure()
    
            #Iterate through both variable 2D-Lists to plot the info from each file
            for i in range(len(thetahS_list)):

                #Decipher the color used for the scatterplot
                t = i / len(file_array)
                color = [start_rgb[c] + t * (end_rgb[c] - start_rgb[c]) for c in range(3)]

                #Initialize both variables to be retrieved from the Point
                variable1 = point_vars[v]
                variable2 = point_vars[j]

                #Get and store the max points for each variable
                point1 = maxpoint_list[i].get_attribute(variable1)
                point2 = maxpoint_list[i].get_attribute(variable2)

                #Plot the variables by file
                plt.scatter(var1[i], var2[i], s=15, c=color, alpha=opac)

                #Plot the max point from the scatterplot [star]
                if i < (len(thetahS_list) - 1):
                    plt.scatter(point1, point2, s=25, c="gold", alpha=opac, marker="*")
                else:
                    plt.scatter(point1, point2, s=60, c="yellow", alpha=opac, marker="*") #Final max point from last file

                opac+=op #adjust the opacity
                
            #Initialize scatterplot labels
            plt.title(f"{var_names[v]} vs {var_names[j]}")
            plt.xlabel(f"{var_names[v]}")
            plt.ylabel(f"{var_names[j]}")

            #Save the figure as a png
            plt.savefig(output_dir + f"{var_names[v]}_vs_{var_names[j]}.png")

            #Close the figure
            plt.close()

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