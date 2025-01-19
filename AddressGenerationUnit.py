class AGU:
    def __init__(self, registers: dict):
        self.Registers = registers

    """
    Converts an direct/indirect address into a memory address value
    (e.g: [rbx+rcx+5] -> 15 (when rbx = 8 and rcx = 2))
    INPUTS: str address ([rbx+rcx+5])
    RETURNS: int memory address (15) 
    """
    def Generate(self, address: str) -> int:
        operators = {'+': 0, # In operator : prescedence pairs
                     '-': 0,
                     '*': 1,
                     '/': 1}
        # Strip []s, remove spaces
        rawInfixExpression = "".join(filter(lambda x: x != ' ', address.strip("[]")))
        # Split operators and values into list (e.g: ['rax', '+', '15'])
        infixExpression = ['']
        for char in rawInfixExpression:
            if char in operators.keys():
                infixExpression.append(char)
                infixExpression.append('') # Don't need to worry about this happening last, as infix expression can't end w/ operator
            else:
                infixExpression[-1] += char

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
                    # If lower/equal prescedence than top stack operator, pop operator to queue
                    if operators[token] <= operators[operatorStack[-1]]:
                        rpnExpression.append(operatorStack.pop())

                    # Push token to stack
                    operatorStack.append(token)

            # If non-operator,
            else:
                # If token is register, find its value
                if token.startswith('r'):
                    operand = self.Registers[token] # TODO: CONVERT TO OOP NOTATION
                # If immediate value, convert to int
                else:
                    operand = int(token)
                # Add to output queue
                rpnExpression.append(operand)
        # At end, pop rest of operator stack to queue
        rpnExpression += reversed(operatorStack)

        # Evaluate RPN expression
        operandStack = []
        for token in rpnExpression:
            # Add operands to stack
            if type(token) is int:
                operandStack.append(token)
            # When an operator is selected, pop 2 off stack, perform operation (in correct order), then push back to stack
            else:
                # Remember, "op1 op2 -" -> "op1 - op2", even though op2 is on top of the stack
                op2 = operandStack.pop()
                op1 = operandStack.pop()
                match token:
                    case '+':
                        result = op1 + op2
                    case '-':
                        result = op1 - op2
                    case '*':
                        result = op1 * op2
                    case '/':
                        result = op1 / op2
                operandStack.append(result)
        # Final item in stack = address
        generatedAddress = operandStack[0]
        return generatedAddress
        