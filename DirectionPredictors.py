class BasePredictor:

    stalled = True # Predictor stalls after an unsuccessful branch (e.g: branch to 10, fetch 10, then predict 11..)
    def Predict(self, programCounter: int):
        if self.stalled:
            self.stalled = False
            return programCounter
        
        return programCounter + 1

    def Update(self):
        pass
    
    # Stall for 1 cycle after branch taken, to ensure first instuction not skipped
    def Stall(self):
        self.stalled = True