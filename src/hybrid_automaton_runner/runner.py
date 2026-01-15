"""Main runner class for hybrid automaton simulations (refactored)."""
import asyncio
import numpy as np
from typing import Optional, Dict, Any, Tuple
from .collectors import (
    ContinuousStateCollector,
    AuxiliaryStateCollector,
    ControlInputCollector,
    AutomatonStateCollector,
    TransitionTimeCollector
)
from hybrid_automaton import Automaton
from hybrid_automaton.automaton_exit_codes import ExitCode as AutomatonExitCode
from .run_data import AutomatonRunData
from .exit_codes import ExitCodes as RunnerExitCodes

class TaskGroupExit(Exception):
    """
    Special exception used to break out of the TaskGroup and carry
    structured exit information back to the run() caller.
    """
    def __init__(
        self,
        runner_exit_code: RunnerExitCodes = None,
        runner_exit_msg: str = None,
        automaton_exit_code: AutomatonExitCode = None,
        automaton_exit_msg: str = None,
    ):
        super().__init__(runner_exit_msg or automaton_exit_msg)
        self.runner_exit_code = runner_exit_code
        self.runner_exit_msg = runner_exit_msg
        self.automaton_exit_code = automaton_exit_code
        self.automaton_exit_msg = automaton_exit_msg


