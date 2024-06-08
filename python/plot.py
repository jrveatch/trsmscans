#!/usr/bin/env python3

import matplotlib.pyplot as plt
import random
import os
import parse
import argparse
from masses import Masses
from model import Model

# Main Function
def main(decay, masses: 'Masses', modelname):

    # Iterate through all files in the given directory
    all_files = iterate_directory(decay, masses, modelname)

    # CHECK IF PRESCAN EXISTS -- If it does, make it the first file to plot
    prescan = "output/"+modelname+"/prescan/"+str(masses)+"/"+modelname+"_prescan.tsv"
    if ((os.path.exists(prescan))):
        all_files.insert(0, prescan)

    # Using Iterate Directory - Plot all files and variables
    plot(all_files, decay, masses, modelname)

#Plot multiple function with the help of AI -- find a way to make the process more efficient and faster !!
def plot(file_array, decay, masses: 'Masses', modelname):
    
    # Create Directory
    output_dir = "output/" + modelname + "/plots/" + decay + "/" + str(masses) + "/" 
    mkdir_p(output_dir) #pass directory to the make directory function

    #Create a model object
    model = Model(modelname)

    #Initialize list that will hold all the maximum points for each file iteration
    maxpoint_list = []

    # Initialize a dictionary to store variable lists
    var_list = {}

    # Iterate through each file
    for file in file_array:

        # Retrieve the variables from the list
        parser = parse.Parse(filename=file, masses=masses, decay=decay, modelname="TRSMBroken") 
        allParams = parser.getParameters()
        xb = parser.getXB(decay)

        # Retrieve maximum point based on the file's variables
        maxpoint = parser.getMaxPoint()

        #Retrieve the variable names for the model
        var_names = model.parameterList()

        #Iterate through the information of each paramater
        for name, par in allParams.items():
        # Ensure the variable list exists for the parameter name
            
            #Check the paramater name
            if name not in var_list:
                var_list[name] = []

            #Append the variable value to the corresponding list
            var_list[name].append(par)
            
        #Check if xb exists in the variable list
        if 'xb' not in var_list:
            var_list['xb'] = []

        #Append xb to the corresponding list
        var_list['xb'].append(xb)

        # Append the maximum point to the list
        maxpoint_list.append(maxpoint)

    #Check if xb exists in the variable name list, if not append
    if 'xb' not in var_names:
        var_names.append('xb')
    
    # Find the Maximum point from the maximum points
    maximum = get_max_point(maxpoint_list)

    #Set the start and end colors by random RGB values
    start_rgb, end_rgb = select_colors()

    #Iterate through the list of all variables to plot each variable combination from each file
    for v in range(len(var_names)-1):

        var1 = var_list[var_names[v]] #Get the first variable 2D-list from the all variable list
        
        for j in range(v+1, len(var_names)):

            var2 = var_list[var_names[j]] #Get the second variable 2D-List from the all variable list

            #Set the opacity to be between values 0.19 and 1 depending on amount of files
            op = (0.8 / len(file_array))
            opac = op + 0.19

            #Create a new scatter figure
            plt.figure()
    
            #Iterate through both variable 2D-Lists to plot the info from each file
            for i in range(len(var_list[name])):

                #Decipher the color used for the scatterplot
                t = i / len(file_array)
                color = [start_rgb[c] + t * (end_rgb[c] - start_rgb[c]) for c in range(3)]

                #Plot the variables by file
                plt.scatter(var1[i], var2[i], s=15, c=color, alpha=opac)
                
                #Adjust the opacity
                opac+=op 

            #Reset opacity for star points
            opac = op
            opac += 0.19
            
            for q in range(len(var_list[name])):

                #Initialize both variables to be retrieved from the Point
                variable1 = var_names[v]
                variable2 = var_names[j]

                #Get and store the max points for each variable
                point1 = maxpoint_list[q].getVal(variable1)
                point2 = maxpoint_list[q].getVal(variable2)

                #Plot the max point from the scatterplot [star]
                if(maxpoint_list[q] != maximum): #Make sure the point is not the maximum point
                    plt.scatter(point1, point2, s=25, c="yellow", alpha=opac, marker="*") #plot normally
                else: #If point is maximum point plot as a bigger star
                    plt.scatter(point1, point2, s=60, c="gold", alpha=0.999, marker="*")

                #Adjust the opacity
                opac+=op

            #Initialize scatterplot labels
            plt.title(f"{var_names[v]} vs {var_names[j]}")
            plt.xlabel(f"{var_names[v]}")
            plt.ylabel(f"{var_names[j]}")

            #Save the figure as a png
            plt.savefig(output_dir + f"{var_names[v]}_vs_{var_names[j]}.png")

            #Close the figure
            plt.close()

#Function that returns the maximum point from all maximum point objects
def get_max_point(points):

    #Initialize the maximum point as the first point
    maxpoint = points[0]

    #Iterate to decipher the maximum point from the list
    for i in range(len(points)-1):
        if maxpoint < points[i+1]:
            maxpoint = points[i+1]

    #Return maximum point
    return maxpoint

#Function that defines colors to plot using random RGB values
def select_colors():

    #Set random RGB values
    r = random.random()
    g = random.random()
    b = random.random()

    #Define two different colors with the given RGB values
    color1 = (r, g, b)
    color2 = (g, b, r)

    #Return the values to call
    return color1, color2

#Function that iterates through a directory to find all tsv files pertaining to the input
def iterate_directory(decay, masses: 'Masses', modelname):

    #Empty array that will hold the files found
    file_array = []

    # Directory for the scan outputs
    directory = "./output/"+modelname+"/scan/" + decay + "/" + str(masses) + "/files/"

    #Iterate through the directory
    for file in os.listdir(directory):

        file_name = file

        # Check if the file is a .tsv file, if it is, append to the list
        if ".tsv" in file_name:
            file_array.append(directory + file)

    #Sort the array so files are in order
    file_array.sort()
    return file_array

# Create a function that will determine if the directory is already made, else it will create it
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
    argparser.add_argument("-X", "--XMass", required=True, type=float)
    argparser.add_argument("-S", "--SMass", required=True, type=float)
    argparser.add_argument("-H", "--HMass", default=125.09, type=float)
    argparser.add_argument("-M", "--model", default="TRSMBroken", type=str)
    args = argparser.parse_args()

    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    main(decay=args.Decay, masses=masses, modelname=args.model)