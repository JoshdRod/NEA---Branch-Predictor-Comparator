"""
Buffer - Temporary storage space, of fixed size 
DATA:
str Name
int Size
list Buffer itself

FUNCTIONALITY:
Add/Remove
Update (a specific index in buffer)
Get (a specific index in buffer)
GetNumberOfFreeSpaces (left)
"""

class Buffer:
    def __init__(self, size, name):
        self._NAME = name # Used when broadcasting errors
        
        self._SIZE = size
        self._Buffer = [{} for i in range(self._SIZE)] # Buffer has size 16 bytes (or 16 mu-ops)

    """
    Gets no. of unallocated bytes in buffer
    RETURNS: number of 'free spaces'
    """
    def GetNumberOfFreeSpaces(self) -> int:
        raise NotImplementedError()

    """
    Retrieves an item in the buffer queue at a specified index
    INPUTS: int index (defaults to front)
    RETURNS: dict buffer item at given index
    """
    def Get(self, index: int = 0) -> dict:
        raise NotImplementedError()

    """
    Adds item to end of buffer
    INPUTS: str item / list of items, int size of operation (bytes)
    """
    def Add(self, item: str|list, size: int):
        raise NotImplementedError()
    
    """
    Remove item at front of buffer
    """
    def Remove(self):
        raise NotImplementedError()
    
    """
    Updates table by replacing the item in the table with an updated version
    INPUTS: int index to replace at, dict item to replace with
    """
    def Update(self, index: int, item: dict):
        raise NotImplementedError()

    """
    Removes all items from buffer
    """
    def Flush(self):
        raise NotImplementedError()

# ----------------------------------------------------------------------------------------
### TYPES OF BUFFER
# Circular Buffer
# Hash Table Buffer
# ----------------------------------------------------------------------------------------

"""
Circular Buffer - Storing data as a Generic Circular Queue
ADDITIONAL DATA:
    int front / rear pointers

REQUIRED FUNCTIONALITY ON SUBCLASSES:
    CreateBufferItem (formats the item fed into Add, so that it can be added to the table with the correct information)
"""
class CircularBuffer(Buffer):
    def __init__(self, size, name):
        super().__init__(size, name)
        self._frontPointer = -1
        self._rearPointer = -1

    # Uses pointers to find no free spaces left
    def GetNumberOfFreeSpaces(self) -> int:
        usedSpaces = (self._rearPointer - self._frontPointer + 1) % self._SIZE
        freeSpaces = self._SIZE - usedSpaces
        return freeSpaces
    
    # Uses pointers to get item at correct index
    def Get(self, index: int = 0) -> dict:
        return self._Buffer[(self._frontPointer + index) % 16]
    
    # Uses pointers to add item/lists of items at end of buffer
    def Add(self, item: str|list, size: int, data: dict = None):
        # If given list of items, add them all iteratively
        if type(item) == list:
            for i in item:
                self.Add(i, size, data)
            return # Recursion isn't very KISS here, use iteration
        
        # If a single item, add to buffer
        # Check if buffer full
        if (self._frontPointer - 1) % 16 == self._rearPointer:
            raise Exception(f"{self._NAME} Full!")
        
        # If buffer empty, set start pointer back to 0
        if self._frontPointer == -1:
            self._frontPointer = 0
        
        # Create item to add to buffer
        bufferItem = self.CreateBufferItem(item, size, data)

        # Add buffer item to end of buffer
        self._rearPointer = (self._rearPointer + 1) % 16
        self._Buffer[self._rearPointer] = bufferItem

    # Uses pointers to remove from end of buffer
    def Remove(self):
        # Check if queue is empty
        if self._frontPointer == -1:
            return
        
        # Remove item at front of buffer
        # If queue now empty, set front and end pointers to -1
        if self._frontPointer == self._rearPointer:
            self._frontPointer = self._rearPointer = -1
        # Else, move front pointer along 1
        else:
            self._frontPointer = (self._frontPointer + 1) % 16

    def Flush(self):
        self._frontPointer = -1
        self._rearPointer = -1


    ## Required methods for child classes
    """
    Takes in an item to be added to buffer, and formats it correctly
    INPUTS: item to be added
    RETURNS: correctly formatted item
    """
    def CreateBufferItem(item):
        raise NotImplementedError()
    
