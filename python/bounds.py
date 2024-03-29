
from twors_higgstools_setup import *
import os

import arrays
import filters

# SETUP STARTS HERE

# get root directory
rootdir = os.getcwd()

print(rootdir)

# SM Higgs mass and VEV
mh = 125.09
v = 246.
# set the SM Higgs mass
h1.setMass(mh)

# get the SM chi-squared for HiggsSignals
HP.effectiveCouplingInput(h1, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")
ress_SM = signals(pred)
print("HiggsSignals chi-sq. for SM =", ress_SM)

# FUNCTION THAT RETURNS HiggsBounds True/False and chi-squared from HiggsSignals
# INPUT IS MH, sintheta and l112, the Scalar-Higgs-Higgs coupling
def check_singlet_point(MH, sintheta, l112, debug=False):
    # get the cosine of theta:
    costheta = math.sqrt(1-sintheta**2)
    
    # set the couplings of the SM-like Higgs boson to be rescaled according to costheta
    HP.effectiveCouplingInput(h, HP.scaledSMlikeEffCouplings(costheta))
    
    # set the mass of the heavy scalar and rescale the couplings according to sintheta (for production)
    # then set the BRs according to the calculation
    H.setMass(MH)
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(sintheta))

    # calculate and print the heavy H branching ratios, given MH, lambda_112 and sintheta
    BR_interpolators_SM = get_BR_interpolators_SM(rootdir)
    heavyBRs = calculate_heavy_BRs_only(BR_interpolators_SM, MH, mh, l112, sintheta)
    heavyBRs = fix_heavy_BRs(heavyBRs)
    if debug is True:
        print_heavy_Higgs_info(heavyBRs, BR_text_array_heavy_withtripleHiggs, 'Heavy Higgs BRs & width')

    # RESET BRs BEFORE SETTING THEM TO AVOID ISSUES WITH BR>1
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

    # SET THE BRS
    H.setBr('bb', heavyBRs[0])
    H.setBr('tautau', heavyBRs[1])
    H.setBr('mumu', heavyBRs[2])
    H.setBr('cc', heavyBRs[3])
    H.setBr('ss', heavyBRs[4])
    H.setBr('tt', heavyBRs[5])
    H.setBr('gg', heavyBRs[6])
    H.setBr('gamgam', heavyBRs[7])
    H.setBr('Zgam', heavyBRs[8])
    H.setBr('WW', heavyBRs[9])
    H.setBr('ZZ', heavyBRs[10])
    H.setBr('h', 'h', heavyBRs[11])
    H.setTotalWidth(heavyBRs[13])

    # SOME TESTS HERE:
    # test whether the BRs have been set correctly
    if debug is True:
        test_BR_array = [H.br('bb'), H.br('tautau'), H.br('mumu'), H.br('cc'), H.br('ss'), H.br('tt'), H.br('gg'), H.br('gamgam'), H.br('Zgam'), H.br('WW'), H.br('ZZ'), H.br('h', 'h'), 0., H.totalWidth()]
        print_heavy_Higgs_info(test_BR_array, BR_text_array_heavy_withtripleHiggs, 'Heavy Higgs BRs & width TEST')
        print('gg > h cross section @ pp @ 13 TeV=', h.cxn('LHC13', "ggH"))
        print('gg > H cross section @ pp @ 13 TeV=', H.cxn('LHC13', "ggH"))
        # compare to independent calculations:
        XS_interpolator_SM_13TeV_NNLONNLL = get_XS_interpolator_SM_13TeV_NNLONNLL(rootdir)
        xs13_nnlonnll = round_sig(sintheta**2 * XS_interpolator_SM_13TeV_NNLONNLL(MH),5)
        print('independent calculation of the cross section:')
        print('gg > H cross section @ pp @ 13 TeV (N^2LO+NNLL)=',  xs13_nnlonnll)
        

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

