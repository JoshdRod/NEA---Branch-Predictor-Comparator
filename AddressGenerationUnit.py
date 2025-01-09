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
        operators = {'+': 0, # In operator : prescedence pairs
                     '-': 0,
                     '*': 1,
                     '/': 1}
        # Strip []s, remove spaces
        rawInfixExpression = str(filter(lambda x: x != ' ',preIndexAddress.strip("[]")))
        # Split operators and values into list (e.g: ['rax', '+', '15'])
        infixExpression = []
        for char in rawInfixExpression:
            if char in operators.keys():
                infixExpression.append(char)
                infixExpression.append()
            else:
                infixExpression[-1] += char
        infixExpression.pop(-1)

        # Use Shunting Yard to create RPN expression
        rpnExpression = []
        operatorStack = []
        # Iterate over tokens
        for token in infixExpression:
            # If operator,
            if token in operators.keys():
                # If op stack empty, add to stack
                if len(operatorStack) == 0:
                    operatorStack.append(token)
                else:
                    # Peek at operator stack
                    # If lower/equal prescedence than top stack operator, pop stack to queue
                    if operators[token] <= operators[operatorStack[-1]]:
                        rpnExpression.append(operatorStack.pop())

                    # Push to stack
                    operatorStack.append(token)

            # If non-operator,
            else:
                # If token is register, find its value
                if token.startswith('r'):
                    operand = self.Registers[token] 
                # If immediate value, convert to int
                else:
                    operand = int(token)
                # Add to output queue
                rpnExpression.append(operand)
        # Evaluate RPN expression

