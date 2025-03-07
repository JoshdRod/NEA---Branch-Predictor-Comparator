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
    def __init__(self, branchTargetBuffer: object, directionBuffer: object, name: str):
        self.name = name
        self.BTB = branchTargetBuffer # BTB stores location branches branch to {from: --, to: --}
        self.DirectionBuffer = directionBuffer # Direction Buffer stores whether to predict a branch taken or not {source: --, taken: --}
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
    INPUT int branch source location, int branch destination location, bool branch outcome (T = Taken, F = Not taken)
    """
    def Update(self, source: int, destination: int, branchOutcome: bool):
        raise NotImplementedError()

# Always not taken
class AlwaysNotTaken(BasePredictor): 
    def __init__(self, BTB, directionBuffer, name="Always Not Taken"):
        super().__init__(None, None, name) # None, as no BTB needed

    def Predict(self, programCounter: int):
        if self.stalled:
            self.stalled = False
            return programCounter
        
        return programCounter + 1

    # No BTB in ANT, so no need for update
    def Update(self, source: int, destination: int, branchOutcome: bool):
        return

# Always Taken
class AlwaysTaken(BasePredictor):
    def __init__(self, BTB, directionBuffer, name="Always Taken"):
        super().__init__(BTB, None, name)

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
    
    def Update(self, source: int, destination: int, branchOutcome: bool):
        ## Check if source already in BTB
        sourceInBTB = type(self.BTB.Get(source)) is dict
        ## If so, return
        if sourceInBTB:
            return
        ## If not, add it
        self.BTB.Add({"source": source,
                      "destination": destination})
        
class BaseLastTime(BasePredictor):
    def __init__(self, BTB, directionBuffer, name):
        super().__init__(BTB, directionBuffer, name)

    def Predict(self, programCounter: int) -> int:
        if self.stalled == True:
            self.stalled = False
            return programCounter

        ## Check if program counter is a key in BTB
        BTBEntry = self.BTB.Get(programCounter)
        # If not, return pc + 1
        if type(BTBEntry) != dict:
            return programCounter + 1
        
        ## Check outcome of last instance of this branch
        # If last instance of this branch taken, return btb entry
        predictedTaken = self.CheckIfBranchShouldBePredicted(programCounter)
        if predictedTaken:
            return BTBEntry["destination"]
        # If not taken, return pc + 1
        return programCounter + 1
    
    def Update(self, source: int, destination: int, branchOutcome: bool):
        ## Set lastBranchOutcome to the branch's outcome
        self.newDirectionCertainty = self.CalculateNewDirectionCertainty(branchOutcome)
        btbItem = {"source": source,
                    "destination": destination}
        directionItem = {"source": source,
                         "taken": self.newDirectionCertainty}

        ## Update BTB
        # Check if source already in BTB
        sourceInBTB = type(self.BTB.Get(source)) is dict
        ## If not, add it
        if not sourceInBTB:
            self.BTB.Add(btbItem)
        
        ## Update Direction Buffer
        sourceInDirectionBuffer = type(self.DirectionBuffer.Get(source)) is dict
        # If so, update
        if sourceInDirectionBuffer:
            self.DirectionBuffer.Update(directionItem)
            return
        # If not, add it
        self.DirectionBuffer.Add(directionItem)

    def CheckIfBranchShouldBePredicted(self, programCounter: int) -> bool:
        raise NotImplementedError
    
    def CalculateNewDirectionCertainty(self, previousBranchOutcome: bool) -> int:
        raise NotImplementedError

class OneBitLastTime(BaseLastTime):
    def __init__(self, BTB, directionBuffer, name="1 bit Last Time"):
        super().__init__(BTB, directionBuffer, name)

    def CheckIfBranchShouldBePredicted(self, programCounter: int) -> bool:
        return self.DirectionBuffer.Get(programCounter)["taken"]

    def CalculateNewDirectionCertainty(self, previousBranchOutcome: bool) -> int:
        return previousBranchOutcome
        
class TwoBit(BasePredictor):
    def __init__(self, BTB, directionBuffer, name="Two Bit"):
        super().__init__(BTB, directionBuffer, name)