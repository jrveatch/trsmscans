
# standard libraries
from functools import cached_property
import logging
import os
from typing import Any, Dict, Tuple

# third-party libraries
import yaml

# local modules
from utils.env_utils import data_dir

# class that holds information about the model being used
class Model:

    def __init__(self,
                 name: str,
                 masses: Dict[str, float]) -> None:

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # name of the model
        self.name = name

        # read model yaml file
        self.__read_yaml()

        # store masses and build mass maps
        self.masses = masses

    @property
    def name(self) -> str:
        """Model name"""
        return self.__name

    @name.setter
    def name(self,
             new_name: str) -> None:
        """Set the name property"""
        self.__name = new_name

    @cached_property
    def model_dir(self) -> str:
        """Directory where model information is stored"""
        return os.path.join(data_dir(),"models")

    @cached_property
    def template_ini(self) -> str:
        """Model template .ini file name"""
        return os.path.join(self.model_dir, f"{self.name}_template.ini")

    @property
    def masses(self) -> Dict[str,float]:
        """Dictionary of particle masses"""
        return self.__masses

    @masses.setter
    def masses(self,
                new_masses: Dict[str,float]) -> None:
        """Set the masses dictionary and build mass maps"""
        self.__masses = new_masses
        self.__build_mass_maps()

    @property
    # TODO: Make this more generalized
    def mass_string(self) -> str:
        """
        Returns a formatted string in the form "X<XMass>_S<SMass>".

        :return: A string representation of the masses of X and S.
        """
        x_mass = self.masses["X"]
        s_mass = self.masses["S"]
        return f"X{int(x_mass)}_S{int(s_mass)}"

    @cached_property
    def yaml_name(self) -> str:
        """Model yaml file name"""
        return os.path.join(self.model_dir, f"{self.name}_params.yml")

    @property
    def input_parameters(self) -> Dict[str, Any]:
        """Dictionary of input parameters"""
        return self.__input_params

    @input_parameters.setter
    def input_parameters(self,
                         new_input_params: Dict[str, Any]) -> None:
        """Set the input parameters dictionary"""
        self.__input_params = new_input_params

    @property
    def output_parameters(self) -> dict:
        """Dictionary of output parameters"""
        return self.__output_params

    @output_parameters.setter
    def output_parameters(self,\
                          new_output_params: Dict[str, Any]) -> None:
        """Set the output parameters dictionary"""
        self.__output_params = new_output_params

    @cached_property
    def width_parameters(self) -> Dict[str, Dict[str, str]]:
        """Dictionary mapping 'w<particle>' to {'fullname': 'w_<H_i>'}."""
        return {
            "w" + particle: {
                'fullname': f"w_{self.get_ordered_scalar_name(particle)}"
            }
            for particle in self.AllScalars
        }

    @property
    def input_parameter_full_names(self) -> Tuple[str, ...]:
        """List of input parameter full names"""
        return tuple(item["fullname"] for item in self.input_parameters.values())

    @cached_property
    def input_parameter_names(self) -> Tuple[str, ...]:
        """List of input parameter names"""
        return tuple(self.input_parameters.keys())

    @cached_property
    def output_parameter_names(self) -> Tuple[str, ...]:
        """List of output parameter names"""
        return tuple(self.output_parameters.keys())

    @cached_property
    def width_parameter_names(self) -> Tuple[str, ...]:
        """List of output parameter names"""
        return tuple(self.width_parameters.keys())

    @cached_property
    def all_parameter_names(self) -> Tuple[str, ...]:
        """List of all parameter names"""
        return self.input_parameter_names + self.output_parameter_names + self.width_parameter_names

    @cached_property
    def input_parameter_full_names(self) -> Tuple[str, ...]:
        """List of input parameter full names"""
        return tuple(item["fullname"] for item in self.input_parameters.values())

    @cached_property
    def ini_name_to_fullname_map(self) -> Dict[str, str]:
        return {
            item["ini_name"]: item["fullname"]
            for item in self.input_parameters.values()
            if "ini_name" in item and "fullname" in item
        }

    @cached_property
    def fullname_to_ini_name_map(self) -> Dict[str, str]:
        return {
            item["ini_name"]: item["fullname"]
            for item in self.input_parameters.values()
            if "ini_name" in item and "fullname" in item
        }

    @property
    def particles(self) -> Dict[str, Any]:
        """Dictionary of particles"""
        return self.__particles

    @particles.setter
    def particles(self,
                   new_particles: Dict[str, Any]) -> None:
        """Set the particles dictionary"""
        self.__particles = new_particles

    def __read_yaml(self) -> None:
        """Read the model .yml file and store the information."""

        # read in model yaml file
        with open(self.yaml_name,'r') as file:
            # read yaml data for model
            yaml_data = yaml.safe_load(file)[self.name]
            # read particles
            self.particles = yaml_data['particles']
            # read input parameters
            self.input_parameters = yaml_data['input_parameters']
            # read output parameters
            self.output_parameters = yaml_data['output_parameters']

        # convert NoneType entries to empty dictionaries
        for key in self.particles:
            if self.particles[key] == None:
                self.particles[key] = {}

        # make sure exactly 1 SM-like Higgs is provided
        if not len(self.particles['SMHiggs']) == 1:
            self.logger.warning(f'1 SM Higgs expected, found {len(self.particles["SMHiggs"])}')
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
        if not all(k in self.masses for k in self.AllScalars):
            raise ValueError(f"Mass dictionary must contain keys {self.AllScalars}. Provided keys: {list(self.masses.keys())}")

        # Sort particles by mass and assign "H_i" names
        sorted_particles = sorted(self.masses.items(), key=lambda x: x[1])
        self.name_map = {}  # Maps scalar particle names to 'H_i' names
        self.h_map = {}  # Maps 'H_i' names to (original name, mass)

        for i, (particle, mass) in enumerate(sorted_particles, start=1):
            hi_name = f"H{i}"
            self.name_map[particle] = hi_name
            self.h_map[hi_name] = (particle, mass)

    def get_mass(self,
                 name: str) -> float:
        """
        Retrieve the mass of a particle using either its original name (e.g., 'H', 'S', 'X')
        or its mass-ordered 'H_i' name ('H1', 'H2', 'H3').

        :param name: Particle name (e.g., 'H', 'S', 'X') or 'H_i' name ('H1', 'H2', 'H3').
        :return: Corresponding mass value.
        """
        if name in self.masses:
            return self.masses[name]
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

    def input_parameter(self,
                        par_name: str) -> Dict[str, Any]:
        """Get a single input parameter"""
        return self.input_parameters[par_name]

    def starting_min(self,
                     par_name: str) -> float:
        """Get model parameter starting min"""
        return self.input_parameters[par_name]['min']

    def starting_max(self,
                     par_name: str) -> float:
        """Get parameter starting max"""
        return self.input_parameters[par_name]['max']
