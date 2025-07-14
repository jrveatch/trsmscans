#!/usr/bin/env python3

"""
run_process.py

Unified entry point for running prescan or scan jobs on the TRSM model,
either locally or via HTCondor. Supports grid scanning, logging, and dry-run mode.

Usage examples:
    python run_process.py --mode scan -X 600 -S 300 -m TRSMBroken -d SHbbbb -s zoom -n 1000
    python run_process.py --mode scan --batch -l -i CMS -m TRSMBroken -d SHbbbb -s zoom -n 5000
"""

import argparse
import os
import subprocess
from typing import Optional

# import logging utils first to ensure no messages are lost
import utils.logging_utils as logging_utils

from utils.env_utils import env_sh
from utils.file_utils import prescan_dir, scan_dir
from utils.metadata_utils import get_mass_point_status
from prescan.prescan import prescan
from scan.scan import Scan
from utils.model import Model, supported_models
from utils.precision_utils import Precision
import utils.htcondor_utils as htcondor_utils
from mass_grid.mass_json_utils import get_mass_permutations

def run_prescan(model: Model,
                num_points: int,
                overwrite: bool,
                dry_run: bool = False) -> None:
    """
    Run a prescan for a single mass point.

    Args:
        model (Model): The scalar model to scan.
        num_points (int): Number of points to sample.
        overwrite (bool): Whether to overwrite existing results.
        dry_run (bool): If True, print message but do not run job.
    """

    if dry_run:
        print(f"[DRY-RUN] Would run: prescan for {model.mass_string}")
        return None

    prescan(model=model,
            num_points=num_points,
            overwrite=overwrite)

def run_scan(model: Model,
             decay: str,
             strategy: str,
             num_points: int,
             prescan_points: int,
             iterations: int,
             precision: Optional[Precision] = None,
             limit_target: float = -1.0,
             dry_run: bool = False) -> None:
    """
    Run a scan (zoom or meanshift) for a single mass point.

    Args:
        model (Model): The scalar model to scan.
        decay (str): The decay mode (e.g., 'SAA').
        strategy (str): Optimization strategy ('zoom' or 'meanshift').
        num_points (int): Number of points to start the scan.
        prescan_points (int): Number of prescan points to use.
        iterations (int): Max number of scan iterations or shifters.
        precision (Optional[Precision]): Precision level for optimization.
        limit_target (float): The target experimental limit for setting precision.
        dry_run (bool): If True, print message but do not run job.

    Raises:
        ValueError: If the strategy is invalid.
    """

    if dry_run:
        print(f"[DRY-RUN] Would run: scan for {model.mass_string} using {strategy}")
        return None

    scan = Scan(model=model,
                decay=decay,
                prescan_points=prescan_points,
                precision=precision,
                limit_target=limit_target)

    if strategy == "zoom":
        scan.run_zoom_optimization(num_points=num_points, niter=iterations)
    elif strategy == "meanshift":
        scan.run_ms_optimization(num_optimizers=iterations)
    else:
        raise ValueError(f"Invalid strategy: {strategy}")

