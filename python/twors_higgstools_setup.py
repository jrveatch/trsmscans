import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS

import os

from twors_higgstools_functions import *   # probably need much less as in principle can read in everything from the .tsv output from scanners

def setupHiggsTools():

    # get signals dataset
    signals = getHiggsSignals()

    # create the model predictions
    pred = HP.Predictions()

    # add a SM-like Higgs boson with SM-like couplings
    H = pred.addParticle(HP.NeutralScalar("H", "even"))

    # add BSM boson S that decays to SM particles
    S = pred.addParticle(HP.NeutralScalar("S", "even"))

    # add BSM boson X that decays two H+S
    X = pred.addParticle(HP.NeutralScalar("X", "even"))

    # SM Higgs mass and VEV
    mH = 125.09

    # set the SM Higgs mass
    H.setMass(mH)

    # get the SM chi-squared for HiggsSignals
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")
    ress_SM = signals(pred)
    #print("HiggsSignals chi-sq. for SM =", ress_SM)

    return pred, H, S, X, ress_SM

def getHiggsData():

    # get HB dataset
    bounds = getHiggsBounds()

    # get HS dataset
    signals = getHiggsSignals()

    return bounds, signals

def getHiggsSignals():

    # get data directory
    datadir = os.environ['DATADIR']

    # get HS dataset
    signals = HS.Signals(datadir+'hsdataset')

    return signals

def getHiggsBounds():

    # get data directory
    datadir = os.environ['DATADIR']

    # get HB dataset
    bounds = HB.Bounds(datadir+'hbdataset')

    return bounds

