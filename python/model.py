
import os

# class that holds information about the model being used
class Model():
    
    def __init__(self,name):

        # name of the model
        self.name = name

        # directory where model information is stored
        self.modeldir = os.environ['DATADIR']+"/models/"

        # template .ini filename
        self.templateini = self.modeldir + self.name + "_template.ini"
        
        return
