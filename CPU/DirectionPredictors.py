"""
Branch Predictor Interface
DATA:
    str name
    bool stalled
FUNCTIONALITY:
    Stall

REQUIRED FUNCITONALITY ON SUBCLASSES:
    Predict
    Update
"""
class BasePredictor:
    def __init__(self, name):
        self.name = name
        self._stalled = True
    """
    Sets predictor to stalled state (e.g: On mispredict, to ensure first instruction isn't skipped due to predicting rip + 1)
    """
    def Stall(self):
        self.stalled = True

    """
    Predicts the next instruction to fetch based on the program counter
    INPUT: int program counter
    RETURNS: int predicted next program counter
    """
    def Predict(self, programCounter: int) -> int:
        raise NotImplementedError()

    """
    Updates branch target buffer with the given branch instruction
    INPUT int address of branch location
    """
    def Update(self, location: int):
        raise NotImplementedError()

# Always not taken
class AlwaysNotTaken(BasePredictor): 
    def __init__(self, name="Always Not Taken"):
        super.__init__(name)

    def Predict(self, programCounter: int):
        if self.stalled:
            self.stalled = False
            return programCounter
        
        return programCounter + 1

    # No BTB in ANT, so no need for update
    def Update(self, location: int):
        return
