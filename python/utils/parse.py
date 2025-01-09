
# standard libraries
import logging

# third-party libraries
import diptest
import pandas as pd

# local modules
from utils.decay_utils import valid_decays
from utils.df_utils import get_df, get_header_string
from utils.masses import Masses
from utils.model import Model
from utils.point import Point

# class to parse arrays and provide details about data
class Parse:

    # load new set of arrays
    def __init__(self,
                 masses: Masses,
                 model_name: str,
                 file_name: str = ""):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # initialize model name
        self.__model_name = model_name

        # initialize model
        self.__model = Model(model_name)

        # initialize HName and SName
        self.__HName = masses.HName
        self.__SName = masses.SName

        # initialize dictionary of parameter arrays
        self.__par_arrays: dict[str,pd.Series] = {}

        # get arrays from file name if it is provided
        if file_name:
            self.read_file(file_name)

    # load new arrays
    def read_file(self,
                  file_name: str) -> None:

        # create dataframe object if it does not exist
        if not hasattr(self,"tsv_data"):
            self.data = get_df(file_name)

        # get arrays masked by filters
        self.__make_filtered_arrays()

    # find the point that maximizes xb
    def get_max_xb_point(self,
                         decay: str) -> Point:
        
        # get xb
        xb = self.get_xb(decay)

        # get index of maximum xsec times BR
        self.max_idx = xb.idxmax()
        
        # make dictionary for parameter values for max_xb
        max_xb_par_vals = {par: array[self.max_idx] for par, array in self.__par_arrays.items()}

        # return a point object holding xb and other parameters
        return Point(xb = xb[self.max_idx],
                     model_name = self.__model_name,
                     par_vals = max_xb_par_vals)

    @property
    def tsv_header(self) -> str:
        """Header from .tsv file"""
        return get_header_string(self.data)

    # get minimum value of a parameter
    def get_min(self,
                par_name: str) -> float:
        return self.__par_arrays[par_name].min()

    # get maximum value of a parameter
    def get_max(self,
                par_name: str) -> float:
        return self.__par_arrays[par_name].max()
    
    @property
    def parameter_arrays(self) -> dict[str,pd.Series]:
        """Dictionary of the parameter arrays"""
        return self.__par_arrays

    # function that checks whether xb is unimodal in a parameter
    def is_bimodal(self,
                   param_name: str,
                   decay: str) -> bool:

        # percentile threshold for xb
        percentile_threshold = 0.98

        # get xb
        xb = self.get_xb(decay)

        # number of points available
        num_points = len(xb)

        # minimum number of points for test
        min_points = 200

        # modify percentile threshold to ensure there are at least min_points
        if num_points * (1.0 - percentile_threshold ) < min_points:
            percentile_threshold = 1.0 - min_points/num_points

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # get xb value that corresponds to percentile threshold
        threshold_value = xb.quantile(percentile_threshold)

        # get set of parameter values with xb in selected percentile
        param_selected = self.__par_arrays[param_name][xb > threshold_value] 

        # use Hartigan's dip test for unimodality
        dip, pval = diptest.diptest(param_selected)

        # p-value threshold for multimodality
        pval_threshold = 0.05

        # if p-value is below threshold, return True, otherwise return False
        if pval < pval_threshold:
            return True
        else:
            return False

    # get xb array
    def get_xb(self,
               decay: str) -> pd.Series:

        # get production cross section
        xb_prod = self.__get_xb_prod()

        # if NoDecay is specified, only return production cross-section
        if decay == "NoDecay":
            xb = xb_prod
        # otherwise include decay BR in xb
        else:
            # get branching ratio
            xb_decay = self.__get_xb_decay(decay)

            # get total xsec times BR
            xb = xb_prod * xb_decay

        # return total xsec time BR
        return xb

    # get maximum xb for the production
    def __get_xb_prod(self) -> pd.Series:

        # TODO: take decay as argument for other production modes

        # get production cross section
        # currently for gg->X->SH
        xb_prod = self.filtered_data['x_H3_gg'] * self.filtered_data['b_H3_H1H2']

        return xb_prod

    # get maximum xb for the decay
    def __get_xb_decay(self,
                       decay: str) -> pd.Series:

        # H xsec and BR values
        br_H_bb = self.filtered_data['b_'+self.__HName+'_bb']
        br_H_tautau = self.filtered_data['b_'+self.__HName+'_tautau']
        br_H_WW = self.filtered_data['b_'+self.__HName+'_WW']
        br_H_ZZ = self.filtered_data['b_'+self.__HName+'_ZZ']
        br_H_gamgam = self.filtered_data['b_'+self.__HName+'_gamgam']

        # S xsec and BR values
        br_S_bb = self.filtered_data['b_'+self.__SName+'_bb']
        br_S_tautau = self.filtered_data['b_'+self.__SName+'_tautau']
        br_S_WW = self.filtered_data['b_'+self.__SName+'_WW']
        br_S_ZZ = self.filtered_data['b_'+self.__SName+'_ZZ']
        br_S_gamgam = self.filtered_data['b_'+self.__SName+'_gamgam']

        # get appropriate BR for decay mode
        match decay:

            # 4b case
            case "SHbbbb":
                xb_decay = br_S_bb * br_H_bb

            # bbtautau cases
            case "SbbHtautau":
                xb_decay = br_S_bb * br_H_tautau
            case "StautauHbb":
                xb_decay = br_S_tautau * br_H_bb
            case "SHbbtautau":
                arr1 = br_S_bb * br_H_tautau
                arr2 = br_S_tautau * br_H_bb
                xb_decay = arr1 + arr2

            # bbWW cases
            case "SbbHWW":
                xb_decay = br_S_bb * br_H_WW
            case "SWWHbb":
                xb_decay = br_S_WW * br_H_bb
            case "SHbbWW":
                arr1 = br_S_bb * br_H_WW
                arr2 = br_S_WW * br_H_bb
                xb_decay = arr1 + arr2

            # bbZZ cases
            case "SbbHZZ":
                xb_decay = br_S_bb * br_H_ZZ
            case "SZZHbb":
                xb_decay = br_S_ZZ * br_H_bb
            case "SHbbZZ":
                arr1 = br_S_bb * br_H_ZZ
                arr2 = br_S_ZZ * br_H_bb
                xb_decay = arr1 + arr2

            # VVtautau cases
            case "SVVHbb":
                xb_decay = (br_S_WW + br_S_ZZ) * br_H_bb
            case "SbbHVV":
                xb_decay = br_S_bb * (br_H_WW + br_H_ZZ)
            case "SHVVbb":
                arr1 = (br_S_WW + br_S_ZZ) * br_H_bb
                arr2 = br_S_bb + (br_H_WW + br_H_ZZ)
                xb_decay = arr1 + arr2

            # WWtautau cases
            case "SWWHtautau":
                xb_decay = br_S_WW * br_H_tautau
            case "StautauHWW":
                xb_decay = br_S_tautau * br_H_WW
            case "SHWWtautau":
                arr1 = br_S_WW * br_H_tautau
                arr2 = br_S_tautau * br_H_WW
                xb_decay = arr1 + arr2

            # ZZtautau cases
            case "SZZHtautau":
                xb_decay = br_S_ZZ * br_H_tautau
            case "StautauHZZ":
                xb_decay = br_S_tautau * br_H_ZZ
            case "SHZZtautau":
                arr1 = br_S_ZZ * br_H_tautau
                arr2 = br_S_tautau * br_H_ZZ
                xb_decay = arr1 + arr2

            # VVtautau cases
            case "SVVHtautau":
                xb_decay = (br_S_WW + br_S_ZZ) * br_H_tautau
            case "StautauHVV":
                xb_decay = br_S_tautau * (br_H_WW + br_H_ZZ)
            case "SHVVtautau":
                arr1 = (br_S_WW + br_S_ZZ) * br_H_tautau
                arr2 = br_S_tautau * (br_H_WW + br_H_ZZ)
                xb_decay = arr1 + arr2

            # bbgamgam cases
            case "SbbHgamgam":
                xb_decay = br_S_bb * br_H_gamgam
            case "SgamgamHbb":
                xb_decay = br_S_gamgam * br_H_bb
            case "SHbbgamgam":
                arr1 = br_S_bb * br_H_gamgam
                arr2 = br_S_gamgam * br_H_bb
                xb_decay = arr1 + arr2

            # raise an exception in all other cases
            case _:
                raise ValueError(
                    f"Unrecognized decay {decay}\n"
                    f"Allowed decays are: {', '.join(valid_decays())}."
                )

        # return the decay BR
        return xb_decay

    # get arrays of the filters
    def __set_filters(self) -> None:
        self.__filters = (self.data['filt_width'] * self.data['filt_bounds'] * self.data['filt_signals']).astype(bool)

    # apply filters as mask
    def __make_filtered_arrays(self) -> None:
        
        # get array of filters to use as a mask
        self.__set_filters()

        # populate a dictionary of series for each model parameter
        model_parameters = self.__model.parameters
        self.__par_arrays = {name: self.filtered_data[par['fullname']] for name, par in model_parameters.items()}

    @property
    def num_filtered_points(self) -> int:
        """Number of filtered points"""
        return len(self.filtered_data)

    @property
    def num_unfiltered_points(self) -> int:
        """Number of unfiltered points"""
        return len(self.data)
    
    # write max xb line to a .tsv file
    def write_max_xb_line(self,
                          file_name: str
                         ) -> None:

        # get max xb row from dataframe
        row = self.data.loc[[self.max_idx]]

        # write it to the summary .tsv
        row.to_csv(file_name,
                   sep='\t',
                   index=True,
                   mode='a',
                   header=False)

        return

    @property
    def filtered_data(self) -> pd.DataFrame:
        return self.data[self.__filters]
