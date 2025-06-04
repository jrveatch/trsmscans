
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
    """
    Represents a physics model with scalar particles, parameter definitions, and mass mappings.

    This class loads model configuration from a YAML file, manages scalar particle metadata,
    input/output/width parameters, and provides methods for working with scalar mass ordering.

    Key Features:
    - Loads particle and parameter definitions from '<model_name>_params.yml'.
    - Maps scalar names (e.g., 'S', 'X') to mass-ordered names (e.g., 'H1', 'H2').
    - Provides access to input/output/width parameter dictionaries and their full names.
    - Supports reading associated template .ini files and extracting scalar masses.
    """

    def __init__(self,
                 name: str,
                 masses: Dict[str, float]) -> None:
        """
        Initializes a Model object with the given name and particle masses.

        Args:
            name (str): The name of the model.
            masses (Dict[str, float]): A dictionary mapping particle names to their masses.
        """

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
        """Returns the name of the model."""
        return self.__name

    @name.setter
    def name(self,
             new_name: str) -> None:
        """Sets the model name."""
        self.__name = new_name

    @cached_property
    def model_dir(self) -> str:
        """Returns the directory path where model data files are stored."""
        return os.path.join(data_dir(), "models")

    @cached_property
    def template_ini(self) -> str:
        """Returns the file path of the model's template .ini file."""
        return os.path.join(self.model_dir, f"{self.name}_template.ini")

    @property
    def masses(self) -> Dict[str,float]:
        """Returns the dictionary of scalar particle masses."""
        return self.__masses

    @masses.setter
    def masses(self,
                new_masses: Dict[str,float]) -> None:
        """Sets the particle masses and rebuilds the internal scalar mass maps."""
        self.__masses = new_masses
        self.__build_mass_maps()

    @property
    # TODO: Make this more generalized
    def mass_string(self) -> str:
        """Returns a formatted string like 'X400_S150' encoding X and S scalar masses."""
        x_mass = self.masses["X"]
        s_mass = self.masses["S"]
        return f"X{int(x_mass)}_S{int(s_mass)}"

    @cached_property
    def yaml_name(self) -> str:
        """Returns the file path to the model's YAML configuration file."""
        return os.path.join(self.model_dir, f"{self.name}_params.yml")

    @property
    def input_parameters(self) -> Dict[str, Any]:
        """Returns a dictionary of input parameter definitions."""
        return self.__input_params

    @input_parameters.setter
    def input_parameters(self,
                         new_input_params: Dict[str, Any]) -> None:
        """Sets the dictionary of input parameters."""
        self.__input_params = new_input_params

    @property
    def output_parameters(self) -> dict:
        """Returns a dictionary of output parameter definitions."""
        return self.__output_params

    @output_parameters.setter
    def output_parameters(self,\
                          new_output_params: Dict[str, Any]) -> None:
        """Sets the dictionary of output parameters."""
        self.__output_params = new_output_params

    @cached_property
    def width_parameters(self) -> Dict[str, Dict[str, str]]:
        """Returns a dictionary mapping width parameter names (e.g. 'wH1') to metadata (e.g. fullname)."""
        return {
            "w" + particle: {
                'fullname': f"w_{self.get_ordered_scalar_name(particle)}"
            }
            for particle in self.AllScalars
        }

    @cached_property
    def input_parameter_names(self) -> Tuple[str, ...]:
        """Returns a tuple of input parameter names."""
        return tuple(self.input_parameters.keys())

    @cached_property
    def output_parameter_names(self) -> Tuple[str, ...]:
        """Returns a tuple of output parameter names."""
        return tuple(self.output_parameters.keys())

    @cached_property
    def width_parameter_names(self) -> Tuple[str, ...]:
        """Returns a tuple of width parameter names."""
        return tuple(self.width_parameters.keys())

    @cached_property
    def all_parameter_names(self) -> Tuple[str, ...]:
        """Returns a tuple containing all parameter names (input, output, and width)."""
        return self.input_parameter_names + self.output_parameter_names + self.width_parameter_names

    @cached_property
    def input_parameter_full_names(self) -> Tuple[str, ...]:
        """Returns a tuple of full names for input parameters."""
        return tuple(item["fullname"] for item in self.input_parameters.values())

    @cached_property
    def ini_name_to_fullname_map(self) -> Dict[str, str]:
        """Returns a mapping from .ini parameter names to full parameter names."""
        return {
            item["ini_name"]: item["fullname"]
            for item in self.input_parameters.values()
            if "ini_name" in item and "fullname" in item
        }

    @cached_property
    def fullname_to_ini_name_map(self) -> Dict[str, str]:
        """Returns a mapping from full parameter names to .ini names."""
        return {
            item["fullname"]: item["ini_name"]
            for item in self.input_parameters.values()
            if "ini_name" in item and "fullname" in item
        }

    @property
    def particles(self) -> Dict[str, Any]:
        """Returns the dictionary of particles grouped by role (e.g., SMHiggs, Scalars)."""
        return self.__particles

    @particles.setter
    def particles(self,
                   new_particles: Dict[str, Any]) -> None:
        """Sets the dictionary of particles used in the model."""
        self.__particles = new_particles

    def __read_yaml(self) -> None:
        """
        Loads model configuration from the associated YAML file.

        Populates the model's particle content, input/output parameter definitions, and
        derives scalar classification (SMHiggs, BSMScalars, AllScalars).
        """

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
        if len(self.particles['SMHiggs']) != 1:
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
        """
        Constructs maps between scalar particle names and their ordered H_i names based on mass.

        Raises:
            ValueError: If the mass dictionary is missing any required scalar particles.
        """

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
        Returns the mass of a scalar particle by name or H_i label.

        Args:
            name (str): Particle name (e.g., 'X', 'S') or ordered name (e.g., 'H1').

        Returns:
            float: The mass of the particle.

        Raises:
            KeyError: If the particle name is invalid or not found.
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
        Returns the mass-ordered scalar name (e.g., 'H1', 'H2') for a given particle.

        Args:
            particle_name (str): Original name of the particle (e.g., 'S', 'X').

        Returns:
            str: Ordered name (e.g., 'H1').

        Raises:
            KeyError: If the input name is not in the scalar list.
        """

        if particle_name in self.name_map:
            return self.name_map[particle_name]
        else:
            raise KeyError(
                f"Invalid original name: {particle_name}. Available names: {self.AllScalars}"
            )

    def input_parameter(self,
                        par_name: str) -> Dict[str, Any]:
        """
        Returns the dictionary of metadata for a specific input parameter.

        Args:
            par_name (str): Name of the input parameter.

        Returns:
            Dict[str, Any]: Metadata for the input parameter.
        """
        return self.input_parameters[par_name]

    def starting_min(self,
                     par_name: str) -> float:
        """
        Returns the starting minimum value for a model input parameter.

        Args:
            par_name (str): Parameter name.

        Returns:
            float: Minimum value from parameter definition.
        """
        return self.input_parameters[par_name]['min']

    def starting_max(self,
                     par_name: str) -> float:
        """
        Returns the starting maximum value for a model input parameter.

        Args:
            par_name (str): Parameter name.

        Returns:
            float: Maximum value from parameter definition.
        """
        return self.input_parameters[par_name]['max']
