
# standard libraries
import logging
import os
from typing import Dict, List

# third-party libraries
import yaml

# class that holds information about the model being used
class Model:

    def __init__(self,
                 name: str,
                 masses: Dict[str,float] = {}) -> None:
        
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

        # read model yaml file
        self.__read_yaml()

        # make mass maps
        self.__masses = masses
        self.__build_mass_maps()

        # make dictionary of width parameters
        self.__make_width_params()

    def __read_yaml(self) -> None:
        """Read the model .yml file and store the information."""
      
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


    def __build_mass_maps(self) -> None:
        """Build dictionaries to map between original particle names and mass-ordered 'H_i' names."""

        # check that all scalar masses are provided
        if not all(k in self.__masses for k in self.AllScalars):
            raise ValueError(f"Mass dictionary must contain keys {self.AllScalars}. Provided keys: {list(self.__masses.keys())}")
        
        # Sort particles by mass and assign "H_i" names
        sorted_particles = sorted(self.__masses.items(), key=lambda x: x[1])
        self.name_map = {}  # Maps scalar particle names to 'H_i' names
        self.h_map = {}  # Maps 'H_i' names to (original name, mass)

        for i, (particle, mass) in enumerate(sorted_particles, start=1):
            hi_name = f"H{i}"
            self.name_map[particle] = hi_name
            self.h_map[hi_name] = (particle, mass)

    def __make_width_params(self) -> None:
        """Make dictionary of width parameters, mapping particle name to mass-ordered 'H_i' name."""
        self.__width_params: dict[str,any] = {}
        for particle in self.AllScalars:
            self.__width_params["w"+particle] = {'fullname': f"w_{self.get_ordered_scalar_name(particle)}"}

    def get_mass(self,
                 name: str) -> float:
        """
        Retrieve the mass of a particle using either its original name (e.g., 'H', 'S', 'X')
        or its mass-ordered 'H_i' name ('H1', 'H2', 'H3').

        :param name: Particle name (e.g., 'H', 'S', 'X') or 'H_i' name ('H1', 'H2', 'H3').
        :return: Corresponding mass value.
        """
        if name in self.__masses:
            return self.__masses[name]
        elif name in self.h_map:
            return self.h_map[name][1]
        else:
            raise KeyError(
                f"Invalid particle name: {name}. Available names: {self.AllScalars + list(self.h_map.keys())}"
            )

    def get_ordered_scalar_name(self,
                                particle_name: str) -> str:
        """
        Retrieve the 'H_i' name given an original particle name (e.g., 'H', 'S', 'X').

        :param original_name: 'H', 'S', or 'X'.
        :return: Corresponding 'H_i' name (e.g., 'H1', 'H2', 'H3').
        """
        if particle_name in self.name_map:
            return self.name_map[particle_name]
        else:
            raise KeyError(
                f"Invalid original name: {particle_name}. Available names: {self.AllScalars}"
            )

    @property
    # TODO: Make this more generalized
    def mass_string(self) -> str:
        """
        Returns a formatted string in the form "X<XMass>_S<SMass>".

        :return: A string representation of the masses of X and S.
        """
        x_mass = self.__masses["X"]
        s_mass = self.__masses["S"]
        return f"X{int(x_mass)}_S{int(s_mass)}"

    @property
    def input_parameters(self) -> dict:
        """Dictionary of input parameters"""
        return self.__input_params

    @property
    def output_parameters(self) -> dict:
        """Dictionary of output parameters"""
        return self.__output_params

    @property
    def width_parameters(self) -> dict:
        """Dictionary of width parameters"""
        return self.__width_params

    # get a single input parameter
    def input_parameter(self,
                        par_name: str) -> Dict[str,any]:
        return self.__input_params[par_name]

    @property
    def input_parameter_names(self) -> List[str]:
        """List of input parameter names"""
        return list(self.__input_params.keys())

    @property
    def output_parameter_names(self) -> List[str]:
        """List of output parameter names"""
        return list(self.__output_params.keys())

    @property
    def width_parameter_names(self) -> List[str]:
        """List of output parameter names"""
        return list(self.__width_params.keys())

    @property
    def all_parameter_names(self) -> List[str]:
        """List of all parameter names"""
        return self.input_parameter_names + self.output_parameter_names + self.width_parameter_names

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
