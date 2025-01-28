class BasePredictor:
    def __init__(self, name):
        self.name = name

    """
    Predicts the next instruction to fetch based on the program counter
    INPUT: int program counter
    RETURNS: int predicted next program counter
    """
    def Predict(self, programCounter: int) -> int:
        pass

    """
    Updates branch target buffer with the given branch instruction
    INPUT:
    """
    def Update(self):
        pass

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
