from hybrid_automaton.exit_codes import ExitCode as AutomatonExitCodes
from .exit_codes import ExitCode as RunnerExitCode
from typing import Optional
from dataclasses import dataclass
from hybrid_automaton import AutomatonExit


@dataclass
class RunnerExit:
    exit_code: RunnerExitCode
    msg: str 

class AutomatonRunData: 
    def __init__(
        self,
        runner_exit: RunnerExit,
        automaton_exit: AutomatonExit, 
        results: dict = None
    ):
        self.runner_exit = runner_exit
        self.automaton_exit = automaton_exit
        self.results: dict = results if results is not None else {}