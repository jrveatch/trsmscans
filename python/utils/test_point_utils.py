
# standard libraries
from collections import OrderedDict
import logging
import math
import operator
import os
from typing import List

# third-party libraries
from prettytable import PrettyTable
from scipy.interpolate import interp1d

# local modules
from utils.math_utils import round_sig

# get logger
logger = logging.getLogger(__name__)

# create interpolators for the various BRs and total width and return a dictionary
def interpolate_HiggsBR(brdict) -> List[interp1d]:

    # the kind of interpolation
    interp_kind = 'cubic'

    # define an array of interpolators
    interp_higgs_brs: List[interp1d] = []

    # find out how many BRs+width we have:
    first_key = next(iter(brdict))
    first_value = brdict[first_key]
    NBRs = len(first_value)
  
    # push back all the values of the masses, brs and width into arrays
    mass_array = list(brdict.keys())
    br_array =[[] for _ in range(NBRs)]

    # get the mass and the corresponding BR arrays
    for mass in mass_array:
        for ii in range(NBRs):
            br_array[ii].append(brdict[mass][ii])

    # now create the interpolators and put them in the array:
    for ii in range(NBRs):
        interpolator = interp1d(mass_array, br_array[ii], kind=interp_kind, bounds_error=False)
        interp_higgs_brs.append(interpolator)

    return interp_higgs_brs

# branching ratio RESCALING for h2 -> xx given Gamma_SM, sin_theta, m1, m2, l112:
def RES_BR_h2_to_xx(sth: float,
                    Gam_SM: float,
                    m1: float,
                    m2: float,
                    l112: float) -> float:
    Gam_h2h1h1 = Gam_h2_to_h1h1(m1, m2, l112)
    RES_h2xx = sth**2 * Gam_SM / ( Gam_SM * sth**2 + Gam_h2h1h1 )
    return RES_h2xx

# calculate the width h2 -> h1 h1, given the mass, the self-coupling l112 (in GeV) and the sin(mixing angle)
def Gam_h2_to_h1h1(m1: float,
                   m2: float,
                   l112: float) -> float:
    if m2 < 2*m1:
        return 0.
    width_h2h1h1 = l112**2 * math.sqrt( 1 - 4 * m1**2 / m2**2 ) / 8 / math.pi / m2
    return width_h2h1h1

# function to read in the branching ratios into a dictionary in the format:
# mass [GeV] | H -> bbbar | H -> tautau | H -> mumu | H -> cc | H -> ss | H -> tt | H -> gg | H -> gammagamma | H -> Zgamma | H -> WW | H -> ZZ | total width [GeV]
# see https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR2014#SM_Higgs_Branching_Ratios_and_Pa
def read_higgsBR(br_file: str):

    # initialize BRs dictionary
    higgs_brs = {}

    # open file of BRs
    with open(br_file, 'r') as br_stream:

        # loop over the file
        for line in br_stream:

            # split line by whitespace
            values_raw = line.strip().split()

            # convert values to floats
            values = [float(value) for value in values_raw]

            # create br_array from all values except first
            br_array = values[1:]

            # create BRs dictionary from br_array
            higgs_brs[values[0]] = br_array

    # sort by increasing value of HYmass
    sorted_x = sorted(list(higgs_brs.items()), key=operator.itemgetter(0))
    sorted_higgs_brs = OrderedDict(sorted_x)
    return sorted_higgs_brs

# minor correction to rescale all BRs to make sure that sum(BRs) = 1
def fix_heavy_BRs(heavyBRs: List[float]) -> List[float]:
    sumBRs = 0
    heavyBRs_fixed: List[float] = []
    for i in range(0,12):
        sumBRs = sumBRs + heavyBRs[i]
    logger.debug('sumBRs = {sumBRs}')
    for j in range(len(heavyBRs)-1):
        heavyBRs_fixed.append(heavyBRs[j]/sumBRs)
    heavyBRs_fixed.append(heavyBRs[-1])
    return heavyBRs_fixed

