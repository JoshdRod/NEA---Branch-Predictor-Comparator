import os
from Compiler.Compiler import Compiler
from CPU.Processor import Processor
import CPU.DirectionPredictors
import matplotlib.pyplot as plt

C = Compiler()

CURRENT_PATH = os.curdir
ALGORITHMS_PATH = os.path.join(CURRENT_PATH, "Algorithms")


## Allow user to select algorithm
# Display files  in algorithms folder
AvailableAlgorithms = os.listdir(ALGORITHMS_PATH)
print("Select which algorithm you would like to run: ")
for index, alg in enumerate(AvailableAlgorithms):
    print(f"{index}. {alg.removesuffix(".txt")}")

SelectedAlgorithm = AvailableAlgorithms[int(input())]

# Open correct file and compile it
with open(os.path.join(ALGORITHMS_PATH, f"{SelectedAlgorithm}"), 'r') as f:
    print("Compiling...")
    executable = C.Compile(f)
    print("Compiled to executable!")

## Allow user to select branch predictor to run
while True:
    print("Select Branch Predictor to run: ")
    print("""0. Always Not Taken
1. Always Taken
2. One-Bit Last Time""")
    match input():
        case '0':
            predictor = CPU.DirectionPredictors.AlwaysNotTaken
            break
        case '1':
            predictor = CPU.DirectionPredictors.AlwaysTaken
            break
        case '2':
            predictor = CPU.DirectionPredictors.OneBitLastTime
            break
        case _:
            continue

P = Processor(predictor)

## Run on processor
debug = None
while type(debug) != bool:
    debug = input("Run in debug mode? (y/n): ").upper()
    if debug == "Y":
        debug = True
    elif debug == "N":
        debug = False

predictionResults = P.Compute(executable, debug)

## Display graph of mispredictions/cycles
predictedY = [i for i in range(1, len(predictionResults["Predicted"]) + 1)]
mispredictedY = [i for i in range(1, len(predictionResults["Mispredicted"]) + 1)]

plt.title(SelectedAlgorithm)
plt.xlabel("Cycles") 
plt.ylabel("Total") 
plt.plot(predictionResults["Mispredicted"], mispredictedY, "o-", color="blue", label="Mispredicted")
plt.plot(predictionResults["Predicted"], predictedY, "o-", color="green", label="Predicted")
plt.legend()
plt.show()


