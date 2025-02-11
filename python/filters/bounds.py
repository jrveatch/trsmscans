#!/usr/bin/env python3

# standard libraries
import logging
from collections import defaultdict
from typing import Dict, Tuple

# third-party libraries
import pandas as pd

# local modules
from filters.setup_higgs_tools import *
from utils.model import Model

# get logger
logger = logging.getLogger(__name__)

SM_decays = ["WW", "ZZ", "Zgam", "gamgam", "gg", "bb", "tt", "ss", "cc", "mumu", "tautau"]

# TODO: Make this work for other models
def filter_bounds(dataframe: pd.DataFrame,
                  header_bounds: str,
                  header_signals: str,
                  model: 'Model'
                 ) -> None:

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

    # get filter lists
    filt_bounds = []
    filt_signals = []

    for i in range(len(dataframe.index)):

        idx = i

        # masses
        mH = float(dataframe['m'+HName][i])
        mS = float(dataframe['m'+SName][i])
        mX = float(dataframe['m'+XName][i])

        # rescalings
        if HName == "H2": # mH > mS
            RS = float(dataframe['R11'][i])
            RH = float(dataframe['R21'][i])
        else: # mH < mS
            RH = float(dataframe['R11'][i])
            RS = float(dataframe['R21'][i])
        RX = float(dataframe['R31'][i])

        logger.verbose(f'rescalings are {RH} {RS} {RX}')

        # get SM BRs
        for decay in SM_decays:
            br_H_SM[decay] = float(dataframe['b_'+HName+'_'+decay][i])
            br_S_SM[decay] = float(dataframe['b_'+SName+'_'+decay][i])
            br_X_SM[decay] = float(dataframe['b_'+XName+'_'+decay][i])
        
        # get BSM BRs
        if HName == "H2": # mH > mS
            br_H_BSM['S','S'] = float(dataframe['b_H2_H1H1'][i])
        if SName == "H2": # mH < mS
            br_S_BSM['H','H'] = float(dataframe['b_H2_H1H1'][i])
        br_X_BSM['H','H'] = float(dataframe['b_H3_'+HName+HName][i])
        br_X_BSM['S','S'] = float(dataframe['b_H3_'+SName+SName][i])
        br_X_BSM['S','H'] = float(dataframe['b_H3_H1H2'][i])

        # Widths
        w_H = float(dataframe['w_'+HName][i])
        w_S = float(dataframe['w_'+SName][i])
        w_X = float(dataframe['w_'+XName][i])
        
        # Set masses and widths
        H.setMass(mH)
        S.setMass(mS)
        X.setMass(mX)

        H.setTotalWidth(w_H)
        S.setTotalWidth(w_S)
        X.setTotalWidth(w_X)

        # set effective couplings for each scalar
        set_effective_couplings(particle=H,mass=mH,rescaling=RH)
        set_effective_couplings(particle=S,mass=mS,rescaling=RS)
        set_effective_couplings(particle=X,mass=mX,rescaling=RX)

        # RESET BRs BEFORE SETTING THEM TO AVOID ISSUES WITH BR>1

        H.setTotalWidth(w_H)
        S.setTotalWidth(w_S)
        X.setTotalWidth(w_X)

        logger.verbose(f"Scalar widths are:")
        logger.verbose(f"  H: {w_H}")
        logger.verbose(f"  S: {w_S}")
        logger.verbose(f"  X: {w_X}")

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

    # add filters to dataframe
    dataframe[header_bounds] = filt_bounds
    dataframe[header_signals] = filt_signals

    return

def set_effective_couplings(particle,
                            mass: float,
                            rescaling: float
                           ) -> None:
    
    if mass < 150:
        HP.effectiveCouplingInput(particle, HP.scaledSMlikeEffCouplings(rescaling),reference="SMHiggsEW")
    else:
        HP.effectiveCouplingInput(particle, HP.scaledSMlikeEffCouplings(rescaling))
    
    return

def set_BRs(particle,
            BRs_SM: Dict[str,float],
            BRs_BSM: Dict[Tuple[str,str],float],
            adjust_ZZ: bool
           ) -> None:
    
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

    return

def print_bounds_result(bounds_result,
                        idx: int,
                        mX: float,
                        mS: float,
                        mH: float) -> None:

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
