
# third-party libraries
from sigfig import round

def round_sig(val: float,
              sig_figs: int = 3) -> float:
    return round(val, sigfigs = sig_figs)
