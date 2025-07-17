"""
Provides access to cached Higgs sector predictions, bounds, and signals for scalar models.
"""

# standard libraries
from functools import lru_cache

# local modules
import Higgs.bounds as HB
import Higgs.predictions as HP
import Higgs.signals as HS
from utils.env_utils import hbdataset_dir, hsdataset_dir
from utils.model import Model

@lru_cache(maxsize=None)
def get_higgs_predictions(model: Model):
    """
    Constructs and caches HiggsBounds/HiggsSignals-compatible predictions for a model.

    Builds a set of Higgs sector particle predictions based on the scalar content of the
    provided model, including SM and BSM Higgs bosons. This is used by external tools to
    evaluate model constraints.

    Args:
        model (Model): The scalar model containing mass and particle information.

    Returns:
        HP.Predictions: A populated Predictions object suitable for use with
        HiggsBounds and HiggsSignals.
    """

    # create the model predictions
    pred = HP.Predictions()  # type: ignore[attr-defined]

    # add a SM-like Higgs boson with SM-like couplings
    H = pred.addParticle(HP.NeutralScalar(model.SMHiggs, "even"))  # type: ignore[attr-defined]

    # SM Higgs mass
    mH = 125.09

    # set the SM Higgs mass
    H.setMass(mH)

    # TODO: Is this necessary?
    HP.effectiveCouplingInput(H, HP.scaledSMlikeEffCouplings(1.0),reference="SMHiggsEW")  # type: ignore[attr-defined]

    # add BSM CP-even neutral scalars
    for scalar in model.particles['neutralScalarsCPEven']:
        pred.addParticle(HP.NeutralScalar(scalar, 'even'))  # type: ignore[attr-defined]

    # add BSM CP-odd neutral scalars
    for scalar in model.particles['neutralScalarsCPOdd']:
        pred.addParticle(HP.NeutralScalar(scalar, 'odd'))  # type: ignore[attr-defined]

    # add BSM charged scalars
    for scalar in model.particles['chargedScalars']:
        pred.addParticle(HP.ChargedScalar(scalar))  # type: ignore[attr-defined]

    # add BSM doubly charged scalars
    for scalar in model.particles['doublyChargedScalars']:
        pred.addParticle(HP.DoublyChargedScalar(scalar))  # type: ignore[attr-defined]

    return pred

@lru_cache(maxsize=None)
def get_higgs_signals():
    """
    Loads and caches the HiggsSignals dataset.

    Returns:
        HS.Signals: An object containing the experimental Higgs signal measurements.
    """

    # get HS dataset
    signals = HS.Signals(hsdataset_dir())  # type: ignore[attr-defined]

    return signals

@lru_cache(maxsize=None)
def get_higgs_bounds():
    """
    Loads and caches the HiggsBounds dataset.

    Returns:
        HB.Bounds: An object containing the experimental Higgs exclusion bounds.
    """

    # get HB dataset
    bounds = HB.Bounds(hbdataset_dir())  # type: ignore[attr-defined]

    return bounds
