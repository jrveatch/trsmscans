#!/usr/bin/env python3

# standard libraries
from collections import defaultdict
import logging
import multiprocessing as mp
import numpy as np
from typing import Dict, List, Tuple

# third-party libraries
import pandas as pd

# local modules
from filters.setup_higgs_tools import *
from utils.config_loader import ConfigLoader
from utils.model import Model

# get logger
logger = logging.getLogger(__name__)

# get configurations
config_loader = ConfigLoader(config_file_name="RunConfig.yml")
try:
    # fraction of cpus to use when parallel processing
    frac_cpu: float = config_loader.get('MultiProcessing', 'frac_cpu')
    # minimum chunk size for parallel processing
    min_chunk_size: int = config_loader.get('bounds', 'min_chunk_size')
except KeyError as e:
    logger.error(e)
    raise
except Exception as e:
    logger.error(e)
    raise

SM_decays = ["WW", "ZZ", "Zgam", "gamgam", "gg", "bb", "tt", "ss", "cc", "mumu", "tautau"]

def filter_bounds(dataframe: pd.DataFrame,
                  header_bounds: str,
                  header_signals: str,
                  model: Model
                 ) -> None:
    """Run bounds filter for the dataframe using the given model"""
    dataframe[header_bounds], dataframe[header_signals] = parallel_process(df=dataframe,
                                                                           model=model,
                                                                           n_workers=int(mp.cpu_count()*frac_cpu))

# TODO: Make this work for other models
def process_data(df: pd.DataFrame,
                 model: Model) -> Tuple[List[int], List[int]]:
    """Function to process a DataFrame."""

    # make filter lists
    filt_bounds = []
    filt_signals = []

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

    # dictionaries of branching ratios
    br_H_SM = defaultdict(float)
    br_S_SM = defaultdict(float)
    br_X_SM = defaultdict(float)

    br_H_BSM = defaultdict(float)
    br_S_BSM = defaultdict(float)
    br_X_BSM = defaultdict(float)

    # rescaling column names
    RH_name = 'R11'
    RS_name = 'R21'
    if HName == "H2":
        RH_name = 'R21'
        RS_name = 'R11'
    RX_name = 'R31'

    for idx, (_, row) in enumerate(df.iterrows()):

        # get masses
        mH = float(row['m'+HName])
        mS = float(row['m'+SName])
        mX = float(row['m'+XName])

        # get widths
        wH = float(row['w_'+HName])
        wS = float(row['w_'+SName])
        wX = float(row['w_'+XName])

        # get rescalings
        RH = float(row[RH_name])
        RS = float(row[RS_name])
        RX = float(row[RX_name])

        logger.verbose(f'Rescalings are {RH} {RS} {RX}')

        # get SM BRs
        for decay in SM_decays:
            br_H_SM[decay] = float(row['b_'+HName+'_'+decay])
            br_S_SM[decay] = float(row['b_'+SName+'_'+decay])
            br_X_SM[decay] = float(row['b_'+XName+'_'+decay])

        # get BSM BRs
        if HName == "H2": # mH > mS
            br_H_BSM['S','S'] = float(row['b_H2_H1H1'])
        if SName == "H2": # mH < mS
            br_S_BSM['H','H'] = float(row['b_H2_H1H1'])
        br_X_BSM['H','H'] = float(row['b_H3_'+HName+HName])
        br_X_BSM['S','S'] = float(row['b_H3_'+SName+SName])
        br_X_BSM['S','H'] = float(row['b_H3_H1H2'])

        # set scalar masses and widths
        H.setMass(mH)
        S.setMass(mS)
        X.setMass(mX)

        H.setTotalWidth(wH)
        S.setTotalWidth(wS)
        X.setTotalWidth(wX)

        # set effective couplings for each scalar
        set_effective_couplings(particle=H,mass=mH,rescaling=RH)
        set_effective_couplings(particle=S,mass=mS,rescaling=RS)
        set_effective_couplings(particle=X,mass=mX,rescaling=RX)

        # RESET BRs BEFORE SETTING THEM TO AVOID ISSUES WITH BR>1

        H.setTotalWidth(wH)
        S.setTotalWidth(wS)
        X.setTotalWidth(wX)

        logger.verbose(f"Scalar widths are:")
        logger.verbose(f"  H: {wH}")
        logger.verbose(f"  S: {wS}")
        logger.verbose(f"  X: {wX}")

        # set BRs for H
        set_BRs(particle=H,
                BRs_SM=br_H_SM,
                BRs_BSM=br_H_BSM,
                adjust_ZZ=True)

        # set BRs for S
        set_BRs(particle=S,
                BRs_SM=br_S_SM,
                BRs_BSM=br_S_BSM,
                adjust_ZZ=True)

        # set BRs for X
        set_BRs(particle=X,
                BRs_SM=br_X_SM,
                BRs_BSM=br_X_BSM,
                adjust_ZZ=False)

        # get bounds and signals results
        bounds_result = bounds(pred)
        signals_result = signals(pred)

        # get HiggsSignals result using model and SM
        # this is now specific for bp1
        # bp1 and bp4 and low low
        #if mH3-mH1-mH2< 0:
        # bp2 and bp5 and high low
        #if mH2-2*mH1 < 0:
        HS_allowed = signals_result - signals_result_SM < 4.00

        # print out debug information
        if logger.isEnabledFor(logging.VERBOSE):
            print_bounds_result(bounds_result=bounds_result,
                                idx=idx,
                                mX=mX,
                                mS=mS,
                                mH=mH)
            logger.verbose(f"signals_result = {signals_result}")
            logger.verbose(f"HS_allowed = {HS_allowed}")

        # save whether requirements are passed
        filt_bounds.append(int(bounds_result.allowed))
        filt_signals.append(int(HS_allowed))

    return filt_bounds, filt_signals  # Return as separate lists

def set_effective_couplings(particle,
                            mass: float,
                            rescaling: float
                           ) -> None:
    """Set effective couplings"""
    if mass < 150:
        HP.effectiveCouplingInput(particle, HP.scaledSMlikeEffCouplings(rescaling),reference="SMHiggsEW")
    else:
        HP.effectiveCouplingInput(particle, HP.scaledSMlikeEffCouplings(rescaling))

def set_BRs(particle,
            BRs_SM: Dict[str,float],
            BRs_BSM: Dict[Tuple[str,str],float],
            adjust_ZZ: bool
           ) -> None:
    """Set scalar branching ratios"""
    # check total width and return if it is too small
    if particle.totalWidth() < 1e-11:
        return

    # keep track of the sum of BRs
    sum_BR = 0.0

    # reset SM BRs to 0 to start from a clean slate
    for decay in BRs_SM.keys():
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
                        mX: float,
                        mS: float,
                        mH: float) -> None:
    """Print results of bounds check"""

    logger.verbose(bounds_result)
    logger.verbose(f"bounds_result.allowed = {bounds_result.allowed}")

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
    """Splits a DataFrame into n_chunks approximately equal parts."""
    chunk_size = int(np.ceil(len(df) / n_chunks))
    return [df.iloc[i * chunk_size:(i + 1) * chunk_size] for i in range(n_chunks)]

def parallel_process(df: pd.DataFrame,
                     model: 'Model',
                     n_workers: int = 1) -> Tuple[List[int], List[int]]:
    """
    Automatically parallelizes processing based on DataFrame size.
    Avoids parallelism if not worth the overhead.
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