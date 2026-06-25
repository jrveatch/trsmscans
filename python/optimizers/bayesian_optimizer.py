
from typing import Optional
from bayes_opt import BayesianOptimization
from utils.param_space import ParamSpace
from utils.model import Model
from utils.point import Point
from utils.point_sampler import PointSampler
from utils.file_utils import scan_dir 
from utils.tsv_utils import write_point_to_summary_file, initialize_summary_file

class BayesianOptimizer:
    def __init__(self, 
                 model: Model,
                 decay: str,
                 param_space: ParamSpace,
                 num_points: Optional[int] = None,
                 num_samples: Optional[int] = None):
        # TODO: automate finding ranges
        self.model = model
        self.decay = decay
        self.ranges = {k: [v['min'], v['max']] for k, v in self.model.input_parameters.items()}
        self.num_points = num_points
        self.num_samples = num_samples
        self.param_space = param_space
        self.out_dir = scan_dir(model=model,
                                decay=decay)
        
        if self.num_samples is None:
            self.num_samples = model.default_bayes_starting_points
        if self.num_points is None:
            self.num_points = model.default_bayes_sampling_points

    def set_ranges(self): # or get prescan ranges
        # TODO: automate ranges depending on config files

        # create new dictionary for ranges
        new_ranges = {}

        # loop through all param_space and their values
        for param_name, param_values in self.param_space.parameter_ranges.items():
            # set each parameter with its new high and low values
            new_ranges[param_name] = [param_values.low, param_values.high]

        # set self.ranges to the new ranges
        self.ranges = new_ranges

    def point_getter(self, thetaHS, thetaHX, thetaSX, vs, vx):
        # get a random point using these values
        # create or modify param_space object with min and max being equal to point_getter parameters
        # point_sampler with parmas object, npoints=1, and good_points_only=false identifier doesnt matter
        # call sample_points, returns parse object
        # get xb_max from parse object
        # return xb_max from parse object
        low_dict = {'thetaHS': thetaHS, 'thetaHX': thetaHX, 'thetaSX': thetaSX, 'vs': vs, 'vx': vx}
        point = Point(model=self.model,par_vals=low_dict)
        point_sampler = PointSampler(self.model, self.out_dir)
        # debug: print(low_dict)
        try:
            point = point_sampler.sample_single_point(point=point,
                                                      decay=self.decay,
                                                      identifier='x')
        except TimeoutError:
            write_point_to_summary_file(self.out_file, point)
            return 0

        # write point to summary file
        write_point_to_summary_file(self.out_file, point)

        # debug: print(point.xb)
        return point.xb

    def run(self):
        # set new ranges
        self.set_ranges()

        # get output file name
        self.out_file = self.out_dir + "/bayes/tsv/TRSMBroken.tsv"

        # create an empty output file
        with open(self.out_file, 'w') as file:
            print("Creating output file...")

        # initialize summary file
        initialize_summary_file(self.out_file, self.model)

        # create an optimizer
        optimizer = BayesianOptimization(
            f=self.point_getter, # function that returns a point
            pbounds=self.ranges, # ranges of each parameter
            verbose=2 # verbose=1 gives message when new max found, verbose=2 gives messages at each point
        )

        print("num_points: " + str(self.num_points))
        print("num_samples: " + str(self.num_samples))

        optimizer.maximize(
            init_points=self.num_points,
            n_iter=self.num_samples # amount of points to search and optimize
        )

        # optimizer.res # gets all points that were tested and saves their data

        # gets the max value
        print("Max point: ", end='')
        print(optimizer.max)

        # TODO: decide if using optimizer.res to find data (quick and easy)
        # or manually keep data in self.point_getter() to keep all data in a csv,
        # which would include more in depth data