def submit_htcondor(mode: str,
                    model: Model,
                    num_points: int,
                    num_cpus: int,
                    job_length: str,
                    decay: Optional[str] = None,
                    strategy: Optional[str] = None,
                    xmass: float = -1.0,
                    smass: float = -1.0,
                    precision: Optional[Precision] = None,
                    limit_target: float = -1.0,
                    prescan_points: int = -1,
                    iterations: int = -1,
                    force_rerun: bool = False,
                    dry_run: bool = False) -> None:
    """
    Generate and optionally submit an HTCondor job for prescan or scan.

    Args:
        mode (str): Either 'prescan' or 'scan'.
        model (Model): The scalar model being scanned.
        num_points (int): Number of starting points for scan or prescan.
        num_cpus (int): Number of CPUs to request.
        job_length (str): Job runtime class (e.g., 'microcentury').
        decay (Optional[str]): Decay mode (required for scan).
        strategy (Optional[str]): Optimization strategy (required for scan).
        xmass (float): X scalar mass in GeV.
        smass (float): S scalar mass in GeV.
        precision (Optional[Precision]): Precision level for optimization.
        limit_target (float): The target experimental limit for setting precision.
        prescan_points (int): Number of prescan points to use for scan.
        iterations (int): Iteration count for optimizer.
        force_rerun (bool): Force a new run, overwriting the previous results.
        dry_run (bool): If True, write scripts but do not submit job.

    Side Effects:
        - Writes `.sh` and `.sub` files to submission directories.
        - Optionally submits job via `condor_submit`.
        - Creates log and submission directories if needed.
    """

    job_name = f"{mode}_{model.name}_{decay if mode == 'scan' else mode}_X{int(xmass)}_S{int(smass)}"

    submissions_dir = htcondor_utils.submissions_dir(model.name, mode, decay)

    # Ensure directories exist
    htcondor_utils.make_dirs(model.name, mode, decay)

    # Delete old log files if it exists
    htcondor_utils.delete_log_file(model=model.name,
                                   job_name=job_name,
                                   mode=mode,
                                   decay=decay)

    # Shell script path and content
    sh_file = submissions_dir / f"{job_name}.sh"
    sub_file = submissions_dir / f"{job_name}.sub"

    # Get htcondor templates
    sh_template = htcondor_utils.templates_dir() / "process_template.sh.j2"
    sub_template = htcondor_utils.templates_dir() / "submit_template.sub.j2"

    sh_lines = [
        "run_process.py \\",
        f"    --mode {mode} \\",
        f"    -X {xmass} -S {smass} -H {model.masses['H']} \\",
        f"    -m {model.name} -n {num_points} \\",
    ]

    # Add scan-specific options
    if mode == "scan":
        sh_lines.append(f"    -d {decay} \\")
        sh_lines.append(f"    -s {strategy} \\")
        sh_lines.append(f"    --prescan-points {prescan_points} \\")
        if precision is not None:
            sh_lines.append(f"    -p {precision.name.lower()} \\")
        sh_lines.append(f"    --limit-target {limit_target} \\")
        if strategy == "meanshift":
            sh_lines.append(f"    -t {iterations} \\")
    if force_rerun:
        sh_lines.append("    --force_rerun \\")
    
    # Remove trailing backslash from the last line
    sh_lines[-1] = sh_lines[-1].rstrip(" \\")

    # Render shell script
    job_script = htcondor_utils.render_template(
        sh_template,
        {"command": sh_lines}
    )
    
    # Write the shell script to file
    sh_file.write_text(job_script)
    sh_file.chmod(0o755)

    # Make list of input files needed for the job
    input_files = [env_sh()]

    # Render condor submit file
    submit_file = htcondor_utils.render_template(
        sub_template,
        {"job_script": str(sh_file),
         "logs_dir": htcondor_utils.logs_dir(model.name, mode, decay),
         "job_name": job_name,
         "input_files": input_files,
         "num_cpus": num_cpus,
         "job_length": job_length}
    )
    sub_file.write_text(submit_file)

    # Submit the job
    if not dry_run:
        print(f"[HTCONDOR] Submitting {sub_file}")
        subprocess.run(["condor_submit", str(sub_file)], check=True)
    else:
        print(f"[DRY-RUN] Would submit: condor_submit {sub_file}")