# function that calculates the heavy Higgs branching ratios
def calculate_heavy_BRs_only(interpolators_SM: List[interp1d],
                             mh2: float,
                             l112: float,
                             sin_theta: float) -> List[float]:
    heavyBRs: List[float] = []
    # fix the SM Higgs mass
    mh1 = 125.09
    if mh2 < 1000.: # 
        Gamma_SM = interpolators_SM[-1](mh2)
    else:
        Gamma_SM = interpolators_SM[-1](1000.)
        logger.warning("mh2 > 1000.! (tree level)")
    # get the rescaling factor of the SM BRs:
    rescale_fac = RES_BR_h2_to_xx(sin_theta, Gamma_SM, mh1, mh2, l112)
    # loop over the SM BRs and rescale with the factor:
    for hh in range(len(interpolators_SM)-1):
        if mh2 < 1000.:
            heavyBRs.append(interpolators_SM[hh](mh2) * rescale_fac)
        else:
            heavyBRs.append(interpolators_SM[hh](1000.) * rescale_fac)
    # add the h1h1 decay:
    BR_hh = BR_h2_to_h1h1(sin_theta, mh1, mh2, l112, Gamma_SM)
    heavyBRs.append(BR_hh)
    # add the h1h1h1 decay (DON'T DO THIS HERE):
    BR_tripleHiggs = 0.
    heavyBRs.append(BR_tripleHiggs)

    # add the total heavy Higgs width:
    heavyBRs.append(width_h2(sin_theta, mh1, mh2, l112, Gamma_SM))
    
    return heavyBRs

# the BR h2 -> h1 h1, given the m2, sin_theta, l112, Gam_SM (total SM BR)
def BR_h2_to_h1h1(sth: float,
                  m1: float,
                  m2: float,
                  l112: float,
                  Gam_SM: float) -> float:
    BRh2h1h1 = Gam_h2_to_h1h1(m1, m2, l112) / ( Gam_SM * sth**2 + Gam_h2_to_h1h1(m1, m2, l112) )
    return BRh2h1h1

def width_h2(sth, m1, m2, l112, Gam_SM):
    total_width = Gam_SM * sth**2 + Gam_h2_to_h1h1(m1, m2, l112)
    return total_width

def get_BR_interpolators_SM() -> List[interp1d]:

    # get data directory
    data_dir = os.environ['DATADIR']

    # the file containing the branching ratios for the SM Higgs boson:
    BR_file = data_dir + "higgsBR_YR4.txt"

    # read the file:
    higgs_brs = read_higgsBR(BR_file)

    # get the BR interpolators
    interpolators = interpolate_HiggsBR(higgs_brs)

    return interpolators

# print the heavy Higgs info:
def print_heavy_Higgs_info(HeavyHiggsBRs, text_info) -> None:
    print(text_info)
    tbl = PrettyTable(["process", "BR"])
    BR_text_array_heavy_triple = get_BR_text_array_heavy_withtripleHiggs()
    for idx in range(len(HeavyHiggsBRs)):
      tbl.add_row([BR_text_array_heavy_triple[idx].replace('$', ''), round_sig(HeavyHiggsBRs[idx], sig_figs=5)])
    print(tbl)
    BRsum_heavy = round(sum(HeavyHiggsBRs[:-1]), 12)
    print(f"Consistency test: sum(BRs) = {BRsum_heavy}\n")

def get_BR_text_array_heavy_withtripleHiggs() -> List[str]:
    BR_text_array: List[str] = []
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
def read_higgsXS_N3LO(xs_file: str):

    # initialize xsec dictionary
    higgs_xss = {}

    # open xsec file
    with open(xs_file, 'r') as xs_stream:

        # loop over the file
        for line in xs_stream:

            # split line by whitespace
            values_raw = line.strip().split()

            # convert values to floats
            values = [float(value) for value in values_raw]

            # create br_array from all values except first
            xs_array = values[1:]

            # create BRs dictionary from br_array
            higgs_xss[values[0]] = xs_array

    # sort by increasing value of HYmass
    sorted_x = sorted(list(higgs_xss.items()), key=operator.itemgetter(0))
    sorted_higgs_xss = OrderedDict(sorted_x)
    return sorted_higgs_xss

# create interpolators for the XS and return a dictionary
def interpolate_HiggsXS(xs_dict):

    # the kind of interpolation
    interp_kind = 'linear'

    # define an array of interpolators
    interp_higgs_xss = []
  
    # push back all the values of the masses, brs and width into arrays
    mass_array = []
    xs_array =[]

    # get the mass and the corresponding BR arrays
    for key in list(xs_dict.keys()):
        mass_array.append(key)
        xs_array.append(xs_dict[key][0])

    # now create the interpolators and put them in the array:
    interp_higgs_xss = interp1d(mass_array, xs_array, kind=interp_kind, bounds_error=False)

    return interp_higgs_xss

def get_XS_interpolator_SM_13TeV_NNLONNLL():

    # get data directory
    data_dir = os.environ['DATADIR']

    # the 13 TeV ggF cross sections at NNLO+NNLL
    XS13_file = data_dir + "higgsXS_YR4_13TeV_NNLONNLL.txt"
    HiggsXS_13_NNLONNLL = read_higgsXS_N3LO(XS13_file)

    # get the interpolated XS
    interpolator = interpolate_HiggsXS(HiggsXS_13_NNLONNLL)

    return interpolator