def tanb_to_lambda112(mh, mH, sintheta, v, tanb):
    costheta = math.sqrt(1-sintheta**2)
    x = v/tanb
    lambda1 = (mh**2 / (2 * v**2)) * costheta**2 + (mH**2 / (2 * v**2)) * sintheta**2
    lambda2 = (mh**2 / (2 * x**2)) * sintheta**2 + (mH**2 / (2 * x**2)) * costheta**2
    lambda3 = ((mH**2 - mh**2)/(v*x)) * sintheta * costheta
    lambda112 = - (lambda3 / 2)  * ( x * costheta**3 + v*sintheta**3) + (lambda3 - 3 * lambda1) * v * costheta**2 * sintheta + (lambda3 - 3 * lambda2) * x * costheta * sintheta**2
    # cross check:
    #sin2alpha = lambda3 * x * v / math.sqrt( (lambda1 * v**2 - lambda2 * x**2)**2 + (lambda3 * x * v)**2)
    #sinalpha_xcheck = math.sqrt( (1 - math.sqrt(1-sin2alpha**2))/2) 
    #print('sin2alpha=', sin2alpha, 'corresponding to', sinalpha_xcheck)
    
    return lambda112

def testpoint(mH,sintheta,tanb):
    print('mh, mH, sintheta, v, tanb=', mh, mH, sintheta, v, tanb)
    l112 = tanb_to_lambda112(mh, mH, sintheta, v, tanb)
    print('l112=', l112)
    
    # check this example point:
    print('HiggsBounds Allowed, HiggsSignals chi-sq.=', check_singlet_point(mH, sintheta, l112, debug=True))

