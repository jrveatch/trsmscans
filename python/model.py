
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

        # template .ini filename
        self.__templateini = self.__model_dir + self.__name + "_template.ini"

        # model yaml file
        __ymlname = self.__model_dir + self.__name + "_params.yml"

        # create empty __model_params dictionary
        self.__model_params = {}

        # TODO: Check to make sure .ini template and yaml exist

        # read in model yaml file as a dictionary
        with open(__ymlname,'r') as file:
            self.__model_params = yaml.safe_load(file)[self.__name]

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
