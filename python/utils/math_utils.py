
# third-party libraries
from sigfig import round

def round_sig(val: float,
              sig_figs: int = 3) -> float:
    """
    Rounds a given value to a specified number of significant figures.
    If the value is close to 0 (within a given tolerance), it returns 0 directly.

    Args:
        val (float): The number to be rounded.
        sig_figs (int): The number of significant figures to round to (default is 3).

    Returns:
        The rounded value, or 0 if the input value is close to 0.
    """
    if abs(val) < 1e-12:
        return 0.0
    return round(val, sigfigs = sig_figs)
