#!/usr/bin/env python3

"""
Applies experimental constraints to model scan data using HiggsBounds and HiggsSignals.

This module filters parameter scan results by checking:
- Exclusion limits from HiggsBounds
- Compatibility with SM-like signals from HiggsSignals

It supports serial and parallel processing of scan results, and rescaling of couplings
and branching ratios based on scalar properties.

Intended for use within a physics model scanning pipeline.
"""

# standard libraries
from collections import defaultdict
import logging
import multiprocessing as mp
import numpy as np
from typing import Dict, List, Tuple

# third-party libraries
import pandas as pd

# local modules
from utils.cpu_utils import get_n_cpus
import Higgs.predictions as HP
from filters.setup_higgs_tools import get_higgs_bounds, get_higgs_signals, get_higgs_predictions
from utils.config_loader import ConfigLoader
from utils.model import Model

# get logger
logger = logging.getLogger(__name__)

# get configurations
config_loader = ConfigLoader(config_file_name="RunConfig.yml")
try:
    # minimum chunk size for parallel processing
    min_chunk_size: int = config_loader.get('bounds', 'min_chunk_size')
except Exception as e:
    logger.exception(e)
    raise

SM_decays = ["WW", "ZZ", "Zgam", "gamgam", "gg", "bb", "tt", "ss", "cc", "mumu", "tautau"]

def filter_bounds(dataframe: pd.DataFrame,
                  header_bounds: str,
                  header_signals: str,
                  model: Model,
                  use_multiprocessing: bool = True
                 ) -> None:
    """
    Runs exclusion and signal strength filters and adds results to the DataFrame.

    Args:
        dataframe (pd.DataFrame): Input scan data with masses, widths, BRs, etc.
        header_bounds (str): Column name for the HiggsBounds result (0 or 1).
        header_signals (str): Column name for the HiggsSignals result (0 or 1).
        model (Model): Model object used for particle and parameter names.
        use_multiprocessing (bool): Flag to use parallel processing.
    """

    n_workers = 1
    if use_multiprocessing:
        n_workers = get_n_cpus()
    dataframe[header_bounds], dataframe[header_signals] = run_processing(df=dataframe,
                                                                         model=model,
                                                                         n_workers=n_workers)

