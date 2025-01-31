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
    def __init__(self, name, BranchTargetBuffer: object):
        self.name = name
        self.BTB = BranchTargetBuffer
        self.stalled = True

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
    INPUT int branch source location, int branch destination location
    """
    def Update(self, source: int, destination: int):
        raise NotImplementedError()

# Always not taken
class AlwaysNotTaken(BasePredictor): 
    def __init__(self, name="Always Not Taken"):
        super.__init__(name, None) # None, as no BTB needed

    def Predict(self, programCounter: int):
        if self.stalled:
            self.stalled = False
            return programCounter
        
        return programCounter + 1

    # No BTB in ANT, so no need for update
    def Update(self, source: int, destination: int):
        return

# Always Taken
class AlwaysTaken(BasePredictor):
    def __init__(self, BTB, name="Always Taken"):
        super().__init__(name, BTB)

    def Predict(self, programCounter: int) -> int:
        if self.stalled == True:
            self.stalled = False
            return programCounter
            
        ## Check if program counter is a key in BTB
        BTBEntry = self.BTB.Get(programCounter)
        ## If not, return pc + 1
        if type(BTBEntry) != dict:
            return programCounter + 1
        ## If so, return destination of found entry
        return BTBEntry["destination"]
    
    def Update(self, source: int, destination: int):
        ## Check if source already in BTB
        sourceInBTB = type(self.BTB.Get(source)) is dict
        ## If so, return
        if sourceInBTB:
            return
        ## If not, add it
        self.BTB.Add({"source": source,
                      "destination": destination})