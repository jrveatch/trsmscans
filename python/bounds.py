
from twors_higgstools_setup import *

import arrays
import filters

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
        print('gg > h cross section @ pp @ 13 TeV=', H.cxn('LHC13', "ggH"))
        print('gg > X cross section @ pp @ 13 TeV=', X.cxn('LHC13', "ggH"))
        # compare to independent calculations:
        XS_interpolator_SM_13TeV_NNLONNLL = get_XS_interpolator_SM_13TeV_NNLONNLL()
        xs13_nnlonnll = round_sig(sintheta**2 * XS_interpolator_SM_13TeV_NNLONNLL(MX),5)
        print('independent calculation of the cross section:')
        print('gg > X cross section @ pp @ 13 TeV (N^2LO+NNLL)=',  xs13_nnlonnll)
        

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
    print('HiggsBounds Allowed, HiggsSignals chi-sq.=', check_singlet_point(mX, sintheta, l112, debug=True))

def filterbounds(filename,SMass,debug=False):

    # get data and tools
    bounds, signals = getHiggsData()
    pred, H, S, X, ress_SM = setupHiggsTools()

    # get strings for 3 bosons
    HName = 'H1'
    SName = 'H2'
    XName = 'H3'

    # if mS > mH, switch order
    HgtS = False
    if SMass < 125:
        SName = 'H2'
        HName = 'H1'
        HgtS = True

    # check whether filt_width column exists, if not initialize it
    if not filters.column_exists(filename,"filt_bounds"):
        filters(filename)

    # load in arrays from .tsv file
    arrs = arrays.Arrays(filename)
    arrs.loadArrays()

    # get filt_bounds array
    filt_bounds = arrs.data['filt_bounds']

    for i in range(arrs.data['idx'].size):

        idx = int(arrs.data['idx'][i])

        # masses
        mH = float(arrs.data['m'+HName][i])
        mS = float(arrs.data['m'+SName][i])
        mX = float(arrs.data['m'+XName][i])

        # rescalings
        if HgtS:
            RS = float(arrs.data['R11'][i])
            RH = float(arrs.data['R21'][i])
        else:
            RH = float(arrs.data['R11'][i])
            RS = float(arrs.data['R21'][i])
        RX = float(arrs.data['R31'][i])

        if debug is True:
            print('rescalings are ', R11,R21,R31)

        # H BRs
        b_H_WW = float(arrs.data['b_'+HName+'_WW'][i])
        b_H_ZZ = float(arrs.data['b_'+HName+'_ZZ'][i])
        b_H_Zgam = float(arrs.data['b_'+HName+'_Zgam'][i])
        b_H_bb = float(arrs.data['b_'+HName+'_bb'][i])
        b_H_cc = float(arrs.data['b_'+HName+'_cc'][i])
        b_H_gamgam = float(arrs.data['b_'+HName+'_gamgam'][i])
        b_H_gg = float(arrs.data['b_'+HName+'_gg'][i])
        b_H_mumu = float(arrs.data['b_'+HName+'_mumu'][i])
        b_H_ss = float(arrs.data['b_'+HName+'_ss'][i])
        b_H_tautau = float(arrs.data['b_'+HName+'_tautau'][i])
        b_H_tt = float(arrs.data['b_'+HName+'_tt'][i])
        # H->SS BR is 0 for mS > mH, otherwise get its value
        b_H_SS = 0
        if HgtS: # mH > mS
            b_H_SS = float(arrs.data['b_H2_H1H1'][i])

        # H2 BRs
        b_S_WW = float(arrs.data['b_'+SName+'_WW'][i])
        b_S_ZZ = float(arrs.data['b_'+SName+'_ZZ'][i])
        b_S_Zgam = float(arrs.data['b_'+SName+'_Zgam'][i])
        b_S_bb = float(arrs.data['b_'+SName+'_bb'][i])
        b_S_cc = float(arrs.data['b_'+SName+'_cc'][i])
        b_S_gamgam = float(arrs.data['b_'+SName+'_gamgam'][i])
        b_S_gg = float(arrs.data['b_'+SName+'_gg'][i])
        b_S_mumu = float(arrs.data['b_'+SName+'_mumu'][i])
        b_S_ss = float(arrs.data['b_'+SName+'_ss'][i])
        b_S_tautau = float(arrs.data['b_'+SName+'_tautau'][i])
        b_S_tt = float(arrs.data['b_'+SName+'_tt'][i])
        # S->HH BR is 0 for mH > mS, otherwise get its value
        b_S_HH = 0
        if not HgtS: # mH < mS
            b_S_HH = float(arrs.data['b_H2_H1H1'][i])

        # X BRs
        b_X_WW = float(arrs.data['b_'+XName+'_WW'][i])
        b_X_ZZ = float(arrs.data['b_'+XName+'_ZZ'][i])
        b_X_Zgam = float(arrs.data['b_'+XName+'_Zgam'][i])
        b_X_bb = float(arrs.data['b_'+XName+'_bb'][i])
        b_X_cc = float(arrs.data['b_'+XName+'_cc'][i])
        b_X_gamgam = float(arrs.data['b_'+XName+'_gamgam'][i])
        b_X_gg = float(arrs.data['b_'+XName+'_gg'][i])
        b_X_mumu = float(arrs.data['b_'+XName+'_mumu'][i])
        b_X_ss = float(arrs.data['b_'+XName+'_ss'][i])
        b_X_tautau = float(arrs.data['b_'+XName+'_tautau'][i])
        b_X_tt = float(arrs.data['b_'+XName+'_tt'][i])
        if HgtS: # mH > mS
            b_X_HH = float(arrs.data['b_H3_H2H2'][i])
            b_X_SS = float(arrs.data['b_H3_H1H1'][i])
        else: # mH < mS
            b_X_HH = float(arrs.data['b_H3_H1H1'][i])
            b_X_SS = float(arrs.data['b_H3_H2H2'][i])
        b_X_SH = float(arrs.data['b_H3_H1H2'][i])

        # Widths
        w_H = float(arrs.data['w_'+HName][i])
        w_S = float(arrs.data['w_'+SName][i])
        w_X = float(arrs.data['w_'+XName][i])
        
        # i do everything at once here
        H.setMass(mH)
        S.setMass(mS)
        X.setMass(mX)

        H.setTotalWidth(w_H)
        S.setTotalWidth(w_S)
        X.setTotalWidth(w_X)

        # TODO: get the correct rescalings for either heirarchy
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

        if w_H > 1.e-13 :
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
            if HgtS:
                H.setBr('S', 'S', b_H_SS)
            # some debug printouts to check BRs
            if debug is True:
                print ('brs so far ', b_H_bb, b_H_tautau, b_H_mumu, b_H_cc, b_H_ss, b_H_tt, b_H_gg, b_H_gamgam, b_H_Zgam, b_H_WW, b_H_ZZ, b_H_SS)
                print('sum before zz', b_H_bb + b_H_tautau + b_H_mumu + b_H_cc + b_H_ss + b_H_tt + b_H_gg + b_H_gamgam + b_H_Zgam + b_H_WW + b_H_SS)
                print('sum after zz',b_H_bb + b_H_tautau + b_H_mumu + b_H_cc + b_H_ss + b_H_tt + b_H_gg + b_H_gamgam + b_H_Zgam + b_H_WW + b_H_SS + b_H_ZZ)
                print('width ',w_H)
            sum = b_H_bb + b_H_tautau + b_H_mumu + b_H_cc + b_H_ss + b_H_tt + b_H_gg + b_H_gamgam + b_H_Zgam + b_H_WW + b_H_SS + b_H_ZZ

            if sum > 1:
                b_H_ZZ=b_H_ZZ-sum+1
                if debug is True:
                    print ('adjusted last br by ',sum-1)
                    print ('new zz', b_H_ZZ)

            H.setBr('ZZ',b_H_ZZ)

        if w_S != 0: # TODO: Should this be > e-13?
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
            S.setBr('ZZ',b_S_ZZ)
            if not HgtS:
                S.setBr('H', 'H', b_S_HH)

        if w_X != 0: # TODO: Should this be > e-13?
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

        resb = bounds(pred)

        if debug is True:
            print(resb)
            print(resb.allowed)

        if resb.allowed == False:
            limits1 = [a for a in bounds(pred).appliedLimits if "H" in a.contributingParticles()]
            limits2 = [a for a in bounds(pred).appliedLimits if "S" in a.contributingParticles()]
            limits3 = [a for a in bounds(pred).appliedLimits if "X" in a.contributingParticles()]
            limits = [a for a in bounds(pred).appliedLimits if a.obsRatio() > 1.0]

            # TODO: lim.limit().id() is the channel identifier
            # we will want to ignore 13022 at least near 125 since it excludes SM
            if debug is True:
                for lim in limits1:
                    if lim.expRatio() > 1 and lim.obsRatio() > 1:
                        print('\t hbexcl1 ', idx,'\t 1',  mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())
                for lim in limits2:
                    if lim.expRatio() > 1 and lim.obsRatio() > 1:
                        print('\t hbexcl2 ', idx,'\t 2', mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())
                for lim in limits3:
                    if lim.expRatio() > 1 and lim.obsRatio() > 1:
                        print('\t hbexcl3 ', idx,'\t 3', mH, mS, mX, lim.limit().id(), lim.obsRatio(), lim.expRatio())

        # get and print the HiggsSignal result
        ress = signals(pred)
        if debug is True:
            print(ress)

        # this is now specific for bp1
        HS_allowed = False
        # bp1 and bp4 and low low
        #if mH3-mH1-mH2< 0:
        # bp2 and bp5 and high low
        #if mH2-2*mH1 < 0:
        if ress - ress_SM < 4.00:
            HS_allowed = True
        else:
            HS_allowed = False

        if debug is True:
            print(resb.allowed)
            print(HS_allowed)

        # check whether requirements are passed
        pass_filt = False
        if int(resb.allowed) and int(HS_allowed):
            pass_filt = True
        filt_bounds[i] = int(pass_filt)

    # save array of results and write to output file
    arrs.setArray('filt_bounds',filt_bounds)
    arrs.writeFile(filename)

    if debug is True:
        print("Done!")
        print('Total number of points =', i)

    # number of entries that pass
    npass = filt_bounds.sum()
    return npass

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