class AutomatonRunner:
    """Runner for hybrid automaton with data collection."""

    def __init__(self, hybrid_automaton: Automaton, sampling_rate: float = 0.01):
        self.ha = hybrid_automaton
        self.sampling_rate = sampling_rate

        # Initialize collectors
        self.continuous_collector = ContinuousStateCollector(sampling_rate)
        self.auxiliary_collector = AuxiliaryStateCollector(sampling_rate)
        self.control_collector = ControlInputCollector(sampling_rate)
        self.automaton_collector = AutomatonStateCollector(sampling_rate)
        self.transition_collector = TransitionTimeCollector(sampling_rate)

        # Events that the supervisor will wait on:
        self._automaton_run_complete = asyncio.Event()
        self._automaton_run_timeout = asyncio.Event()
        self._automaton_run_exception = asyncio.Event()
        self._automaton_run_stop_requested = asyncio.Event()

        # canonical completion result dict:
        self._completion_result: Dict[str, Any] = {
            'runner_exit_code': None,
            'runner_exit_msg': None,
            'automaton_exit_code': None,
            'automaton_exit_msg': None,
        }

    async def run(
        self,
        x0: np.ndarray = None,
        aux_x0: Dict = {},
        u0: Dict = {},
        duration: float = np.inf,
        real_time_mode: bool = False,
        integrate: bool = True,
        dt: float = 0.01,
        collect_continuous: bool = True,
        collect_auxiliary: bool = False,
        collect_control: bool = False,
        collect_automaton: bool = True,
        collect_transitions: bool = True,
        inject_continuous: bool = False,
        inject_auxiliary: bool = False,
        inject_control: bool = False,
        continuous_state_fn: Optional[callable] = None,
        auxiliary_fn: Optional[callable] = None,
        control_fn: Optional[callable] = None,
        injector_update_rate: float = 0.001,
    ) -> AutomatonRunData:
        """
        Run the hybrid automaton simulation with data collection and/or injection.
        Returns an AutomatonRunData constructed from the captured completion result.
        """

        # Reset automaton runtime if necessary
        if self.ha._runtime is not None:
            self.ha.reset()

        # Clear previous data and events
        self.clear_all_data()
        self._automaton_run_complete.clear()
        self._automaton_run_exception.clear()
        self._automaton_run_stop_requested.clear()
        self._automaton_run_timeout.clear()
        self._completion_result = {
            'runner_exit_code': None,
            'runner_exit_msg': None,
            'automaton_exit_code': None,
            'automaton_exit_msg': None,
        }

        try:
            async with asyncio.TaskGroup() as tg:
                # Main automaton task: THIS is the primary task that can finish the run.
                tg.create_task(
                    self._wrapped_task(
                        coro=self.ha.activate(
                            x0=x0,
                            aux_x0=aux_x0,
                            u0=u0,
                            real_time_mode=real_time_mode,
                            integrate=integrate,
                            dt=dt
                        ),
                        success_event=self._automaton_run_complete,
                        event_runner_code=RunnerExitCodes.AUTOMATON_RUN_COMPLETE,
                        source_name="automaton"
                    ),
                    name="automaton_runtime_task"
                )

                # Data collection tasks: they should NOT signal normal run completion.
                if collect_continuous:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self.continuous_collector.collect(self.ha),
                            success_event=None,
                            source_name="continuous_collector"
                        ),
                        name="collect_continuous_state_task"
                    )

                if collect_auxiliary:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self.auxiliary_collector.collect(self.ha, auxiliary_fn),
                            success_event=None,
                            source_name="auxiliary_collector"
                        ),
                        name="collect_auxiliary_states_task"
                    )

                if collect_control:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self.control_collector.collect(self.ha, control_fn),
                            success_event=None,
                            source_name="control_collector"
                        ),
                        name="collect_control_states_task"
                    )

                if collect_automaton:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self.automaton_collector.collect(self.ha),
                            success_event=None,
                            source_name="automaton_collector"
                        ),
                        name="collect_automaton_discrete_data"
                    )

                if collect_transitions:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self.transition_collector.collect(self.ha),
                            success_event=None,
                            source_name="transition_collector"
                        ),
                        name="collect_transitions_task"
                    )

                # Data injection tasks: injectors also should not signal run completion on normal exit.
                if inject_continuous:
                    if continuous_state_fn is None:
                        raise ValueError("inject_continuous=True requires continuous_state_fn")
                    from .injectors import ContinuousStateInjector
                    injector = ContinuousStateInjector(continuous_state_fn, injector_update_rate)
                    tg.create_task(
                        self._wrapped_task(
                            coro=injector.inject(self.ha),
                            success_event=None,
                            source_name="continuous_injector"
                        ),
                        name="continuous_state_injector_task"
                    )

                if inject_auxiliary:
                    if auxiliary_fn is None:
                        raise ValueError("inject_auxiliary=True requires auxiliary_fn")
                    from .injectors import AuxiliaryStateInjector
                    injector = AuxiliaryStateInjector(auxiliary_fn, injector_update_rate)
                    tg.create_task(
                        self._wrapped_task(
                            coro=injector.inject(self.ha),
                            success_event=None,
                            source_name="auxiliary_injector"
                        ),
                        name="auxiliary_injector_task"
                    )

                if inject_control:
                    if control_fn is None:
                        raise ValueError("inject_control=True requires control_fn")
                    from .injectors import ControlInputInjector
                    injector = ControlInputInjector(control_fn, injector_update_rate)
                    tg.create_task(
                        self._wrapped_task(
                            coro=injector.inject(self.ha),
                            success_event=None,
                            source_name="control_injector"
                        ),
                        name="control_input_task"
                    )

                # Timeout monitor: if finite duration provided, this can finish the run.
                if np.isfinite(duration) and duration > 0:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self._timeout_monitor(duration),
                            success_event=self._automaton_run_timeout,
                            event_runner_code=RunnerExitCodes.AUTOMATON_RUN_TIMEOUT,
                            source_name="timeout_monitor"
                        ),
                        name="timeout_monitor_task"
                    )

                # Supervisor watches the run events and raises TaskGroupExit to finish the TaskGroup.
                tg.create_task(self._supervisor(), name="supervisor_task")

            # exiting the TaskGroup context means supervisor raised TaskGroupExit and tasks were cancelled,
            # or everything finished normally. We handle the TaskGroupExit below in except.
    
        except* TaskGroupExit as tge:
            # Supervisor signalled a controlled exit with detailed info
            self._completion_result = {
                'runner_exit_code': tge.exceptions[0].runner_exit_code,
                'runner_exit_msg': tge.exceptions[0].runner_exit_msg,
                'automaton_exit_code': tge.exceptions[0].automaton_exit_code,
                'automaton_exit_msg': tge.exceptions[0].automaton_exit_msg,
            }    
        except* Exception as e:
            # Unexpected error bubbled out of a task; mark as exception exit
            self._completion_result = {
                'runner_exit_code': RunnerExitCodes.AUTOMATON_RUN_EXCEPTION,
                'runner_exit_msg': str(e),
                'automaton_exit_code': None,
                'automaton_exit_msg': None,
            }
        except* asyncio.CancelledError:
            # expected when the group is cancelled during cleanup
            pass


        # Build AutomatonRunData from the captured completion result:
        if self._completion_result and self._completion_result.get('runner_exit_code') is not None:
            # Prefer to return the automaton-level message/code if present, else runner message.
            automaton_code = self._completion_result.get('automaton_exit_code')
            automaton_msg = self._completion_result.get('automaton_exit_msg')
            runner_msg = self._completion_result.get('runner_exit_msg')
            runner_code = self._completion_result.get('runner_exit_code')

            # If automaton provided a code/message, prefer that in the returned AutomatonRunData.
            return AutomatonRunData(
                runner_exit_code=runner_code,
                runner_exit_msg=runner_msg,
                automaton_exit_code=automaton_code,
                automaton_exit_msg=automaton_msg
            )
        else:
            # Fallback if nothing meaningful was captured
            return AutomatonRunData(
                runner_exit_code=RunnerExitCodes.AUTOMATON_NO_RUN,
                message="No completion result captured"
            )

    async def _wrapped_task(self, coro, success_event: Optional[asyncio.Event], event_runner_code: RunnerExitCodes = None, source_name: str = "<task>"):
        """
        Wrapper for every spawned coroutine:
          - If the coroutine raises, sets the _automaton_run_exception event (so supervisor notices)
          - If it returns successfully and a success_event is supplied, record that as the canonical completion result
            (only the first such success is recorded)
        - success_event: if provided, indicates that normal completion of this task should trigger run termination.
        - event_runner_code: RunnerExitCodes value to associate with that success_event (optional).
        """
        try:
            result = await coro
        except asyncio.CancelledError:
            # Propagate cancellation normally
            raise
        except Exception as exc:
            # On any exception in a task, capture the exception and signal the exception event.
            # Record the message (first exception wins).
            if not self._automaton_run_exception.is_set():
                self._completion_result.update({
                    'runner_exit_code': RunnerExitCodes.AUTOMATON_RUN_EXCEPTION,
                    'runner_exit_msg': f"{source_name} raised: {exc}",
                    'automaton_exit_code': None,
                    'automaton_exit_msg': None,
                })
                self._automaton_run_exception.set()
            # Re-raise so the TaskGroup machinery cancels the other tasks
            raise

        # If success_event is set and no run-termination event has been set yet, capture the result as the run result.
        if success_event is not None and \
                not self._automaton_run_complete.is_set() and \
                not self._automaton_run_exception.is_set() and \
                not self._automaton_run_stop_requested.is_set() and \
                not self._automaton_run_timeout.is_set():

            # Map runner code
            runner_code = event_runner_code if event_runner_code is not None else RunnerExitCodes.AUTOMATON_RUN_COMPLETE

            # Attempt to extract automaton exit details if present on result (flexible)
            automaton_code = getattr(result, "exit_code", None)
            automaton_msg = getattr(result, "message", None)

            # Compose a runner message: prefer meaningful returned message or use a synthetic fallback.
            runner_msg = None
            if automaton_msg:
                runner_msg = automaton_msg
            else:
                # If the coroutine returned a plain string, use it; else use repr(result)
                if isinstance(result, str):
                    runner_msg = result
                else:
                    runner_msg = f"{source_name} completed successfully."

            self._completion_result.update({
                'runner_exit_code': runner_code,
                'runner_exit_msg': runner_msg,
                'automaton_exit_code': automaton_code,
                'automaton_exit_msg': automaton_msg,
            })

            # Signal the event so the supervisor can pick it up.
            success_event.set()

        return result

    async def _supervisor(self):
        """
        Wait for the first of the run-level events and raise TaskGroupExit populated with the stored result.
        This runs inside the TaskGroup so raising TaskGroupExit will cancel sibling tasks and unwind the TaskGroup.
        """
        # Create tasks mapped to their RunnerExitCodes for clarity.
        wait_map = {
            asyncio.create_task(self._automaton_run_complete.wait()): RunnerExitCodes.AUTOMATON_RUN_COMPLETE,
            asyncio.create_task(self._automaton_run_timeout.wait()): RunnerExitCodes.AUTOMATON_RUN_TIMEOUT,
            asyncio.create_task(self._automaton_run_exception.wait()): RunnerExitCodes.AUTOMATON_RUN_EXCEPTION,
            asyncio.create_task(self._automaton_run_stop_requested.wait()): RunnerExitCodes.AUTOMATON_RUN_STOP_REQUESTED,
        }

        done, pending = await asyncio.wait(list(wait_map.keys()), return_when=asyncio.FIRST_COMPLETED)

        # Cancel other waiters
        for p in pending:
            p.cancel()

        completed = done.pop()
        runner_code = wait_map[completed]

        # Prefer the stored completion_result fields; they will have been set by the _wrapped_task that completed.
        r = self._completion_result
        runner_msg = r.get('runner_exit_msg')
        automaton_code = r.get('automaton_exit_code')
        automaton_msg = r.get('automaton_exit_msg')

        # Raise TaskGroupExit to unwind the TaskGroup and provide structured info.
        raise TaskGroupExit(
            runner_exit_code=runner_code,
            runner_exit_msg=runner_msg,
            automaton_exit_code=automaton_code,
            automaton_exit_msg=automaton_msg
        )

    async def _timeout_monitor(self, timeout_sec: float) -> str:
        """"""
        while self.ha.get_runtime_time_elapsed() < timeout_sec:
            await asyncio.sleep(0.1)
        return f"{self.ha.get_automaton_name()} runtime timeout after specified period: '{timeout_sec}'"

    # """ === post run metadata utilities ==== """

    # def get_results(self) -> Dict[str, Any]:
    #     """Get all collected data."""
    #     return {
    #         'continuous_states': self.continuous_collector.get_data(),
    #         'auxiliary_states': self.auxiliary_collector.get_data(),
    #         'control_inputs': self.control_collector.get_data(),
    #         'automaton_states': self.automaton_collector.get_data(),
    #         'transition_times': self.transition_collector.get_data(),
    #     }

    def clear_all_data(self):
        """Clear all collected data."""
        self.continuous_collector.clear()
        self.auxiliary_collector.clear()
        self.control_collector.clear()
        self.automaton_collector.clear()
        self.transition_collector.clear()

    # def print_summary(self):
    #     """Print summary of collected data."""
    #     print(f"{self.ha.get_automaton_name()} Run Summary:")
    #     print(f"\tTime Elapsed: {self.ha.get_runtime_time_elapsed()}")

    #     if getattr(self.continuous_collector, "data", None):
    #         print(f"\tCollected {len(self.continuous_collector.data)} continuous state samples")
    #     if getattr(self.auxiliary_collector, "data", None):
    #         print(f"\tCollected {len(self.auxiliary_collector.data)} auxiliary state samples")
    #     if getattr(self.control_collector, "data", None):
    #         print(f"\tCollected {len(self.control_collector.data)} control input samples")
    #     if getattr(self.automaton_collector, "data", None):
    #         print(f"\tCollected {len(self.automaton_collector.data)} automaton state samples")
    #     if getattr(self.transition_collector, "data", None):
    #         print(f"\tCollected {len(self.transition_collector.data)} transition time samples")
