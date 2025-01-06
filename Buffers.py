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
    def __init__(self, name, size):
        self._NAME = name # Used when broadcasting errors
        self._SIZE = size
        self.Buffer = [{} for i in range(self._SIZE)] # Buffer has size 16 bytes (or 16 mu-ops)
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
    INPUTS: int index
    RETURNS: dict buffer item at given index
    """
    def Get(self, index: int) -> dict:
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
        self.Buffer[self._rearPointer] = bufferItem
    
    """
    Remove item at front of buffer
    """
    def Remove(self):
        # Check if queue is empty
        if self._frontPointer == -1:
            raise Exception(f"{self._NAME} Empty!")
        
        # Remove item at front of buffer
        self._frontPointer = (self._frontPointer + 1) % 16

        # If queue now empty, set front and end pointers to -1
        if self._frontPointer > self._rearPointer:
            self._frontPointer = self._rearPointer = -1

    ## Required methods for child classes
    """
    Takes in an item to be added to buffer, and formats it correctly
    INPUTS: item to be added
    RETURNS: correctly formatted item
    """
    def CreateBufferItem(item):
        return item

class ReadOnlyBuffer(Buffer):
    def __init__(self, size: int = 16, name: str = "ROB"):
        super().__init__(size, name) # super() calls the method on the superclass
        
    def CreateBufferItem(self, item: str) -> list:
        bufferItem = []
        bufferItem.append(item.split()[0]) # Add opcode
        bufferItem.append(item.endswith('*')) # Add whether a branch was predicted to be taken or not (* = taken)

class PipelineBuffer(Buffer):
    def __init__(self, size: int = 16, name: str = "Pipeline Buffer"):
        super().__init__(size, name)

    # Expected input: mu-op, w/ a * at end if it's speculative
    def CreateBufferItem(self, item: str) -> str:
        return item.rstrip('*')