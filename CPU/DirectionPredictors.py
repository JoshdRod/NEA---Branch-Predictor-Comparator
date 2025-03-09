import CPU.Buffers as Buffers
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
    def __init__(self, branchTargetBuffer: type[Buffers.BranchTargetBuffer], directionBuffer: type[Buffers.DirectionBuffer], name: str):
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
        
"""
Base Last Time Predictor - Predicts direction based on last n times that branch was reached
EXTRA DATA:

EXTRA FUNCTIONALITY:

REQUIRED FUNCTIONALITY ON SUBCLASSES:
    CheckIfBranchShouldBePredicted (Takes in branch location, then checks direction buffer to see what to predict)
    CalculateNewDirectionUncertainty (Takes in branch location, and updates certainty to reflect outcome of this cycle)
"""
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
        ## Create Items to add to BTB and Direction Buffer
        self.newDirectionCertainty = self.CalculateNewDirectionCertainty(source, branchOutcome)
        btbItem = {"source": source,
                    "destination": destination}
        directionItem = {"source": source,
                         "certainty": self.newDirectionCertainty}

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

    """
    Checks if direction certainty indicates branch should be predicted taken
    INPUTS: int current program counter
    RETURNS: bool whether branch should be predicted or not
    """
    def CheckIfBranchShouldBePredicted(self, programCounter: int) -> bool:
        raise NotImplementedError()
    
    """
    Takes in result of current branch (predicted/mispredicted), and returns new certainty
    INPUTS: int current program counter, bool outcome of branch
    RETURNS:
    """
    def CalculateNewDirectionCertainty(self, programCounter: int, branchOutcome: bool) -> int:
        raise NotImplementedError()

class OneBitLastTime(BaseLastTime):
    def __init__(self, BTB, directionBuffer, name="1 bit Last Time"):
        super().__init__(BTB, directionBuffer, name)

    ## DIRECTION CERTAINTY GUIDE
    # -------------------------------
    # True - Predict Taken
    # False - Preict Not Taken
    # -------------------------------

    def CheckIfBranchShouldBePredicted(self, programCounter: int) -> bool:
        return self.DirectionBuffer.Get(programCounter)["certainty"]

    def CalculateNewDirectionCertainty(self, programCounter: int, branchOutcome: bool) -> int:
        return branchOutcome
        
class TwoBitLastTime(BaseLastTime):
    def __init__(self, BTB, directionBuffer, name="Two Bit"):
        super().__init__(BTB, directionBuffer, name)

    ## DIRECTION CERTAINTY GUIDE
    # -------------------------------
    # 3 - Double Predict Taken
    # 2 - Predict Taken
    # -------------------------------
    # 1 - Predict Not Taken
    # 0 - Double Predict Not Taken
    # --------------------------------

    def CheckIfBranchShouldBePredicted(self, programCounter: int) -> bool:
        sourceInDirectionBuffer = self.DirectionBuffer.Get(programCounter)
        certainty = sourceInDirectionBuffer["certainty"]

        return True if certainty >= 2 else False

    def CalculateNewDirectionCertainty(self, programCounter: int, branchOutcome: bool) -> int:
        # Find branch in direction buffer
        sourceInDirectionBuffer = self.DirectionBuffer.Get(programCounter)
        # If not in direction buffer, return 2 if predicted taken, 1 if predicted not taken
        if type(sourceInDirectionBuffer) is not dict:
            return 2 if branchOutcome else 1
        # If in buffer, find current certainty
        else:
            # If outcome = taken, add 1 if certainty not 3
            certainty = sourceInDirectionBuffer["certainty"]
            if branchOutcome:
                return certainty if certainty == 4 else certainty + 1
            # If not taken, sub 1 if certainty not 0 
            else:
                return certainty if certainty == 0 else certainty - 1
            
breakpoint