"""
Hash Table Buffer - Storing data as a hash table
EXTRA DATA:

EXTRA FUNCTIONALITY:
    Hash 

REQUIRED FUNCTIONALITY ON SUBCLASSES:
    GetIndexFromItem (Takes in a value to be added to/ in bin, and returns the unique index identifier from it)
    CreateBufferItem (formats the item fed into Add, so that it can be added to the table with the correct information)
"""
class HashTableBuffer(Buffer):
    def __init__(self, size, name):
        super().__init__(size, name)

    # Finds number of free spaces in hash table
    def GetNumberOfFreeSpaces(self) -> int:
        return len(list(filter(lambda x: x == {}, self._Buffer)))

    # Hashes mem address location, index, then uses hash to find value in hash table 
    def Get(self, index: int = 0) -> dict:
        # Hash
        key = self.Hash(index)
        # Search from key, until we hit an empty bin - in which case, value is not in table
        for i in range(self._SIZE):
            binPointer = (key + i) % self._SIZE
            item = self._Buffer[binPointer]
            if item != {}:
                if self.GetIndexFromItem(item) == index:
                    return item

            # -1 = Not in hash table
            return -1
        else:
            raise Exception(f"{self._NAME} is full!")
        
    # Hashes index of item, then uses that as key to insert into hash table
    def Add(self, item: dict|list, size: int =1):
        if item == []:
            return
        elif type(item) == list:
            self.Add(item.pop())
            return self.Add(item)

        # Hash
        key = self.GetIndexFromItem(item)
        key = self.Hash(key)

        # Insert buffer item into buffer
        for i in range(self._SIZE):
            if self._Buffer[(key + i) % self._SIZE] != {}: continue

            self._Buffer[(key + i) % self._SIZE] = self.CreateBufferItem(item)
            break
        else:
            raise Exception("Hash Table is full!")
        return
    
    # Hash index, find index in table, then replace current item in table with item
    def Update(self, index: int, item: dict):
        key = self.Hash(index)
        
        # Search from key, until we hit an empty bin - in which case, value is not in table
        for i in range(self._SIZE):
            binPointer = (key + i) % self._SIZE
            currentItem = self._Buffer[binPointer]
            if currentItem != {}:
                if self.GetIndexFromItem(currentItem) == index:
                    # Replace current item with item
                    self._Buffer[binPointer] = item

            # -1 = Not in hash table
            return -1
        else:
            raise Exception(f"{self._NAME} is full!")
        

    """
    Hashes integer
    INPUT: int value
    RETURNS: int hashed value
    """
    def Hash(self, value: int) -> int:
        return value % self._SIZE
    
    """
    Takes in a dict item to be added to / already in bin, and returns its index
    INPUT: dict item
    RETURNS: int index of item
    """
    def GetIndexFromItem(self, item: dict) -> int:
        raise NotImplementedError()
    
    """
    Converts an item to be added to the buffer, into the correct form
    INPUT: dict item
    RETURNS: dict buffer item
    """
    def CreateBufferItem(self, item: dict) -> dict:
        raise NotImplementedError()


# ----------------------------------------------------------------------------------------
### BUFFER IMPLEMENTATIONS 
# Re-Order Buffer (Circular)
# Pipeline Buffer (Circular)
# Branch Target Buffer (Hash Table)
# ----------------------------------------------------------------------------------------

# Buffer of mu-op metadata [{opcode: __, location: ____, speculative, ___}, ..]
class ReorderBuffer(CircularBuffer):
    def __init__(self, size: int = 16, name: str = "ROB"):
        super().__init__(size, name) # super() calls the method on the superclass
        
    def CreateBufferItem(self, item: str, size: int, data: dict) -> dict:
        bufferItem = {"opcode": item.split()[0].rstrip('*'),
                      "location": data["location"],
                      "speculative": item.endswith('*')} # * at end indicates BP predicted branch taken 
        return bufferItem

# Buffer of mu-ops [{opcode: __, operand: __}, ..]
class PipelineBuffer(CircularBuffer):
    def __init__(self, size: int = 16, name: str = "Pipeline Buffer"):
        super().__init__(size, name)

    # Expected input: mu-op, w/ a * at end if it's speculative (Not expecting any extra data)
    def CreateBufferItem(self, item: str, operandSize: int, data: dict) -> dict:
        bufferItem = {"opcode": None, "operand": None, "operandSize": operandSize} # operandSize is the no. bytes the operation involves (e.g: In MOV [10] r10b, the mu_op STO [10] has an operand size of 1 byte)

        decomposedMu_op = item.split()
        match len(decomposedMu_op):
            case 1:
                bufferItem["opcode"] = decomposedMu_op[0].rstrip('*')
            case 2:
                bufferItem["opcode"] = decomposedMu_op[0]
                # Convert operand to int, if possible
                operand = decomposedMu_op[1].rstrip('*')
                bufferItem["operand"] = int(operand) if operand.isnumeric() else operand
            case _:
                raise Exception(f"mu-op has unexpected number of operands! Expected 1 or 2, got {len(decomposedMu_op)}\n\
                                Recieved mu-op: {item}\n\
                                Decomposed mu-op: {decomposedMu_op}")
        
        return bufferItem

# Buffer of branch instruction {from: location, to: location}
class BranchTargetBuffer(HashTableBuffer):
    def __init__(self, size: int = 16, name: str = "Branch Target Buffer"):
        super().__init__(size, name)

    def GetIndexFromItem(self, item: dict) -> int:
        return item["source"]

    def CreateBufferItem(self, item: dict) -> dict:
        return {"source": item["source"],
                "destination": item["destination"]}
    
# Buffer of branch locations, and wether to predict taken or not
class DirectionBuffer(HashTableBuffer):
    def __init__(self, size: int = 16, name: str = "Branch Direction Buffer"):
        super().__init__(size, name)

    def GetIndexFromItem(self, item: dict) -> int:
        return item["source"]

    def CreateBufferItem(self, item: dict) -> dict:
        return {"source": item["source"],
                "taken": item["taken"]}
    