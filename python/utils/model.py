
# standard libraries
import logging
import os

# third-party libraries
import yaml

# class that holds information about the model being used
class Model:

    def __init__(self,
                 name: str):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # name of the model
        self.__name = name

        # directory where model information is stored
        self.__model_dir = os.environ['DATADIR']+"models/"

        # model yaml file
        self.__yaml_name = os.path.join(self.__model_dir, f"{self.__name}_params.yml")

        # template .ini file name
        self.__template_ini = os.path.join(self.__model_dir, f"{self.__name}_template.ini")

        self.__read_yaml()

    # read .yml file
    def __read_yaml(self):
      
        # create empty particles dictionary
        self.particles = {}

        # create empty dictionary of input parameters
        self.__input_params: dict[str,any] = {}

        # create empty list of of output parameters
        self.__output_params: dict[str,any] = {}

        # read in model yaml file
        with open(self.__yaml_name,'r') as file:
            # read yaml data for model
            yaml_data = yaml.safe_load(file)[self.__name]
            # read particles
            self.particles = yaml_data['particles']
            # read input parameters
            self.__input_params = yaml_data['input_parameters']
            # read output parameters
            self.__output_params = yaml_data['output_parameters']

        # convert NoneType entries to empty dictionaries
        for key in self.particles:
            if self.particles[key] == None:
                self.particles[key] = {}
        
        # make sure exactly 1 SM-like Higgs is provided
        if not len(self.particles['SMHiggs']) == 1:
            self.logger.warning('1 SM Higgs expected, found ' + len(self.particles['SMHiggs']))
            return
        
        # store SM-like Higgs
        self.SMHiggs = self.particles['SMHiggs'][0]

        # store BSM scalars
        self.BSMScalars = []
        for key in self.particles:
            # skip SM-like Higgs for this list
            if key == 'SMHiggs':
                continue
            self.BSMScalars.extend(self.particles[key])
        
        # store list of all scalars
        self.AllScalars = self.particles['SMHiggs'] + self.BSMScalars

    @property
    def input_parameters(self) -> dict:
        """Dictionary of input parameters"""
        return self.__input_params

    @property
    def output_parameters(self) -> dict:
        """Dictionary of output parameters"""
        return self.__output_params

    # get a single input parameter
    def input_parameter(self,
                        par_name: str) -> dict[str,any]:
        return self.__input_params[par_name]

    @property
    def input_parameter_names(self) -> list[str]:
        """List of input parameter names"""
        return list(self.__input_params.keys())

    @property
    def output_parameter_names(self) -> list[str]:
        """List of output parameter names"""
        return list(self.__output_params.keys())

    @property
    def parameter_names(self) -> list[str]:
        """List of all parameter names"""
        return list(self.__input_params.keys()) + list(self.__output_params.keys())

    # get model parameter starting min
    def starting_min(self,par_name) -> float:
        return self.__input_params[par_name]['min']

    # get model parameter starting max
    def starting_max(self,par_name) -> float:
        return self.__input_params[par_name]['max']

    @property
    def name(self) -> str:
        """Model name"""
        return self.__name

    @property
    def template_ini(self) -> str:
        """Model template .ini file name"""
        return self.__template_ini
