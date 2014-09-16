
class RBError(Exception):
    pass

class BailOut(RBError):
    """ Is used to terminate the program with an error message """
    pass
