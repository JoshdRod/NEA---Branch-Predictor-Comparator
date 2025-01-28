"""
Branch Predictor Interface
DATA:
    str name
    bool stalled
FUNCTIONALITY:
    Predict
    Update
    Stall
"""
class BasePredictor:
    def __init__(self, name):
        self.name = name
        self._stalled = True

    """
    Predicts the next instruction to fetch based on the program counter
    INPUT: int program counter
    RETURNS: int predicted next program counter
    """
    def Predict(self, programCounter: int) -> int:
        pass

    """
    Updates branch target buffer with the given branch instruction
    INPUT int address of branch location
    """
    def Update(self):
        pass

    """
    Sets predictor to stalled state (e.g: On mispredict, to ensure first instruction isn't skipped due to predicting rip + 1)
    """
    def Stall(self):
        pass

class AlwaysNotTaken(BasePredictor): 
    def __init__(self, name):
        super.__init__(name)

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