def main():
    """
    Entry point for the CLI interface. Parses command-line arguments and dispatches
    to either local execution or HTCondor submission based on flags.

    Supported modes:
        - prescan (interactive or batch)
        - scan (zoom or meanshift; interactive or batch)
    
    Mass points may be specified via:
        - Single point: --XMass and --SMass
        - Mass list: --use-mass-list and --identifier

    Raises:
        ValueError: If required arguments are missing or invalid combinations are used.
    """

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("--mode", type=str, choices=["scan", "prescan"], required=True, help="Mode of operation: 'scan' or 'prescan'")
    arg_parser.add_argument("-b", "--batch", action="store_true", help="Submit to HTCondor instead of running interactively")
    arg_parser.add_argument("-l", "--use-mass-list", action="store_true", help="Run over a mass list instead of a single mass point")
    arg_parser.add_argument("-X", "--XMass", type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-i", "--identifier", type=str, help="Mass set identifier")
    arg_parser.add_argument("-m", "--model", default="TRSMBroken", type=str, choices=supported_models, help="Model name")
    arg_parser.add_argument("-d", "--decay", type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", default="zoom", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    arg_parser.add_argument("-n", "--num-points", default=-1, type=int, help="Initial number of scan points")
    arg_parser.add_argument("--limit-target", default=-1.0, type=float, help="Target limit to determine precision on the fly")
    arg_parser.add_argument("--prescan-points", default=-1, type=int, help="Number of prescan points when using scan mode")
    arg_parser.add_argument("-t", "--iterations", default=-1, type=int, help="Maximum number of iterations/optimizers")
    arg_parser.add_argument("-c", "--num-cpus", default=8, type=int, help="Number of CPUs to request for the job")
    arg_parser.add_argument("-j", "--job-length", default='microcentury', type=str, choices=htcondor_utils.job_lengths.keys(),
                            help="HTCondor job length strategy")
    arg_parser.add_argument("--log-level", default="info", type=str.lower, choices=logging_utils.LOG_LEVELS.keys(), help="Set the logging level")
    arg_parser.add_argument("--dry-run", action="store_true", help="Print submission steps without running condor_submit")
    arg_parser.add_argument("-p", "--precision", type=Precision.from_string, choices=list(Precision), default=None,
                            help="Fix optimization precision level. If not set, precision is adapted automatically")
    arg_parser.add_argument("-r", "--rerun-precision", type=Precision.from_string, choices=list(Precision), default=None,
                            help="Rerun scan jobs if existing precision is below this level. Ignored for prescan or if --force-rerun is set")
    arg_parser.add_argument("-f", "--force-rerun", action="store_true", help="Force a rerun, overwriting previous results")
    args = arg_parser.parse_args()

    # Copy arguments into local variables
    mode: str = args.mode
    strategy: str = args.strategy
    decay: Optional[str] = args.decay
    identifier: Optional[str] = args.identifier
    num_points: int = args.num_points
    iterations: int = args.iterations
    HMass: float = args.HMass
    SMass: Optional[float] = args.SMass
    XMass: Optional[float] = args.XMass
    precision: Optional[Precision] = args.precision
    rerun_precision: Optional[Precision] = args.rerun_precision
    force_rerun: bool = args.force_rerun
    dry_run: bool = args.dry_run

    # Validate arguments
    if mode == "scan":
        if not decay:
            raise ValueError("Scan mode requires -d/--decay")
        if strategy == "zoom" and num_points <= 0:
            raise ValueError("Zoom strategy requires -n/--num_points to be greater than 0")
        if strategy == "meanshift" and iterations <= 0:
            raise ValueError("Mean shift strategy requires -t/--iterations to be greater than 0")

    # Load mass points
    if args.use_mass_list:
        if not decay:
            raise ValueError("Decay mode (-d/--decay) is required to run over a mass list")
        if not identifier:
            raise ValueError("Identifier (-i/--identifier) is required to run over a mass list")
        permutations = get_mass_permutations(decay=decay, identifier=identifier)
        mass_points = [(x, s, HMass, limits) for x, s, _, limits in permutations]
        print(f"Loaded {len(mass_points)} mass points from identifier '{identifier}' with decay '{decay}'")
    elif XMass is not None and SMass is not None:
        mass_points = [(XMass, SMass, HMass, {})]
    else:
        raise ValueError("Please specify either -l/--use-mass-list or provide -X/--XMass and -S/--SMass")

    job_count = 0
    skip_count = 0

    for xmass, smass, hmass, limits in mass_points:
        mass_string = f"X={xmass}, S={smass}"
        model = Model(name=args.model, masses={"H": hmass, "S": smass, "X": xmass})
        limit_target = min(limits.values()) if limits else args.limit_target
        if precision is None and limit_target < 0.0:
            raise ValueError("If no precision is set, a limit target must be provided, either from a .json file or using the --limit-target argument.")
        if mode == "scan" and not force_rerun:
            try:
                status, count, prev_precision = get_mass_point_status(
                    model=model,
                    decay=decay,
                    threshold=num_points,
                    mode=mode,
                    strategy=strategy
                )
            except Exception as e:
                print(f"[ERROR] Failed to evaluate {mass_string}: {e}")
                continue
            if status == "non_calculable":
                print(f"Skipping {mass_string} because it is not calculable")
                continue
            elif status == "missing":
                print(f"No previous scan found for {mass_string}: running")
            elif status == "below_threshold":
                print(f"Previous scan for {mass_string} only has {count} points (required: {num_points}): re-running")
            elif prev_precision is None:
                print(f"Previous scan for {mass_string} has no precision metadata: re-running")
            elif (
                rerun_precision is not None
                and prev_precision >= rerun_precision
                and prev_precision != Precision.SATURATED
            ):
                print(f"Previous scan for {mass_string} has precision {prev_precision} ≥ {rerun_precision}: re-running")
            else:
                print(f"Skipping {mass_string}: status = {status}, count = {count}, precision = {prev_precision}")
                skip_count += 1
                continue

        log_level = logging_utils.LOG_LEVELS[args.log_level.lower()]
        log_file = os.path.join(prescan_dir(model), "prescan.log")
        if mode == "scan":
            log_file = os.path.join(scan_dir(model=model, decay=decay), f"{strategy}.log")

        logging_utils.setup_logging(log_file=log_file,
                                    level=log_level)

        if args.batch:
            submit_htcondor(mode=mode,
                            model=model,
                            num_points=num_points,
                            num_cpus=args.num_cpus,
                            job_length=args.job_length,
                            decay=decay,
                            strategy=strategy,
                            xmass=xmass,
                            smass=smass,
                            precision=precision,
                            limit_target=limit_target,
                            prescan_points=args.prescan_points,
                            iterations=iterations,
                            force_rerun=force_rerun,
                            dry_run=dry_run)
            job_count += 1
        else:
            if mode == "prescan":
                run_prescan(model=model,
                            num_points=num_points,
                            overwrite=force_rerun,
                            dry_run=dry_run)
            else:
                run_scan(model=model,
                         decay=decay,
                         strategy=strategy,
                         num_points=num_points,
                         precision=precision,
                         limit_target=limit_target,
                         prescan_points=args.prescan_points,
                         iterations=iterations,
                         dry_run=dry_run)
            job_count += 1

    if job_count > 0:
        if args.use_mass_list:
            print(f"\nSuccessfully submitted {job_count} job{'s' if job_count > 1 else ''} for '{decay}' '{identifier}'")
            if skip_count > 0:
                print(f"Skipped {skip_count} calculable job{'s' if skip_count > 1 else ''}. "
                      "Use the -f/--force-rerun option to force them to be rerun.")
        else:
            print(f"\nSuccessfully processed job for X={XMass}, S={SMass}")
    if job_count == 0:
        print("\nNo jobs were submitted or executed. All mass points may already be processed.")

if __name__ == "__main__":
    main()
