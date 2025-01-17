# TODO: WHAT ABOUT MOV [memaddr] rbxb?? Wouldn't that move the 0s in as well?
class Registers:
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
    
    """
    LOADS REGISTER VALUES INTO AN OPERATION
    INPUT: Register to access (including suffix)
    RETURNS: list value of register (in mode denoted by suffix) 
    """
    def Load(self, register: str) -> list:
        try:
            suffix = register.pop()
            match suffix:
                # Byte (8 bits) (last byte)
                case 'b':
                    return self.Registers[register][0] + [0 for i in range(7)] # Take lowest bit from reg, then add 7 0s on end
                # Word (16 bits) (last 2 bytes)
                case 'w':
                    return self.Registers[register][0:2] + [0 for i in range(6)]
                # Long (32 bits) (last 4 bytes)
                case 'l':
                    return self.Registers[register][0:5] + [0 for i in range(4)]
                # Quadword (64 bits) (whole 8 bytes)
                case 'q':
                    return self.Registers[register]
                # If no suffix, return whole register (8 bytes)
                case _:
                    register.append(suffix)
                    return self.Registers[register]
        except:
            raise Exception(f"Invalid register name accessed! {register}")

    def Store(self, register: str, value: list|int):
        return