# TODO: Make this work for other models
def process_data(df: pd.DataFrame,
                 model: Model) -> Tuple[List[int], List[int]]:
    """
    Processes a DataFrame of scan points and applies HiggsBounds and HiggsSignals.

    This function sets scalar properties, rescaling factors, and branching ratios,
    then evaluates whether each point is allowed.

    Args:
        df (pd.DataFrame): Subset of scan data to evaluate.
        model (Model): Model object defining scalar structure.

    Returns:
        Tuple[List[int], List[int]]: (HiggsBounds results, HiggsSignals results)
                                     as binary 0/1 values per row.
    """

    # get bounds and signals data
    bounds = get_higgs_bounds()
    signals = get_higgs_signals()

    # get Higgs predictions
    pred = get_higgs_predictions(model)

    # get HiggsSignals Chi^2 for SM
    signals_result_SM = signals(pred)

    # get particles
    H = pred.particle('H')
    S = pred.particle('S')
    X = pred.particle('X')

    # get strings for 3 bosons
    HName = model.get_ordered_scalar_name('H')
    SName = model.get_ordered_scalar_name('S')
    XName = model.get_ordered_scalar_name('X')

    # rescaling column names
    RH_name = 'R11'
    RS_name = 'R21'
    if HName == "H2":
        RH_name = 'R21'
        RS_name = 'R11'
    RX_name = 'R31'

    # make filter lists
    filt_bounds: List[int] = []
    filt_signals: List[int] = []

    for idx, (_, row) in enumerate(df.iterrows()):

        # get masses
        masses = extract_scalar_masses(row=row,
                                       HName=HName,
                                       SName=SName,
                                       XName=XName)

        # get widths
        widths = extract_scalar_widths(row=row,
                                       HName=HName,
                                       SName=SName,
                                       XName=XName)
        logger.verbose('Scalar widths are:')
        logger.verbose(f'  H: {widths["H"]}')
        logger.verbose(f'  S: {widths["S"]}')
        logger.verbose(f'  X: {widths["X"]}')

        # get rescalings
        rescalings = extract_rescalings(row=row,
                                        RH_name=RH_name,
                                        RS_name=RS_name,
                                        RX_name=RX_name)
        logger.verbose(f'Rescalings are {rescalings["H"]} {rescalings["S"]} {rescalings["X"]}')

        # get SM and BSM BRs
        br_SM = extract_SM_BRs(row=row,
                               HName=HName,
                               SName=SName,
                               XName=XName)
        br_BSM = extract_BSM_BRs(row=row,
                                 HName=HName,
                                 SName=SName)

        # configure scalars
        configure_particle(particle=H, label="H", masses=masses, widths=widths, rescalings=rescalings, BRs_SM=br_SM, BRs_BSM=br_BSM, adjust_ZZ=True)
        configure_particle(particle=S, label="S", masses=masses, widths=widths, rescalings=rescalings, BRs_SM=br_SM, BRs_BSM=br_BSM, adjust_ZZ=True)
        configure_particle(particle=X, label="X", masses=masses, widths=widths, rescalings=rescalings, BRs_SM=br_SM, BRs_BSM=br_BSM, adjust_ZZ=False)

        # get bounds and signals results
        bounds_result = bounds(pred)
        signals_result = signals(pred)

        # get HiggsSignals result using model and SM
        # this is now specific for bp1
        # bp1 and bp4 and low low
        #if mH3-mH1-mH2< 0:
        # bp2 and bp5 and high low
        #if mH2-2*mH1 < 0:
        HS_allowed = signals_result - signals_result_SM < 4.0

        # print out debug information
        if logger.isEnabledFor(logging.VERBOSE):
            print_bounds_result(bounds_result=bounds_result,
                                idx=idx,
                                masses=masses)
            logger.verbose(f"signals_result = {signals_result}")
            logger.verbose(f"HS_allowed = {HS_allowed}")

        # save whether requirements are passed
        filt_bounds.append(int(bounds_result.allowed))
        filt_signals.append(int(HS_allowed))

    return filt_bounds, filt_signals  # Return as separate lists

def extract_scalar_masses(row: pd.Series,
                          HName: str,
                          SName: str,
                          XName: str) -> Dict[str, float]:
    """
    Extracts the scalar particle masses from a DataFrame row.

    Args:
        row (pd.Series): A single row of scan data.
        HName (str): Model-defined name of the H scalar (e.g., 'H1', 'H2').
        SName (str): Model-defined name of the S scalar.
        XName (str): Model-defined name of the X scalar.

    Returns:
        Dict[str, float]: Mapping from {'H', 'S', 'X'} to their respective masses.
    """
    return {
        "H": float(row["m" + HName]),
        "S": float(row["m" + SName]),
        "X": float(row["m" + XName])
    }

def extract_scalar_widths(row: pd.Series,
                          HName: str,
                          SName: str,
                          XName: str) -> Dict[str, float]:
    """
    Extracts the total widths of scalar particles from a DataFrame row.

    Args:
        row (pd.Series): A single row of scan data.
        HName (str): Name of the H scalar.
        SName (str): Name of the S scalar.
        XName (str): Name of the X scalar.

    Returns:
        Dict[str, float]: Dictionary mapping {'H', 'S', 'X'} to total widths.
    """
    return {
        "H": float(row["w_" + HName]),
        "S": float(row["w_" + SName]),
        "X": float(row["w_" + XName])
    }

def extract_rescalings(row: pd.Series,
                       RH_name: str,
                       RS_name: str,
                       RX_name: str) -> Dict[str, float]:
    """
    Extracts the rescalings of scalar particles from a DataFrame row.

    Args:
        row (pd.Series): A single row of scan data.
        RH_name (str): Name of the H scalar rescaling.
        RS_name (str): Name of the S scalar rescaling.
        RX_name (str): Name of the X scalar rescaling.

    Returns:
        Dict[str, float]: Dictionary mapping {'H', 'S', 'X'} to total widths.
    """
    return {
        "H": float(row[RH_name]),
        "S": float(row[RS_name]),
        "X": float(row[RX_name])
    }

