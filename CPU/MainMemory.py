class MainMemory:
    # WIP - Figure out how main memory actually communicates w/ the cpu
    def __init__(self, size: int):
        self._SIZE = size
        self.__data__ = [None for i in range(self._SIZE)] # For now, store all data in memory in 4 byte sections
    
    """
    Retrieves data from main memory
    INPUTS: str location to retrieve from
    RETURNS: int/str value at given location
    """
    def Retrieve(self, location: str) -> str: 
        try:
            location = int(location.strip('[]'))
            return self.__data__[location]
        except:
            raise Exception(f"Tried to access invalid memory location:\n\
                            location: {location}")
    
    """
    Stores data in memory
    INPUTS: str location to store in, int/str value to store/list of register values to store
    """
    def Store(self, location: str, value: list|int|str):
        try:
            # Find location to store in
            location = int(location.strip('[]'))
            # Store value(s)
            if type(value) == int or type(value) == str:
                self.__data__[location] = value
            else:
                for i in range(len(value)):
                    self.__data__[location+i] = value[i]
        except:
            raise Exception(f"Error trying to store data:\n\
                            Tried to store {value} at {location}")