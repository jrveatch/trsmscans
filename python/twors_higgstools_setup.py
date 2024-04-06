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
    h1 = pred.addParticle(HP.NeutralScalar("h1", "even"))

    # add second BSM Higgs boson which decays to two h bosons and is produced via gluon fusion
    h2 = pred.addParticle(HP.NeutralScalar("h2", "even"))
    h3 = pred.addParticle(HP.NeutralScalar("h3", "even"))

    # SM Higgs mass and VEV
    mh = 125.09
    # set the SM Higgs mass
    h1.setMass(mh)

    # get the SM chi-squared for HiggsSignals
    HP.effectiveCouplingInput(h1, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")
    ress_SM = signals(pred)
    #print("HiggsSignals chi-sq. for SM =", ress_SM)

    return pred, h1, h2, h3, ress_SM

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

