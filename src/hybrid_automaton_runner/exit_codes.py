from enum import Enum, auto


class ExitCodes(Enum): 
    AUTOMATON_NO_RUN=auto()
    AUTOMATON_RUN_COMPLETE=auto()
    AUTOMATON_RUN_TIMEOUT=auto()
    AUTOMATON_RUN_EXCEPTION=auto()
    AUTOMATON_RUN_STOP_REQUESTED=auto()