def extract_SM_BRs(row: pd.Series,
                   HName: str,
                   SName: str,
                   XName: str) -> Dict[str, Dict[str, float]]:
    """
    Extracts SM branching ratios for each scalar from a scan row.

    Args:
        row (pd.Series): A row from the scan DataFrame.
        HName (str): Name of the H scalar.
        SName (str): Name of the S scalar.
        XName (str): Name of the X scalar.

    Returns:
        Dict[str, Dict[str, float]]: A dictionary of the form:
            {
                'H': {decay: BR, ...},
                'S': {decay: BR, ...},
                'X': {decay: BR, ...}
            }
    """
    br_H = {decay: float(row[f"b_{HName}_{decay}"]) for decay in SM_decays}
    br_S = {decay: float(row[f"b_{SName}_{decay}"]) for decay in SM_decays}
    br_X = {decay: float(row[f"b_{XName}_{decay}"]) for decay in SM_decays}
    return {"H": br_H, "S": br_S, "X": br_X}

def extract_BSM_BRs(row: pd.Series,
                    HName: str,
                    SName: str,) -> Dict[str, Dict[Tuple[str, str], float]]:
    """
    Extracts BSM branching ratios (2-body decays) for each scalar from a scan row.

    Args:
        row (pd.Series): A row from the scan DataFrame.
        HName (str): Name of the H scalar.
        SName (str): Name of the S scalar.

    Returns:
        Dict[str, Dict[Tuple[str, str], float]]: A dictionary of the form:
            {
                'H': {('S', 'S'): BR, ...},
                'S': {('H', 'H'): BR, ...},
                'X': {('H', 'H'): BR, ('S', 'S'): BR, ('S', 'H'): BR, ...}
            }
    """
    br_H = defaultdict(float)
    br_S = defaultdict(float)
    br_X = defaultdict(float)

    if HName == "H2":
        br_H[("S", "S")] = float(row["b_H2_H1H1"])
    if SName == "H2":
        br_S[("H", "H")] = float(row["b_H2_H1H1"])

    br_X[("H", "H")] = float(row[f"b_H3_{HName}{HName}"])
    br_X[("S", "S")] = float(row[f"b_H3_{SName}{SName}"])
    br_X[("S", "H")] = float(row["b_H3_H1H2"])

    return {"H": br_H, "S": br_S, "X": br_X}

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

def chunk_dataframe(df: pd.DataFrame,
                    n_chunks: int) -> List[pd.DataFrame]:
    """
    Splits a DataFrame into approximately equal-sized chunks.

    Args:
        df (pd.DataFrame): DataFrame to split.
        n_chunks (int): Number of chunks.

    Returns:
        List[pd.DataFrame]: List of DataFrame chunks.
    """
    chunk_size = int(np.ceil(len(df) / n_chunks))
    return [df.iloc[i * chunk_size:(i + 1) * chunk_size] for i in range(n_chunks)]

def run_processing(df: pd.DataFrame,
                   model: Model,
                   n_workers: int = 1) -> Tuple[List[int], List[int]]:
    """
    Distributes scan filtering across multiple processes for performance.

    Automatically falls back to serial processing if the data is too small
    or only one worker is specified.

    Args:
        df (pd.DataFrame): DataFrame containing scan points.
        model (Model): Model object used for interpretation.
        n_workers (int): Number of parallel workers to use.

    Returns:
        Tuple[List[int], List[int]]: (bounds results, signals results) as binary lists.
    """

    df_len = len(df)

    if df_len < min_chunk_size or n_workers <= 1:
        # Too small — run serially
        return process_data(df, model)

    # Determine optimal number of chunks to balance load vs overhead
    n_chunks = min(n_workers, max(1, df_len // min_chunk_size))

    if n_chunks == 1:
        # Not enough data to justify parallelism
        return process_data(df, model)

    chunks = chunk_dataframe(df, n_chunks)

    with mp.Pool(n_chunks) as pool:
        results = pool.starmap(process_data, [(chunk, model) for chunk in chunks])

    # Unpack the results
    filt_bounds, filt_signals = zip(*results)

    # Return flattened lists
    return (
        [item for sublist in filt_bounds for item in sublist],
        [item for sublist in filt_signals for item in sublist],
    )
