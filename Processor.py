class Processor:

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
                "eflags": 0, # Status/condition code bits - used to store result of comp operations
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

    #-------------
    # mov r1, r2
    # Moves bytes from r2 to r1 (not a typo)
    #-------------
    def Move():
        pass

    def Push():
        pass

    def Pop():
        pass
    
    #------ARITHMETIC------#

    #-------------
    # add r1, r2/const.
    # Adds together 2 operands, and stores result in r1
    #-------------
    def Add():
        pass

    #-------------
    # sub r1, r2/const.
    # Subtracts r2/const from r1, and stores result in r1
    #-------------
    def Subtract():
        pass

    #-------------
    # inc r1
    # Increments contents of r1 by 1
    #-------------
    def Increment():
        pass

    #-------------
    # dec r1
    # Decrements contents of r1 by 1
    #-------------
    def Decrement():
        pass

    #------LOGIC------#
    def Compare():
        pass
    #------CONTROL FLOW------#

    def Branch():
        pass

    def Call():
        pass

    def Return():
        pass

    def Syscall():
        pass

    

    
    



