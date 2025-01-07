class BasePredictor:
    def Predict():
        pass
    def Update():
        pass
    # Stall for 1 cycle after branch taken, to ensure first instuction not skipped
    def Stall():
        pass