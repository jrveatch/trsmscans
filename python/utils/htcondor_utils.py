
from pathlib import Path
from jinja2 import Template

from utils.env_utils import htcondor_dir

def templates_dir() -> Path:
    """
    Return the directory containing HTCondor Jinja2 template files.

    Returns:
        Path: Path object pointing to the HTCondor templates directory.
    """
    return Path(htcondor_dir()) / "templates"

def logs_dir(model: str,
             decay: str) -> Path:
    """
    Construct the directory path where HTCondor log files will be stored.

    Args:
        model (str): Name of the model.
        decay (str): Decay mode.

    Returns:
        Path: Path object pointing to the logs directory for the given model and decay.
    """
    return Path(htcondor_dir()) / "logs" / model / decay

def submissions_dir(model: str,
                    decay: str) -> Path:
    """
    Construct the directory path for storing HTCondor submission files (.sh and .sub).

    Args:
        model (str): Name of the model.
        decay (str): Decay mode.

    Returns:
        Path: Path object pointing to the submissions directory for the given model and decay.
    """
    return Path(htcondor_dir()) / "submissions" / model / decay

def render_template(template_file: Path, context: dict) -> str:
    """
    Render a Jinja2 template file with the given context.

    Args:
        template_file (Path): Path to the .j2 template file.
        context (dict): Dictionary of key-value pairs to substitute into the template.

    Returns:
        str: Rendered template as a string.
    """
    with open(template_file) as f:
        return Template(f.read()).render(context)

def make_dirs(model: str,
              decay: str) -> None:
    """
    Create the directory structure required for HTCondor job submissions, including logs and submissions.

    Args:
        model (str): Name of the model.
        decay (str): Decay mode.

    Side Effects:
        Creates the following directories if they do not exist:
        - logs/{model}/{decay}/out
        - logs/{model}/{decay}/err
        - logs/{model}/{decay}/log
        - submissions/{model}/{decay}
    """
    (logs_dir(model, decay) / "out").mkdir(parents=True, exist_ok=True)
    (logs_dir(model, decay) / "log").mkdir(parents=True, exist_ok=True)
    (logs_dir(model, decay) / "err").mkdir(parents=True, exist_ok=True)
    submissions_dir(model, decay).mkdir(parents=True, exist_ok=True)

def delete_log_file(model: str,
                    decay: str,
                    job_name: str) -> None:
    """
    Delete the log file for a given job.

    Args:
        model (str): Name of the model.
        decay (str): Decay mode.
        job_name (str): Name of the job whose logs are to be deleted.

    Side Effects:
        Deletes the log file for the job.
    """
    log_file = logs_dir(model, decay) / "log" / f"{job_name}.log"
    log_file.unlink(missing_ok=True)

#: Dictionary mapping HTCondor job flavors to their wall-time limits.
job_lengths = {
    'espresso': '00:20:00',       # Short jobs (under 20 minutes)
    'microcentury': '01:00:00',   # Jobs ~1 hour
    'longlunch': '02:00:00',      # Medium jobs ~2 hours
    'workday': '08:00:00',        # Jobs that can run during a full workday
    'tomorrow': '24:00:00',       # Up to one day
    'testmatch': '72:00:00',      # Up to three days
    'nextweek': '168:00:00'       # Up to one week
}
