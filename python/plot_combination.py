import numpy as np
import scipy.interpolate as spi
import matplotlib.pyplot as plt # type: ignore
import matplotlib.colors as mcolors
from utils.env_utils import output_dir
import argparse 
import os

def plot_combination(model:str,
                     decay:str,
                     identifier:str):
   
    filename = f'{output_dir()}/{model}/scan/{decay}/{decay}_{identifier}_combination.tsv'
    columns = np.genfromtxt(filename, delimiter='\t' , skip_header=1)
    

    x_values = columns[:,0]
    y_values = columns[:,1]
    z_values = columns[:,3]

    xi = np.linspace(min(x_values), max(x_values), 231)
    yi = np.linspace(min(y_values), max(y_values), 100)
    Xi, Yi = np.meshgrid(xi, yi)

    Zi = spi.griddata((x_values, y_values), z_values, (Xi, Yi), method='linear')

    fig = plt.figure()
    ax = fig.add_subplot(111)
    contour = ax.contourf(Xi, Yi, Zi, levels=30, norm=mcolors.LogNorm(), cmap='viridis')


    ax.set_xlabel('XMass')
    ax.set_ylabel('SMass')



    scatter = ax.scatter(x_values, y_values, c=z_values,norm=mcolors.LogNorm(), cmap='viridis')

    cbar = plt.colorbar(scatter)
    cbar.set_label('Max xb')


    ax.legend
    output_directory  = f'{output_dir()}/{model}/plots/{decay}'
    output_filename  = f'{output_directory}/{decay}_{identifier}_combination.png'
    os.makedirs(output_directory, exist_ok=True)
    fig.savefig(output_filename)

if __name__ =="__main__":
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Identifier")
    args = arg_parser.parse_args()
    plot_combination(model = args.model, decay=args.decay, identifier=args.identifier)