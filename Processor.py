from MainMemory import MainMemory
import DirectionPredictors
from ReadOnlyBuffer import ReadOnlyBuffer

class Processor:

    def __init__(self):
        self.mainMemory = MainMemory() # Add a size on here? Don't really need to, but might be nice
        self.predictor = DirectionPredictors.BasePredictor() # TODO
        self.readOnlyBuffer = ReadOnlyBuffer() # TODO

    ##-------REGISTERS-------##
    Registers = {
                #--CALLEE-OWNED--#
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
                #--SPECIAL--#
                "rax": 0, # Return value - callee-owned
                "rsp": 0, # Stack pointer - caller-owned

                "rip": 0, # Instruction pointer


                # Status/condition code bits - used to store result of comp operations
                "eflags": {
                           'PF': 0, # Parity Flag - Indicates result of previous operation was odd (0) or even (1)
                           'ZF': 0, # Zero Flag - Indicates result of previous operation was 0
                           'SF': 0, # Sign Flag - Indicates result of previous operation was negative
                           #CF, OF, AF Only needed if compaisons are done between binary numbers 
                           }, 
                }
    # Going to need (what's the fetch one called?), MBR, CIR, to store the instructions during FDE

    ##-------PIPELINE STAGES-------##
    
    def Prefetch(): # What happens in prefetching? Is it just prediction? (Can I get away with saying it's just prediction?)
        pass
    def Fetch():
        pass
    def Decode():
        pass
    def Execute():
        pass

    ##-------INSTRUCTION SET-------##
    #------DATA MANIPULATION------#

    """UNTESTED"""
    #-------------
    # mov dest, src 
    # Copies bytes from src to dest. At the end of the operation, src and dest both contain the same contents
    #              src                 |   
    # immediate | register | mem. addr |  dest
    #----------------------------------|
    #   Y           Y          Y       | register
    #   Y           Y          N       | mem addr.
    #-------------
    def Move(self, operand: list):
        try:
            # Find value of src
            if self.isMemoryAddress(operand[1]):
                src = self.mainMemory.Retrieve(operand[1])
            elif self.isRegister(operand[1]):
                src = self.Registers[operand[1]]
            elif int(operand[1]): # Immediate value
                src = operand[1]

            # Find location of dest, dest <-- src
            if self.isMemoryAddress(operand[0]):
                self.mainMemory.Store(src)
            elif self.isRegister(operand[0]):
                self.Registers[operand[0]] = src
        except:
            pass

    def Push():
        pass

    def Pop():
        pass
    
    #------ARITHMETIC------#

    """UNTESTED"""
    """TODO: What if b is an immediate value?"""
    #-------------
    # add a, b
    # where a,b is either register or memory address, and a,b are not both memory address
    # Adds together 2 operands, and stores result in a
    #-------------
    def Add(self, operand : list):
        try:
            # If a and b are both memory addresses, throw error
            if self.isMemoryAddress(operand[0]):
                if self.isMemoryAddress(operand[1]): raise Exception("Invlid Combination of Opcode and Operands")
                if not self.isRegister(operand[1]): raise Exception("TOADD: Operand not register or mem. address")

                sum = self.mainMemory.Retrieve(operand[0]) + self.Registers[operand[1]]
            
            elif self.isRegister(operand[0]):
                if self.isRegister(operand[1]):
                    sum = self.Registers[operand[0]] + self.Registers[operand[1]] 
                if self.isMemoryAddress(operand[1]):
                    sum = self.Registers[operand[0]] + self.mainMemory.Retrieve(operand[1])
                else:
                    raise Exception("TOADD: Operand not register or mem. address")

            else:
                raise Exception("TOADD: Operand not register or mem. address")
            
            self.mainMemory.Store(operand[0], sum) # What about if a is a register?
            # Find location of a    

            # Find value of b
            # Add b to a
        except:
            pass # How do I make this throw a message that the register doesn't exist, and the exit nicely?

    """TODO: FINISH"""
    #-------------
    # sub r1, r2/const.
    # Subtracts r2/const from r1, and stores result in r1
    #-------------
    def Subtract(self, operand : list):
        try:
            self.Registers[operand[0]] -= self.Registers[operand[1]] if # operand1 can be an int? how do I check that well?
        except:
            pass # How do I make this throw a message that the register doesn't exist, and the exit nicely?

    """UNTESTED"""
    #-------------
    # inc src
    # Increments contents of src (register or mem. address) by 1
    #-------------
    def Increment(self, src: str):
        try:
            if self.isMemoryAddress(src):
                self.mainMemory.Store(src, self.mainMemory.Retrieve(src) + 1)
            elif self.isRegister(src):
                self.Registers[src] += 1
        except:
            pass # Error?

    #-------------
    # dec r1
    # Decrements contents of r1 by 1
    #-------------
    def Decrement(self, src: str):
        try:
            if self.isMemoryAddress(src):
                self.mainMemory.Store(src, self.mainMemory.Retrieve(src) - 1)
            elif self.isRegister(src):
                self.Registers[src] -= 1
        except:
            pass # Error?

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

    def Call():
        pass

    def Return():
        pass

    # TODO: Make actually work
    def Syscall(self):
        print(self.Registers["rsi"])
        return

    ##-------SPECIAL INSTRUCTIONS-------##
    def isMemoryAddress(src: str) -> bool:
        return True if src.startswith("0x") else False

    def isRegister(src: str) -> bool:
        return True if src.startswith('r') else False


    
    

    
    



