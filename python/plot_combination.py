#!/usr/bin/env python3

import argparse
import os
import numpy as np
import pandas as pd
import scipy.interpolate as spi
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from utils.env_utils import output_dir

def plot_combination(model :str,
                     decay: str,
                     identifier: str) -> None:

    plot_xb_max(model=model, decay=decay, identifier=identifier)
    
def plot_xb_max(model: str,
                decay: str,
                identifier: str) -> None:

    filename = os.path.join(output_dir(), model, "scan", decay, f"{decay}_{identifier}_combination.tsv")

    # Load data from the TSV file
    x_values, y_values, z_values = load_data(filename)

    xi = np.linspace(min(x_values), max(x_values), 231)
    yi = np.linspace(min(y_values), max(y_values), 100)
    Xi, Yi = np.meshgrid(xi, yi)

    Zi = spi.griddata((x_values, y_values), z_values, (Xi, Yi), method='linear')

    fig = plt.figure()
    ax = fig.add_subplot(111)
    contour = ax.contourf(Xi, Yi, Zi, levels=30, norm=mcolors.LogNorm(), cmap='viridis')

    ax.set_xlabel('XMass')
    ax.set_ylabel('SMass')

    #scatter = ax.scatter(x_values, y_values, c=z_values, norm=mcolors.LogNorm(), cmap='viridis')

    cbar = plt.colorbar(contour)
    cbar.set_label('Max xb')

    output_directory = os.path.join(output_dir(), model, "plots", decay, "combination")
    output_filename = os.path.join(output_directory, f"{decay}_{identifier}_combination.png")
    os.makedirs(output_directory, exist_ok=True)
    fig.savefig(output_filename)

def load_data(file_path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load XMass, SMass, and MaxXB from a TSV file using column names.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        tuple: Three numpy arrays containing XMass, SMass, and MaxXB.

    Raises:
        RuntimeError: If the file cannot be read or parsed correctly.
    """
    try:
        df = pd.read_csv(file_path, sep='\t')
        required_cols = {'XMass', 'SMass', 'xbmax'}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"TSV file must contain columns: {required_cols}")
        
        x = df['XMass'].to_numpy()
        y = df['SMass'].to_numpy()
        z = df['xbmax'].to_numpy()
        return x, y, z

    except Exception as e:
        raise RuntimeError(f"Failed to read or parse data from {file_path}: {e}")

if __name__ =="__main__":

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Identifier")
    args = arg_parser.parse_args()

    plot_combination(model = args.model,
                     decay=args.decay,
                     identifier=args.identifier)
