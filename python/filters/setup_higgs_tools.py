
# standard libraries
from functools import lru_cache

# local modules
import Higgs.bounds as HB
import Higgs.predictions as HP
import Higgs.signals as HS
from utils.env_utils import hbdataset_dir, hsdataset_dir
from utils.model import Model

@lru_cache(maxsize=None)
def get_higgs_predictions(model: 'Model'):

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

    # get HS dataset
    signals = HS.Signals(hsdataset_dir())

    return signals

@lru_cache(maxsize=None)
def get_higgs_bounds():

    # get HB dataset
    bounds = HB.Bounds(hbdataset_dir())

    return bounds
