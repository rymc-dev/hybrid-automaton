from enum import Enum

class ExitCode(Enum):
    """   
    automaton run exit codes.
    """
    SUCCESS = 0
    """ The automaton run completed successfully. """
    
    """ General Exception = 1 """
    FAILURE = 1
    
    """ Runtime Exceptions = 2-99 """
    INVARIANT_EXCEPTION = 2
    GUARD_EVALUATION_EXCEPTION = 3
    CONTINUOUS_DYNAMICS_EXCEPTION = 4
    TRANSITION_EXCEPTION = 8
    RESET_EXCEPTION = 5
    
    CONFIGURATION_EXCEPTION = 6
    CLOCK_EXCEPTION = 7
    
    INVARIANT_FAILURE = 9
    EVL_STP_COMPLETION = 10
    
    AUTOMATON_TIMEOUT = 11
    
    