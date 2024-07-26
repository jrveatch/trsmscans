
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

        self.readYaml()

    # read .yml file
    def readYaml(self):

        # read in model yaml file
        with open(self.ymlfile,'r') as file:
            # read yaml data for model
            yaml_data = yaml.safe_load(file)[self.name]
            # read particles
            self.particles = yaml_data['particles']
            # read parameters
            self.params = yaml_data['parameters']

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

    # get list of parameter name
    def parameterList(self):
        return list(self.params.keys())

    # get parameter min
    def min(self,parname):
        return self.params[parname]['min']

    # get parameter max
    def max(self,parname):
        return self.params[parname]['max']
