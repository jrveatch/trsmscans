import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS

import os

from twors_higgstools_functions import *   # probably need much less as in principle can read in everything from the .tsv output from scanners

def setupHiggsTools():

    # get signals and bounds
    bounds, signals = getHiggsData()

    pred = HP.Predictions() # create the model predictions

    # add a SM-like Higgs boson with SM-like couplings
    h1 = pred.addParticle(HP.NeutralScalar("h1", "even"))

    # add second BSM Higgs boson which decays to two h bosons and is produced via gluon fusion
    h2 = pred.addParticle(HP.NeutralScalar("h2", "even"))
    h3 = pred.addParticle(HP.NeutralScalar("h3", "even"))

    # SM Higgs mass and VEV
    mh = 125.09
    v = 246.
    # set the SM Higgs mass
    h1.setMass(mh)

    # get the SM chi-squared for HiggsSignals
    HP.effectiveCouplingInput(h1, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")
    ress_SM = signals(pred)
    print("HiggsSignals chi-sq. for SM =", ress_SM)

    return pred, h1, h2, h3, ress_SM

def getHiggsData():

    datadir = os.environ['DATADIR']

    print(datadir)
    print(datadir+'hbdataset')

    bounds = HB.Bounds(datadir+'hbdataset') # load HB dataset
    signals = HS.Signals(datadir+'hsdataset') # load HS dataset

    return bounds, signals

