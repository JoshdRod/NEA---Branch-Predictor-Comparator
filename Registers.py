# TODO: WHAT ABOUT MOV [memaddr] rbxb?? Wouldn't that move the 0s in as well?
class Registers:
    ##-------REGISTERS-------##
    Registers = {
                #--CALLEE-OWNED--#
                "rax": [0 for i in range(8)], # Accumulator / Return value
                "rdi": [0 for i in range(8)], # 1st arg
                "rsi": [0 for i in range(8)], # 2nd arg
                "rdx": [0 for i in range(8)], # 3rd arg
                "rcx": [0 for i in range(8)], # 4th arg
                "r8": [0 for i in range(8)], # 5th arg
                "r9": [0 for i in range(8)], # 6th arg
                "r10": [0 for i in range(8)], # temp
                "r11": [0 for i in range(8)], # temp
                #--CALLER-OWNED (local vars)--#
                "rbx": [0 for i in range(8)], 
                "rbp": [0 for i in range(8)],
                "r12": [0 for i in range(8)],
                "r13": [0 for i in range(8)],
                "r14": [0 for i in range(8)],
                "r15": [0 for i in range(8)],
                #--Address Registers--#
                "rsp": [0 for i in range(8)], # Stack pointer - caller-owned

                # Status/condition code bits - used to store result of comp operations
                "eflags": {
                           'PF': 0, # Parity Flag - Indicates result of previous operation was odd (0) or even (1)
                           'ZF': 0, # Zero Flag - Indicates result of previous operation was 0
                           'SF': 0, # Sign Flag - Indicates result of previous operation was negative
                           #CF, OF, AF Only needed if compaisons are done between binary numbers 
                           }, 

                #--INTERNAL REGISTERS--#
                "rip": [0 for i in range(8)], # Instruction pointer (Program Counter)
                "mbr": [0 for i in range(8)], # Memory Buffer Register
                "mar": [0 for i in range(8)], # Memory Address Register
                "cir": [0 for i in range(8)] # Current Instruction register (Can't find any documentation on this - might be bc you can't change its value programatically?)
                }
    
    """
    LOADS REGISTER VALUES INTO AN OPERATION
    INPUT: Register to access (including suffix)
    RETURNS: list/int(if suffix=b) value of register (in mode denoted by suffix) 
    """
    def Load(self, register: str) -> list:
        try:
            suffix = register[-1]
            register = register[:-1]
            match suffix:
                # Byte (8 bits) (last byte)
                case 'b':
                    return self.Registers[register][0] # Take lowest bit from reg
                # Word (16 bits) (last 2 bytes)
                case 'w':
                    return self.Registers[register][0:2] 
                # Long (32 bits) (last 4 bytes)
                case 'l':
                    return self.Registers[register][0:5]
                # Quadword (64 bits) (whole 8 bytes)
                case 'q':
                    return self.Registers[register]
                # If no suffix, return whole register (8 bytes)
                case _:
                    register += suffix
                    return self.Registers[register]
        except:
            raise Exception(f"Invalid register name accessed! {register}")

    """
    Stores value (either 8-byte list, or single int, or an instruction string) into register
    INPUTS: str register to store in, list/int/str value to store 
    """
    def Store(self, register: str, value: list|int|str):
        # eflags stores dictionary of flags, so overwrite eflags with dictionary
        if register == "eflags":
            self.Registers["eflags"] = value
            return

        # String instructions are 8 bytes, so overwrite whole register with string
        if type(value) == str:
            self.Registers[register] = value
            return
        

        # As registers are 8 byte, convert single ints into 6 byte lists
        if type(value) == int:
            value = [value] + [0 for i in range(7)]
        
        try:
            # Select correct amount of bits to overwrite based on suffix
            suffix = register[-1]
            register = register[:-1]
            match suffix:
                # Byte (8 bits) (last byte)
                case 'b':
                    bitsAffected = 1
                # Word (16 bits) (last 2 bytes)
                case 'w':
                    bitsAffected = 2
                # Long (32 bits) (last 4 bytes)
                case 'l':
                    bitsAffected = 4
                # Quadword (64 bits) (whole 8 bytes)
                case 'q':
                    bitsAffected = 8
                # If no suffix, return whole register (8 bytes)
                case _:
                    register += suffix
                    bitsAffected = 8
            
            # Overwrite those register bits
            self.Registers[register][0:bitsAffected] = value[0:bitsAffected]
        except:
            raise Exception(f"Invalid register name accessed! {register}")