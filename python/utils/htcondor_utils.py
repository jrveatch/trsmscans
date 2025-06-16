from jinja2 import Template
from pathlib import Path
from typing import Optional

from utils.env_utils import htcondor_dir

def templates_dir() -> Path:
    """
    Get the path to the HTCondor templates directory.

    Returns:
        Path: Path to the directory containing .j2 templates for job and submit files.
    """
    return Path(htcondor_dir()) / "templates"

def logs_dir(model: str,
             mode: str,
             decay: Optional[str] = None) -> Path:
    """
    Get the path to the HTCondor logs directory for a given model and job mode.

    For scan jobs: logs/{model}/{decay}/  
    For prescan jobs: logs/{model}/prescan/

    Args:
        model (str): Model name (e.g., "TRSMBroken").
        mode (str): Either "scan" or "prescan".
        decay (Optional[str]): Decay mode (e.g., "SAA"). Required if mode is "scan".

    Returns:
        Path: Path to the relevant logs directory.
    """
    return Path(htcondor_dir()) / "logs" / model / str(decay if mode == "scan" else mode)

def submissions_dir(model: str,
                    mode: str,
                    decay: Optional[str] = None) -> Path:
    """
    Get the path to the HTCondor submission directory for a given model and mode.

    For scan jobs: submissions/{model}/{decay}/  
    For prescan jobs: submissions/{model}/prescan/

    Args:
        model (str): Model name.
        mode (str): "scan" or "prescan".
        decay (Optional[str]): Decay mode (required if mode is "scan").

    Returns:
        Path: Path to the submissions directory.
    """
    return Path(htcondor_dir()) / "submissions" / model / str(decay if mode == "scan" else mode)

def render_template(template_file: Path,
                    context: dict) -> str:
    """
    Render a Jinja2 template file using the provided context.

    Args:
        template_file (Path): Path to the template (.j2) file.
        context (dict): Key-value pairs to populate the template.

    Returns:
        str: The rendered template content as a string.
    """
    with open(template_file) as f:
        return Template(f.read()).render(context)

def make_dirs(model: str,
              mode: str,
              decay: Optional[str] = None) -> None:
    """
    Create necessary HTCondor directory structure for logs and submissions.

    Directories created:
    - logs/{model}/{decay|prescan}/out
    - logs/{model}/{decay|prescan}/err
    - logs/{model}/{decay|prescan}/log
    - submissions/{model}/{decay|prescan}/

    Args:
        model (str): Model name.
        mode (str): "scan" or "prescan".
        decay (Optional[str]): Decay mode (used if mode is "scan").
    """
    (logs_dir(model, mode, decay) / "out").mkdir(parents=True, exist_ok=True)
    (logs_dir(model, mode, decay) / "err").mkdir(parents=True, exist_ok=True)
    (logs_dir(model, mode, decay) / "log").mkdir(parents=True, exist_ok=True)
    submissions_dir(model, mode, decay).mkdir(parents=True, exist_ok=True)

def delete_log_file(model: str,
                    job_name: str,
                    mode: str,
                    decay: Optional[str] = None) -> None:
    """
    Delete the HTCondor log file for a specific job, if it exists.

    This is useful to ensure a fresh `.log` file is created on re-submission.

    Args:
        model (str): Model name.
        job_name (str): Full job name prefix (used as log file basename).
        mode (str): "scan" or "prescan".
        decay (Optional[str]): Decay mode (used if mode is "scan").

    Side Effects:
        Deletes logs/{model}/{decay|prescan}/log/{job_name}.log if it exists.
    """
    log_file = logs_dir(model, mode, decay) / "log" / f"{job_name}.log"
    log_file.unlink(missing_ok=True)

#: Dictionary mapping HTCondor job flavors to their wall-time limits.
job_lengths = {
    'espresso': '00:20:00',       # Very short test jobs (max 20 min)
    'microcentury': '01:00:00',   # Typical short jobs (1 hour)
    'longlunch': '02:00:00',      # Moderate jobs (2 hours)
    'workday': '08:00:00',        # Day-long jobs (8 hours)
    'tomorrow': '24:00:00',       # Full-day jobs
    'testmatch': '72:00:00',      # 3-day jobs
    'nextweek': '168:00:00'       # Up to one week
}
