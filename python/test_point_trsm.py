#!/usr/bin/env python3

import math

import Higgs.predictions as HP

from utils.math_utils import round_sig
from utils.model import Model
from filters.setup_higgs_tools import get_higgs_bounds, get_higgs_signals, get_higgs_predictions
from utils.test_point_utils import calculate_heavy_BRs_only, print_heavy_Higgs_info, fix_heavy_BRs
from utils.test_point_utils import get_BR_interpolators_SM, get_XS_interpolator_SM_13TeV_NNLONNLL

# SETUP STARTS HERE

# FUNCTION THAT RETURNS HiggsBounds True/False and chi-squared from HiggsSignals
# INPUT IS MH, sintheta and l112, the Scalar-Higgs-Higgs coupling
def check_singlet_point(mX: float,
                        sintheta: float,
                        l112: float,
                        debug: bool = False):

    # get bounds and signals data
    bounds = get_higgs_bounds()
    signals = get_higgs_signals()

    # get Higgs predictions
    pred = get_higgs_predictions(Model(name="TRSMBroken",masses={"H":125.09,"S":500,"X":1000}))

    # get HiggsSignals Chi^2 for SM
    ress_SM = signals(pred)
    print("HiggsSignals chi-sq. for SM =", ress_SM)

    # get H and X particles
    H = pred.particle('H')
    X = pred.particle('X')

    # get the cosine of theta:
    costheta = math.sqrt(1-sintheta**2)

    # set the couplings of the SM-like Higgs boson to be rescaled according to costheta
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(costheta))

    # set the mass of the heavy scalar and rescale the couplings according to sintheta (for production)
    # then set the BRs according to the calculation
    X.setMass(mX)
    HP.effectiveCouplingInput(X, HP.scaledSMlikeEffCouplings(sintheta))

    # calculate and print the heavy H branching ratios, given MH, lambda_112 and sintheta
    BR_interpolators_SM = get_BR_interpolators_SM()
    heavyBRs = calculate_heavy_BRs_only(BR_interpolators_SM, mX, l112, sintheta)
    heavyBRs = fix_heavy_BRs(heavyBRs)
    if debug is True:
        print_heavy_Higgs_info(heavyBRs, 'Heavy Higgs BRs & width')

    # RESET BRs BEFORE SETTING THEM TO AVOID ISSUES WITH BR>1
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

    # SET THE BRS
    X.setBr('bb', heavyBRs[0])
    X.setBr('tautau', heavyBRs[1])
    X.setBr('mumu', heavyBRs[2])
    X.setBr('cc', heavyBRs[3])
    X.setBr('ss', heavyBRs[4])
    X.setBr('tt', heavyBRs[5])
    X.setBr('gg', heavyBRs[6])
    X.setBr('gamgam', heavyBRs[7])
    X.setBr('Zgam', heavyBRs[8])
    X.setBr('WW', heavyBRs[9])
    X.setBr('ZZ', heavyBRs[10])
    X.setBr('h', 'h', heavyBRs[11])
    X.setTotalWidth(heavyBRs[13])

    # SOME TESTS HERE:
    # test whether the BRs have been set correctly
    if debug is True:
        test_BR_array = []
        test_BR_array.append(X.br('bb'))
        test_BR_array.append(X.br('tautau'))
        test_BR_array.append(X.br('mumu'))
        test_BR_array.append(X.br('cc'))
        test_BR_array.append(X.br('ss'))
        test_BR_array.append(X.br('tt'))
        test_BR_array.append(X.br('gg'))
        test_BR_array.append(X.br('gamgam'))
        test_BR_array.append(X.br('Zgam'))
        test_BR_array.append(X.br('WW'))
        test_BR_array.append(X.br('ZZ'))
        test_BR_array.append(X.br('h', 'h'))
        test_BR_array.append(0.)
        test_BR_array.append(X.totalWidth())
        print_heavy_Higgs_info(test_BR_array, 'Heavy Higgs BRs & width TEST')
        print('gg -> H cross section @ pp @ 13 TeV =', H.cxn('LHC13', "ggH"))
        print('gg -> X cross section @ pp @ 13 TeV =', X.cxn('LHC13', "ggH"))
        # compare to independent calculations:
        XS_interpolator_SM_13TeV_NNLONNLL = get_XS_interpolator_SM_13TeV_NNLONNLL()
        xs13_nnlonnll = round_sig(sintheta**2 * XS_interpolator_SM_13TeV_NNLONNLL(mX), sig_figs=5)
        print('independent calculation of the cross section:')
        print('gg -> X cross section @ pp @ 13 TeV (N^2LO+NNLL) =',  xs13_nnlonnll)

    # get and print the HiggsBounds results
    resb = bounds(pred)
    #print(resb)
    #print(resb.allowed)
    #print(resb.appliedLimits)
    #print([a for a in resb.appliedLimits if "H" in a.contributingParticles()])

    # get and print the HiggsSignal result
    ress = signals(pred)
    #print(signals(pred).appliedLimits)
    #print(ress)
    HS_allowed = ress - ress_SM < 4.0

    # return HiggsBounds (True/False) for Allowed/Disallowed and the chi-squared from HiggsSignals
    return resb.allowed, HS_allowed

def tanb_to_lambda112(mH: float,
                      mX: float,
                      sintheta: float,
                      v: float,
                      tanb: float) -> float:

    costheta = math.sqrt(1-sintheta**2)
    x = v/tanb
    lambda1 = (mH**2 / (2 * v**2)) * costheta**2 + (mX**2 / (2 * v**2)) * sintheta**2
    lambda2 = (mH**2 / (2 * x**2)) * sintheta**2 + (mX**2 / (2 * x**2)) * costheta**2
    lambda3 = ((mX**2 - mH**2)/(v*x)) * sintheta * costheta
    lambda112 = - (lambda3 / 2) * ( x * costheta**3 + v*sintheta**3)
    lambda112 += (lambda3 - 3 * lambda1) * v * costheta**2 * sintheta
    lambda112 += (lambda3 - 3 * lambda2) * x * costheta * sintheta**2

    return lambda112

def test_point(mX: float,
               sintheta: float,
               tanb: float) -> None:

    # SM Higgs mass and VEV
    mH = 125.09
    v = 246.
    l112 = tanb_to_lambda112(mH, mX, sintheta, v, tanb)

    print('mH =', mH)
    print('mX =', mX)
    print('sintheta =', sintheta)
    print('v =', v)
    print('tanb =', tanb)
    print('l112 =', l112)

    # check this example point:
    print('HiggsBounds Allowed, HiggsSignals chi-sq. =', check_singlet_point(mX, sintheta, l112, debug=True))

# test a single point if called as a standalone script
if __name__ == "__main__":

    # Singlet parameters, Tania:
    #mX = 966.278
    #sintheta = -0.25468226979564057
    #tanb = 1.0678636931186718

    mX = 218.98275755792929
    sintheta = -8.9105204943541461E-002
    tanb = 0.96965458337420274

    test_point(mX,sintheta,tanb)
