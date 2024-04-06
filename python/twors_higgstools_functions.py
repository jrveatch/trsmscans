import math
import operator
from prettytable import PrettyTable
from collections import OrderedDict
from scipy.interpolate import interp1d
import os

# round to sig significant figures
def round_sig(x, sig=2):
    if x == 0.:
        return 0.
    if math.isnan(x) is True:
        print('Warning, NaN!')
        return 0.
    return round(x, sig-int(math.floor(math.log10(abs(x))))-1)

# create interpolators for the various BRs and total width and return a dictionary
def interpolate_HiggsBR(brdict):

    # the kind of interpolation
    interpkind = 'cubic'

    # define an array of interpolators
    interp_higgsbrs = []

    # find out how many BRs+width we have:
    values_view = list(brdict.values())
    value_iterator = iter(values_view)
    first_value = next(value_iterator)
    NBRs = len(first_value)
  
    # push back all the values of the masses, brs and width into arrays
    mass_array = []
    br_array =[[] for yy in range(NBRs)]

    # get the mass and the corresponding BR arrays
    for key in list(brdict.keys()):
        mass_array.append(key)
        for ii in range(NBRs):
            br_array[ii].append(brdict[key][ii])

    # now create the interpolators and put them in the array:
    for ii in range(NBRs):
        interpolator = interp1d(mass_array, br_array[ii], kind=interpkind, bounds_error=False)
        interp_higgsbrs.append(interpolator)

    return interp_higgsbrs

# branching ratio RESCALING for h2 -> xx given Gamma_SM, sintheta, m1, m2, l112:
def RES_BR_h2_to_xx(sth, Gam_SM, m1, m2, l112):
    Gam_h2h1h1 = Gam_h2_to_h1h1(m1, m2, l112, sth)
    RES_h2xx = sth**2 * Gam_SM/ ( Gam_SM * sth**2  + Gam_h2h1h1)
    return RES_h2xx

# calculate the width h2 -> h1 h1, given the mass, the self-coupling l112 (in GeV) and the sin(mixing angle)
def Gam_h2_to_h1h1(m1, m2, l112, sth):
    if m2 < 2*m1:
        return 0.
    width_h2h1h1 = l112**2 * math.sqrt( 1 - 4 * m1**2 / m2**2 ) / 8 / math.pi / m2
    return width_h2h1h1

# function to read in the branching ratios into a dictionary in the format:
# mass [GeV] | H -> bbbar | H -> tautau | H -> mumu | H -> cc | H -> ss | H -> tt | H -> gg | H -> gammagamma | H -> Zgamma | H -> WW | H -> ZZ | total width [GeV]
# see https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR2014#SM_Higgs_Branching_Ratios_and_Pa
def read_higgsBR(brfile):
    higgsbrs = {}
    brstream = open(brfile, 'r')
    brarray = []
    for line in brstream:
        brarray = [ float(line.split()[1]), float(line.split()[2]), float(line.split()[3]), float(line.split()[4]), float(line.split()[5]), float(line.split()[6]), float(line.split()[7]), float(line.split()[8]), float(line.split()[9]), float(line.split()[10]), float(line.split()[11]), float(line.split()[12])]
        higgsbrs[float(line.split()[0])] = brarray
    # sort by increasing value of HYmass
    sorted_x = sorted(list(higgsbrs.items()), key=operator.itemgetter(0))
    sorted_higgsbrs = OrderedDict(sorted_x)
    return sorted_higgsbrs

# minor correction to rescale all BRs to make sure that sum(BRs) = 1
def fix_heavy_BRs(heavyBRs):
    sumBRs = 0
    heavyBRs_fixed = []
    for i in range(0,12):
        sumBRs = sumBRs + heavyBRs[i]
    #print('sumBRs=',sumBRs)
    for j in range(len(heavyBRs)-1):
        heavyBRs_fixed.append(heavyBRs[j]/sumBRs)
    heavyBRs_fixed.append(heavyBRs[-1])
    return heavyBRs_fixed

# function that calculates the heavy Higgs branching ratios
def calculate_heavy_BRs_only(interpolators_SM, mh2, l112, sintheta):
    heavyBRs = []
    # fix the SM Higgs mass
    mh1 = 125.09
    if mh2 < 1000.: # 
        Gamma_SM = interpolators_SM[-1](mh2)
    else:
        Gamma_SM = interpolators_SM[-1](1000.)
        print("WARNING: mh2 > 1000.! (tree level)")
    # get the rescaling factor of the SM BRs:
    rescale_fac = RES_BR_h2_to_xx(sintheta, Gamma_SM, mh1, mh2, l112)
    # loop over the SM BRs and rescale with the factor:
    for hh in range(len(interpolators_SM)-1):
        if mh2 < 1000.:
            heavyBRs.append(interpolators_SM[hh](mh2) * rescale_fac)
        else:
            heavyBRs.append(interpolators_SM[hh](1000.) * rescale_fac)
    # add the h1h1 decay:
    BR_hh = BR_h2_to_h1h1(sintheta, mh1, mh2, l112, Gamma_SM)
    heavyBRs.append(BR_hh)
    # add the h1h1h1 decay (DON'T DO THIS HERE):
    BR_tripleHiggs = 0.
    heavyBRs.append(BR_tripleHiggs)

    # add the total heavy Higgs width:
    heavyBRs.append(width_h2(sintheta, mh1, mh2, l112, Gamma_SM))
    
    return heavyBRs

