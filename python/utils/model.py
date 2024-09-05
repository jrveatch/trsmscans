
import os
import yaml

# class that holds information about the model being used
class Model:

    def __init__(self,
                 name: str):

        # name of the model
        self.__name = name

        # directory where model information is stored
        self.__model_dir = os.environ['DATADIR']+"models/"

        # model yaml file
        self.__ymlname = self.__model_dir + self.__name + "_params.yml"

        # template .ini file name
        self.__templateini = self.__model_dir + self.__name + "_template.ini"

        self.__read_yaml()

    # read .yml file
    def __read_yaml(self):
      
        # create empty particles dictionary
        self.particles = {}

        # create empty __model_params dictionary
        self.__model_params = {}

        # read in model yaml file
        with open(self.__ymlname,'r') as file:
            # read yaml data for model
            yaml_data = yaml.safe_load(file)[self.__name]
            # read particles
            self.particles = yaml_data['particles']
            # read parameters
            self.__model_params = yaml_data['parameters']

        # convert NoneType entries to empty dictionaries
        for key in self.particles:
            if self.particles[key] == None:
                self.particles[key] = {}
        
        # make sure exactly 1 SM-like Higgs is provided
        if not len(self.particles['SMHiggs']) == 1:
            print('1 SM Higgs expected, found ' + len(self.particles['SMHiggs']))
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

    # get dictionary of model parameters
    def parameters(self) -> dict:
        return self.__model_params

    # get a single model parameter
    def parameter(self,parname) -> dict:
        return self.__model_params[parname]

    # get list of model parameter names
    def parameter_names(self) -> list:
        return list(self.__model_params.keys())

    # get model parameter starting min
    def starting_min(self,parname) -> float:
        return self.__model_params[parname]['min']

    # get model parameter starting max
    def starting_max(self,parname) -> float:
        return self.__model_params[parname]['max']

    # get model name
    def name(self) -> str:
        return self.__name

    # get model template .ini file
    def template_ini(self) -> str:
        return self.__templateini
