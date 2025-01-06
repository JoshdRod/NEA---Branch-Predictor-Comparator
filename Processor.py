"""
TODO:
- Complete SUB, JUMP, COMPARE, SYSCALL micro-operation functions
- Implement functionality into MainMemory
- Implement pipeline flushing method
- Remove bugs
"""

from MainMemory import MainMemory
import DirectionPredictors
from Buffers import ReadOnlyBuffer, PipelineBuffer

class Processor:

    def __init__(self):
        self.mainMemory = MainMemory() # Add a size on here? Don't really need to, but might be nice
        self.predictor = DirectionPredictors.BasePredictor() # TODO
        self.readOnlyBuffer = ReadOnlyBuffer(16) # 16 byte (section) buffer
        self.pipelineBuffer = PipelineBuffer(16)

    ##-------REGISTERS-------##
    Registers = {
                #--CALLEE-OWNED--#
                "rax": 0, # Accumulator / Return value
                "rdi": 0, # 1st arg
                "rsi": 0, # 2nd arg
                "rdx": 0, # 3rd arg
                "rcx": 0, # 4th arg
                "r8": 0, # 5th arg
                "r9": 0, # 6th arg
                "r10": 0, # temp
                "r11": 0, # temp
                #--CALLER-OWNED (local vars)--#
                "rbx": 0, 
                "rbp": 0,
                "r12": 0,
                "r13": 0,
                "r14": 0,
                "r15": 0,
                #--Address Registers--#
                "rsp": 0, # Stack pointer - caller-owned

                # Status/condition code bits - used to store result of comp operations
                "eflags": {
                           'PF': 0, # Parity Flag - Indicates result of previous operation was odd (0) or even (1)
                           'ZF': 0, # Zero Flag - Indicates result of previous operation was 0
                           'SF': 0, # Sign Flag - Indicates result of previous operation was negative
                           #CF, OF, AF Only needed if compaisons are done between binary numbers 
                           }, 

                #--INTERNAL REGISTERS--#
                "rip": 0, # Instruction pointer (Program Counter)
                "mbr": 0, # Memory Buffer Register
                "mar": 0, # Memory Address Register
                "cir": 0 # Current Instruction register (Can't find any documentation on this - might be bc you can't change its value programatically?)
                }

    ##-------PIPELINE STAGES-------##
    
    def Prefetch(): # What happens in prefetching? Is it just prediction? (Can I get away with saying it's just prediction?)
        pass

    def Fetch(self):
        ## Stage 1: Branch Prediction (Predict next rip value)
        prediction = self.predictor.Predict(self.Registers["rip"])
        if self.Registers["rip"] != prediction:
            speculative = True
            self.Registers["rip"] = prediction
        else:
            speculative = False # For now, speculative = branch taken

        ## Stages 2 - 4: Put instruction into cir
        self.Registers["mar"] = self.Registers["rip"]
        self.Registers["mbr"] = MainMemory.Retrieve([self.Registers["mar"]])
        self.Registers["cir"] = self.Registers["mbr"]

        if speculative: self.Registers["cir"] += '*' # Denotes to decoder that mu-ops should be marked as speculative in ROB

    def Decode(self):
        # TODO: Return if nothing in cir
        ## Stage 0 (*): Determine if instruction is speculative
        currentInstruction = self.Registers["cir"]
        if currentInstruction.endswith('*'):
            speculative = True # If so, will need to be marked in mu-op queue to be marked in ROB
            currentInstruction.rstrip('*')
        else:
            speculative = False

        ## Stage 1: Break instruction into mu-ops
        # Split into tokens [opcode, operands..]
        decomposedInstruction = currentInstruction.split()
    
        # Match opcode to set of mu-ops
        opcode = decomposedInstruction[0]
        operands = decomposedInstruction[1:]

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
            case _:
                raise Exception(f"Invalid operation recieved: {opcode}")
        
        # Mark instructions if speculative
        if speculative:
            mu_opBuffer = list(map(lambda x: x+'*' , mu_opBuffer))

        ## Stage 2 - 3 : Insert mu-ops into ROB and Pipeline Buffer (Not using reservation stations, as no tommasulo)
        # Check if there's enough space in ROB for mu-ops (if not, pipeline stalls) (TODO: If pipeline stalls, we'll have to decode the instruction all over again, surely that doesn't happen irl?)
        if self.readOnlyBuffer.GetNumberOfFreeSpaces() < len(mu_opBuffer):
            raise Exception(f"Not enough space in ROB to insert mu-ops:\
                             needed {len(mu_opBuffer)}, available {self.readOnlyBuffer.GetNumberOfFreeSpaces()} - pipeline stall needed")
        
        # Check if there's enough space in Pipeline Buffer for mu-ops (if not, pipeline stalls) (TODO: If pipeline stalls, we'll have to decode the instruction all over again, surely that doesn't happen irl?)
        if self.pipelineBuffer.GetNumberOfFreeSpaces() < len(mu_opBuffer):
            raise Exception(f"Not enough space in Pipeline Buffer to insert mu-ops:\
                             needed {len(mu_opBuffer)}, available {self.pipelineBuffer.GetNumberOfFreeSpaces()} - pipeline stall needed")
        # TODO: This really does NOT seem very DRY

        # Insert mu-ops into ROB and pipeline buffer
        self.readOnlyBuffer.Add(mu_opBuffer)
        self.pipelineBuffer.Add(mu_opBuffer)

    def Execute(self):
        # Stage 1 : Get next mu-op in pipeline buffer
        mu_op = self.pipelineBuffer.Get()

        # Stage 2 : Invoke correct subroutine for instruction
        match mu_op["opcode"]:
            case "LOAD":
                return self.Load(mu_op["operand"])
            case "STO":
                return self.Store(mu_op["operand"])
            case "JMP":
                return self.Jump(mu_op["operand"])
            case "ADD":
                return self.Add(mu_op["operand"])
            case "SUB":
                return self.Subtract(mu_op["operand"])
            case "CMP":
                return self.Compare(mu_op["operand"])
            case "SYSCALL":
                return self.Syscall() # Syscall doesn't take an operand
            
        # Stage 3 : Remove mu-op from pipeline buffer + ROB
        self.pipelineBuffer.Remove()
        self.readOnlyBuffer.Remove()

    ##-------INSTRUCTION SET-------##
    #------DATA MANIPULATION------#

    """UNTESTED"""
    #-------------
    # LOAD a
    # Load a into rax
    #-------------
    def Load(self, operand: int|str):
        # Find value of src
        match operand:
            case self.isMemoryAddress(operand):
                src = self.mainMemory.Retrieve(operand)

            case self.isRegister(operand):
                src = self.Registers[operand]

            case self.isImmediateValue(operand): # Immediate value
                src = operand
            
            case _:
                raise Exception(f"Unexpected error on Load:\n\
                                Operand: {operand}")
        # rax <- src
        self.Registers["rax"] = src

    
    #-------------
    # STO a
    # Store value of rax in location a
    #-------------
    def Store(self, operand: int|str):
        value = self.Registers["rax"]
        # Find location to store
        match operand:
            case self.isMemoryAddress(operand):
                self.mainMemory.Store(operand, value)

            case self.isRegister(operand):
                self.Registers[operand] = value

            case _:
                raise Exception(f"Unexpected location in Store operation:\n\
                                Operand: {operand}")

    #------ARITHMETIC------#

    """UNTESTED"""
    #-------------
    # ADD a
    # Add a to rax. a could be register, location, or immediate value
    #-------------
    def Add(self, operand : int|str):
        match operand:
            case self.isMemoryAddress(operand):
                self.Registers["rax"] += self.mainMemory.Retrieve(operand)
            
            case self.isRegister(operand):
                self.Registers["rax"] += self.Registers[operand]

            case self.isImmediateValue(operand):
                self.Registers["rax"] += int(operand.lstrip('#'))
    """TODO: does it make more sense to just call add here? Becuase a - b = a + (-b), and that's ETC"""

    #-------------
    # sub r1, r2/const.
    # Subtracts r2/const from r1, and stores result in r1
    #-------------
    def Subtract(self, operand : list):
        try:
            # If a and b are both memory addresses, throw error
            if self.isMemoryAddress(operand[0]):
                if self.isMemoryAddress(operand[1]): raise Exception("Invlid Combination of Opcode and Operands")
                if not self.isRegister(operand[1]): raise Exception("TOADD: Operand not register or mem. address")

                difference = self.mainMemory.Retrieve(operand[0]) - self.Registers[operand[1]]
            
            elif self.isRegister(operand[0]):
                if self.isRegister(operand[1]):
                    difference = self.Registers[operand[0]] - self.Registers[operand[1]] 
                if self.isMemoryAddress(operand[1]):
                    difference = self.Registers[operand[0]] - self.mainMemory.Retrieve(operand[1])
                else:
                    raise Exception("TOADD: Operand not register or mem. address")

            else:
                raise Exception("TOADD: Operand not register or mem. address")
            
            self.mainMemory.Store(operand[0], difference) # What about if a is a register?
            # Find location of a    

            # Find value of b
            # Add b to a
        except:
            pass # How do I make this throw a message that the register doesn't exist, and the exit nicely?

    #------LOGIC------#
    #-------------
    # cmp minuend, subtrahend
    # Changes flags in eflags based on a comparison between minuend and subtrahend
    #-------------
    def Compare(self, operand: list):
        # Calculate Difference
        minuend = operand[0]
        subtrahend = operand[1]

        difference = minuend - subtrahend
        # SF = 1 if difference < 0
        self.Registers["eflags"]["SF"] = 1 if difference < 0 else 0
        # ZF = 1 if difference = 0
        self.Registers["eflags"]["ZF"] = 1 if difference == 0 else 0
        # PF = 1 if difference = even
        self.Registers["eflags"]["PF"] = 1 if difference % 2 == 0 else 0

        return
    
    #------CONTROL FLOW------#
    #-------------
    # jmp/je/jg/jl loc
    # Changes program counter to point at location specified 
    #-------------
    def Jump(self, condition: str, loc: str):
        # Check if comparison condition is met in eflags
        comparisonMet = True # TODO: Change this to correct condition in eflags = 1
        # If met, next fetch location = loc
        if comparisonMet:
            nextFetchLocation = loc
        # Else, next fetch location = jump instruction location + [instruction size]
        else:
            nextFetchLocation = self.readOnlyBuffer.Get(0)["from"] + 2 # TODO: Fix this offset to point to the next instruction, after the memory module has been properly set out

        # Check if next instruction has came from new fetch location (using ROB) - if so, all good, no changes needed
        nextPipelineInstructionLocation = self.readOnlyBuffer.Get(1)["from"]

        # If not, flush pipline and set rip to new fetch location
        if nextFetchLocation != nextPipelineInstructionLocation:
            #TODO: FLUSH INSTRUCTION PIPELINE# 
            self.Registers["rip"] = nextFetchLocation

        # Update branch predictor with result
        self.predictor.Update()
        return

    # TODO: Make actually work
    def Syscall(self):
        print(self.Registers["rsi"])
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
    def isMemoryAddress(src: str) -> bool:
        return True if src.startswith("[") and src.endswith("]") else False

    def isRegister(src: str) -> bool:
        return src.startswith('r')
    
    def isImmediateValue(src: str) -> bool:
        return src.startswith('#')


    
    

    
    



