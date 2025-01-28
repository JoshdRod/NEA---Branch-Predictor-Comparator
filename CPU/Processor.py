"""
TODO:
- Implement branch predictors!
- Cycle number filter doesn't always seem to jump to the correct cycle number?
- Change processor operating mode - currently, branch prediction doesn't improve anything, because there's no misfetch penalty
- Clean up passing operand into mu-op functions in execute - most functions just take the int value of the operator (jmp and sto being the issue), try to convert it before!
- Fix fact that all computed memory addresses can't contain spaces in the compiler (e.g: Won't accept "[rax + 5]" must be "[rax+5]")
- A direct CPU interface would be nice (like the IDLE interpreter)
"""

from CPU.MainMemory import MainMemory
import CPU.DirectionPredictors
from CPU.Buffers import ReorderBuffer, PipelineBuffer
from CPU.AddressGenerationUnit import AGU
from CPU.Registers import Registers

class Processor:

    def __init__(self):
        self.predictor = CPU.DirectionPredictors.BasePredictor() # TODO
        self.registers = Registers()
        self.mainMemory = MainMemory(100) # 100 byte (lines) main memory
        self.reorderBuffer = ReorderBuffer(16) # 16 byte (section) buffer
        self.pipelineBuffer = PipelineBuffer(16)
        self.AGU = AGU(self.registers)

        ## Control signals
        self.running = True # TODO: REPLACE FLAG IN EFLAGS W/ THIS
        self.stalledStages = {"Fetch" : False,
                      "Decode" : True,
                      "Execute" : True}
        
        ## Misprediction Counting
        self.predictionTracker = {"Predicted": [], # List contains cycle no.s where mis/prediction occurs
                                  "Mispredicted": []}
        self.cycleCount = 0

    DEBUG = {
            "fetchedInstruction": None,
            "decodedInstruction": None,
            "decodedMicroOps": [],
            "executedMicroOps": {"opcode": None,
                                   "operand": None,
                                   "operandSize": None}}
    
    """
    Computes an executable algorithm inoput to it
    INPUTS: list executable file to run, bool run in debug mode or not
    RETURNS: dict {cycle nos. of correctly predicted branches, cycle no.s of mispredicted branches}
    """
    def Compute(self, executable: list, debug: bool) -> dict:
        # Stage 1 - Move executable into memory
        for index, line in enumerate(executable):
            self.mainMemory.Store(f"[{index}]", line)
        
        # Stage 2 - Assign start of text/data section to segment registers
        self.registers.Store("cs", self.mainMemory.Retrieve(f"[0]"))
        self.registers.Store("ds", self.mainMemory.Retrieve(f"[1]"))

        # Stage 3 - Assign rip to start of text section
        self.registers.Store("ripw", self.registers.Load("cs")) # w, as cs is 2 bytes
        
        filterOpcode = None
        filterOperand = None
        filterCycle = None
        # Stage 4 - Fetch, Decode, Execute, until exit syscall changes running flag
        while self.running:
            # Ignore stalled parts of pipeline
            if not self.stalledStages["Execute"]:
                self.Execute()
            if not self.stalledStages["Decode"]:
                self.Decode()
            if not self.stalledStages["Fetch"]:
                self.Fetch()

            if  (
                    (
                        (self.DEBUG["executedMicroOps"]["opcode"] == filterOpcode and filterOpcode is not None)\
                        or (self.DEBUG["executedMicroOps"]["operand"] == filterOperand and filterOperand is not None)\
                        or (self.cycleCount == filterCycle and filterCycle is not None)\
                    )\
                    and not self.stalledStages["Execute"]\
                )\
                or (\
                        filterOpcode == None\
                        and filterOperand == None\
                        and filterCycle == None\
                    )\
                and debug == True:
                
                # Reset filters
                filterOpcode = None 
                filterOperand = None
                filterCycle = None
                
                print(f"""
    -----------------------CYCLE {self.cycleCount}-----------------------
                    PROGRAM COUNTER: {self.registers.Load("rip")}
                    {f"Fetched: {self.DEBUG["fetchedInstruction"]} from location: {self.registers.Load("mar")}" if self.DEBUG["fetchedInstruction"] is not None else "Fetched stalled!"}
                    Decoded: 
                    {f"{self.DEBUG["decodedInstruction"]} into micro-ops: {self.DEBUG["decodedMicroOps"]}." if self.DEBUG["decodedMicroOps"] != [] else "Decode Stalled!"}
                    Executed: 
                    {f"{self.DEBUG["executedMicroOps"]}." if self.DEBUG["executedMicroOps"]["opcode"] is not None else "Execute Stalled!"}
                    
                    Pipeline: {self.pipelineBuffer._Buffer}
                    (Front Pointer: {self.pipelineBuffer._frontPointer} Rear Pointer: {self.pipelineBuffer._rearPointer})

                    Re-Order Buffer: {self.reorderBuffer._Buffer}
                    (Front Pointer: {self.reorderBuffer._frontPointer} Rear Pointer: {self.reorderBuffer._rearPointer})

                    Registers: {self.registers.Registers.items()}

                    Main Memory: {self.mainMemory.__data__}

                    NEXT CYCLE? (C to set breakpoint on next opcode, A to set breakpoint on next operand, N to set breakpoint on specific cycle)
                    """)

                response = input()
                if response == 'C':
                    filterOpcode = input("Enter opcode to set breakpoint on: ")
                elif response == 'A':
                    filterOperand = input("Enter operand to set breakpoint on: ")
                elif response == 'N':
                    filterCycle = int(input("Enter cycle number to set breakpoint on: "))

            # Reset cycle data, increment cycle no, unstall fetch if stalled
            self.DEBUG = {
            "fetchedInstruction": None,
            "decodedInstruction": None,
            "decodedMicroOps": [],
            "executedMicroOps": {"opcode": None,
                                   "operand": None,
                                   "operandSize": None}}
            self.stalledStages["Fetch"] = False
            self.cycleCount += 1

        # Stage 5 - Stop executing
        print(f"DONE! In {self.cycleCount} cycles\nHave a nice day :)")
        return self.predictionTracker # TODO: IMPLEMENT RETURNING CORRECT DICT (In fun definition)
            


    ##-------PIPELINE STAGES-------##

    def Fetch(self):
        ## Stage 1: Branch Prediction (Predict next rip value)
        rip = self.registers.Load("ripb") # As only first byte contains instruction pointer (bodge as rip is an 8 byte int on a cpu that only deals with 1 byte ints)
        prediction = self.predictor.Predict(rip)
        if rip + 1 == prediction: # No branch taken
            speculative = False # TODO: Bug that predictions from a stall are considered speculative, when they're not..
        else: # Branch taken
            speculative = True # For now, speculative = branch taken

        self.registers.Store("rip", prediction)

        ## Stages 2 - 4: Put instruction into cir
        self.registers.Store("mar", self.registers.Load("rip"))

        # Check rip value is within text section
        if prediction < self.registers.Load("csb") or prediction >= self.registers.Load("dsb"):
            self.registers.Store("mbr", "noop")
        else:
            self.registers.Store("mbr", self.mainMemory.Retrieve(f"[{self.registers.Load("marb")}]"))

        if speculative: # Denote to decoder that mu-ops should be marked as speculative in ROB (by putting a * at end of instruction)
            self.registers.Store("cir", f"{self.registers.Load("mbr")}*")
        else:
            self.registers.Store("cir", self.registers.Load("mbr"))
        
        # Unstall Decode for next cycle
        self.stalledStages["Decode"] = False

        ## Return fetched instruction for output console
        self.DEBUG["fetchedInstruction"] = self.registers.Load("cir")

    def Decode(self):
        # TODO: Return if nothing in cir
        ## Stage 0 (*): Determine if instruction is speculative
        currentInstruction = self.registers.Load("cir")

        if currentInstruction.endswith('*'):
            speculative = True # If so, will need to be marked in mu-op queue to be marked in ROB
            currentInstruction = currentInstruction.rstrip('*')
        else:
            speculative = False

        ## Stage 1: Break instruction into mu-ops
        # Split into tokens [opcode, operands..]
        decomposedInstruction = currentInstruction.split()
    
        # Match opcode to set of mu-ops
        opcode = decomposedInstruction[0]
        operands = decomposedInstruction[1:]

        # Determine size of operands
        size = 8 # 8 bytes = 64 bit
        for op in operands:
            match op[-1]:
                case 'b':
                    size = 1
                    break
                case 'w':
                    if size > 2:
                        size = 2
                case 'l':
                    if size > 4:
                        size = 4
                case 'q':
                    continue
                case _:
                    continue

        mu_opBuffer = []
        match opcode:
            # mov a, b -> LOAD b, STO a
            case "mov":
                mu_opBuffer.append("LOAD " + operands[1])
                mu_opBuffer.append("STO " + operands[0])
            # jmp/je a -> JMP/JE/..
            case "jmp" | "je" | "jne" | "jg" | "jl" | "jge" | "jle":
                mu_opBuffer.append("LOAD " + operands[0])
                mu_opBuffer.append("JMP " + opcode.lstrip('j')) # e.g: JMP e / JMP ne / JMP g / JMP l / JMP mp (unconditional)
            # inc/dec a -> LOAD a, ADD/SUB 1, STO a
            case "inc" | "dec":
                mu_opBuffer.append("LOAD " + operands[0])
                mu_opBuffer.append("ADD 1" if opcode == "inc" else "SUB 1")
                mu_opBuffer.append("STO " + operands[0])
            # cmp a, b -> LOAD b, CMP a
            case "cmp":
                mu_opBuffer.append("LOAD " + operands[1])
                mu_opBuffer.append("CMP " + operands[0])
            # syscall -> syscall
            case "syscall":
                mu_opBuffer.append("SYSCALL")
            # noop -> NOOP
            case "noop":
                mu_opBuffer.append("NOOP")
            case _:
                raise Exception(f"Invalid operation recieved: {opcode}")
        
        # Mark instructions if speculative
        if speculative:
            mu_opBuffer = list(map(lambda x: x+'*' , mu_opBuffer))

        ## Stage 2 - 3 : Insert mu-ops into ROB and Pipeline Buffer (Not using reservation stations, as no tommasulo)

        # Check if there's enough space in ROB and Pipeline Buffer for mu-ops (if not, fetch stalls) 
        robOutOfSpace = self.reorderBuffer.GetNumberOfFreeSpaces() < len(mu_opBuffer)
        pipelineOutOfSpace = self.pipelineBuffer.GetNumberOfFreeSpaces() < len(mu_opBuffer)

        if robOutOfSpace or pipelineOutOfSpace:
            self.stalledStages["Fetch"] = True
            return

        # Insert mu-ops into ROB and pipeline buffer
        self.reorderBuffer.Add(mu_opBuffer, size, {"location" :self.registers.Load("ripb")})
        self.pipelineBuffer.Add(mu_opBuffer, size)

        # Unstall fetch and execute for next cycle
        self.stalledStages["Fetch"] = False
        self.stalledStages["Execute"] = False
        
        self.DEBUG["decodedInstruction"] = currentInstruction
        self.DEBUG["decodedMicroOps"] = mu_opBuffer

    def Execute(self):
        # Stage 1 : Get next mu-op in pipeline buffer
        mu_op = self.pipelineBuffer.Get()
        self.DEBUG["executedMicroOps"] = mu_op

        # Stage 2 : If operand is a memory address, run through AGU to calculate mem address to access
        if self.isMemoryAddress(mu_op["operand"]):
            mu_op["operand"] = self.AGU.Generate(mu_op["operand"])

        # Stage 2 : Invoke correct subroutine for instruction
        match mu_op["opcode"]:
            case "LOAD":
                self.Load(mu_op["operand"])
            case "STO":
                self.Store(mu_op["operand"])
            case "JMP":
                self.Jump(mu_op["operand"])
            case "ADD":
                self.Add(mu_op["operand"])
            case "SUB":
                self.Subtract(mu_op["operand"])
            case "CMP":
                self.Compare(mu_op["operand"])
            case "SYSCALL":
                self.Syscall() # Syscall doesn't take an operand
            case "NOOP":
                pass # No operation
            
        # Stage 3 : Remove mu-op from pipeline buffer + ROB
        self.pipelineBuffer.Remove()
        self.reorderBuffer.Remove()


    ##-------INSTRUCTION SET-------##
    #------DATA MANIPULATION------#

    #-------------
    # LOAD a
    # Load a into rax
    #-------------
    def Load(self, operand: int|str):
        # Find value of src
        if self.isMemoryAddress(operand):
            src = self.mainMemory.Retrieve(operand)

        elif self.isRegister(operand):
            src = self.registers.Load(operand)

        elif self.isImmediateValue(operand): # Immediate value
            src = operand
        
        else:
            raise Exception(f"Unexpected error on Load:\n\
                            Operand: {operand}")
        # rax <- src
        self.registers.Store("rax", src)

    
    #-------------
    # STO a
    # Store value of rax in location a
    #-------------
    def Store(self, operand: int|str):
        operandSize = self.pipelineBuffer.Get()["operandSize"]
        match operandSize:
            case 1:
                address = "raxb"
            case 2:
                address = "raxw"
            case 4:
                address = "raxl"
            case 8:
                address = "raxq"
            case _:
                raise Exception(f"Invalid operand size specified: Expected 1, 2, 4, or 8, got {operandSize}")
            
        value = self.registers.Load(address)
        # Find location to store
        if self.isMemoryAddress(operand):
            self.mainMemory.Store(operand, value)

        elif self.isRegister(operand):
            self.registers.Store(operand, value)

        else:
            raise Exception(f"Unexpected location in Store operation:\n\
                            Operand: {operand}")

    #------ARITHMETIC------#

    """UNTESTED"""
    #-------------
    # ADD a
    # Add a to rax. a could be register, location, or immediate value
    #-------------
    def Add(self, operand : int|str):
        if self.isMemoryAddress(operand):
            value = self.mainMemory.Retrieve(operand)
        
        elif self.isRegister(operand):
            value = self.registers.Load(operand)

        elif self.isImmediateValue(operand):
            value = operand
        
        else:
            raise Exception(f"Unexpected value to add:\n\
                Operand: {operand}")
        
        # Add value to rax
        try:
            rax = self.registers.Load("rax")
            # If int, just add to lowest byte of rax
            if type(value) == int:
                rax[0] += value
            # If list, add each element of value to rax in correct index
            else:
                for i in range(len(value)):
                    rax[i] += value[i]

            self.registers.Store("rax", rax)

        except:
            raise Exception(f"Couldn't add operand\n\
                            Operand: {operand} -> {value}, which could not be cast as int")
        
    #-------------
    # SUB a
    # Subtract a from rax 
    #-------------
    def Subtract(self, operand : int|str):
        return self.Add(-operand)

    #------LOGIC------#
    #-------------
    # cmp a
    # Changes flags in eflags based on a comparison between minuend and subtrahend
    #-------------
    def Compare(self, operand: list):
        # Retrieve minuend, convert from list of bytes to int
        minuend = 0
        rax = self.registers.Load("rax")
        for index, byte in enumerate(rax):
            minuend += byte * 2**index

        # Retrieve Subtrahend
        if self.isMemoryAddress(operand):
            subtrahend = self.mainMemory.Retrieve(operand)

        elif self.isRegister(operand):
            # Convert from list of bytes to int
            subtrahend = 0
            register = self.registers.Load(operand)
            if type(register) is int:
                subtrahend = register
            else:
                for index, byte in enumerate(register):
                    subtrahend += byte * 2**index

        elif self.isImmediateValue(operand): # Immediate value
            subtrahend = operand
        
        else:
            raise Exception(f"Unexpected minuend:\n\
                            Operand: {operand}")

        difference = minuend - int(subtrahend)

        ## Modify eflags based on changes
        eflags = self.registers.Load("eflags")
        # SF = 1 if difference < 0
        eflags["SF"] = 1 if difference < 0 else 0
        # ZF = 1 if difference = 0
        eflags["ZF"] = 1 if difference == 0 else 0
        # PF = 1 if difference = even
        eflags["PF"] = 1 if difference % 2 == 0 else 0

        self.registers.Store("eflags", eflags)

        return
    
    #------CONTROL FLOW------#
    #-------------
    # JMP a
    # Jumps to address in rax, based on result of condition a
    #-------------
    def Jump(self, operand: int|str):
        # Check if comparison condition is met in eflags
        # JMP e / JMP ne / JMP g / JMP l / JMP ge / JMP le / JMP mp
        eflags = self.registers.Load("eflags")
        match operand:
            case 'e':
                comparisonMet = eflags["ZF"]
            case "ne":
                comparisonMet = not eflags["ZF"]
            case 'g':
                comparisonMet = eflags["SF"]
            case 'l':
                comparisonMet = not eflags["SF"]
            case "ge":
                comparisonMet = eflags["SF"] or eflags["ZF"]
            case "le":
                comparisonMet = not eflags["SF"] or eflags["ZF"] # Seems to logically be LE
            case "mp":
                comparisonMet = True

        # If met, next fetch location = rax
        if comparisonMet:
            nextFetchLocation = self.registers.Load("rax")
        else:
            nextFetchLocation = self.reorderBuffer.Get()["location"]

        # Check if direction of branch correctly predicted - if not, flush pipeline, stall predictor, and point rip to correct address
        nextMu_op = self.reorderBuffer.Get(1)
        if comparisonMet != nextMu_op["speculative"]:
            self.Flush()
            self.predictor.Stall()
            self.registers.Store("rip", nextFetchLocation)
            # Add cycle number to misprediction tracker
            self.predictionTracker["Mispredicted"].append(self.cycleCount)
        else:
            # Add cycle number to prediction tracker
            self.predictionTracker["Predicted"].append(self.cycleCount)

        # Update branch predictor with result
        self.predictor.Update()
        return

    # TODO: Make actually work
    # SYSCALL
    # Performs a OS call operation (like printing to screen)
    def Syscall(self):
        ## Accepted Syscalls
        callType = self.registers.Load("raxb")
        match callType:
            ## 1 - Write
            case 1:
                ## Get all elements in memory that are in range
                # Convert start address and size from list -> ints
                rsi = self.registers.Load("rsi")
                startAddress = 0
                for index, byte in enumerate(rsi):
                    startAddress += byte * 2**index

                rdx = self.registers.Load("rdx")
                size = 0
                for index, byte in enumerate(rdx):
                    size += byte * 2**index
                # Put elements in write buffer
                writeBuffer = []
                for i in range(size):
                    writeBuffer.append(self.mainMemory.Retrieve(f"[{startAddress + i}]"))

                ## Output elements
                print(writeBuffer)
                return
            ## 60 - Exit
            case 60:
                # Set running signal to 0 - stops FDE
                self.running = False
                # Flush pipeline
                self.Flush()
                return
    
    def Call():
        pass

    def Return():
        pass

    def Push():
        pass

    def Pop():
        pass


    ##-------SPECIAL INSTRUCTIONS-------##
    # Flushes pipeline
    def Flush(self):
        # Clear ROB, Pipeline buffer
        self.reorderBuffer.Flush()
        self.pipelineBuffer.Flush()
        # Clear mar, mbr, cir
        self.registers.Store("mar", 0)
        self.registers.Store("mbr", '')
        self.registers.Store("cir", '')
        # Stall all pipeline stages
        self.stalledStages = {"Fetch": True,
                      "Decode": True,
                      "Execute": True}

    def isMemoryAddress(self, src: str) -> bool:
        if type(src) is not str:
            return False
        return True if src.startswith("[") and src.endswith("]") else False

    def isRegister(self, src: str) -> bool:
        if type(src) is int:
            return False
        return src.startswith('r') or src.startswith('e')
        
    def isImmediateValue(self, src: int) -> bool:
        return True if type(src) is int else False

# P = Processor()
# P.Compute()
