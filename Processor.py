"""
TODO:
- Implement register addresing modes (e.g b, h, etc.) (as can't access registers correctly w/o them)
- Make processor halt at end of program
- Remove bugs
- Change processor operating mode - currently, branch prediction doesn't improve anything, because there's no misfetch penalty
- Clean up passing operand into mu-op functions in execute - most functions just take the int value of the operator (jmp and sto being the issue), try to convert it before!
- Fix fact that all computed memory addresses can't contain spaces in the compiler (e.g: Won't accept "[rax + 5]" must be "[rax+5]")
- A direct CPU interface would be nice (like the IDLE interpreter)
"""

from MainMemory import MainMemory
import DirectionPredictors
from Buffers import ReorderBuffer, PipelineBuffer
from AddressGenerationUnit import AGU
from Registers import Registers

class Processor:

    def __init__(self):
        self.predictor = DirectionPredictors.BasePredictor() # TODO
        self.registers = Registers()
        self.mainMemory = MainMemory(100) # 100 byte (lines) main memory
        self.reorderBuffer = ReorderBuffer(16) # 16 byte (section) buffer
        self.pipelineBuffer = PipelineBuffer(16)
        self.AGU = AGU(self.Registers)

    DEBUG = {"decoded-micro-ops": None,
            "executed-micro-ops": None}
    
    def Compute(self):
        executable = ['mov rbx 29', 'mov rbp 34', 'mov rdi rbx', 'jmp 4', 'cmp rdi rbp', 'je 16', 'mov r10b [rdi]', 'cmp r10b [rdi+1]', 'jg 10', 'jmp 14', 'mov r11b [rdi+1]', 'mov [rdi] r11b', 'mov [rdi+1] r10b', 'jmp 14', 'inc rdi', 'jmp 4', 'dec rbp', 'cmp rbx rbp', 'je 21', 'mov rdi rbx', 'jmp 4', 'mov rax 1', 'mov rdi 1', 'mov rsi 29', 'mov rdx 6', 'syscall', 'mov rax 60', 'mov rdi 0', 'syscall', '81', '77', '68', '69', '74', '65']
        for index, line in enumerate(executable):
            self.mainMemory.Store(index, line)
        
        cycleNumber = 0
        while True:
            self.Fetch()
            self.Decode()
            self.Execute()

            print(f"""
                  
   -----------------------CYCLE {cycleNumber}-----------------------
                  PROGRAM COUNTER: {self.Registers["rip"]}
                  Fetched: {self.Registers["cir"]} from location: {self.Registers["mar"]}.
                  Decoded: {self.Registers["cir"]} into micro-ops: {self.DEBUG["decoded-micro-ops"]}.
                  Executed: {self.DEBUG["executed-micro-ops"]}.
                  
                  Pipeline: {self.pipelineBuffer._Buffer}
                  (Front Pointer: {self.pipelineBuffer._frontPointer} Rear Pointer: {self.pipelineBuffer._rearPointer})

                  Re-Order Buffer: {self.reorderBuffer._Buffer}
                  (Front Pointer: {self.reorderBuffer._frontPointer} Rear Pointer: {self.reorderBuffer._rearPointer})

                  Registers: {self.Registers.items()}

                  Main Memory: {self.mainMemory.__data__}

                  NEXT CYCLE?
                  """)
            input()
            


    ##-------PIPELINE STAGES-------##
    
    def Prefetch(): # What happens in prefetching? Is it just prediction? (Can I get away with saying it's just prediction?)
        pass

    def Fetch(self):
        ## Stage 1: Branch Prediction (Predict next rip value)
        prediction = self.predictor.Predict(self.Registers["rip"])
        if self.Registers["rip"] + 1 == prediction: # No branch taken
            speculative = False # TODO: Bug that predictions from a stall are considered speculative, when they're not..
        else: # Branch taken
            speculative = True # For now, speculative = branch taken

        self.Registers["rip"] = prediction

        ## Stages 2 - 4: Put instruction into cir
        self.Registers["mar"] = self.Registers["rip"]
        self.Registers["mbr"] = self.mainMemory.Retrieve(self.Registers["mar"])
        self.Registers["cir"] = self.Registers["mbr"]

        if speculative: self.Registers["cir"] += '*' # Denotes to decoder that mu-ops should be marked as speculative in ROB

    def Decode(self):
        # TODO: Return if nothing in cir
        ## Stage 0 (*): Determine if instruction is speculative
        currentInstruction = self.Registers["cir"]

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
        if self.reorderBuffer.GetNumberOfFreeSpaces() < len(mu_opBuffer):
            raise Exception(f"Not enough space in ROB to insert mu-ops:\
                             needed {len(mu_opBuffer)}, available {self.reorderBuffer.GetNumberOfFreeSpaces()} - pipeline stall needed")
        
        # Check if there's enough space in Pipeline Buffer for mu-ops (if not, pipeline stalls) (TODO: If pipeline stalls, we'll have to decode the instruction all over again, surely that doesn't happen irl?)
        if self.pipelineBuffer.GetNumberOfFreeSpaces() < len(mu_opBuffer):
            raise Exception(f"Not enough space in Pipeline Buffer to insert mu-ops:\
                             needed {len(mu_opBuffer)}, available {self.pipelineBuffer.GetNumberOfFreeSpaces()} - pipeline stall needed")
        # TODO: This really does NOT seem very DRY

        # Insert mu-ops into ROB and pipeline buffer
        self.reorderBuffer.Add(mu_opBuffer)
        self.pipelineBuffer.Add(mu_opBuffer)

        self.DEBUG["decoded-micro-ops"] = mu_opBuffer

    def Execute(self):
        # Stage 1 : Get next mu-op in pipeline buffer
        mu_op = self.pipelineBuffer.Get()

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
            
        # Stage 3 : Remove mu-op from pipeline buffer + ROB
        self.pipelineBuffer.Remove()
        self.reorderBuffer.Remove()

        self.DEBUG["executed-micro-ops"] = mu_op

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
            src = self.Registers[operand]

        elif self.isImmediateValue(operand): # Immediate value
            src = operand
        
        else:
            raise Exception(f"Unexpected error on Load:\n\
                            Operand: {operand}")
        # rax <- src
        self.Registers["rax"] = int(src)

    
    #-------------
    # STO a
    # Store value of rax in location a
    #-------------
    def Store(self, operand: int|str):
        value = self.Registers["rax"]
        # Find location to store
        if self.isMemoryAddress(operand):
            self.mainMemory.Store(operand, value)

        elif self.isRegister(operand):
            self.Registers[operand] = value

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
            value = self.Registers[operand]

        elif self.isImmediateValue(operand):
            value = operand
        
        else:
            raise Exception(f"Unexpected value to add:\n\
                Operand: {operand}")
        
        # Add value to rax
        try:
            self.Registers["rax"] += int(value)
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
        # Retrieve minuend
        minuend = self.Registers["rax"]
        
        # Retrieve Subtrahend
        if self.isMemoryAddress(operand):
            subtrahend = self.mainMemory.Retrieve(operand)

        elif self.isRegister(operand):
            subtrahend = self.Registers[operand]

        elif self.isImmediateValue(operand): # Immediate value
            subtrahend = operand
        
        else:
            raise Exception(f"Unexpected minuend:\n\
                            Operand: {operand}")

        difference = minuend - int(subtrahend)
        # SF = 1 if difference < 0
        self.Registers["eflags"]["SF"] = 1 if difference < 0 else 0
        # ZF = 1 if difference = 0
        self.Registers["eflags"]["ZF"] = 1 if difference == 0 else 0
        # PF = 1 if difference = even
        self.Registers["eflags"]["PF"] = 1 if difference % 2 == 0 else 0

        return
    
    #------CONTROL FLOW------#
    #-------------
    # JMP a
    # Jumps to address in rax, based on result of condition a
    #-------------
    def Jump(self, operand: int|str):
        # Check if comparison condition is met in eflags
        # JMP e / JMP ne / JMP g / JMP l / JMP ge / JMP le / JMP mp
        match operand:
            case 'e':
                comparisonMet = self.Registers["eflags"]["ZF"]
            case "ne":
                comparisonMet = not self.Registers["eflags"]["ZF"]
            case 'g':
                comparisonMet = self.Registers["eflags"]["SF"]
            case 'l':
                comparisonMet = not self.Registers["eflags"]["SF"]
            case "ge":
                comparisonMet = self.Registers["eflags"]["SF"] or self.Registers["eflags"]["ZF"]
            case "le":
                comparisonMet = not self.Registers["eflags"]["SF"] or self.Registers["eflags"]["ZF"] # Seems to logically be LE
            case "mp":
                comparisonMet = True

        # If met, next fetch location = rax
        if comparisonMet:
            nextFetchLocation = self.Registers["rax"]

        # Take next mu-op
        nextMu_op = self.reorderBuffer.Get(1)

        # If mu-op prediction and actual result don't match up, flush pipline and reset rip
        if comparisonMet != nextMu_op["speculative"]:
            self.Flush()
            self.Registers["rip"] = self.Registers["rax"]

        # Update (and stall for 1 cycle) branch predictor with result
        self.predictor.Update()
        self.predictor.Stall()
        return

    # TODO: Make actually work
    # SYSCALL
    # Performs a OS call operation (like printing to screen)
    def Syscall(self):
        ## Accepted Syscalls
        callType = self.Registers["rax"]
        match callType:
            ## 1 - Write
            case 1:
                print(self.Registers["rsi"])
                return
            ## 60 - Exit
            case 60:
                self.Flush()
                return # TODO: Set this up to change a flag in the interrupts register, that then stops the CPU from running
    
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
        self.Registers["mar"] = 0
        self.Registers["mbr"] = 0
        self.Registers["cir"] = 0

    def isMemoryAddress(self, src: str) -> bool:
        if type(src) is int:
            return False
        return True if src.startswith("[") and src.endswith("]") else False

    def isRegister(self, src: str) -> bool:
        if type(src) is int:
            return False
        return src.startswith('r')
        
    def isImmediateValue(self, src: int) -> bool:
        return True if type(src) is int else False
P = Processor()
P.Compute()
