
import os
from pathlib import Path
from jinja2 import Template

def htcondor_dir() -> str:
    """
    Get path to htcondor directory.
    """
    return os.environ['HTCONDOR_DIR']

def templates_dir() -> Path:
    """
    Returns the directory where HTCondor templates are stored.
    """
    return Path(htcondor_dir()) / "templates"

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

def render_template(template_file: Path, context: dict) -> str:
    with open(template_file) as f:
        return Template(f.read()).render(context)

job_lengths = {
    'espresso': '00:20:00',
    'microcentury': '01:00:00',
    'longlunch': '02:00:00',
    'workday': '08:00:00',
    'tomorrow': '24:00:00',
    'testmatch': '72:00:00',
    'nextweek': '168:00:00'
}