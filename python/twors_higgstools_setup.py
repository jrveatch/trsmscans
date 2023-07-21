import Higgs.predictions as HP
import Higgs.bounds as HB
import Higgs.signals as HS

from twors_higgstools_functions import *   # probably need much less as in principle can read in everything from the .tsv output from scanners

pred = HP.Predictions() # create the model predictions

#bounds = HB.Bounds('../hbdataset') # load HB dataset
#signals = HS.Signals('../hsdataset') # load HS dataset

bounds = HB.Bounds('../data/hbdataset') # load HB dataset                                                                                                                       
signals = HS.Signals('../data/hsdataset') # load HS dataset

# add a SM-like Higgs boson with SM-like couplings

h1 = pred.addParticle(HP.NeutralScalar("h1", "even"))

# add second BSM Higgs boson which decays to two h bosons and is produced via gluon fusion

h2 = pred.addParticle(HP.NeutralScalar("h2", "even"))

h3 = pred.addParticle(HP.NeutralScalar("h3", "even"))


