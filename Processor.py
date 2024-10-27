class Processor:
    def Prefetch(): # What happens in prefetching? Is it just prediction? (Can I get away with saying it's just prediction?)
        pass
    def Fetch():
        pass
    def Decode():
        pass
    def Execute():
        pass

    ##-------INSTRUCTION SET-------##
    #-------------
    # add r1, r2/const.
    # Adds together 2 operands, and stores result in r1
    #-------------
    def Add():
        pass

    def Branch():
        pass
    
    def Compare():
        pass

    #-------------
    # dec r1
    # Decrements contents of r1 by 1
    #-------------
    def Decrement():
        pass

    #-------------
    # inc r1
    # Increments contents of r1 by 1
    #-------------
    def Increment():
        pass
    
    #-------------
    # mov r1, r2
    # Moves bytes from r2 to r1 (not a typo)
    #-------------
    def Move():
        pass
    
    #-------------
    # sub r1, r2/const.
    # Subtracts r2/const from r1, and stores result in r1
    #-------------
    def Subtract():
        pass