def filterbounds(filename,debug=False):

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
        mH1 = float(arrs.data['mH1'][i])
        mH2 = float(arrs.data['mH2'][i])
        mH3 = float(arrs.data['mH3'][i])

        # rescalings
        R11 = float(arrs.data['R11'][i])
        R21 = float(arrs.data['R21'][i])
        R31 = float(arrs.data['R31'][i])

        if debug is True:
            print('rescalings are ', R11,R21,R31)

        # H1 BRs
        b_H1_WW = float(arrs.data['b_H1_WW'][i])
        b_H1_ZZ = float(arrs.data['b_H1_ZZ'][i])
        b_H1_Zgam = float(arrs.data['b_H1_Zgam'][i])
        b_H1_bb = float(arrs.data['b_H1_bb'][i])
        b_H1_cc = float(arrs.data['b_H1_cc'][i])
        b_H1_gamgam = float(arrs.data['b_H1_gamgam'][i])
        b_H1_gg = float(arrs.data['b_H1_gg'][i])
        b_H1_mumu = float(arrs.data['b_H1_mumu'][i])
        b_H1_ss = float(arrs.data['b_H1_ss'][i])
        b_H1_tautau = float(arrs.data['b_H1_tautau'][i])
        b_H1_tt = float(arrs.data['b_H1_tt'][i])

        # H2 BRs
        b_H2_H1H1 = float(arrs.data['b_H2_H1H1'][i])
        b_H2_WW = float(arrs.data['b_H2_WW'][i])
        b_H2_ZZ = float(arrs.data['b_H2_ZZ'][i])
        b_H2_Zgam = float(arrs.data['b_H2_Zgam'][i])
        b_H2_bb = float(arrs.data['b_H2_bb'][i])
        b_H2_cc = float(arrs.data['b_H2_cc'][i])
        b_H2_gamgam = float(arrs.data['b_H2_gamgam'][i])
        b_H2_gg = float(arrs.data['b_H2_gg'][i])
        b_H2_mumu = float(arrs.data['b_H2_mumu'][i])
        b_H2_ss = float(arrs.data['b_H2_ss'][i])
        b_H2_tautau = float(arrs.data['b_H2_tautau'][i])
        b_H2_tt = float(arrs.data['b_H2_tt'][i])

        # H3 BRs
        b_H3_H1H1 = float(arrs.data['b_H3_H1H1'][i])
        b_H3_H1H2 = float(arrs.data['b_H3_H1H2'][i])
        b_H3_H2H2 = float(arrs.data['b_H3_H2H2'][i])
        b_H3_WW = float(arrs.data['b_H3_WW'][i])
        b_H3_ZZ = float(arrs.data['b_H3_ZZ'][i])
        b_H3_Zgam = float(arrs.data['b_H3_Zgam'][i])
        b_H3_bb = float(arrs.data['b_H3_bb'][i])
        b_H3_cc = float(arrs.data['b_H3_cc'][i])
        b_H3_gamgam = float(arrs.data['b_H3_gamgam'][i])
        b_H3_gg = float(arrs.data['b_H3_gg'][i])
        b_H3_mumu = float(arrs.data['b_H3_mumu'][i])
        b_H3_ss = float(arrs.data['b_H3_ss'][i])
        b_H3_tautau = float(arrs.data['b_H3_tautau'][i])
        b_H3_tt = float(arrs.data['b_H3_tt'][i])

        # Widths
        w_H1 = float(arrs.data['w_H1'][i])
        w_H2 = float(arrs.data['w_H2'][i])
        w_H3 = float(arrs.data['w_H3'][i])
        
        # i do everything at once here
        h1.setMass(mH1)
        h2.setMass(mH2)
        h3.setMass(mH3)

        h1.setTotalWidth(w_H1)
        h2.setTotalWidth(w_H2)
        h3.setTotalWidth(w_H3)

        if mH1 < 150:
            HP.effectiveCouplingInput(h1, HP.scaledSMlikeEffCouplings(R11),reference="SMHiggsEW")
        else:
            HP.effectiveCouplingInput(h1, HP.scaledSMlikeEffCouplings(R11))

        if mH2 < 150:
            HP.effectiveCouplingInput(h2, HP.scaledSMlikeEffCouplings(R21),reference="SMHiggsEW")
        else:
            HP.effectiveCouplingInput(h2, HP.scaledSMlikeEffCouplings(R21))

        if mH3 < 150:
            HP.effectiveCouplingInput(h3, HP.scaledSMlikeEffCouplings(R31),reference="SMHiggsEW")
        else:
            HP.effectiveCouplingInput(h3, HP.scaledSMlikeEffCouplings(R31))

        # set the mass of the heavy scalar and rescale the couplings according to sintheta (for production)
        # then set the BRs according to the calculation
        # h1.setMass(mH1)
        # h2.setMass(mH2)
        # h3.setMass(mH3)

        # RESET BRs BEFORE SETTING THEM TO AVOID ISSUES WITH BR>1

        h1.setTotalWidth(w_H1)
        h2.setTotalWidth(w_H2)
        h3.setTotalWidth(w_H3)

        if debug is True:
            print ("widths are ",w_H1,w_H2,w_H3)

        if w_H1 > 1.e-13 :
            h1.setBr('bb', 0.)
            h1.setBr('tautau', 0.)
            h1.setBr('mumu', 0.)
            h1.setBr('cc', 0.)
            h1.setBr('ss', 0.)
            h1.setBr('tt', 0.)
            h1.setBr('gg', 0.)
            h1.setBr('gamgam', 0.)
            h1.setBr('Zgam', 0.)
            h1.setBr('WW', 0.)
            h1.setBr('ZZ', 0.)

            h1.setBr('bb',b_H1_bb)
            h1.setBr('tautau',b_H1_tautau)
            h1.setBr('mumu',b_H1_mumu)
            h1.setBr('cc',b_H1_cc)
            h1.setBr('ss',b_H1_ss)
            h1.setBr('tt',b_H1_tt)
            h1.setBr('gg',b_H1_gg)
            h1.setBr('gamgam',b_H1_gamgam)
            h1.setBr('Zgam',b_H1_Zgam)
            h1.setBr('WW',b_H1_WW)
            if debug is True:
                print ('brs so far ', b_H1_bb, b_H1_tautau, b_H1_mumu, b_H1_cc, b_H1_ss, b_H1_tt, b_H1_gg, b_H1_gamgam, b_H1_Zgam, b_H1_WW, b_H1_ZZ)
                print('sum before zz', b_H1_bb+ b_H1_tautau+ b_H1_mumu+ b_H1_cc+b_H1_ss+b_H1_tt+ b_H1_gg+b_H1_gamgam+ b_H1_Zgam+ b_H1_WW)
                print('sum after zz',b_H1_bb+ b_H1_tautau+ b_H1_mumu+ b_H1_cc+b_H1_ss+b_H1_tt+ b_H1_gg+b_H1_gamgam+ b_H1_Zgam+ b_H1_WW+b_H1_ZZ)
                print('width ',w_H1)
            sum = b_H1_bb+ b_H1_tautau+ b_H1_mumu+ b_H1_cc+b_H1_ss+b_H1_tt+ b_H1_gg+b_H1_gamgam+ b_H1_Zgam+ b_H1_WW+b_H1_ZZ

            if sum > 1:
                b_H1_ZZ=b_H1_ZZ-sum+1
                if debug is True:
                    print ('adjusted last br by ',sum-1)
                    print ('new zz', b_H1_ZZ)

            h1.setBr('ZZ',b_H1_ZZ)

        if w_H2 != 0:
            h2.setBr('bb', 0.)
            h2.setBr('tautau', 0.)
            h2.setBr('mumu', 0.)
            h2.setBr('cc', 0.)
            h2.setBr('ss', 0.)
            h2.setBr('tt', 0.)
            h2.setBr('gg', 0.)
            h2.setBr('gamgam', 0.)
            h2.setBr('Zgam', 0.)
            h2.setBr('WW', 0.)
            h2.setBr('ZZ', 0.)

            h2.setBr('bb',b_H2_bb)
            h2.setBr('tautau',b_H2_tautau)
            h2.setBr('mumu',b_H2_mumu)
            h2.setBr('cc',b_H2_cc)
            h2.setBr('ss',b_H2_ss)
            h2.setBr('tt',b_H2_tt)
            h2.setBr('gg',b_H2_gg)
            h2.setBr('gamgam',b_H2_gamgam)
            h2.setBr('Zgam',b_H2_Zgam)
            h2.setBr('WW',b_H2_WW)
            h2.setBr('ZZ',b_H2_ZZ)
            h2.setBr('h1', 'h1', b_H2_H1H1)

        if w_H3 != 0:
            h3.setBr('bb', 0.)
            h3.setBr('tautau', 0.)
            h3.setBr('mumu', 0.)
            h3.setBr('cc', 0.)
            h3.setBr('ss', 0.)
            h3.setBr('tt', 0.)
            h3.setBr('gg', 0.)
            h3.setBr('gamgam', 0.)
            h3.setBr('Zgam', 0.)
            h3.setBr('WW', 0.)
            h3.setBr('ZZ', 0.)

            h3.setBr('bb',b_H3_bb)
            h3.setBr('tautau',b_H3_tautau)
            h3.setBr('mumu',b_H3_mumu)
            h3.setBr('cc',b_H3_cc)
            h3.setBr('ss',b_H3_ss)
            h3.setBr('tt',b_H3_tt)
            h3.setBr('gg',b_H3_gg)
            h3.setBr('gamgam',b_H3_gamgam)
            h3.setBr('Zgam',b_H3_Zgam)
            h3.setBr('WW',b_H3_WW)
            h3.setBr('ZZ',b_H3_ZZ)
            h3.setBr('h1', 'h1', b_H3_H1H1)
            h3.setBr('h2', 'h2', b_H3_H2H2)
            h3.setBr('h1', 'h2', b_H3_H1H2)

        resb = bounds(pred)

        if debug is True:
            print(resb)
            print(resb.allowed)

        if resb.allowed == False:
            limits1 = [a for a in bounds(pred).appliedLimits if "h1" in a.contributingParticles()]
            limits2 = [a for a in bounds(pred).appliedLimits if "h2" in a.contributingParticles()]
            limits3 = [a for a in bounds(pred).appliedLimits if "h3" in a.contributingParticles()]
            limits = [a for a in bounds(pred).appliedLimits if a.obsRatio() > 1.0]

            # TODO: lim.limit().id() is the channel identifier
            # we will want to ignore 13022 at least near 125 since it excludes SM
            if debug is True:
                for lim in limits1:
                    if lim.expRatio() > 1 and lim.obsRatio() > 1:
                        print('\t hbexcl1 ', idx,'\t 1',  mH1, mH2, mH3, lim.limit().id(), lim.obsRatio(), lim.expRatio())
                for lim in limits2:
                    if lim.expRatio() > 1 and lim.obsRatio() > 1:
                        print('\t hbexcl2 ', idx,'\t 2', mH1, mH2, mH3, lim.limit().id(), lim.obsRatio(), lim.expRatio())
                for lim in limits3:
                    if lim.expRatio() > 1 and lim.obsRatio() > 1:
                        print('\t hbexcl3 ', idx,'\t 3', mH1, mH2, mH3, lim.limit().id(), lim.obsRatio(), lim.expRatio())

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

################################
# START LOOP OR TESTING HERE
################################

TEST_SINGLE = False # do not use

# TEST ONE SET OF VALUES HERE:
if TEST_SINGLE is True:
    # Singlet parameters, Tania:
    #mH = 966.278
    #sintheta = -0.25468226979564057
    #tanb = 1.0678636931186718

    mH = 218.98275755792929
    sintheta = -8.9105204943541461E-002
    tanb = 0.96965458337420274

    testpoint(mH,sintheta,tanb)
