from hybrid_automaton.automaton_exit_codes import ExitCode as AutomatonExitCodes
from .exit_codes import ExitCodes as RunnerExitCodes
from typing import Optional

class AutomatonRunData: 
    def __init__(
        self,
        runner_exit_code: RunnerExitCodes,
        runner_exit_msg: Optional[str] = None,
        automaton_exit_code: Optional[AutomatonExitCodes] = None,
        automaton_exit_msg: Optional[str] = None,
        results: dict = None
    ):
        self.runner_exit_code: RunnerExitCodes = runner_exit_code 
        self.runner_exit_msg: str = runner_exit_msg
        self.automaton_exit_code: AutomatonExitCodes = automaton_exit_code
        self.automaton_exit_msg: str = automaton_exit_msg
        self.results: dict = results if results is not None else {}