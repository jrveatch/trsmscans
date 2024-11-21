#!/usr/bin/env python3

from filters.setup_higgs_tools import *

from utils.arrays import Arrays
from utils.tsv_utils import initialize_column

from utils.masses import Masses

import pandas as pd

# TODO: Make this work for other models
def filter_bounds(file_name: str,
                  model_name: str,
                  masses: Masses,
                  debug = False) -> int:

    # get bounds and signals data
    bounds = get_higgs_bounds()
    signals = get_higgs_signals()

    # get Higgs predictions
    pred = get_higgs_predictions(model_name=model_name)

    # get HiggsSignals Chi^2 for SM
    signals_result_SM = signals(pred)

    # get particles
    H = pred.particle('H')
    S = pred.particle('S')
    X = pred.particle('X')

    # get strings for 3 bosons
    HName = masses.HName
    SName = masses.SName
    XName = masses.XName

    # initialize columns in case they don't exist
    # TODO: Is this still needed?
    initialize_column(file_name=file_name,
                      column_header="filt_bounds",
                      value=1)
    initialize_column(file_name=file_name,
                      column_header="filt_signals",
                      value=1)

    # load in arrays from .tsv file
    arrs = Arrays(file_name)

    # get filter arrays
    filt_bounds = []
    filt_signals = []

    for i in range(len(arrs.data().index)):

        idx = i

        # masses
        mH = float(arrs.data('m'+HName)[i])
        mS = float(arrs.data('m'+SName)[i])
        mX = float(arrs.data('m'+XName)[i])

        # rescalings
        if HName == "H2":
            RS = float(arrs.data('R11')[i])
            RH = float(arrs.data('R21')[i])
        else:
            RH = float(arrs.data('R11')[i])
            RS = float(arrs.data('R21')[i])
        RX = float(arrs.data('R31')[i])

        if debug is True:
            print('rescalings are ', RH,RS,RX)

        # H BRs
        b_H_WW = float(arrs.data('b_'+HName+'_WW')[i])
        b_H_ZZ = float(arrs.data('b_'+HName+'_ZZ')[i])
        b_H_Zgam = float(arrs.data('b_'+HName+'_Zgam')[i])
        b_H_bb = float(arrs.data('b_'+HName+'_bb')[i])
        b_H_cc = float(arrs.data('b_'+HName+'_cc')[i])
        b_H_gamgam = float(arrs.data('b_'+HName+'_gamgam')[i])
        b_H_gg = float(arrs.data('b_'+HName+'_gg')[i])
        b_H_mumu = float(arrs.data('b_'+HName+'_mumu')[i])
        b_H_ss = float(arrs.data('b_'+HName+'_ss')[i])
        b_H_tautau = float(arrs.data('b_'+HName+'_tautau')[i])
        b_H_tt = float(arrs.data('b_'+HName+'_tt')[i])
        # H->SS BR is 0 for mS > mH, otherwise get its value
        b_H_SS = 0
        if HName == "H2": # mH > mS
            b_H_SS = float(arrs.data('b_H2_H1H1')[i])

        # H2 BRs
        b_S_WW = float(arrs.data('b_'+SName+'_WW')[i])
        b_S_ZZ = float(arrs.data('b_'+SName+'_ZZ')[i])
        b_S_Zgam = float(arrs.data('b_'+SName+'_Zgam')[i])
        b_S_bb = float(arrs.data('b_'+SName+'_bb')[i])
        b_S_cc = float(arrs.data('b_'+SName+'_cc')[i])
        b_S_gamgam = float(arrs.data('b_'+SName+'_gamgam')[i])
        b_S_gg = float(arrs.data('b_'+SName+'_gg')[i])
        b_S_mumu = float(arrs.data('b_'+SName+'_mumu')[i])
        b_S_ss = float(arrs.data('b_'+SName+'_ss')[i])
        b_S_tautau = float(arrs.data('b_'+SName+'_tautau')[i])
        b_S_tt = float(arrs.data('b_'+SName+'_tt')[i])
        # S->HH BR is 0 for mH > mS, otherwise get its value
        b_S_HH = 0
        if SName == "H2": # mH < mS
            b_S_HH = float(arrs.data('b_H2_H1H1')[i])

        # X BRs
        b_X_WW = float(arrs.data('b_'+XName+'_WW')[i])
        b_X_ZZ = float(arrs.data('b_'+XName+'_ZZ')[i])
        b_X_Zgam = float(arrs.data('b_'+XName+'_Zgam')[i])
        b_X_bb = float(arrs.data('b_'+XName+'_bb')[i])
        b_X_cc = float(arrs.data('b_'+XName+'_cc')[i])
        b_X_gamgam = float(arrs.data('b_'+XName+'_gamgam')[i])
        b_X_gg = float(arrs.data('b_'+XName+'_gg')[i])
        b_X_mumu = float(arrs.data('b_'+XName+'_mumu')[i])
        b_X_ss = float(arrs.data('b_'+XName+'_ss')[i])
        b_X_tautau = float(arrs.data('b_'+XName+'_tautau')[i])
        b_X_tt = float(arrs.data('b_'+XName+'_tt')[i])
        b_X_HH = float(arrs.data('b_H3_'+HName+HName)[i])
        b_X_SS = float(arrs.data('b_H3_'+SName+SName)[i])
        b_X_SH = float(arrs.data('b_H3_H1H2')[i])

        # Widths
        w_H = float(arrs.data('w_'+HName)[i])
        w_S = float(arrs.data('w_'+SName)[i])
        w_X = float(arrs.data('w_'+XName)[i])
        
        # i do everything at once here
        H.setMass(mH)
        S.setMass(mS)
        X.setMass(mX)

        H.setTotalWidth(w_H)
        S.setTotalWidth(w_S)
        X.setTotalWidth(w_X)

        # TODO: get the correct rescalings for either hierarchy
        if mH < 150:
            HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(RH),reference="SMHiggsEW")
        else:
            HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(RH))

        if mS < 150:
            HP.effectiveCouplingInput(S, HP.scaledSMlikeEffCouplings(RS),reference="SMHiggsEW")
        else:
            HP.effectiveCouplingInput(S, HP.scaledSMlikeEffCouplings(RS))

        if mX < 150:
            HP.effectiveCouplingInput(X, HP.scaledSMlikeEffCouplings(RX),reference="SMHiggsEW")
        else:
            HP.effectiveCouplingInput(X, HP.scaledSMlikeEffCouplings(RX))

        # set the mass of the heavy scalar and rescale the couplings according to sintheta (for production)
        # then set the BRs according to the calculation
        # H.setMass(mH)
        # S.setMass(mS)
        # X.setMass(mX)

        # RESET BRs BEFORE SETTING THEM TO AVOID ISSUES WITH BR>1

        H.setTotalWidth(w_H)
        S.setTotalWidth(w_S)
        X.setTotalWidth(w_X)

        if debug is True:
            print ("widths are ",w_H,w_S,w_X)

        if w_H > 1e-13 :
            H.setBr('bb', 0.)
            H.setBr('tautau', 0.)
            H.setBr('mumu', 0.)
            H.setBr('cc', 0.)
            H.setBr('ss', 0.)
            H.setBr('tt', 0.)
            H.setBr('gg', 0.)
            H.setBr('gamgam', 0.)
            H.setBr('Zgam', 0.)
            H.setBr('WW', 0.)
            H.setBr('ZZ', 0.)

            H.setBr('bb',b_H_bb)
            H.setBr('tautau',b_H_tautau)
            H.setBr('mumu',b_H_mumu)
            H.setBr('cc',b_H_cc)
            H.setBr('ss',b_H_ss)
            H.setBr('tt',b_H_tt)
            H.setBr('gg',b_H_gg)
            H.setBr('gamgam',b_H_gamgam)
            H.setBr('Zgam',b_H_Zgam)
            H.setBr('WW',b_H_WW)
            # include H->SS if mH > mS
            if HName == "H2":
                H.setBr('S', 'S', b_H_SS)

            # some debug printouts to check BRs
            if debug is True:
                print ('brs so far ', b_H_bb, b_H_tautau, b_H_mumu, b_H_cc, b_H_ss, b_H_tt, b_H_gg, b_H_gamgam, b_H_Zgam, b_H_WW, b_H_ZZ, b_H_SS)
                print('sum before zz', b_H_bb + b_H_tautau + b_H_mumu + b_H_cc + b_H_ss + b_H_tt + b_H_gg + b_H_gamgam + b_H_Zgam + b_H_WW + b_H_SS)
                print('sum after zz',b_H_bb + b_H_tautau + b_H_mumu + b_H_cc + b_H_ss + b_H_tt + b_H_gg + b_H_gamgam + b_H_Zgam + b_H_WW + b_H_SS + b_H_ZZ)
                print('width ',w_H)
            sum_H = b_H_bb + b_H_tautau + b_H_mumu + b_H_cc + b_H_ss + b_H_tt + b_H_gg + b_H_gamgam + b_H_Zgam + b_H_WW + b_H_SS + b_H_ZZ

            # if BR sum is too large, adjust H->ZZ BR
            if sum_H > 1:
                b_H_ZZ=b_H_ZZ-sum_H+1
                if debug is True:
                    print ('adjusted last br by ',sum-1)
                    print ('new zz', b_H_ZZ)

            # add H->ZZ BR
            H.setBr('ZZ',b_H_ZZ)

        if w_S > 1e-13:
            S.setBr('bb', 0.)
            S.setBr('tautau', 0.)
            S.setBr('mumu', 0.)
            S.setBr('cc', 0.)
            S.setBr('ss', 0.)
            S.setBr('tt', 0.)
            S.setBr('gg', 0.)
            S.setBr('gamgam', 0.)
            S.setBr('Zgam', 0.)
            S.setBr('WW', 0.)
            S.setBr('ZZ', 0.)

            S.setBr('bb',b_S_bb)
            S.setBr('tautau',b_S_tautau)
            S.setBr('mumu',b_S_mumu)
            S.setBr('cc',b_S_cc)
            S.setBr('ss',b_S_ss)
            S.setBr('tt',b_S_tt)
            S.setBr('gg',b_S_gg)
            S.setBr('gamgam',b_S_gamgam)
            S.setBr('Zgam',b_S_Zgam)
            S.setBr('WW',b_S_WW)
            if SName == "H2":
                S.setBr('H', 'H', b_S_HH)

            # some debug printouts to check BRs
            if debug is True:
                print ('brs so far ', b_S_bb, b_S_tautau, b_S_mumu, b_S_cc, b_S_ss, b_S_tt, b_S_gg, b_S_gamgam, b_S_Zgam, b_S_WW, b_S_ZZ, b_S_HH)
                print('sum before zz', b_S_bb + b_S_tautau + b_S_mumu + b_S_cc + b_S_ss + b_S_tt + b_S_gg + b_S_gamgam + b_S_Zgam + b_S_WW + b_S_HH)
                print('sum after zz',b_S_bb + b_S_tautau + b_S_mumu + b_S_cc + b_S_ss + b_S_tt + b_S_gg + b_S_gamgam + b_S_Zgam + b_S_WW + b_S_HH + b_S_ZZ)
                print('width ',w_S)
            sum_S = b_S_bb + b_S_tautau + b_S_mumu + b_S_cc + b_S_ss + b_S_tt + b_S_gg + b_S_gamgam + b_S_Zgam + b_S_WW + b_S_HH + b_S_ZZ

            # if BR sum is too large, adjust S->ZZ BR
            if sum_S > 1:
                b_S_ZZ=b_S_ZZ-sum_S+1
                if debug is True:
                    print ('adjusted last br by ',sum-1)
                    print ('new zz', b_S_ZZ)

            # add S->ZZ BR
            S.setBr('ZZ',b_S_ZZ)

        if w_X > 1e-13:
            X.setBr('bb', 0.)
            X.setBr('tautau', 0.)
            X.setBr('mumu', 0.)
            X.setBr('cc', 0.)
            X.setBr('ss', 0.)
            X.setBr('tt', 0.)
            X.setBr('gg', 0.)
            X.setBr('gamgam', 0.)
            X.setBr('Zgam', 0.)
            X.setBr('WW', 0.)
            X.setBr('ZZ', 0.)

            X.setBr('bb',b_X_bb)
            X.setBr('tautau',b_X_tautau)
            X.setBr('mumu',b_X_mumu)
            X.setBr('cc',b_X_cc)
            X.setBr('ss',b_X_ss)
            X.setBr('tt',b_X_tt)
            X.setBr('gg',b_X_gg)
            X.setBr('gamgam',b_X_gamgam)
            X.setBr('Zgam',b_X_Zgam)
            X.setBr('WW',b_X_WW)
            X.setBr('ZZ',b_X_ZZ)
            X.setBr('H', 'H', b_X_HH)
            X.setBr('S', 'S', b_X_SS)
            X.setBr('H', 'S', b_X_SH)

        # get bounds and signals results
        bounds_result = bounds(pred)
        signals_result = signals(pred)

        # get HiggsSignals result using model and SM
        # this is now specific for bp1
        HS_allowed = False
        # bp1 and bp4 and low low
        #if mH3-mH1-mH2< 0:
        # bp2 and bp5 and high low
        #if mH2-2*mH1 < 0:
        if signals_result - signals_result_SM < 4.00:
            HS_allowed = True
        else:
            HS_allowed = False

        # print out debug information
        if debug is True:
            print_bounds_result(bounds_result=bounds_result,
                                idx=idx,
                                mX=mX,
                                mS=mS,
                                mH=mH)
            print(signals_result)
            print(HS_allowed)

        # save whether requirements are passed
        filt_bounds.append(int(bounds_result.allowed))
        filt_signals.append(int(HS_allowed))

    # save arrays of results and write to output file
    arrs.set_array('filt_bounds',pd.Series(filt_bounds, index=arrs.data().index))
    arrs.set_array('filt_signals',pd.Series(filt_signals, index=arrs.data().index))
    arrs.write_file(file_name)

    # number of entries that pass
    nbounds = sum(filt_bounds)
    nsignals = sum(filt_signals)
    return nbounds, nsignals

def print_bounds_result(bounds_result,
                        idx: int,
                        mX: float,
                        mS: float,
                        mH: float) -> None:

    print(bounds_result)
    print(bounds_result.allowed)
    
    if bounds_result.allowed is False:
        limits1 = [a for a in bounds_result.appliedLimits if "H" in a.contributingParticles()]
        limits2 = [a for a in bounds_result.appliedLimits if "S" in a.contributingParticles()]
        limits3 = [a for a in bounds_result.appliedLimits if "X" in a.contributingParticles()]
        limits = [a for a in bounds_result.appliedLimits if a.obsRatio() > 1.0]
        
        # TODO: lim.limit().id() is the channel identifier
        # we will want to ignore 13022 at least near 125 since it excludes SM
        for lim in limits1:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                print('\t hbexcl1 ', idx,'\t 1',  mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())
        for lim in limits2:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                print('\t hbexcl2 ', idx,'\t 2', mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())
        for lim in limits3:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                print('\t hbexcl3 ', idx,'\t 3', mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())
        for lim in limits:
            if lim.expRatio() > 1 and lim.obsRatio() > 1:
                print('\t hbexcl ', idx, mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())
