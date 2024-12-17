class Compiler:
    SymbolTable = [None for i in range(100)]
    Offsets = {}

    # TODO: Fix complier not dealing with numeric addition on pointer addresses
    # (e.g: "mov rbp, array + 5" -> ["mov", "rbp,", "{location of pointer array + 5}"]
    # instead of: ["mov", "rbp,", "array", "+", "5"])

    # Deal w/ data values in the _data section (assign them locations in memory + replace pointers w/ their locations)
    def Compile(self, fileName):
        # Read in file
        with open(fileName, 'r') as f:
            asm = f.readlines()

            ## GENERIC
            # Remove Empty lines/indentation
            asm = list(filter(lambda x: not x.isspace(), asm)) # isspace returns true of whole string only consists of spaces
            asm = list(map(lambda x: x.strip(), asm))
            # Remove Whole line Comments
            asm = list(filter(lambda x: not x.startswith(';'), asm)) # Filter only returns elements that return true out of the function
            # Remove inline Comments
            asm = list(map(lambda x: x[:x.find(';') - 1] if x.find(';') != -1 else x, asm)) # Find returns 1st instance of substring in string (or -1 if not found)
            # Remove all commas from entries
            asm = list(map(lambda x: x.replace(',', ''), asm))
            # Convert to 1d array of tokens (a token is separated by whitespace) 
            asm = " ".join(asm) 
            asm = asm.split(' ')

            ##DATA SECTION
            # Find the start and end of data section
            data = self.FindSection(asm, "data")

            # Remove all db/dw/dq, for now
            data = list(filter(lambda x: not x in ["db", "dw", "dd", "dq", "dt"], data))

            # Generate a list of pointers in data section, and their locations
            dataPointers = []
            for index, token in enumerate(data):
                # If token is a pointer, add it and location to list of pointers, then remove it
                if not token.isnumeric():
                    dataPointers.append({"name": token,
                                         "location": index,
                                         "section": "data"})
                    data.pop(index)

            ##TEXT SECTION
            # Find the start and end of the text section
            text = self.FindSection(asm, "text")

            # Generate a list of labels in text section, and their location
            labels = []
            for index, token in enumerate(text):
                if token.startswith('.') and token.endswith(':'):
                    labels.append({"name": token[:-1], # Remove the last (:) part of token
                                   "location": index,
                                   "section": "text"})
                    text.pop(index)

            #text = list(filter(lambda x: not (x.startswith('.') and x.endswith(':')), text)) # Remove label definitions used to generate symbol table
            #text = list(map(self.ConvertLabelToMemoryAddress, text)) # Replace label references with direct memory addresses
            # Create Symbol Table
            self.GenerateSymbolTable(dataPointers + labels) # Generate symbol table

            # Generate executable file
            self.Offsets = {"text": 0,
                            "data": len(text)}
            executable = text + data # text section, then data section

            # Final pass - remove symbols
            executable = list(map(self.ReplaceSymbols, executable))
        return

    # Should get an error, because as when the label is eventually removed from the source code, its pointer,
    # and all subsequent, are going to be off by an offset of 1. This offset increases for every new label defined
    # But we're not.. and I've not no clue why...
    def GenerateSymbolTable(self, symbols: list):
        for symbol in symbols:
            #location = "0x" + str(symbol["location"])
            # Hash
            key = self.hash(symbol["name"])
            # Insert dict {name: memory location} into index of hash in symbol table
            for i in range(100):
                if self.SymbolTable[(key + i) % 100] is not None: continue

                self.SymbolTable[(key + i) % 100] = symbol
                break
            else:
                raise Exception("Symbol Table is full!")
        return

    """
    Takes in tokens, and, if they are are a symbol, converts them to their corresponding memory address in the symbol table
    INPUT: string token
    RETURNS: string token or, if token is a symbol, the mem. address that label points to
    """
    def ReplaceSymbols(self, token: str) -> str:
        if type(token) is int: return token
        # Remove []s, to allow symbols inside direct addresses to be replaced
        rawToken = token.strip('[').strip(']')
        # Deal with +-/* (arithmetic) operations next to symbols
        operator = None
        operand = None
        arithmeticOperators = ['+', '-', '/', '*']
        for arithmeticOperator in arithmeticOperators:
            if arithmeticOperator in rawToken:
                operator = arithmeticOperator
                potentialSymbolName = rawToken.split(arithmeticOperator)[0] # Name of potential symbol is first half of token
                operand = int(rawToken.split(arithmeticOperator)[1]) # Bit to add/sub/mult/div is 2nd half of token
                # e.g "array+5" -> operator: +, potentialSymbolName: array, operand: 5
                break
        else:
            potentialSymbolName = rawToken

        # Find the label in the symbol table
        key = self.hash(potentialSymbolName) # There's never going to be a comma on the end of a label, is there? I don't believe so, as we should only be using them for jumps
        for i in range(100):
            # If token doesn't exist in table (so not a symbol), return token  
            if self.SymbolTable[key + i] is None: 
                return token
            # When found, check if the token is acutally a symbol
            if self.SymbolTable[key + i]["name"] == potentialSymbolName:
                # If so, return the location
                location = self.SymbolTable[key + i]["location"] + self.Offsets[self.SymbolTable[key + i]["section"]]
                # Perform arithmetic operation, if needed
                if operator is not None: 
                    match operator:
                        case '+':
                            location += operand
                        case '-':
                            location -= operand
                        case '*':
                            location *= operand
                        case '/':
                            location /= operand
                # Return the value
                return '[' + str(location) + ']'
            
        raise Exception(f"Symbol Table full (and label {rawToken} couldn't be found)! {self.SymbolTable}")
    
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
    
    """
    Finds a given section in an asm file, and returns it
    INPUT: string[] asm file
    RETURNS: string[] section in asm file, from start to end
    """
    def FindSection(self, asm: list, sectionName: str) -> list:
        startPointer = asm.index('.' + sectionName) + 1
        for i in range(startPointer, len(asm)):
            if asm[i] == "section": 
                endPointer = i
                break
        else:
            endPointer = None
        return asm[startPointer : endPointer]
        

C = Compiler()
C.Compile("test.txt")



