#!/usr/bin/env python3

import subprocess
import os
from pathlib import Path
from jinja2 import Template

from utils.env_utils.py import htcondor_dir

TEMPLATES_DIR = Path(htcondor_dir()) / "templates"
LOGS_DIR = Path(htcondor_dir()) / "logs"
SUBMISSIONS_DIR = Path(htcondor_dir()) / "submissions"

def render_template(template_file: Path, context: dict) -> str:
    with open(template_file) as f:
        return Template(f.read()).render(context)

def make_dirs() -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    SUBMISSIONS_DIR.mkdir(exist_ok=True)

def submit_single_mass(xmass: float, smass: float):
    job_name = f"job_{xmass}_{smass}"

    make_dirs()

    # Paths
    job_script_path = SUBMISSIONS_DIR / f"{job_name}.sh"
    submit_file_path = SUBMISSIONS_DIR / f"{job_name}.sub"

    # Render shell script
    job_script = render_template(TEMPLATES_DIR / "job_template.sh.j2", {"xmass": xmass, "smass": smass})
    job_script_path.write_text(job_script)
    job_script_path.chmod(0o755)

    # Render condor submit file
    submit_file = render_template(
        TEMPLATES_DIR / "submit_template.sub.j2",
        {"xmass": xmass, "smass": smass, "job_script": job_script_path.name}
    )
    submit_file_path.write_text(submit_file)

    # Submit the job
    subprocess.run(["condor_submit", str(submit_file_path)], check=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--xmass", type=float, required=True)
    parser.add_argument("--smass", type=float, required=True)
    args = parser.parse_args()
    submit_single_mass(args.xmass, args.smass)
