# define column indices

class Columns:

    def __init__(self,filename):

        with open(filename,"r") as f:
            first_line = f.readline()
        
        headers = first_line.split()

        # index
        self.idx = 0

        # masses
        self.mH1 = headers.index("mH1") + 1
        self.mH2 = headers.index("mH2") + 1
        self.mH3 = headers.index("mH3") + 1

        # mixing angles
        self.thetahS = headers.index("thetahS") + 1
        self.thetahX = headers.index("thetahX") + 1
        self.thetaSX = headers.index("thetaSX") + 1

        # vevs
        self.v = headers.index("v") + 1
        self.vs = headers.index("vs") + 1
        self.vx = headers.index("vx") + 1

        # Rs
        self.R11 = headers.index("R11") + 1
        self.R12 = headers.index("R12") + 1
        self.R13 = headers.index("R13") + 1
        self.R21 = headers.index("R21") + 1
        self.R22 = headers.index("R22") + 1
        self.R23 = headers.index("R23") + 1
        self.R31 = headers.index("R31") + 1
        self.R32 = headers.index("R32") + 1
        self.R33 = headers.index("R33") + 1

        # widths
        self.w_H1 = headers.index("w_H1") + 1
        self.w_H2 = headers.index("w_H2") + 1
        self.w_H3 = headers.index("w_H3") + 1

        # x-sections
        self.x_H1_gg = headers.index("x_H1_gg") + 1
        self.x_H1_vbf = headers.index("x_H1_vbf") + 1
        self.x_H2_gg = headers.index("x_H2_gg") + 1
        self.x_H2_vbf = headers.index("x_H2_vbf") + 1
        self.x_H3_gg = headers.index("x_H3_gg") + 1
        self.x_H3_vbf = headers.index("x_H3_vbf") + 1

        # BRs H1
        self.b_H1_WW = headers.index("b_H1_WW") + 1
        self.b_H1_ZZ = headers.index("b_H1_ZZ") + 1
        self.b_H1_Zgam = headers.index("b_H1_Zgam") + 1
        self.b_H1_gamgam = headers.index("b_H1_gamgam") + 1
        self.b_H1_gg = headers.index("b_H1_gg") + 1
        self.b_H1_ss = headers.index("b_H1_ss") + 1
        self.b_H1_cc = headers.index("b_H1_cc") + 1
        self.b_H1_bb = headers.index("b_H1_bb") + 1
        self.b_H1_tt = headers.index("b_H1_tt") + 1
        self.b_H1_mumu = headers.index("b_H1_mumu") + 1
        self.b_H1_tautau = headers.index("b_H1_tautau") + 1

        # BRs H2
        self.b_H2_H1H1 = headers.index("b_H2_H1H1") + 1
        self.b_H2_WW = headers.index("b_H2_WW") + 1
        self.b_H2_ZZ = headers.index("b_H2_ZZ") + 1
        self.b_H2_Zgam = headers.index("b_H2_Zgam") + 1
        self.b_H2_gamgam = headers.index("b_H2_gamgam") + 1
        self.b_H2_gg = headers.index("b_H2_gg") + 1
        self.b_H2_ss = headers.index("b_H2_ss") + 1
        self.b_H2_cc = headers.index("b_H2_cc") + 1
        self.b_H2_bb = headers.index("b_H2_bb") + 1
        self.b_H2_tt = headers.index("b_H2_tt") + 1
        self.b_H2_mumu = headers.index("b_H2_mumu") + 1
        self.b_H2_tautau = headers.index("b_H2_tautau") + 1

        # BRs H3
        self.b_H3_H1H1 = headers.index("b_H3_H1H1") + 1
        self.b_H3_H1H2 = headers.index("b_H3_H1H2") + 1
        self.b_H3_H2H2 = headers.index("b_H3_H2H2") + 1
        self.b_H3_WW = headers.index("b_H3_WW") + 1
        self.b_H3_ZZ = headers.index("b_H3_ZZ") + 1
        self.b_H3_Zgam = headers.index("b_H3_Zgam") + 1
        self.b_H3_gamgam = headers.index("b_H3_gamgam") + 1
        self.b_H3_gg = headers.index("b_H3_gg") + 1
        self.b_H3_ss = headers.index("b_H3_ss") + 1
        self.b_H3_cc = headers.index("b_H3_cc") + 1
        self.b_H3_bb = headers.index("b_H3_bb") + 1
        self.b_H3_tt = headers.index("b_H3_tt") + 1
        self.b_H3_mumu = headers.index("b_H3_mumu") + 1
        self.b_H3_tautau = headers.index("b_H3_tautau") + 1

        return
    
    def printcols(self):

        print("\nColumns numbers:")

        print("idx",self.idx)

        print("mH1",self.mH1)
        print("mH2",self.mH2)
        print("mH3",self.mH3)

        print("thetahS",self.thetahS)
        print("thetahX",self.thetahX)
        print("thetaSX",self.thetaSX)

        print("v",self.v)
        print("vs",self.vs)
        print("vx",self.vx)

        print("R11",self.R11)
        print("R12",self.R12)
        print("R13",self.R13)
        print("R21",self.R21)
        print("R22",self.R22)
        print("R23",self.R23)
        print("R31",self.R31)
        print("R32",self.R32)
        print("R33",self.R33)

        print("w_H1",self.w_H1)
        print("w_H2",self.w_H2)
        print("w_H3",self.w_H3)

        print("x_H1_gg",self.x_H1_gg)
        print("x_H1_vbf",self.x_H1_vbf)
        print("x_H2_gg",self.x_H2_gg)
        print("x_H2_vbf",self.x_H2_vbf)
        print("x_H3_gg",self.x_H3_gg)
        print("x_H3_vbf",self.x_H3_vbf)

        print("b_H1_WW",self.b_H1_WW)
        print("b_H1_ZZ",self.b_H1_ZZ)
        print("b_H1_Zgam",self.b_H1_Zgam)
        print("b_H1_gamgam",self.b_H1_gamgam)
        print("b_H1_gg",self.b_H1_gg)
        print("b_H1_ss",self.b_H1_ss)
        print("b_H1_cc",self.b_H1_cc)
        print("b_H1_bb",self.b_H1_bb)
        print("b_H1_tt",self.b_H1_tt)
        print("b_H1_mumu",self.b_H1_mumu)
        print("b_H1_tautau",self.b_H1_tautau)

        print("b_H2_H1H1",self.b_H2_H1H1)
        print("b_H2_WW",self.b_H2_WW)
        print("b_H2_ZZ",self.b_H2_ZZ)
        print("b_H2_Zgam",self.b_H2_Zgam)
        print("b_H2_gamgam",self.b_H2_gamgam)
        print("b_H2_gg",self.b_H2_gg)
        print("b_H2_ss",self.b_H2_ss)
        print("b_H2_cc",self.b_H2_cc)
        print("b_H2_bb",self.b_H2_bb)
        print("b_H2_tt",self.b_H2_tt)
        print("b_H2_mumu",self.b_H2_mumu)
        print("b_H2_tautau",self.b_H2_tautau)

        print("b_H3_H1H1",self.b_H3_H1H1)
        print("b_H3_H1H2",self.b_H3_H1H2)
        print("b_H3_H2H2",self.b_H3_H2H2)
        print("b_H3_WW",self.b_H3_WW)
        print("b_H3_ZZ",self.b_H3_ZZ)
        print("b_H3_Zgam",self.b_H3_Zgam)
        print("b_H3_gamgam",self.b_H3_gamgam)
        print("b_H3_gg",self.b_H3_gg)
        print("b_H3_ss",self.b_H3_ss)
        print("b_H3_cc",self.b_H3_cc)
        print("b_H3_bb",self.b_H3_bb)
        print("b_H3_tt",self.b_H3_tt)
        print("b_H3_mumu",self.b_H3_mumu)
        print("b_H3_tautau",self.b_H3_tautau)
