
import os
import yaml

# class that holds information about the model being used
class Model():

    def __init__(self,name):

        # name of the model
        self.name = name

        # directory where model information is stored
        self.modeldir = os.environ['DATADIR']+"models/"

        # template .ini filename
        self.templateini = self.modeldir + self.name + "_template.ini"

        # read in model yaml file
        filename = self.modeldir + self.name + "_params.yml"
        with open(filename,'r') as file:
            self.params = yaml.safe_load(file)[self.name]

    def parameterList(self):
        return self.params.keys()

    def min(self,parname):
        return self.params[parname]['min']

    def max(self,parname):
        return self.params[parname]['max']
