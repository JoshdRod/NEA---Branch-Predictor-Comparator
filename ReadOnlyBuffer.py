class ReadOnlyBuffer:
    Buffer = [{} for i in range(16)] # Buffer has size 16 bytes (or 16 mu-ops)
    frontPointer = -1
    rearPointer = -1
    # pointers at -1 indicates empty buffer

    """
    Retrieves an item in the buffer queue at a specified index
    INPUTS: int index
    RETURNS: dict buffer item at given index
    """
    def Get(self, index: int) -> dict:
        return self.Buffer[(self.frontPointer + index) % 16]

    """
    Adds item to end of buffer
    INPUTS: str mu-op
    """
    def Add(self, mu_op: str):
        # Check if buffer full
        if (self.frontPointer - 1) % 16 == self.rearPointer:
            raise Exception("ROB Full!")
        
        # If buffer empty, set start pointer back to 0
        if self.frontPointer == -1:
            self.frontPointer = 0
        
        # Create item to add to buffer
        item = []
        item.append(mu_op.split()[0]) # Add opcode
        item.append(mu_op.endswith('*')) # Add wether a branch was predicted to be taken or not (* = taken)

        # Add item to end of buffer
        self.rearPointer = (self.rearPointer + 1) % 16
        self.Buffer[self.rearPointer] = item
    
    """
    Remove item at front of buffer
    """
    def Remove(self):
        # Check if queue is empty
        if self.frontPointer == -1:
            raise Exception("ROB Empty!")
        
        # Remove item at front of buffer
        self.frontPointer = (self.frontPointer + 1) % 16

        # If queue now empty, set front and end pointers to -1
        if self.frontPointer > self.rearPointer:
            self.frontPointer = self.rearPointer = -1