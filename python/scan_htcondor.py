#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path
from jinja2 import Template

from utils.env_utils import htcondor_dir, env_sh

TEMPLATES_DIR = Path(htcondor_dir()) / "templates"

def logs_dir(model: str,
             decay: str) -> Path:
    """
    Returns the directory where HTCondor logs are stored.
    """
    return Path(htcondor_dir()) / "logs" / model / decay

def submissions_dir(model: str,
                    decay: str) -> Path:
    """
    Returns the directory where HTCondor submission files are stored.
    """
    return Path(htcondor_dir()) / "submissions" / model / decay

def render_template(template_file: Path, context: dict) -> str:
    with open(template_file) as f:
        return Template(f.read()).render(context)

def make_dirs(model: str,
              decay: str) -> None:
    (logs_dir(model, decay) / "out").mkdir(parents=True, exist_ok=True)
    (logs_dir(model, decay) / "log").mkdir(parents=True, exist_ok=True)
    (logs_dir(model, decay) / "err").mkdir(parents=True, exist_ok=True)
    submissions_dir(model, decay).mkdir(parents=True, exist_ok=True)

def scan_htcondor(model: str,
                  xmass: float,
                  smass: float,
                  decay: str,
                  strategy: str,
                  num_points: int,
                  num_cpus: int,
                  job_length: str) -> None:

    job_name = f"scan_{model}_{decay}_X{int(xmass)}_S{int(smass)}"

    make_dirs(model, decay)

    # Paths
    job_script_path = submissions_dir(model, decay) / f"{job_name}.sh"
    submit_file_path = submissions_dir(model, decay) / f"{job_name}.sub"

    # Render shell script
    job_script = render_template(TEMPLATES_DIR / "scan_template.sh.j2", {"xmass": xmass,
                                                                         "smass": smass,
                                                                         "model": model,
                                                                         "decay": decay,
                                                                         "strategy": strategy,
                                                                         "npoints": num_points})
    job_script_path.write_text(job_script)
    job_script_path.chmod(0o755)

    # Make list of input files needed for the job
    input_files = [env_sh()]

    # Render condor submit file
    submit_file = render_template(
        TEMPLATES_DIR / "submit_template.sub.j2",
        {"job_script": job_script_path,
         "logs_dir": logs_dir(model, decay),
         "job_name": job_name,
         "input_files": input_files,
         "num_cpus": num_cpus,
         "job_length": job_length}
    )
    submit_file_path.write_text(submit_file)

    print(f"Submitting HTCondor job: {job_name}")

    # Submit the job
    subprocess.run(["condor_submit", str(submit_file_path)], check=True)

if __name__ == "__main__":

    job_lengths = {
        'espresso': '00:20:00',
        'microcentury': '01:00:00',
        'longlunch': '02:00:00',
        'workday': '08:00:00',
        'tomorrow': '24:00:00',
        'testmatch': '72:00:00',
        'nextweek': '168:00:00'
    }

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    arg_parser.add_argument("-n", "--num_points", default=10000, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-c", "--num_cpus", default=8, type=int, help="Number of CPUs to request for the job")
    arg_parser.add_argument("-l", "--job_length", default='microcentury', type=str, choices=job_lengths.keys(), help="HTCondor job length strategy")
    args = arg_parser.parse_args()

    scan_htcondor(model=args.model,
                  xmass=args.XMass,
                  smass=args.SMass,
                  decay=args.decay,
                  strategy=args.strategy,
                  num_points=args.num_points,
                  num_cpus=args.num_cpus,
                  job_length=args.job_length)
