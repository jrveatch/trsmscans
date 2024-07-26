
import os
import yaml

# class that holds information about the model being used
class Model():

    def __init__(self,name):

        # name of the model
        self.name = name

        # directory where model information is stored
        self.modeldir = os.environ['DATADIR']+"models/"

        # model yaml file
        self.ymlfile = self.modeldir + self.name + "_params.yml"

        # template .ini filename
        self.templateini = self.modeldir + self.name + "_template.ini"

        # make sure .yml file exists
        if not os.path.isfile(self.ymlfile):
            raise FileNotFoundError("YAML file " + self.ymlfile + " does not exist. Exiting.")

        # make sure template .ini file exists
        if not os.path.isfile(self.templateini):
            raise FileNotFoundError("Template .ini file " + self.templateini + " does not exist. Exiting.")

        # read in model yaml file
        with open(self.ymlfile,'r') as file:
            self.params = yaml.safe_load(file)[self.name]

    # get list of parameter name
    def parameterList(self):
        return list(self.params.keys())

    # get parameter min
    def min(self,parname):
        return self.params[parname]['min']

    # get parameter max
    def max(self,parname):
        return self.params[parname]['max']
