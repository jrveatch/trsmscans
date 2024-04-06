
from twors_higgstools_setup import *

from twors_higgstools_functions import *

# SETUP STARTS HERE

# FUNCTION THAT RETURNS HiggsBounds True/False and chi-squared from HiggsSignals
# INPUT IS MH, sintheta and l112, the Scalar-Higgs-Higgs coupling
def check_singlet_point(MX, sintheta, l112, debug=False):

    bounds, signals = getHiggsData()
    pred, H, S, X, ress_SM = setupHiggsTools()

    # get the cosine of theta:
    costheta = math.sqrt(1-sintheta**2)
    
    # set the couplings of the SM-like Higgs boson to be rescaled according to costheta
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(costheta))
    
    # set the mass of the heavy scalar and rescale the couplings according to sintheta (for production)
    # then set the BRs according to the calculation
    X.setMass(MX)
    HP.effectiveCouplingInput(X, HP.scaledSMlikeEffCouplings(sintheta))

    # calculate and print the heavy H branching ratios, given MH, lambda_112 and sintheta
    BR_interpolators_SM = get_BR_interpolators_SM()
    heavyBRs = calculate_heavy_BRs_only(BR_interpolators_SM, MX, l112, sintheta)
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
        test_BR_array = [X.br('bb'), X.br('tautau'), X.br('mumu'), X.br('cc'), X.br('ss'), X.br('tt'), X.br('gg'), X.br('gamgam'), X.br('Zgam'), X.br('WW'), X.br('ZZ'), X.br('h', 'h'), 0., X.totalWidth()]
        print_heavy_Higgs_info(test_BR_array, 'Heavy Higgs BRs & width TEST')
        print('gg -> H cross section @ pp @ 13 TeV =', H.cxn('LHC13', "ggH"))
        print('gg -> X cross section @ pp @ 13 TeV =', X.cxn('LHC13', "ggH"))
        # compare to independent calculations:
        XS_interpolator_SM_13TeV_NNLONNLL = get_XS_interpolator_SM_13TeV_NNLONNLL()
        xs13_nnlonnll = round_sig(sintheta**2 * XS_interpolator_SM_13TeV_NNLONNLL(MX),5)
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
    HS_allowed = False
    if ress - ress_SM < 4.00:
        HS_allowed = True
    else:
        HS_allowed = False

    # return HiggsBounds (True/False) for Allowed/Disallowed and the chi-squared from HiggsSignals
    return resb.allowed, HS_allowed

def tanb_to_lambda112(mH, mX, sintheta, v, tanb):
    costheta = math.sqrt(1-sintheta**2)
    x = v/tanb
    lambda1 = (mH**2 / (2 * v**2)) * costheta**2 + (mX**2 / (2 * v**2)) * sintheta**2
    lambda2 = (mH**2 / (2 * x**2)) * sintheta**2 + (mX**2 / (2 * x**2)) * costheta**2
    lambda3 = ((mX**2 - mH**2)/(v*x)) * sintheta * costheta
    lambda112 = - (lambda3 / 2)  * ( x * costheta**3 + v*sintheta**3) + (lambda3 - 3 * lambda1) * v * costheta**2 * sintheta + (lambda3 - 3 * lambda2) * x * costheta * sintheta**2
    # cross check:
    #sin2alpha = lambda3 * x * v / math.sqrt( (lambda1 * v**2 - lambda2 * x**2)**2 + (lambda3 * x * v)**2)
    #sinalpha_xcheck = math.sqrt( (1 - math.sqrt(1-sin2alpha**2))/2) 
    #print('sin2alpha=', sin2alpha, 'corresponding to', sinalpha_xcheck)
    
    return lambda112

def testpoint(mX,sintheta,tanb):

    # SM Higgs mass and VEV
    mH = 125.09
    v = 246.

    print('mH, mX, sintheta, v, tanb=', mH, mX, sintheta, v, tanb)
    l112 = tanb_to_lambda112(mH, mX, sintheta, v, tanb)
    print('l112=', l112)
    
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

    testpoint(mX,sintheta,tanb)
