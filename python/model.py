
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

        # model yaml file
        filename = self.modeldir + self.name + "_params.yml"

        # TODO: Check to make sure .ini template and yaml exist

        # read in model yaml file
        with open(filename,'r') as file:
            self.params = yaml.safe_load(file)[self.name]

    # get list of parameter name
    def parameterList(self):
        return self.params.keys()

    # get parameter min
    def min(self,parname):
        return self.params[parname]['min']

    # get parameter max
    def max(self,parname):
        return self.params[parname]['max']
