#!/usr/bin/env python3

import argparse
import multiprocessing as mp
from tqdm import tqdm
from typing import Dict, List, Tuple

from utils.cpu_utils import get_n_cpus
from mass_grid.mass_json_utils import get_mass_permutations
from utils.model import Model, supported_models
from plot.plot_combination import CombinationPlotter
from plot.plot_meanshift import MeanShiftPlotter
from plot.plot_zoom import ZoomPlotter

def plot_mass_point(args: Tuple[float, float, float, str, str, str]) -> None:
    """
    Plot scan results for a single mass point using the specified strategy.

    Args:
        args: A tuple containing:
            - xmass (float): X scalar mass
            - smass (float): S scalar mass
            - hmass (float): H scalar mass
            - decay (str): Decay mode
            - model_name (str): Model name
            - strategy (str): Optimization strategy ('zoom' or 'meanshift')
    """
    xmass, smass, hmass, decay, model_name, strategy = args
    model = Model(name=model_name, masses={"H": hmass, "S": smass, "X": xmass})
    try:
        if strategy == "zoom":
            zoom_plotter = ZoomPlotter(decay=decay, model=model)
            zoom_plotter.make_scan_plots()
            zoom_plotter.make_max_xb_plots()
        elif strategy == "meanshift":
            meanshift_plotter = MeanShiftPlotter(model=model, decay=decay)
            meanshift_plotter.make_mean_shift_plots()
    except Exception as e:
        print(f"Error while plotting {model.mass_string}: {e}")

def get_calculable_mass_points(model_name: str,
                               permutations: List[Tuple[int, int, bool, Dict[str, float]]],
                               hmass: float) -> List[Tuple[int, int, float]]:
    """
    Filter a list of mass permutations to return only calculable mass points.

    Args:
        model_name (str): Name of the scalar model.
        permutations (List[Tuple[int, int, bool, Dict[str, float]]]): List of (X, S, is_excluded, metadata_dict) tuples.
        hmass (float): Mass of the H scalar (fixed across permutations).

    Returns:
        List of (X, S, H) mass tuples that are valid for plotting.
    """
    valid_points = []
    for x, s, _, _ in permutations:
        model = Model(name=model_name, masses={"H": hmass, "S": s, "X": x})
        if model.is_calculable:
            valid_points.append((x, s, hmass))
    return valid_points

def main() -> None:
    """
    Main CLI entry point for plotting scalar model scan results.

    Supports:
        - Plotting individual mass points with zoom or meanshift
        - Plotting interpolated combination grids
        - Running both or either mode in parallel or sequentially

    Uses argparse to configure behavior.
    """
    arg_parser = argparse.ArgumentParser(
        description="Plot scalar model scan results for mass points and/or combination grids.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    arg_parser.add_argument("-l", "--use-mass-list", action="store_true", help="Run over a mass list instead of a single mass point")
    arg_parser.add_argument("-X", "--XMass", type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-i", "--identifier", type=str, help="Mass set identifier")
    arg_parser.add_argument("-m", "--model", default="TRSMBroken", type=str, choices=supported_models, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", default="zoom", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    arg_parser.add_argument("--no-sigma-bands", action="store_true", help="Do not plot ±1σ and ±2σ expected contours")
    arg_parser.add_argument("--no-plot-limits", action="store_true", help="Do not produce exclusion limits plots")
    arg_parser.add_argument("--log-x", action="store_true", help="Use logarithmic scale for the X mass axis")
    arg_parser.add_argument("--log-y", action="store_true", help="Use logarithmic scale for the S mass axis")
    arg_parser.add_argument("--log-axes", action="store_true", help="Use logarithmic scale for both axes (equivalent to --log_x --log_y)")
    arg_parser.add_argument("--only", choices=["masspoints", "combination"],
        help="Restrict to only plotting individual mass points or the interpolated combination plot (default: both)"
    )
    args = arg_parser.parse_args()

    log_x = args.log_x or args.log_axes
    log_y = args.log_y or args.log_axes

    do_plot_masspoints = False
    do_plot_combination = False

    # Check arguments
    if args.XMass and args.SMass:
        if args.only == "combination":
            raise ValueError("Combination plotting requires a mass list (-l/--use-mass-list).")
        do_plot_masspoints = True

    elif args.use_mass_list:
        if not args.identifier:
            raise ValueError("Identifier (-i/--identifier) is required with -l/--use-mass-list.")
        do_plot_combination = args.only in (None, "combination")
        do_plot_masspoints = args.only in (None, "masspoints")

    else:
        raise ValueError("Please specify either a mass point (-X/--XMass and -S/--SMass) or -l/--use-mass-list.")

    # Plot combination if requested
    if do_plot_combination:
        print(f"\nMaking combination plots for identifier '{args.identifier}' and decay '{args.decay}'")
        combo_plotter = CombinationPlotter(
            model=args.model,
            decay=args.decay,
            identifier=args.identifier,
            plot_limits=not args.no_plot_limits,
            include_sigma_bands=not args.no_sigma_bands,
            log_x=log_x,
            log_y=log_y
        )
        combo_plotter.make_combination_plots()

    # Plot mass points if requested
    if do_plot_masspoints:
        mass_points = []
        if args.use_mass_list:
            print(f"\nMaking mass point plots for identifier '{args.identifier}' and decay '{args.decay}'")
            permutations = get_mass_permutations(decay=args.decay, identifier=args.identifier)
            mass_points = get_calculable_mass_points(model_name=args.model,
                                                     permutations=permutations,
                                                     hmass=args.HMass)
            skipped = len(permutations) - len(mass_points)
            if skipped > 0:
                print(f"Skipping {skipped} non-calculable mass points.")
            if not mass_points:
                print("No calculable mass points found. Skipping mass point plots.")
                return
            print(f"Loaded {len(mass_points)} mass points")

        elif args.XMass and args.SMass:
            print(f"\nMaking mass point plots for mX = {args.XMass}, mS = {args.SMass} and decay '{args.decay}'")
            model = Model(name=args.model, masses={"H": args.HMass, "S": args.SMass, "X": args.XMass})
            if not model.is_calculable:
                print(f"Single point X={args.XMass}, S={args.SMass} is not calculable. Exiting.")
                return
            mass_points = [(args.XMass, args.SMass, args.HMass)]

        args_list = [(x, s, h, args.decay, args.model, args.strategy) for (x, s, h) in mass_points]
        if args_list:
            with mp.Pool(processes=get_n_cpus()) as pool:
                for _ in tqdm(pool.imap_unordered(plot_mass_point, args_list), total=len(args_list)):
                    pass

if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()
