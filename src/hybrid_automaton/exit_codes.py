""" 

"""

from enum import Enum, auto

class ExitCode(Enum):
    """   
    automaton run exit codes.
    """
    SUCCESS = auto()
    """ The automaton run completed successfully. """
    
    """ General Exception = 1 """
    FAILURE = auto()
    
    """ Runtime Exceptions = 2-99 """
    INVARIANT_EXCEPTION = auto()
    GUARD_EVALUATION_EXCEPTION = auto()
    CONTINUOUS_DYNAMICS_EXCEPTION = auto()
    TRANSITION_EXCEPTION = auto()
    RESET_EXCEPTION = auto()
    
    CONFIGURATION_EXCEPTION = auto()
    CLOCK_EXCEPTION = auto()
    
    INVARIANT_FAILURE = auto()
    EVL_STP_COMPLETION = auto()
    
    AUTOMATON_TIMEOUT = auto()
    
    