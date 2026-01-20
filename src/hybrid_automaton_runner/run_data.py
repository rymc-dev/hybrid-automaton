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
        automaton_name: str,
        automaton_version: str,
        run_id: str,
        runner_exit: RunnerExit,
        automaton_exit: AutomatonExit, 
        results: dict = None
    ):
        self.automaton_name = automaton_name
        self.automaton_version = automaton_version
        self.run_id = run_id
        self.runner_exit = runner_exit
        self.automaton_exit = automaton_exit
        self.results: dict = results if results is not None else {}
        
    def print_summary(self):
        """Print summary of collected data."""
        # TODO: UPDATE THIS 
        print ('summary')
        # print(f"{self.ha.get_automaton_name()} Run Summary:")
        # print(f"\tTime Elapsed: {self.ha.get_runtime_time_elapsed()}")
        # if getattr(self.continuous_collector, "data", None):
        #     print(f"\tCollected {len(self.continuous_collector.data)} continuous state samples")
        # if getattr(self.auxiliary_collector, "data", None):
        #     print(f"\tCollected {len(self.auxiliary_collector.data)} auxiliary state samples")
        # if getattr(self.control_collector, "data", None):
        #     print(f"\tCollected {len(self.control_collector.data)} control input samples")
        # if getattr(self.automaton_collector, "data", None):
        #     print(f"\tCollected {len(self.automaton_collector.data)} automaton state samples")
        # if getattr(self.transition_collector, "data", None):
        #     print(f"\tCollected {len(self.transition_collector.data)} transition time samples")