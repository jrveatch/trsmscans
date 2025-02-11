from bayes_opt import BayesianOptimization
from utils.params import Params
from utils.model import Model
from utils.point_sampler import PointSampler
from utils.file_utils import scan_dir

class BayesianOptimizer:
    def __init__(self, 
                 model: 'Model',
                 random_point: int,
                 n_points: int,
                 config_loader):
        # TODO: automate finding ranges
        self.model = model
        self.ranges = {'tHS': [-1.570796, 1.570796], 'tHX': [-1.570796, 1.570796], 'tSX': [-1.570796, 1.570796], 'vs': [0, 1000], 'vx': [0, 1000]} 
        self.random_point = random_point
        self.n_points = n_points
        self.config_loader = config_loader

    def set_ranges(self, model_name): # or get prescan ranges
        # TODO: automate ranges depending on config files
        pass

    def point_getter(self, tHS, tHX, tSX, vs, vx):
        # get a random point using these values
        # create or modify params object with min and max being equal to point_getter parameters
        # point_sampler with parmas object, npoints=1, and good_points_only=false identifier doesnt matter
        # call sample_points, returns parse object
        # get xb_max from parse object
        # return xb_max from parse object
        params = Params(self.model)
        out_dir = scan_dir(model = params.model, decay = params.decay)
        low_dict = {'tHS': tHS, 'tHX': tHX, 'tSX': tSX, 'vs': vs, 'vx': vx}
        params.update_low_high(low_dict, low_dict)
        point_sampler = PointSampler(out_dir, self.config_loader)
        parser = point_sampler.sample_points(params, '', "1", False)
        max_xb_point = parser.get_max_xb_point()
        return max_xb_point.xb

    def run(self):
        # create an optimizer
        optimizer = BayesianOptimization(
            f=self.point_getter, # function that returns a point
            pbounds=self.ranges, # ranges of each parameter
            verbose=0 # verbose=1 gives message when new max found, verbose=2 gives messages at each point
        )

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

