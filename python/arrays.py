# import numpy library as np
import numpy as np

class Arrays:

    def __init__(self,filename):

        with open(filename,'r') as file:
            header_line = file.readline().strip()
            headers = header_line.split('\t')

        headers.insert(0, 'idx')

        data = np.genfromtxt(filename, delimiter='\t', dtype=None, names=headers, encoding=None, skip_header=1)

        self.idx = data['idx']

        self.mH1 = data['mH1']
        self.mH2 = data['mH2']
        self.mH3 = data['mH3']

        self.thetahS = data['thetahS']
        self.thetahX = data['thetahX']
        self.thetaSX = data['thetaSX']

        self.v = data['v']
        self.vs = data['vs']
        self.vx = data['vx']

        self.R11 = data['R11']
        self.R12 = data['R12']
        self.R13 = data['R13']
        self.R21 = data['R21']
        self.R22 = data['R22']
        self.R23 = data['R23']
        self.R31 = data['R31']
        self.R32 = data['R32']
        self.R33 = data['R33']

        self.w_H1 = data['w_H1']
        self.w_H2 = data['w_H2']
        self.w_H3 = data['w_H3']

        self.x_H1_gg = data['x_H1_gg']
        self.x_H1_vbf = data['x_H1_vbf']
        self.x_H2_gg = data['x_H2_gg']
        self.x_H2_vbf = data['x_H2_vbf']
        self.x_H3_gg = data['x_H3_gg']
        self.x_H3_vbf = data['x_H3_vbf']

        self.b_H1_WW = data['b_H1_WW']
        self.b_H1_ZZ = data['b_H1_ZZ']
        self.b_H1_Zgam = data['b_H1_Zgam']
        self.b_H1_bb = data['b_H1_bb']
        self.b_H1_cc = data['b_H1_cc']
        self.b_H1_ss = data['b_H1_ss']
        self.b_H1_tt = data['b_H1_tt']
        self.b_H1_gamgam = data['b_H1_gamgam']
        self.b_H1_gg = data['b_H1_gg']
        self.b_H1_mumu = data['b_H1_mumu']
        self.b_H1_tautau = data['b_H1_tautau']

        self.b_H2_WW = data['b_H2_WW']
        self.b_H2_ZZ = data['b_H2_ZZ']
        self.b_H2_Zgam = data['b_H2_Zgam']
        self.b_H2_bb = data['b_H2_bb']
        self.b_H2_cc = data['b_H2_cc']
        self.b_H2_ss = data['b_H2_ss']
        self.b_H2_tt = data['b_H2_tt']
        self.b_H2_gamgam = data['b_H2_gamgam']
        self.b_H2_gg = data['b_H2_gg']
        self.b_H2_mumu = data['b_H2_mumu']
        self.b_H2_tautau = data['b_H2_tautau']

        self.b_H3_WW = data['b_H3_WW']
        self.b_H3_ZZ = data['b_H3_ZZ']
        self.b_H3_Zgam = data['b_H3_Zgam']
        self.b_H3_bb = data['b_H3_bb']
        self.b_H3_cc = data['b_H3_cc']
        self.b_H3_ss = data['b_H3_ss']
        self.b_H3_tt = data['b_H3_tt']
        self.b_H3_gamgam = data['b_H3_gamgam']
        self.b_H3_gg = data['b_H3_gg']
        self.b_H3_mumu = data['b_H3_mumu']
        self.b_H3_tautau = data['b_H3_tautau']

        self.b_H2_H1H1 = data['b_H2_H1H1']
        self.b_H3_H1H1 = data['b_H3_H1H1']
        self.b_H3_H1H2 = data['b_H3_H1H2']
        self.b_H3_H2H2 = data['b_H3_H2H2']
