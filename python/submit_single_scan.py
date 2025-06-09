#!/usr/bin/env python3

import argparse
import subprocess
from pathlib import Path
from jinja2 import Template

from utils.env_utils import htcondor_dir

TEMPLATES_DIR = Path(htcondor_dir()) / "templates"
LOGS_DIR = Path(htcondor_dir()) / "logs"
SUBMISSIONS_DIR = Path(htcondor_dir()) / "submissions"

def render_template(template_file: Path, context: dict) -> str:
    with open(template_file) as f:
        return Template(f.read()).render(context)

def make_dirs() -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    SUBMISSIONS_DIR.mkdir(exist_ok=True)

def submit_single_mass(model: str,
                       xmass: float,
                       smass: float,
                       decay: str,
                       strategy: str,
                       num_points: int) -> None:
    job_name = f"job_{model}_{decay}_{xmass}_{smass}"

    make_dirs()

    # Paths
    job_script_path = SUBMISSIONS_DIR / f"{job_name}.sh"
    submit_file_path = SUBMISSIONS_DIR / f"{job_name}.sub"

    # Render shell script
    job_script = render_template(TEMPLATES_DIR / "job_template.sh.j2", {"xmass": xmass,
                                                                        "smass": smass,
                                                                        "model": model,
                                                                        "decay": decay,
                                                                        "strategy": strategy,
                                                                        "npoints": num_points})
    job_script_path.write_text(job_script)
    job_script_path.chmod(0o755)

    # Render condor submit file
    submit_file = render_template(
        TEMPLATES_DIR / "submit_template.sub.j2",
        {"job_script": job_script_path.name,
         "logs_dir": LOGS_DIR,
         "model": model,
         "xmass": xmass,
         "smass": smass,
         "decay": decay}
    )
    submit_file_path.write_text(submit_file)

    # Submit the job
    subprocess.run(["condor_submit", str(submit_file_path)], check=True)

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    arg_parser.add_argument("-n", "--num_points", default=10000, type=int, help="Initial number of scan points")
    args = arg_parser.parse_args()

    submit_single_mass(model=args.model,
                       xmass=args.XMass,
                       smass=args.SMass,
                       decay=args.decay,
                       strategy=args.strategy,
                       num_points=args.num_points)
