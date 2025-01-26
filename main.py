import os
from Compiler.Compiler import Compiler
from CPU.Processor import Processor

C = Compiler()
P = Processor()

## Allow user to select algorithm
# Display files in algorithms folder
AvailableAlgorithms = os.listdir("../Algorithms")
print("Select which algorithm you would like to run: ")
for index, alg in enumerate(AvailableAlgorithms):
    print(f"{index}. {alg}")
selectedAlgorithm = AvailableAlgorithms[int(input())]

with open(f"../Algorithms/{selectedAlgorithm}.txt", 'r') as f:
    Compiler.Compile(f)

print("Yippee")
    
# Open correct file and compile it

## Allow user to select branch predictors to run

## Display graph of mispredictions/cycles