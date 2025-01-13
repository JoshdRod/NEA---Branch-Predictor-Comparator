"""
Buffer - Generic Circular Queue, of fixed size 
DATA:
str Name
int Size
list Buffer itself
int front / rear pointers

FUNCTIONALITY:
Add/Remove
Get (a specific index in queue)
GetNumberOfFreeSpaces (left)

REQUIRED FUNCTIONALITY ON SUBCLASSES:
CreateBufferItem (formats an item fed into Add, so that it can be added to the queue)
"""
class Buffer:
    def __init__(self, size, name):
        self._NAME = name # Used when broadcasting errors
        
        self._SIZE = size
        self._Buffer = [{} for i in range(self._SIZE)] # Buffer has size 16 bytes (or 16 mu-ops)
        self._frontPointer = -1
        self._rearPointer = -1
    # pointers at -1 indicates empty buffer

    """
    Gets no. of unallocated bytes in buffer
    RETURNS: number of 'free spaces'
    """
    def GetNumberOfFreeSpaces(self) -> int:
        usedSpaces = (self._rearPointer - self._frontPointer + 1) % self._SIZE
        freeSpaces = self._SIZE - usedSpaces
        return freeSpaces
    
    """
    Retrieves an item in the buffer queue at a specified index
    INPUTS: int index (defaults to front)
    RETURNS: dict buffer item at given index
    """
    def Get(self, index: int = 0) -> dict:
        return self._Buffer[(self._frontPointer + index) % 16]

    """
    Adds item to end of buffer
    INPUTS: str item / list ofitems
    """
    def Add(self, item: str|list):
        # If given list of items, add them all iteratively
        if type(item) == list:
            for i in item:
                self.Add(i)
            return # Recursion isn't very KISS here, use iteration
        
        # If a single item, add to buffer
        # Check if buffer full
        if (self._frontPointer - 1) % 16 == self._rearPointer:
            raise Exception(f"{self._NAME} Full!")
        
        # If buffer empty, set start pointer back to 0
        if self._frontPointer == -1:
            self._frontPointer = 0
        
        # Create item to add to buffer
        bufferItem = self.CreateBufferItem(item)

        # Add buffer item to end of buffer
        self._rearPointer = (self._rearPointer + 1) % 16
        self._Buffer[self._rearPointer] = bufferItem
    
    """
    Remove item at front of buffer
    """
    def Remove(self):
        # Check if queue is empty
        if self._frontPointer == -1:
            return
        
        # Remove item at front of buffer
        self._frontPointer = (self._frontPointer + 1) % 16

        # If queue now empty, set front and end pointers to -1
        if self._frontPointer > self._rearPointer:
            self._frontPointer = self._rearPointer = -1

    """
    Removes all items from buffer
    """
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
        return item

# Buffer of mu-op metadata [{opcode: __, speculative, ___}, ..]
class ReorderBuffer(Buffer):
    def __init__(self, size: int = 16, name: str = "ROB"):
        super().__init__(size, name) # super() calls the method on the superclass
        
    def CreateBufferItem(self, item: str) -> dict:
        bufferItem = {"opcode": item.split()[0].rstrip('*'),
                      "speculative": item.endswith('*')} # * at end indicates BP predicted branch taken 
        return bufferItem

# Buffer of mu-ops [{opcode: __, operand: __}, ..]
class PipelineBuffer(Buffer):
    def __init__(self, size: int = 16, name: str = "Pipeline Buffer"):
        super().__init__(size, name)

    # Expected input: mu-op, w/ a * at end if it's speculative
    def CreateBufferItem(self, item: str) -> dict:
        bufferItem = {"opcode": None, "operand": None}

        decomposedMu_op = item.split()
        match len(decomposedMu_op):
            case 1:
                bufferItem["opcode"] = decomposedMu_op[0].rstrip('*')
            case 2:
                bufferItem["opcode"] = decomposedMu_op[0]
                bufferItem["operand"] = decomposedMu_op[1].rstrip('*')
            case _:
                raise Exception(f"mu-op has unexpected number of operands! Expected 1 or 2, got {len(decomposedMu_op)}\n\
                                Recieved mu-op: {item}\n\
                                Decomposed mu-op: {decomposedMu_op}")
        
        return bufferItem
        