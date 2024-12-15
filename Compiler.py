class Compiler:
    SymbolTable = [None for i in range(100)]

    # TODO: Fix complier not dealing with numeric addition on pointer addresses
    # (e.g: "mov rbp, array + 5" -> ["mov", "rbp,", "{location of pointer array + 5}"]
    # instead of: ["mov", "rbp,", "array", "+", "5"])

    # Deal w/ data values in the _data section (assign them locations in memory + replace pointers w/ their locations)
    def Compile(self, fileName):
        # Read in file
        with open(fileName, 'r') as f:
            asm = f.readlines()
            # Remove Empty lines/indentation
            asm = list(filter(lambda x: not x.isspace(), asm)) # isspace returns true of whole string only consists of spaces
            asm = list(map(lambda x: x.strip(), asm))
            # Remove Whole line Comments
            asm = list(filter(lambda x: not x.startswith(';'), asm)) # Filter only returns elements that return true out of the function
            # 4Remove inline Comments
            asm = list(map(lambda x: x[:x.find(';') - 1] if x.find(';') != -1 else x, asm)) # Find returns 1st instance of substring in string (or -1 if not found)
            # Convert to 1d array of tokens (a token is separated by whitespace) 
            asm = " ".join(asm) 
            asm = asm.split(' ')

            # Replace Symbols with direct memory addresses
            self.GenerateSymbolTable(asm) # Generate symbol table
            asm = list(filter(lambda x: not (x.startswith('.') and x.endswith(':')), asm)) # Remove label definitions used to generate symbol table
            asm = list(map(self.ConvertLabelToMemoryAddress, asm)) # Replace label references with direct memory addresses
        return

    # Should get an error, because as when the label is eventually removed from the source code, its pointer,
    # and all subsequent, are going to be off by an offset of 1. This offset increases for every new label defined
    # But we're not.. and I've not no clue why...
    def GenerateSymbolTable(self, asm: list) -> list:
    ## DATA LABELS (Refer to places in memory)

    ## POSITIONAL LABELS - (just made that term up, idk what the real one is)
        # Cycle through all the tokens in the asm code
        for index, token in enumerate(asm):
            # Check if line starts with a .
            if token.startswith('.') and token.endswith(':'):    
                # Take its name and current memory location
                name = token[:-1] # Get rid of colon
                location = "0x" + str(index)
                #offset += 1
                # Hash
                key = self.hash(name)
                # Insert dict {name: memory location} into index of hash in symbol table
                for i in range(100):
                    if self.SymbolTable[(key + i) % 100] is not None: continue

                    self.SymbolTable[(key + i) % 100] = {"name": name,
                                                         "location" : location}
                    break
                else:
                    raise Exception("Symbol Table is full!")
                asm.pop(index)
        return

    """
    Takes in tokens, and, if they are are a label, converts them to their corresponding memory address in the symbol table
    INPUT: string token
    RETURNS: string token or, if token is a label, the mem. address that label points to
    """
    def ConvertLabelToMemoryAddress(self, token: str) -> str:
        if not token.startswith('.'): return token # token not a label

        # Find the label in the symbol table
        key = self.hash(token) # There's never going to be a comma on the end of a label, is there? I don't believe so, as we should only be using them for jumps
        for i in range(100):
            if self.SymbolTable[key + i] is None: raise Exception(f"Couldn't find label {token} in Symbol table! {self.SymbolTable}")
            # When found, return the location the label points to
            if self.SymbolTable[key + i]["name"] == token:
                return self.SymbolTable[key + i]["location"]
            
        raise Exception(f"Symbol Table full (and label {token} couldn't be found)! {self.SymbolTable}")
    
    """
    Converts input string to a random key between 0 - 99
    INPUT: string s
    RETURNS: int key (0 - 99)
    """
    def hash(self, input: str) -> int:
        SumOfASCIIInput = 0
        for char in input:
            SumOfASCIIInput += ord(char)
        
        return SumOfASCIIInput % 100 


C = Compiler()
C.Compile("test.txt")



