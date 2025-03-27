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

## -----------------------------------------
# STATIC PREDICTORS
## -----------------------------------------

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

## -----------------------------------------
# LOCAL PREDICTORS
## -----------------------------------------
    
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

    def CalculateNewDirectionCertainty(self, programCounter: int, branchOutcome: bool) -> bool:
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
                return certainty if certainty == 3 else certainty + 1
            # If not taken, sub 1 if certainty not 0 
            else:
                return certainty if certainty == 0 else certainty - 1

## -----------------------------------------
# GLOBAL PREDICTORS
## -----------------------------------------

class gshare(BasePredictor):
    # Creates an 8 bit global history register
    def __init__(self, BTB, directionBuffer, name="gshare"):
        super().__init__(BTB, directionBuffer, name)
        ## BUFFERS IN GSHARE PREDICTOR
        # GHR stores result of last 8 branches (including speculatively predicted ones)
        # OBQ stores branches knocked out of GHR due to speculative execution
        # When a branch is predicted, result is added to tail of GHR, and old head appended to OBQ
        # When branch is evaluated, and PREDICTED CORRECTLY, GHR taken, OBQ appended to head, tail cut off to hit correct size. Head of OBQ removed
        # When branch is evaluated, and MISPREDICTED, GHR taken, OBQ appended to head, tail cut off to his correct size. GHR <- this value (reset). OBQ flushed 
        self.GlobalHistoryRegister = Buffers.GlobalHistoryRegister(8) # TODO: Would be cool to allow user to modify this
        self.OutstandingBranchQueue = Buffers.CircularBuffer(16)

    def Predict(self, programCounter):
        if self.stalled == True:
            self.stalled = False
            return programCounter

        ## Check if program counter is a key in BTB
        BTBEntry = self.BTB.Get(programCounter)
        # If not, return pc + 1
        if type(BTBEntry) != dict:
            return programCounter + 1
        
        # XOR program counter and GHR, predict
        DirectionBufferIndex = programCounter ^ self.ConvertBufferToInt(self.GlobalHistoryRegister) # ^ denotes bitwise XOR
        prediction = self.DirectionBuffer.Get(DirectionBufferIndex)
        if type(prediction) == dict: prediction = prediction["certainty"] # Prediction found in Direction Buffer!
        else: prediction = True # For branches that have not been hit with given history yet, assume True
        # Head of GHR added to OBQ
        self.OutstandingBranchQueue.Add(self.GlobalHistoryRegister.Get())
        # Prediction added to GHR
        self.GlobalHistoryRegister.Add(prediction)
        # Return correct program counter value based on prediction
        if prediction:
            return BTBEntry["destination"]
        else:
            return programCounter + 1
    
    def Update(self, source, destination, branchOutcome):
        # Take GHR, add OBQ to the end of it
        nonSpeculativeGlobalHistory = Buffers.CircularBuffer(self.GlobalHistoryRegister._SIZE)
        # OBQ Size = (rear - front) % max size + 1
        OBQSize = self.OutstandingBranchQueue.Size()
        
        # Add non-speculative section of GHR
        for i in range(self.GlobalHistoryRegister._SIZE - OBQSize):
            nonSpeculativeGlobalHistory.Add(self.GlobalHistoryRegister.Get(i))
        # Add oldest entries in OBQ until at GHR length
        for i in range(self.GlobalHistoryRegister._SIZE - nonSpeculativeGlobalHistory.Size()):
            nonSpeculativeGlobalHistory.Add(self.OutstandingBranchQueue.Get(i))

        # Use (value xor source location) as index for BTB insertion
        index = self.ConvertBufferToInt(nonSpeculativeGlobalHistory) ^ source
        btbItem = {"source": source,
                    "destination": destination}
        directionItem = {"source": index,
                         "certainty": branchOutcome}
        
        sourceInBTB = type(self.BTB.Get(source)) is dict
        sourceInDirectionBuffer =  type(self.DirectionBuffer.Get(index)) is dict
        
        # Check if DB needs to be added to, or updated
        if sourceInDirectionBuffer:
            self.DirectionBuffer.Update(directionItem)
        else:
            self.DirectionBuffer.Add(directionItem)

        # Correct prediction => branch outcome is the same as GHR entry that pushed first entry in OBQ (prediction)
        if sourceInBTB: # Have encountered branch before - so we need to UPDATE its entries
            correctlyPredicted = branchOutcome == self.GlobalHistoryRegister.Get(-(OBQSize))

            self.BTB.Update(btbItem)
        else: # Happens when we have not encountered this branch yet - in this case, we need to add to BTB + GHR
            correctlyPredicted = False
            # Set BTB at index == destination
            self.BTB.Add(btbItem)

        # If predicted, remove from front of OBQ and return
        if correctlyPredicted:
            self.OutstandingBranchQueue.Remove()
            return
        # If mispredicted, nonSpecGlobalHistory -> GHR, add new branch, clear OBQ, return
        else:
            # Reset GHR to non-speculative history
            self.GlobalHistoryRegister.Flush()
            self.GlobalHistoryRegister.Add(nonSpeculativeGlobalHistory._Buffer)
            # Add latest branch result 
            self.GlobalHistoryRegister.Add(branchOutcome)
            # Flush OBQ
            self.OutstandingBranchQueue.Flush()
            return

    # Returns contents of buffer as int, by converting list to binary value, where T = 1, F = 0
    def ConvertBufferToInt(self, buffer: type[Buffers.CircularBuffer]) -> int:        
        bufferValue = 0
        # For element in buffer, add 2^i * element to value
        for i in range(buffer._SIZE):
            element = buffer._Buffer[(buffer._frontPointer + i) % buffer._SIZE]
            elementValue = (2**i) if element == True else 0
            bufferValue += elementValue 
        return bufferValue