import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS

from model import Model

import os

def getHiggsPredictions(modelname: str):

    # create model object
    model = Model(modelname)

    # create the model predictions
    pred = HP.Predictions()

    # add a SM-like Higgs boson with SM-like couplings
    H = pred.addParticle(HP.NeutralScalar(model.SMHiggs, "even"))

    # SM Higgs mass
    mH = 125.09

    # set the SM Higgs mass
    H.setMass(mH)

    # TODO: Is this necessary?
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")

    # add BSM CP-even neutral scalars
    for scalar in model.particles['neutralScalarsCPEven']:
        pred.addParticle(HP.NeutralScalar(scalar, 'even'))

    # add BSM CP-odd neutral scalars
    for scalar in model.particles['neutralScalarsCPOdd']:
        pred.addParticle(HP.NeutralScalar(scalar, 'odd'))

    # add BSM charged scalars
    for scalar in model.particles['chargedScalars']:
        pred.addParticle(HP.ChargedScalar(scalar))

    # add BSM doubly charged scalars
    for scalar in model.particles['doublyChargedScalars']:
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
