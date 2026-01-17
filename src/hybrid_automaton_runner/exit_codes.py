"""
hybrid_automaton_runner.exit_codes.py

enumerations of exit codes associated with the 
automaton runner run coro
"""
# TODO: Probably rename this exit codes reserved for 
#       automaton operating systems primarly 

from enum import Enum, auto

# NOTE: Codes returned as part of the 'hybrid_automaton_runner.run_data' instance returned from the 
#       'hybrid_automaton_runner.runner:run', message associated with runner exit returned with it

class ExitCode(Enum): 
    AUTOMATON_NO_RUN=auto()
    """If automaton does not run in the run function"""
    AUTOMATON_RUN_COMPLETE=auto()
    """represents when automaton run task completes successfully without intervention"""
    AUTOMATON_RUN_TIMEOUT=auto()
    """an argument for run is a timeout_sec for the automaton run, if the automaton_runner 
    time has exceeded the timeout_sec a timeout monitor manually closes all remaining tasks and 
    returns this code"""
    AUTOMATON_RUN_EXCEPTION=auto()
    """If an unexpected exception at the run level is raised tasks cancelled this code returned"""
    AUTOMATON_RUN_STOP_REQUESTED=auto()
    """If client to runner instance manually calls requests a stop of the automaton runner tasks cancelled
    this exit code returned"""