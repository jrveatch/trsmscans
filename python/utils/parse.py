
# standard libraries
import logging
from typing import Dict

# third-party libraries
import diptest
import pandas as pd

# local modules
from utils.decay_utils import valid_decays
from utils.df_utils import get_df, get_header_string
from utils.model import Model
from utils.point import Point

# class to parse arrays and provide details about data
class Parse:

    # load new set of arrays
    def __init__(self,
                 model: 'Model',
                 file_name: str = ""):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize model
        self.__model = model

        # initialize HName and SName
        self.__HName = model.get_ordered_scalar_name('H')
        self.__SName = model.get_ordered_scalar_name('S')

        # initialize dictionaries of parameter arrays
        self.__in_par_arrays: Dict[str,pd.Series] = {}
        self.__out_par_arrays: Dict[str,pd.Series] = {}
        self.__width_par_arrays: Dict[str,pd.Series] = {}
        self.__par_arrays: Dict[str,pd.Series] = {}

        # get arrays from file name if it is provided
        if file_name:
            self.read_file(file_name)

    @property
    def filtered_data(self) -> pd.DataFrame:
        return self.data[self.__filters]

    @property
    def tsv_header(self) -> str:
        """Header from .tsv file"""
        return get_header_string(self.data)

    @property
    def input_parameter_arrays(self) -> Dict[str,pd.Series]:
        """Dictionary of the parameter arrays"""
        return self.__in_par_arrays

    @property
    def num_filtered_points(self) -> int:
        """Number of filtered points"""
        return len(self.filtered_data)

    @property
    def num_unfiltered_points(self) -> int:
        """Number of unfiltered points"""
        return len(self.data)

    def read_file(self,
                  file_name: str) -> None:
        """Load new arrays from a .tsv file"""

        # create dataframe object if it does not exist
        if not hasattr(self,"data"):
            self.data = get_df(file_name)

        # get arrays masked by filters
        self.__make_filtered_arrays()

    def get_max_xb_point(self,
                         decay: str) -> Point:
        """Find the point with the highest xb"""
        
        # get xb
        xb = self.get_xb(decay)

        # get index of maximum xsec times BR
        self.max_idx = xb.idxmax()
        
        # make dictionary for parameter values for max_xb
        max_xb_par_vals = {par: array[self.max_idx] for par, array in self.__par_arrays.items()}

        # return a point object holding xb and other parameters
        return Point(xb = xb[self.max_idx],
                     model = self.__model,
                     par_vals = max_xb_par_vals)

    def get_min(self,
                par_name: str) -> float:
        """Get the minimum value for a parameter in the data"""
        return self.__par_arrays[par_name].min()

    def get_max(self,
                par_name: str) -> float:
        """Get the maximum value for a parameter in the data"""
        return self.__par_arrays[par_name].max()

    def is_bimodal(self,
                   param_name: str,
                   decay: str) -> bool:
        """Check whether xb is unimodal in a parameter"""

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
        param_selected = self.__in_par_arrays[param_name][xb > threshold_value] 

        # use Hartigan's dip test for unimodality
        _, pval = diptest.diptest(param_selected)

        # p-value threshold for multimodality
        pval_threshold = 0.05

        # if p-value is below threshold, return True, otherwise return False
        if pval < pval_threshold:
            return True
        else:
            return False

    def get_xb(self,
               decay: str) -> pd.Series:
        """Get array of xb values"""

        # get production cross section
        xsec_prod = self.__get_xsec_prod()

        # if NoDecay is specified, only return production cross-section
        if decay == "NoDecay":
            xb = xsec_prod
        # otherwise include decay BR in xb
        else:
            # get branching ratio
            br_decay = self.__get_br_decay(decay)

            # get total xsec times BR
            xb = xsec_prod * br_decay

        # return total xsec time BR
        return xb

    def __get_xsec_prod(self) -> pd.Series:
        """Get array of production cross-sections"""
        return self.filtered_data['x_H3_gg'] #* self.filtered_data['b_H3_H1H2']

    def __get_br_decay(self,
                       decay: str) -> pd.Series:
        """Get arrays of decay branching ratios"""
        
        # BSM BRs
        br_X_SH = self.filtered_data['b_H3_H1H2']
        br_X_SS = self.filtered_data['b_H3_'+self.__SName+self.__SName]
        br_X_HH = self.filtered_data['b_H3_'+self.__HName+self.__HName]

        # H SM BRs
        br_H_bb = self.filtered_data['b_'+self.__HName+'_bb']
        br_H_tautau = self.filtered_data['b_'+self.__HName+'_tautau']
        br_H_WW = self.filtered_data['b_'+self.__HName+'_WW']
        br_H_ZZ = self.filtered_data['b_'+self.__HName+'_ZZ']
        br_H_gamgam = self.filtered_data['b_'+self.__HName+'_gamgam']

        # S SM BRs
        br_S_bb = self.filtered_data['b_'+self.__SName+'_bb']
        br_S_tautau = self.filtered_data['b_'+self.__SName+'_tautau']
        br_S_WW = self.filtered_data['b_'+self.__SName+'_WW']
        br_S_ZZ = self.filtered_data['b_'+self.__SName+'_ZZ']
        br_S_gamgam = self.filtered_data['b_'+self.__SName+'_gamgam']

        # get appropriate BR for decay mode
        # 4b cases
        if decay == "SHbbbb":
            br_decay = br_X_SH * br_S_bb * br_H_bb
        elif decay == "SSbbbb":
            br_decay = br_X_SS * br_S_bb * br_S_bb
        elif decay == "HHbbbb":
            br_decay = br_X_HH * br_H_bb * br_H_bb
        elif decay == "Xbbbb":
            br1 = br_X_SH * br_S_bb * br_H_bb
            br2 = br_X_SS * br_S_bb * br_S_bb
            br3 = br_X_HH * br_H_bb * br_H_bb
            br_decay = br1 + br2 + br3

        # bbtautau cases
        elif decay == "SbbHtautau":
            br_decay = br_X_SH * br_S_bb * br_H_tautau
        elif decay == "StautauHbb":
            br_decay = br_X_SH * br_S_tautau * br_H_bb
        elif decay == "SHbbtautau":
            br1 = br_X_SH * br_S_bb * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbtautau":
            br_decay = br_X_SS * br_S_bb * br_S_tautau
        elif decay == "HHbbtautau":
            br_decay = br_X_HH * br_H_bb * br_H_tautau
        elif decay == "Xbbtautau":
            br1 = br_X_SH * br_S_bb * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_tautau
            br4 = br_X_HH * br_H_bb * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # bbWW cases
        elif decay == "SbbHWW":
            br_decay = br_X_SH * br_S_bb * br_H_WW
        elif decay == "SWWHbb":
            br_decay = br_X_SH * br_S_WW * br_H_bb
        elif decay == "SHbbWW":
            br1 = br_X_SH * br_S_bb * br_H_WW
            br2 = br_X_SH * br_S_WW * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbWW":
            br_decay = br_X_SS * br_S_bb * br_S_WW
        elif decay == "HHbbWW":
            br_decay = br_X_HH * br_H_bb * br_H_WW
        elif decay == "XbbWW":
            br1 = br_X_SH * br_S_bb * br_H_WW
            br2 = br_X_SH * br_S_WW * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_WW
            br4 = br_X_HH * br_H_bb * br_H_WW
            br_decay = br1 + br2 + br3 + br4

        # bbZZ cases
        elif decay == "SbbHZZ":
            br_decay = br_X_SH * br_S_bb * br_H_ZZ
        elif decay == "SZZHbb":
            br_decay = br_X_SH * br_S_ZZ * br_H_bb
        elif decay == "SHbbZZ":
            br1 = br_X_SH * br_S_bb * br_H_ZZ
            br2 = br_X_SH * br_S_ZZ * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbZZ":
            br_decay = br_X_SS * br_S_bb * br_S_ZZ
        elif decay == "HHbbZZ":
            br_decay = br_X_HH * br_H_bb * br_H_ZZ
        elif decay == "XbbZZ":
            br1 = br_X_SH * br_S_bb * br_H_ZZ
            br2 = br_X_SH * br_S_ZZ * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_ZZ
            br4 = br_X_HH * br_H_bb * br_H_ZZ
            br_decay = br1 + br2 + br3 + br4

        # bbVV cases
        elif decay == "SbbHVV":
            br_decay = br_X_SH * br_S_bb * (br_H_WW + br_H_ZZ)
        elif decay == "SVVHbb":
            br_decay = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_bb
        elif decay == "SHbbVV":
            br1 = br_X_SH * br_S_bb * (br_H_WW + br_H_ZZ)
            br2 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbVV":
            br_decay = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_bb
        elif decay == "HHbbVV":
            br_decay = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_bb
        elif decay == "XbbVV":
            br1 = br_X_SH * br_S_bb * (br_H_WW + br_H_ZZ)
            br2 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_bb
            br3 = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_bb
            br4 = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_bb
            br_decay = br1 + br2 + br3 + br4

        # WWtautau cases
        elif decay == "SWWHtautau":
            br_decay = br_X_SH * br_S_WW * br_H_tautau
        elif decay == "StautauHWW":
            br_decay = br_X_SH * br_S_tautau * br_H_WW
        elif decay == "SHWWtautau":
            br1 = br_X_SH * br_S_WW * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_WW
            br_decay = br1 + br2
        elif decay == "SSWWtautau":
            br_decay = br_X_SS * br_S_WW * br_S_tautau
        elif decay == "HHWWtautau":
            br_decay = br_X_HH * br_H_WW * br_H_tautau
        elif decay == "XWWtautau":
            br1 = br_X_SH * br_S_WW * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_WW
            br3 = br_X_SS * br_S_WW * br_S_tautau
            br4 = br_X_HH * br_H_WW * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # ZZtautau cases
        elif decay == "SZZHtautau":
            br_decay = br_X_SH * br_S_ZZ * br_H_tautau
        elif decay == "StautauHZZ":
            br_decay = br_X_SH * br_S_tautau * br_H_ZZ
        elif decay == "SHZZtautau":
            br1 = br_X_SH * br_S_ZZ * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_ZZ
            br_decay = br1 + br2
        elif decay == "SSZZtautau":
            br_decay = br_X_SS * br_S_ZZ * br_S_tautau
        elif decay == "HHZZtautau":
            br_decay = br_X_HH * br_H_ZZ * br_H_tautau
        elif decay == "XZZtautau":
            br1 = br_X_SH * br_S_ZZ * br_H_tautau
            br2 = br_X_SH * br_S_tautau * br_H_ZZ
            br3 = br_X_SS * br_S_ZZ * br_S_tautau
            br4 = br_X_HH * br_H_ZZ * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # VVtautau cases
        elif decay == "SVVHtautau":
            br_decay = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_tautau
        elif decay == "StautauHVV":
            br_decay = br_X_SH * br_S_tautau * (br_H_WW + br_H_ZZ)
        elif decay == "SHVVtautau":
            br1 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_tautau
            br2 = br_X_SH * br_S_tautau * (br_H_WW + br_H_ZZ)
            br_decay = br1 + br2
        elif decay == "SSVVtautau":
            br_decay = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_tautau
        elif decay == "HHVVtautau":
            br_decay = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_tautau
        elif decay == "XVVtautau":
            br1 = br_X_SH * (br_S_WW + br_S_ZZ) * br_H_tautau
            br2 = br_X_SH * br_S_tautau * (br_H_WW + br_H_ZZ)
            br3 = br_X_SS * (br_S_WW + br_S_ZZ) * br_S_tautau
            br4 = br_X_HH * (br_H_WW + br_H_ZZ) * br_H_tautau
            br_decay = br1 + br2 + br3 + br4

        # bbgamgam cases
        elif decay == "SbbHgamgam":
            br_decay = br_X_SH * br_S_bb * br_H_gamgam
        elif decay == "SgamgamHbb":
            br_decay = br_X_SH * br_S_gamgam * br_H_bb
        elif decay == "SHbbgamgam":
            br1 = br_X_SH * br_S_bb * br_H_gamgam
            br2 = br_X_SH * br_S_gamgam * br_H_bb
            br_decay = br1 + br2
        elif decay == "SSbbgamgam":
            br_decay = br_X_SS * br_S_bb * br_S_gamgam
        elif decay == "HHbbgamgam":
            br_decay = br_X_HH * br_H_bb * br_H_gamgam
        elif decay == "Xbbgamgam":
            br1 = br_X_SH * br_S_bb * br_H_gamgam
            br2 = br_X_SH * br_S_gamgam * br_H_bb
            br3 = br_X_SS * br_S_bb * br_S_gamgam
            br4 = br_X_HH * br_H_bb * br_H_gamgam
            br_decay = br1 + br2 + br3 + br4

        # raise an exception in all other cases
        else:
            raise ValueError(
                f"Unrecognized decay {decay}\n"
                f"Allowed decays are: {', '.join(valid_decays())}."
            )

        # return the decay BR
        return br_decay

    def __set_filters(self) -> None:
        """Get arrays of filter decisions"""
        self.__filters = (self.data['filt_width'] * self.data['filt_bounds'] * self.data['filt_signals']).astype(bool)

    def __make_filtered_arrays(self) -> None:
        """Apply filter decisions as a mask"""
        
        # get array of filters to use as a mask
        self.__set_filters()

        # populate a dictionary of series for each input parameter
        self.__in_par_arrays = {name: self.filtered_data[par['fullname']] for name, par in self.__model.input_parameters.items()}

        # populate a dictionary of series for each output parameter
        self.__out_par_arrays = {name: self.filtered_data[par['fullname']] for name, par in self.__model.output_parameters.items()}

        # populate a dictionary of series for each width parameter
        self.__width_par_arrays = {name: self.filtered_data[par['fullname']] for name, par in self.__model.width_parameters.items()}

        # combine all parameter arrays
        self.__par_arrays = {**self.__in_par_arrays, **self.__out_par_arrays, **self.__width_par_arrays}

    def write_max_xb_line(self,
                          file_name: str
                         ) -> None:
        """Write line with max xb to a .tsv file"""

        # get max xb row from dataframe
        row = self.data.loc[[self.max_idx]]

        # write it to the summary .tsv
        row.to_csv(file_name,
                   sep='\t',
                   index=True,
                   mode='a',
                   header=False)