# the BR h2 -> h1 h1, given the m2, sintheta, l112, Gam_SM (total SM BR)
def BR_h2_to_h1h1(sth, m1, m2, l112, Gam_SM):
    BRh2h1h1 = Gam_h2_to_h1h1(m1, m2, l112, sth) /  ( Gam_SM * sth**2  + Gam_h2_to_h1h1(m1, m2, l112, sth))
    return BRh2h1h1

def width_h2(sth, m1, m2, l112, Gam_SM):
    total_width = Gam_SM * sth**2  + Gam_h2_to_h1h1(m1, m2, l112, sth)
    return total_width

def get_BR_interpolators_SM():

    # get data directory
    datadir = os.environ['DATADIR']

    # the file containing the branching ratios for the SM Higgs boson:
    BR_file = datadir+"higgsBR_YR4.txt"

    # read the file:
    HiggsBRs = read_higgsBR(BR_file)

    # get the BR interpolators
    interpolators = interpolate_HiggsBR(HiggsBRs)

    return interpolators

# print the heavy Higgs info:
def print_heavy_Higgs_info(HeavyHiggsBRs, textinfo):
    print(textinfo)
    tbl = PrettyTable(["process", "BR"])
    BR_text_array_heavy_triple = get_BR_text_array_heavy_withtripleHiggs()
    for idx in range(len(HeavyHiggsBRs)):
      tbl.add_row([BR_text_array_heavy_triple[idx].replace('$', ''), round_sig(HeavyHiggsBRs[idx],5)])
    print(tbl)
    BRsum_heavy = 0.000
    for bb in HeavyHiggsBRs:
        if HeavyHiggsBRs.index(bb) != len(HeavyHiggsBRs)-1:
            BRsum_heavy = BRsum_heavy + bb
    print('consistency test: sum(BRs)=', BRsum_heavy)
    print('\n')

def get_BR_text_array_heavy_withtripleHiggs():
    BR_text_array = []
    BR_text_array.append('$b\\bar{b}$')
    BR_text_array.append('$\\tau \\tau$')
    BR_text_array.append('$\\mu \\mu$')
    BR_text_array.append('$c\\bar{c}$')
    BR_text_array.append('$s\\bar{s}$')
    BR_text_array.append('$t\\bar{t}$')
    BR_text_array.append('$gg$')
    BR_text_array.append('$\\gamma\\gamma$')
    BR_text_array.append('$Z \\gamma$')
    BR_text_array.append('$WW$')
    BR_text_array.append('$ZZ$')
    BR_text_array.append('$h_1 h1$')
    BR_text_array.append('$h_1 h_1 h_1$')
    BR_text_array.append('$\\Gamma$')
    return BR_text_array

###########################################################################################
# below is a calculation of the cross section independently from HiggsTools for validation
#############################################################################################

# function to read in the XS into a dictionary in the format:
# mS or mH (GeV) | Cross Section (pb) |	+Theory | -Theory |	TH Gaussian | -+(PDF+alphaS)
# see https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHXSWG#BSM_Higgs
def read_higgsXS_N3LO(xsfile):
    higgsxss = {}
    xsstream = open(xsfile, 'r')
    xsarray = []
    for line in xsstream:
        xsarray = [ float(line.split()[1]), float(line.split()[2]), float(line.split()[3]), float(line.split()[4]), float(line.split()[5])]
        higgsxss[float(line.split()[0])] = xsarray
    # sort by increasing value of HYmass
    sorted_x = sorted(list(higgsxss.items()), key=operator.itemgetter(0))
    sorted_higgsxss = OrderedDict(sorted_x)
    return sorted_higgsxss

# create interpolators for the XS and return a dictionary
def interpolate_HiggsXS(xsdict):

    # the kind of interpolation
    interpkind = 'linear'

    # define an array of interpolators
    interp_higgsxss = []

    # find out how many BRs+width we have:
    values_view = list(xsdict.values())
    value_iterator = iter(values_view)
    first_value = next(value_iterator)
  
    # push back all the values of the masses, brs and width into arrays
    mass_array = []
    xs_array =[]

    # get the mass and the corresponding BR arrays
    for key in list(xsdict.keys()):
        mass_array.append(key)
        xs_array.append(xsdict[key][0])

    # now create the interpolators and put them in the array:
    interp_higgsxss = interp1d(mass_array, xs_array, kind=interpkind, bounds_error=False)

    return interp_higgsxss

def get_XS_interpolator_SM_13TeV_NNLONNLL():

    # get data directory
    datadir = os.environ['DATADIR']

    # the 13 TeV ggF cross sections at NNLO+NNLL
    XS13_file = datadir+"higgsXS_YR4_13TeV_NNLONNLL.txt"
    HiggsXS_13_NNLONNLL = read_higgsXS_N3LO(XS13_file)

    # get the interpolated XS
    interpolator = interpolate_HiggsXS(HiggsXS_13_NNLONNLL)

    return interpolator
