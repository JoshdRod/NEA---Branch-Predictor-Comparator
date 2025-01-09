class BasePredictor:

    def Predict(self, programCounter: int):
        return programCounter + 1

    def Update():
        pass
    # Stall for 1 cycle after branch taken, to ensure first instuction not skipped
    def Stall():
        pass