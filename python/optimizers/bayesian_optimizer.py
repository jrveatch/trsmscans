from bayes_opt import BayesianOptimization
from utils.params import Params
from utils.model import Model
from utils.point_sampler import PointSampler
from utils.file_utils import scan_dir

class BayesianOptimizer:
    def __init__(self, 
                 model: 'Model',
                 decay: str,
                 random_point: int,
                 n_points: int,
                 config_loader,
                 params):
        # TODO: automate finding ranges
        self.model = model
        self.decay = decay
        self.ranges = {'thetaHS': [-1.570796, 1.570796], 'thetaHX': [-1.570796, 1.570796], 'thetaSX': [-1.570796, 1.570796], 'vs': [0, 1000], 'vx': [0, 1000]} 
        self.random_point = random_point
        self.n_points = n_points
        self.config_loader = config_loader
        self.params = params

    def set_ranges(self): # or get prescan ranges
        # TODO: automate ranges depending on config files

        # create new dictionary for ranges
        new_ranges = {}

        # loop through all params and their values
        for param_name, param_values in self.params.parameters.items():
            # set each parameter with its new high and low values
            new_ranges[param_name] = [param_values.low, param_values.high]

        # set self.ranges to the new ranges
        self.ranges = new_ranges

    def point_getter(self, thetaHS, thetaHX, thetaSX, vs, vx):
        # get a random point using these values
        # create or modify params object with min and max being equal to point_getter parameters
        # point_sampler with parmas object, npoints=1, and good_points_only=false identifier doesnt matter
        # call sample_points, returns parse object
        # get xb_max from parse object
        # return xb_max from parse object
        params = Params(self.model,decay=self.decay)
        out_dir = scan_dir(model = params.model, decay = params.decay)
        low_dict = {'thetaHS': thetaHS, 'thetaHX': thetaHX, 'thetaSX': thetaSX, 'vs': vs, 'vx': vx}
        params.update_low_high(low_dict, low_dict)
        point_sampler = PointSampler(out_dir, self.config_loader)
        print(low_dict)
        try:
            parser = point_sampler.sample_single_point(params=params, identifier='x', good_points_only=False)
        except TimeoutError:
            return 0
        max_xb_point = parser.get_max_xb_point(self.decay)
        return max_xb_point.xb

    def run(self):
        # set new ranges
        self.set_ranges()

        # create an optimizer
        optimizer = BayesianOptimization(
            f=self.point_getter, # function that returns a point
            pbounds=self.ranges, # ranges of each parameter
            verbose=2 # verbose=1 gives message when new max found, verbose=2 gives messages at each point
        )

        print("random_point: " + str(self.random_point))
        print("n_iter: " + str(self.n_points))

        optimizer.maximize(
            init_points=self.random_point,
            n_iter=self.n_points # amount of points to search and optimize
        )

        # optimizer.res # gets all points that were tested and saves their data

        # gets the max value
        print(optimizer.max)

        # TODO: decide if using optimizer.res to find data (quick and easy)
        # or manually keep data in self.point_getter() to keep all data in a csv,
        # which would include more in depth data



# notes for manuel:
# clean up output files (1k points will have 1k ini and output files)
# save output of optimizer (likely one file with points and store the max value)
# make plots
# 1d plot by using the max of each parameter except for the parameter being plotted
# 2d plot the same, and without the workaround, and/or with a plot like zoom plots using only optimizer.res points

