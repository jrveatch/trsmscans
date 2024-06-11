#!/usr/bin/env python3

import matplotlib.pyplot as plt
import random
import os
import parse
import argparse
from utils import fileutils
from masses import Masses
from model import Model

# Plot class
class Plot:

    def __init__(self,
                 decay,
                 masses: 'Masses',
                 modelname):
        
        # Save arguments as class members
        self.decay = decay
        self.masses = masses
        self.model = Model(modelname)

        # Get list of .tsv files
        self.getFileNames()

        # Load data from all of the .tsv files
        self.loadData()

    # Function to get list of .tsv files for plotting
    def getFileNames(self):

        # Empty array that will hold the files found
        self.all_files = []

        # Directory for the scan outputs
        directory = fileutils.scanDir(modelname=self.model.name,decay=self.decay,masses=self.masses) + "files/"

        # Iterate through the directory
        for file_name in os.listdir(directory):

            # Check if the file is a .tsv file, if it is, append to the list
            if ".tsv" in file_name:
                self.all_files.append(directory + file_name)

        # Sort the array so files are in order
        self.all_files.sort()

        # If prescan exists, make it the first file to plot
        prescan = fileutils.prescanTSV(modelname=self.model.name,masses=self.masses)
        if os.path.exists(prescan):
            self.all_files.insert(0, prescan)

        # Store number of files for easy access
        self.nfiles = len(self.all_files)
    
    def loadData(self):

        # Retrieve the variable names for the model
        self.var_names = self.model.parameterList()

        # Check if xb exists in the variable name list, if not append
        if 'xb' not in self.var_names:
            self.var_names.append('xb')

        # Get number of variables for easy access
        self.nvars = len(self.var_names)

        # Initialize list that will hold all the maximum points for each file iteration
        self.maxpoint_list = []

        # Initialize a dictionary to store lists of numpy arrays
        self.var_list = {}

        # Iterate through each file
        for file in self.all_files:

            # Retrieve the variables from the list
            parser = parse.Parse(filename=file, masses=self.masses, decay=self.decay, modelname=self.model.name) 
            allParams = parser.getParameters()
            xb = parser.getXB(self.decay)

            # Retrieve maximum point based on the file's variables
            maxpoint = parser.getMaxPoint()

            #Iterate through the information of each paramater
            for name, par in allParams.items():
            # Ensure the variable list exists for the parameter name
                
                #Check the paramater name
                if name not in self.var_list:
                    self.var_list[name] = []

                # Append the variable value to the corresponding list
                self.var_list[name].append(par)
                
            # Check if xb exists in the variable list
            if 'xb' not in self.var_list:
                self.var_list['xb'] = []

            # Append xb to the corresponding list
            self.var_list['xb'].append(xb)

            # Append the maximum point to the list
            self.maxpoint_list.append(maxpoint)
        return

    # Plot multiple function with the help of AI -- find a way to make the process more efficient and faster !!
    def makeScanPlots(self):
        
        #Create plot output directory
        output_dir = fileutils.plotsDir(modelname=self.model.name,decay=self.decay,masses=self.masses)
        os.makedirs(output_dir, exist_ok=True)
        
        # Find the Maximum point from the maximum points
        maximum = max(self.maxpoint_list)

        # Set the start and end colors by random RGB values
        start_rgb, end_rgb = select_colors()

        # Iterate through the list of all variables to plot each variable combination from each file
        for v in range(self.nvars-1):

            var1 = self.var_list[self.var_names[v]] #Get the first variable 2D-list from the all variable list
            
            for j in range(v+1, self.nvars):

                var2 = self.var_list[self.var_names[j]] #Get the second variable 2D-List from the all variable list

                # Set the opacity to be between values 0.19 and 1 depending on the number of files
                op = (0.8 / self.nfiles)
                opac = op + 0.19

                # Create a new scatter figure
                plt.figure()
        
                # Iterate through both variable 2D-Lists to plot the info from each file
                for i in range(len(self.var_list['xb'])):

                    # Decipher the color used for the scatterplot
                    t = i / self.nfiles
                    color = [start_rgb[c] + t * (end_rgb[c] - start_rgb[c]) for c in range(3)]

                    # Plot the variables by file
                    plt.scatter(var1[i], var2[i], s=15, color=color, alpha=opac)
                    
                    # Adjust the opacity
                    opac+=op 

                # Reset opacity for star points
                opac = op
                opac += 0.19
                
                for q in range(len(self.var_list['xb'])):

                    # Initialize both variables to be retrieved from the Point
                    variable1 = self.var_names[v]
                    variable2 = self.var_names[j]

                    # Get and store the max points for each variable
                    point1 = self.maxpoint_list[q].getVal(variable1)
                    point2 = self.maxpoint_list[q].getVal(variable2)

                    # Plot the max point from the scatterplot [star]
                    if(self.maxpoint_list[q] != maximum): #Make sure the point is not the maximum point
                        plt.scatter(point1, point2, s=25, color="yellow", alpha=opac, marker="*") #plot normally
                    else: #If point is maximum point plot as a bigger star
                        plt.scatter(point1, point2, s=60, color="gold", alpha=0.999, marker="*")

                    # Adjust the opacity
                    opac+=op

                # Initialize scatterplot labels
                plt.title(f"{self.var_names[v]} vs {self.var_names[j]}")
                plt.xlabel(f"{self.var_names[v]}")
                plt.ylabel(f"{self.var_names[j]}")

                # Save the figure as a .png
                plt.savefig(output_dir + f"{self.var_names[v]}_vs_{self.var_names[j]}.png")

                # Close the figure
                plt.close()

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

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-D", "--Decay", required=True, type=str)
    argparser.add_argument("-X", "--XMass", required=True, type=float)
    argparser.add_argument("-S", "--SMass", required=True, type=float)
    argparser.add_argument("-H", "--HMass", default=125.09, type=float)
    argparser.add_argument("-M", "--model", default="TRSMBroken", type=str)
    args = argparser.parse_args()

    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    plotter = Plot(decay=args.Decay, masses=masses, modelname=args.model)
    plotter.makeScanPlots()