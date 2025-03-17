import typing
class Compiler:
    SymbolTable = [None for i in range(100)]
    Offsets = {}

    # TODO: Fix complier not dealing with numeric addition on pointer addresses
    # (e.g: "mov rbp, array + 5" -> ["mov", "rbp,", "{location of pointer array + 5}"]
    # instead of: ["mov", "rbp,", "array", "+", "5"])

    # Deal w/ data values in the _data section (assign them locations in memory + replace pointers w/ their locations)
    def Compile(self, f: typing.TextIO) -> list:
        # Read in file
        asm = f.readlines()

        ## Convert to General Form
        asm = self.ConvertToGeneralForm(asm)

        ##DATA SECTION
        # Find the start and end of data section
        data = self.FindSection(asm, "data")

        # Convert data to 1d array of tokens (a token is separated by whitespace) 
        data = " ".join(data) 
        data = data.split(' ')

        # Remove all db/dw/dq, for now
        data = list(filter(lambda x: not x in ["db", "dw", "dd", "dq", "dt"], data))


        # Generate a list of pointers in data section, and their locations
        dataPointers = []
        for index, token in enumerate(data):
            # If token is non-numeric, it's a pointer, so add it and location to list of pointers, then remove it
            if not token.isnumeric():
                dataPointers.append({"name": token,
                                        "location": index,
                                        "section": "data"})
                data.pop(index)
        
        # Convert all data values to ints
        data = list(map(int, data))

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

        # Create Symbol Table
        self.GenerateSymbolTable(dataPointers + labels) # Generate symbol table

        ## HEADER SECTION
        # Used for ensuring rip doesn't go into data section
        header = [2, # Start of text section
                    2 + len(text) # Start of data section
                    ]
        # Generate executable file
        self.Offsets = {"text": 2,
                        "data": 2 + len(text)}
        executable = header + text + data # header, then text section, then data section

        # Final pass - remove symbols
        executable = list(map(self.ReplaceSymbols, executable))
        return executable

    """
    Converts Assembly file into a generalised form, without whitespace and comments, in order for compilation to begin
    INPUTS: str Assembly file to generalise
    RETURNS: str Assembly file in General Form
    """
    def ConvertToGeneralForm(self, asm: str) -> str:
        # Remove Empty lines/indentation
        asm = list(filter(lambda x: not x.isspace(), asm)) # isspace returns true of whole string only consists of spaces
        asm = list(map(lambda x: x.strip(), asm))
        # Remove Whole line Comments
        asm = list(filter(lambda x: not x.startswith(';'), asm)) # Filter only returns elements that return true out of the function
        # Remove inline Comments
        asm = list(map(lambda x: x[:x.find(';') - 1] if x.find(';') != -1 else x, asm)) # Find returns 1st instance of substring in string (or -1 if not found)
        # Remove all commas from entries
        asm = list(map(lambda x: x.replace(',', ''), asm))

        return asm

    # Should get an error, because as when the label is eventually removed from the source code, its pointer,
    # and all subsequent, are going to be off by an offset of 1. This offset increases for every new label defined
    # But we're not.. and I've not no clue why...
    def GenerateSymbolTable(self, symbols: list):
        if len(symbols) == 0:
            return
        else:
            symbol = symbols.pop()
            # Hash
            key = self.hash(symbol["name"])
            # Insert dict {name: memory location} into index of hash in symbol table
            for i in range(100):
                if self.SymbolTable[(key + i) % 100] is not None: continue

                self.SymbolTable[(key + i) % 100] = symbol
                break
            else:
                raise Exception("Symbol Table is full!")
            return self.GenerateSymbolTable(symbols)

    """
    Takes in line of code, and, if part of the line is a symbol, converts it to the corresponding memory address in the symbol table
    INPUT: string line
    RETURNS: string replacedLine, where all tokens in the line which are symbols are replaced with the correct address
    """
    def ReplaceSymbols(self, line: str) -> str:
        if type(line) is int: return line

        replacedLine = ""
        # Split into tokens
        tokens = line.split(' ')
        for token in tokens:
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
                    replacedLine += token + ' '
                    break
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
                    replacedLine += str(location) + ' ' # Don't think the []s are needed, as [] denotes VALUE of mem. address - we just want the address itself
                    break
            else:  
                raise Exception(f"Symbol Table full (and label {rawToken} couldn't be found)! {self.SymbolTable}")
        
        return replacedLine.strip() # Removes final trailing whitespace
    
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
        startPointer = asm.index('section .' + sectionName) + 1
        for i in range(startPointer, len(asm)):
            if "section" in asm[i]: 
                endPointer = i
                break
        else:
            endPointer = None
        return asm[startPointer : endPointer]
