# import numpy library as np
import numpy as np

# import list of columns
import columns

class Arrays:

    def getarrays(self,filename,cols:columns.Columns):

        self.idx = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.idx)
        
        self.mH1 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.mH1)
        
        self.mH2 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.mH2)
        
        self.mH3 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.mH3)
        
        self.thetahS = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.thetahS)

        self.thetahX = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.thetahX)

        self.thetaSX = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.thetaSX)

        self.v = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.v)

        self.vs = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.vs)

        self.vx = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.vx)

        self.R11 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R11)

        self.R12 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R12)

        self.R13 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R13)

        self.R21 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R21)

        self.R22 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R22)

        self.R23 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R23)

        self.R31 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R31)

        self.R32 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R32)

        self.R33 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.R33)

        self.w_H1 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.w_H1)

        self.w_H2 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.w_H2)

        self.w_H3 = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.w_H3)

        self.x_H1_gg = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.x_H1_gg)

        self.x_H1_vbf = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.x_H1_vbf)

        self.x_H2_gg = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.x_H2_gg)

        self.x_H2_vbf = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.x_H2_vbf)

        self.x_H3_gg = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.x_H3_gg)

        self.x_H3_vbf = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.x_H3_vbf)

        self.b_H1_WW = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_WW)

        self.b_H1_ZZ = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_ZZ)

        self.b_H1_Zgam = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H1_Zgam)

        self.b_H1_bb = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_bb)

        self.b_H1_cc = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_cc)

        self.b_H1_gamgam = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H1_gamgam)

        self.b_H1_gg = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_gg)

        self.b_H1_mumu = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H1_mumu)

        self.b_H1_ss = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_ss)

        self.b_H1_tautau = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H1_tautau)

        self.b_H1_tt = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H1_tt)

        self.b_H2_WW = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_WW)

        self.b_H2_ZZ = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_ZZ)

        self.b_H2_Zgam = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H2_Zgam)

        self.b_H2_bb = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_bb)

        self.b_H2_cc = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_cc)

        self.b_H2_gamgam = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H2_gamgam)

        self.b_H2_gg = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_gg)

        self.b_H2_mumu = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H2_mumu)

        self.b_H2_ss = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_ss)

        self.b_H2_tautau = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H2_tautau)

        self.b_H2_tt = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H2_tt)

        self.b_H2_H1H1 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H2_H1H1)

        self.b_H3_WW = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_WW)

        self.b_H3_ZZ = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_ZZ)

        self.b_H3_Zgam = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_Zgam)

        self.b_H3_bb = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_bb)

        self.b_H3_cc = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_cc)

        self.b_H3_gamgam = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_gamgam)

        self.b_H3_gg = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_gg)

        self.b_H3_mumu = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_mumu)

        self.b_H3_ss = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_ss)

        self.b_H3_tautau = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_tautau)

        self.b_H3_tt = np.loadtxt(filename,
                        delimiter="\t",
                        skiprows=1,
                        usecols=cols.b_H3_tt)

        self.b_H3_H1H1 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_H1H1)

        self.b_H3_H1H2 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_H1H2)

        self.b_H3_H2H2 = np.loadtxt(filename,
                            delimiter="\t",
                            skiprows=1,
                            usecols=cols.b_H3_H2H2)
