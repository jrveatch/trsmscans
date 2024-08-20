# class to hold onto range decay and density growth rates
class Zoom:

    def __init__(self,
                 parameter_rate: float,
                 density_growth_rate: float):
        
        self.parRate = parameter_rate
        self.densityRate = density_growth_rate