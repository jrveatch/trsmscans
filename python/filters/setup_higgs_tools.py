import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS

from utils.model import Model

import os
from functools import lru_cache

@lru_cache(maxsize=None)
def get_higgs_predictions(model_name: str):

    # create model object
    model = Model(model_name)

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

@lru_cache(maxsize=None)
def get_higgs_signals():

    # get data directory
    data_directory = os.environ['DATADIR']

    # get HS dataset
    signals = HS.Signals(data_directory+'hsdataset')

    return signals

@lru_cache(maxsize=None)
def get_higgs_bounds():

    # get data directory
    data_directory = os.environ['DATADIR']

    # get HB dataset
    bounds = HB.Bounds(data_directory+'hbdataset')

    return bounds
