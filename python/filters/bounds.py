#!/usr/bin/env python3

"""
BoundsFilter class for applying HiggsBounds and HiggsSignals filters to scan data.

This module evaluates whether parameter scan points are allowed by experimental
constraints and SM-like signal strength criteria. It supports serial and parallel
execution and avoids multiprocessing pitfalls by creating unpicklable tool objects
inside each worker.
"""

# standard libraries
import multiprocessing as mp
from typing import Any, Dict, List, Tuple

# third-party libraries
import pandas as pd

# local modules
from utils.cpu_utils import get_n_cpus
from utils.df_utils import chunk_dataframe
import Higgs.predictions as HP
from filters.setup_higgs_tools import get_higgs_bounds, get_higgs_signals, get_higgs_predictions
from utils.model import Model

# get logger
import logging
logger = logging.getLogger(__name__)

SM_decays = ["WW", "ZZ", "Zgam", "gamgam", "gg", "bb", "tt", "ss", "cc", "mumu", "tautau"]

class BoundsFilter:
    """
    Applies HiggsBounds and HiggsSignals filters to scalar model scan data.

    This class coordinates the evaluation of parameter points using external
    tools, managing serial or parallel execution as needed.
    """

    def __init__(self,
                 model: Model,
                 min_chunk_size: int):
        """
        Initializes the BoundsFilter with a model and configures processing thresholds.

        Args:
            model (Model): The scalar model to evaluate.
            min_chunk_size (int): Minimum number of events for chunked data.

        Raises:
            KeyError: If configuration keys are missing.
            Exception: For other unexpected config loading failures.
        """
        self.model = model
        self.min_chunk_size = min_chunk_size

        self.HName = model.get_ordered_scalar_name("H")
        self.SName = model.get_ordered_scalar_name("S")
        self.XName = model.get_ordered_scalar_name("X")

        self.RH_name = "R11" if self.HName != "H2" else "R21"
        self.RS_name = "R21" if self.HName != "H2" else "R11"
        self.RX_name = "R31"

        self.mass_keys = {
            "H": f"m{self.HName}",
            "S": f"m{self.SName}",
            "X": f"m{self.XName}",
        }

        self.width_keys = {
            "H": f"w_{self.HName}",
            "S": f"w_{self.SName}",
            "X": f"w_{self.XName}",
        }

        self.rescale_keys = {
            "H": self.RH_name,
            "S": self.RS_name,
            "X": self.RX_name
        }

        self.br_SM_keys = {
            "H": [f"b_{self.HName}_{decay}" for decay in SM_decays],
            "S": [f"b_{self.SName}_{decay}" for decay in SM_decays],
            "X": [f"b_{self.XName}_{decay}" for decay in SM_decays],
        }

        self.bsm_keys = {
            "H": ("H2", "b_H2_H1H1") if self.HName == "H2" else None,
            "S": ("H2", "b_H2_H1H1") if self.SName == "H2" else None,
            "X": {
                ("H", "H"): f"b_H3_{self.HName}{self.HName}",
                ("S", "S"): f"b_H3_{self.SName}{self.SName}",
                ("S", "H"): "b_H3_H1H2",
            }
        }

    def apply(self,
              data: pd.DataFrame,
              header_bounds: str,
              header_signals: str,
              use_multiprocessing: bool = True) -> None:
        """
        Applies bounds and signal filters to a scan DataFrame.

        Adds two columns indicating pass/fail status for HiggsBounds and HiggsSignals.

        Args:
            data (pd.DataFrame): The scan data.
            header_bounds (str): Column name for HiggsBounds result.
            header_signals (str): Column name for HiggsSignals result.
            use_multiprocessing (bool): If True, enables parallel filtering.
        """
        n_workers = get_n_cpus() if use_multiprocessing else 1
        filt_bounds, filt_signals = self._run_processing(data, n_workers)
        data[header_bounds] = filt_bounds
        data[header_signals] = filt_signals

    def _run_processing(self,
                        df: pd.DataFrame,
                        n_workers: int) -> Tuple[List[int], List[int]]:
        """
        Internal method to handle serial or parallel filtering.

        Args:
            df (pd.DataFrame): The scan data.
            n_workers (int): Number of workers to use.

        Returns:
            Tuple[List[int], List[int]]: Filter pass/fail results for bounds and signals.
        """
        if len(df) < self.min_chunk_size or n_workers <= 1:
            return self.process_data(df)

        n_chunks = min(n_workers, max(1, len(df) // self.min_chunk_size))
        chunks = chunk_dataframe(df, n_chunks)

        logger.info(f"BoundsFilter running with {n_chunks} chunks")

        args = [(self.model, chunk, self.min_chunk_size) for chunk in chunks]
        with mp.Pool(n_chunks) as pool:
            results = pool.starmap(_process_chunk, args)

        filt_bounds, filt_signals = zip(*results)
        return ([x for sublist in filt_bounds for x in sublist],
                [x for sublist in filt_signals for x in sublist])

    def process_data(self,
                     df: pd.DataFrame) -> Tuple[List[int], List[int]]:
        """
        Static method to evaluate scan points using Higgs tools.

        Tool objects are created inside the method to avoid pickling issues
        when used with multiprocessing.

        Args:
            df (pd.DataFrame): Chunk of the scan data.
            model (Model): Scalar model to use for evaluation.

        Returns:
            Tuple[List[int], List[int]]: Binary results for HiggsBounds and HiggsSignals.
        """
        bounds = get_higgs_bounds()
        signals = get_higgs_signals()
        pred = get_higgs_predictions(self.model)
        signals_result_SM = signals(pred)

        H = pred.particle("H")
        S = pred.particle("S")
        X = pred.particle("X")

        filt_bounds: List[int] = []
        filt_signals: List[int] = []

        for idx, row in enumerate(df.itertuples(index=False)):
            # Use getattr to access columns via attribute names
            masses = {key: float(getattr(row, col)) for key, col in self.mass_keys.items()}
            widths = {key: float(getattr(row, col)) for key, col in self.width_keys.items()}
            rescalings = {key: float(getattr(row, col)) for key, col in self.rescale_keys.items()}

            # Use Series wrapper for extract methods (they expect pd.Series)
            br_SM = self._extract_SM_BRs(row)
            br_BSM = self._extract_BSM_BRs(row)

            logger.verbose('Scalar widths are:')
            logger.verbose(f'  H: {widths["H"]}')
            logger.verbose(f'  S: {widths["S"]}')
            logger.verbose(f'  X: {widths["X"]}')
            logger.verbose(f'Rescalings are {rescalings["H"]} {rescalings["S"]} {rescalings["X"]}')

            configure_particle(H, "H", masses, widths, rescalings, br_SM, br_BSM, adjust_ZZ=True)
            configure_particle(S, "S", masses, widths, rescalings, br_SM, br_BSM, adjust_ZZ=True)
            configure_particle(X, "X", masses, widths, rescalings, br_SM, br_BSM, adjust_ZZ=False)

            bounds_result = bounds(pred)
            signals_result = signals(pred)
            HS_allowed = signals_result - signals_result_SM < 4.0

            if logging.getLogger().isEnabledFor(logging.VERBOSE):
                print_bounds_result(bounds_result, idx, masses)
                logger.verbose(f"signals_result = {signals_result}")
                logger.verbose(f"HS_allowed = {HS_allowed}")

            filt_bounds.append(int(bounds_result.allowed))
            filt_signals.append(int(HS_allowed))

        return filt_bounds, filt_signals

    def _extract_SM_BRs(self,
                        row: Any) -> Dict[str, Dict[str, float]]:
        """
        Extracts SM branching ratios for each scalar from a scan row.

        Args:
            row (Any): A row from the scan DataFrame.

        Returns:
            Dict[str, Dict[str, float]]: A dictionary of the form:
                {
                    'H': {decay: BR, ...},
                    'S': {decay: BR, ...},
                    'X': {decay: BR, ...}
                }
        """
        get = getattr
        return {
            label: {
                decay: float(get(row, key))
                for decay, key in zip(SM_decays, self.br_SM_keys[label])
            }
            for label in ("H", "S", "X")
        }

    def _extract_BSM_BRs(self,
                         row: Any) -> Dict[str, Dict[Tuple[str, str], float]]:
        """
        Extracts BSM branching ratios (2-body decays) for each scalar from a scan row.

        Args:
            row (Any): A row from the scan DataFrame.

        Returns:
            Dict[str, Dict[Tuple[str, str], float]]: A dictionary of the form:
                {
                    'H': {('S', 'S'): BR, ...},
                    'S': {('H', 'H'): BR, ...},
                    'X': {('H', 'H'): BR, ('S', 'S'): BR, ('S', 'H'): BR, ...}
                }
        """
        get = getattr
        br_H: Dict[Tuple[str, str], float] = {}
        br_S: Dict[Tuple[str, str], float] = {}
        br_X: Dict[Tuple[str, str], float] = {}

        key_H = self.bsm_keys.get("H")
        if key_H is not None:
            _, key = key_H
            br_H[("S", "S")] = float(get(row, key))

        key_S = self.bsm_keys.get("S")
        if key_S is not None:
            _, key = key_S
            br_S[("H", "H")] = float(get(row, key))

        for decay, key in self.bsm_keys["X"].items():
            br_X[decay] = float(get(row, key))

        return {"H": br_H, "S": br_S, "X": br_X}

def _process_chunk(model: Model,
                   chunk: pd.DataFrame,
                   min_chunk_size: int) -> Tuple[List[int], List[int]]:
    temp_filter = BoundsFilter(model, min_chunk_size)
    return temp_filter.process_data(chunk)

def configure_particle(particle,
                       label: str,
                       masses: Dict[str, float],
                       widths: Dict[str, float],
                       rescalings: Dict[str, float],
                       BRs_SM: Dict[str, Dict[str, float]],
                       BRs_BSM: Dict[str, Dict[Tuple[str, str], float]],
                       adjust_ZZ: bool) -> None:
    """
    Sets mass, width, rescaling, and branching ratios for a given Higgs scalar.

    Args:
        particle: The scalar particle object (HiggsPredictions).
        label (str): One of "H", "S", "X".
        masses (Dict[str, float]): Dictionary of scalar masses.
        widths (Dict[str, float]): Dictionary of scalar widths.
        rescalings (Dict[str, float]): Rescaling factors per scalar.
        BRs_SM (Dict[str, float]): SM-like branching ratios.
        BRs_BSM (Dict[Tuple[str, str], float]): BSM branching ratios.
        adjust_ZZ (bool): Whether to normalize the ZZ BR if the total exceeds 1.
    """
    particle.setMass(masses[label])
    particle.setTotalWidth(widths[label])
    set_effective_couplings(particle, mass=masses[label], rescaling=rescalings[label])
    particle.setTotalWidth(widths[label]) # Reset BRs to avoid issues with BR > 1.0
    set_BRs(particle, BRs_SM=BRs_SM[label], BRs_BSM=BRs_BSM[label], adjust_ZZ=adjust_ZZ)

def set_effective_couplings(particle,
                            mass: float,
                            rescaling: float
                           ) -> None:
    """
    Sets effective couplings for a scalar particle using a mass-dependent prescription.

    Args:
        particle: The scalar object from HiggsPredictions.
        mass (float): Mass of the particle.
        rescaling (float): Rescaling factor (e.g., R11, R21, R31).
    """

    if mass < 150:
        HP.effectiveCouplingInput(particle, HP.scaledSMlikeEffCouplings(rescaling),reference="SMHiggsEW")
    else:
        HP.effectiveCouplingInput(particle, HP.scaledSMlikeEffCouplings(rescaling))

def set_BRs(particle,
            BRs_SM: Dict[str,float],
            BRs_BSM: Dict[Tuple[str,str],float],
            adjust_ZZ: bool
           ) -> None:
    """
    Sets the SM and BSM branching ratios for a scalar particle.

    Args:
        particle: The scalar object from HiggsPredictions.
        BRs_SM (Dict[str, float]): SM branching ratios (1-body decays).
        BRs_BSM (Dict[Tuple[str, str], float]): BSM branching ratios (2-body decays).
        adjust_ZZ (bool): Whether to adjust ZZ BR to normalize total width to 1.
    """

    # check total width and return if it is too small
    if particle.totalWidth() < 1e-11:
        return

    # keep track of the sum of BRs
    sum_BR = 0.0

    # reset SM BRs to 0 to start from a clean slate
    for decay in BRs_SM:
        particle.setBr(decay,0)

    # loop over SM decay modes
    for decay, BR in BRs_SM.items():

        # add SM BRs to sum
        sum_BR += BR

        logger.verbose(f"{decay}: {BR} Sum = {sum_BR}")

        # skip ZZ decay
        if adjust_ZZ and decay == "ZZ":
            continue

        # set SM BRs
        particle.setBr(decay,BR)

    # loop over BSM decay modes
    for decay, BR in BRs_BSM.items():

        # set BSM DRs
        particle.setBr(decay[0],decay[1],BR)

        # add BSM BRs to sum
        sum_BR += BR

        logger.verbose(f"{decay}: {BR} Sum = {sum_BR}")

    if adjust_ZZ:

        # original ZZ BR
        BR_ZZ = BRs_SM['ZZ']

        # if BR sum is too large, adjust ZZ BR
        if sum_BR > 1.0:
            BR_ZZ = BRs_SM['ZZ'] - sum_BR + 1.0

        logger.verbose(f"Adjusted ZZ: {BR_ZZ} Sum = {sum_BR - BRs_SM['ZZ'] + BR_ZZ}")

        # set ZZ BR
        particle.setBr('ZZ',BR_ZZ)

def print_bounds_result(bounds_result,
                        idx: int,
                        masses: Dict[str, float]) -> None:
    """
    Prints verbose details for bounds violations, including excluded limits.

    Args:
        bounds_result: Result object from HiggsBounds.
        idx (int): Row index in the scan.
        masses (Dict[str, float]): Masses of the scalars.
    """

    logger.verbose(bounds_result)
    logger.verbose(f"bounds_result.allowed = {bounds_result.allowed}")

    mH = masses["H"]
    mS = masses["S"]
    mX = masses["X"]

    if bounds_result.allowed is False:
        limits1 = [a for a in bounds_result.appliedLimits if "H" in a.contributingParticles()]
        limits2 = [a for a in bounds_result.appliedLimits if "S" in a.contributingParticles()]
        limits3 = [a for a in bounds_result.appliedLimits if "X" in a.contributingParticles()]
        limits = [a for a in bounds_result.appliedLimits if a.obsRatio() > 1.0]

        # TODO: lim.limit().id() is the channel identifier
        # we will want to ignore 13022 at least near 125 since it excludes SM
        for lim in limits1:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                logger.verbose(f'\t hbexcl1 {idx} \t 1 {mH} {mS} {mX} {lim.limit().id()} {lim.obsRatio()} {lim.expRatio()}')
        for lim in limits2:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                logger.verbose(f'\t hbexcl2 {idx} \t 2 {mH} {mS} {mX} {lim.limit().id()} {lim.obsRatio()} {lim.expRatio()}')
        for lim in limits3:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                logger.verbose(f'\t hbexcl3 {idx} \t 3 {mH} {mS} {mX} {lim.limit().id()} {lim.obsRatio()} {lim.expRatio()}')
        for lim in limits:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                logger.verbose(f'\t hbexcl {idx} {mH} {mS} {mX} {lim.limit().id()} {lim.obsRatio()} {lim.expRatio()}')
