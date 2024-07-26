import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS

import os

def getHiggsPredictions(neutralScalars: list[(str,str)] = [],
                        chargedScalars: list[str] = [],
                        doublyChargedScalars: list[str] = []):

    # create the model predictions
    pred = HP.Predictions()

    # add a SM-like Higgs boson with SM-like couplings
    H = pred.addParticle(HP.NeutralScalar("H", "even"))

    # SM Higgs mass and VEV
    mH = 125.09

    # set the SM Higgs mass
    H.setMass(mH)

    # get the SM chi-squared for HiggsSignals
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")

    # add BSM neutral scalars
    for scalar in neutralScalars:
        pred.addParticle(HP.NeutralScalar(scalar[0], scalar[1]))

    # add BSM charged scalars
    for scalar in chargedScalars:
        pred.addParticle(HP.ChargedScalar(scalar))

    # add BSM doubly charged scalars
    for scalar in doublyChargedScalars:
        pred.addParticle(HP.DoublyChargedScalar(scalar))

    return pred

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
