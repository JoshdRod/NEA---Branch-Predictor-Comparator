class AGU:
    def __init__(self, registers: dict):
        self.Registers = registers

    """
    Converts a pre-index Address into a memory address value
    (e.g: [rbx+rcx+5] -> 15 (when rbx = 8 and rcx = 2))
    INPUTS: str pre-index address ([rbx+rcx+5])
    RETURNS: int memory address (15) 
    """
    def Generate(self, preIndexAddress: str) -> int:
        operators = ['+', '-', '*', '/']
        # Strip []s, remove spaces
        rawInfixExpression = str(filter(lambda x: x != ' ',preIndexAddress.strip("[]")))
        # Split operators and values into list (e.g: ['rax', '+', '15'])
        infixExpression = []
        for char in rawInfixExpression:
            if char in operators:
                infixExpression.append(char)
                infixExpression.append()
            else:
                infixExpression[-1] += char
        infixExpression.pop(-1)

        # Use Shunting Yard to create RPN expression
        # Iterate over tokens
        for token in infixExpression:
            # Add non-
            # If token is register, find its value
        # Evaluate RPN expression