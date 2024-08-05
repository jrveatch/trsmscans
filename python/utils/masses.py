
# class to hold onto masses and handle translation
# between X/S/H and H1/H2/H3 bases
class Masses:

    def __init__(self,
                 mX: float,
                 mS: float,
                 mH: float):

        # set X/S/H masses
        self.mX = mX
        self.mS = mS
        self.mH = mH

        # logic to set H1/H2/H3

        # if mX is the largest, it is H3
        if self.mX > self.mS and self.mX > self.mH:
            self.mH3 = self.mX
            self.XName = "H3"

            # if mS is second, it is H2
            if self.mS > self.mH:
                self.mH2 = self.mS
                self.SName = "H2"

                self.mH1 = self.mH
                self.HName = "H1"

            # if mH is second, it is H2
            else:
                self.mH2 = self.mH
                self.HName = "H2"

                self.mH1 = self.mS
                self.SName = "H1"
        
        # complain and exit if X is not the heaviest
        else:
            print("Only mX > mS,mH is currently supported")
            return

        """
        # if mS is the largest, it is H3
        if self.mS > self.mX and self.mS > self.mH:
            self.mH3 = self.mS
            self.SName = "H3"

            # if mX is second, it is H2
            if self.mX > self.mH:
                self.mH2 = self.mX
                self.XName = "H2"

                self.mH1 = self.mH
                self.HName = "H1"

            # if mH is second, it is H2
            else:
                self.mH2 = self.mH
                self.HName = "H2"

                self.mH1 = self.mX
                self.XName = "H1"

        # if mH is the largest, it is H3
        if self.mH > self.mX and self.mH > self.mS:
            self.mH3 = self.mH
            self.HName = "H3"

            # if mX is second, it is H2
            if self.mX > self.mS:
                self.mH2 = self.mX
                self.XName = "H2"

                self.mH1 = self.mS
                self.SName = "H1"

            # if mS is second, it is H2
            else:
                self.mH2 = self.mS
                self.SName = "H2"

                self.mH1 = self.mX
                self.XName = "H1"
        """

    def __str__(self):
        return "X"+str(int(self.mX))+"_S"+str(int(self.mS))