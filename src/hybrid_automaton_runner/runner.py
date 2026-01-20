"""Main runner class for hybrid automaton simulations (refactored)."""
import asyncio
import numpy as np
from typing import Optional, Dict, Any, Tuple
from .samplers import (
    StateSampler,
    ContinuousStateSampler, 
    AuxiliaryStateSampler,
    ControlInputStateSampler,
)
from .injectors import (
    ContinuousStateInjector,
    AuxiliaryStateInjector,
    ControlInputInjector
)
from hybrid_automaton import Automaton
from hybrid_automaton.exit_codes import ExitCode as AutomatonExitCode
from .run_data import AutomatonRunData
from .exit_codes import ExitCode as RunnerExitCode
from .run_data import RunnerExit
from hybrid_automaton.automaton_exit import AutomatonExit
import uuid
from datetime import datetime, timezone
import json
import hashlib
import yaml
import sys
import socket
import os

python_version = sys.version
host_name = socket.gethostname()
pid = os.getpid()

class TaskGroupExit(Exception):
    """
    Special exception used to break out of the TaskGroup and carry
    structured exit information back to the run() caller.
    """
    def __init__(
        self,
        runner_exit_code: RunnerExitCode = None,
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

    def __init__(self, hybrid_automaton: Automaton):
        self.ha = hybrid_automaton

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

    def _generate_run_identity(self, run_hash, output_dir):
        ha_hash = self.ha._definition.get_configuration_hash()
        return {
            "run_id": f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:6]}",
            "automaton name": self.ha.get_automaton_name(),
            "automaton_version": self.ha.get_automaton_version(),
            "logs_output_directory": output_dir, 
            "configuration_info": {
                "run_hash": run_hash,
                "ha_hash": ha_hash,
                "config_hash": f"{run_hash}_{ha_hash}"
            },
            "environment_info": {
                "python_version": f"{python_version}" ,
                "host_name": f"{host_name}",
                "pid": f"{pid}"
            }
        }
    
    def _generate_run_configuration_hash(self, timeout_sec, real_time_mode_enabled, should_integrate, delta_time): 
        serialized = json.dumps(
            {
                "timeout_sec": timeout_sec, 
                "real_time_mode_enabled": real_time_mode_enabled, 
                "should_integrate": should_integrate,
                "delta_time": delta_time
            }
        )
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return digest[:12]

    async def activate(
        self,
        initial_continuous_state: np.ndarray = None,
        initial_auxiliary_states: Dict = {},
        initial_control_inputs: Dict = {},
        timeout_sec: float = np.inf,
        enable_real_time_mode: bool = False,
        should_integrate: bool = True,
        delta_time: float = 0.01,
        should_sample_continuous_states: bool = True,
        sample_rate_continuous_states: float = 0.01,
        should_sample_auxiliary_states: bool = False,
        sample_rate_auxiliary_states: float = 0.1,
        should_sample_control_input_states: bool = False,
        sample_rate_control_input_states: float = 0.1,
        should_inject_continuous_state: bool = False,
        continuous_state_injection_fn: Optional[callable] = None,
        continuous_states_injection_rate: float = 0.001,
        should_inject_auxiliary_states: bool = False,
        auxiliary_states_injection_fn: Optional[callable] = None,
        auxiliary_states_injection_rate: float = 0.001,
        should_inject_control_states: bool = False,
        control_states_injection_fn: Optional[callable] = None,
        control_states_injection_rate: float = 0.001,
        output_dir: str = "./log_hybrid_automaton/"
    ) -> AutomatonRunData:
        """
        Run the hybrid automaton simulation with data collection and/or injection.
        Returns an AutomatonRunData constructed from the captured completion result.
        """
        # TODO: Continue updating this.
        # Reset automaton runtime if necessary
        if self.ha._runtime is not None:
            self.ha.reset()

        """ create the runtime identity for the results"""
        StateSampler.output_dir = output_dir
        
        run_hash = self._generate_run_configuration_hash(
            timeout_sec=timeout_sec,
            real_time_mode_enabled=enable_real_time_mode,
            should_integrate=should_integrate,
            delta_time=delta_time
        )
        run_id = self._generate_run_identity(
            run_hash=run_hash,
            output_dir=output_dir           
        )          
        
        self._automaton_run_complete.clear()
        self._automaton_run_exception.clear()
        self._automaton_run_stop_requested.clear()
        self._automaton_run_timeout.clear()
    
        try:
            async with asyncio.TaskGroup() as tg:
                # Main automaton task: THIS is the primary task that can finish the run.
                tg.create_task(
                    self._wrapped_task(
                        coro=self.ha.activate(
                            x0=initial_continuous_state,
                            aux_x0=initial_auxiliary_states,
                            u0=initial_control_inputs,
                            real_time_mode=enable_real_time_mode,
                            integrate=should_integrate,
                            dt=delta_time
                        ),
                        success_event=self._automaton_run_complete,
                        event_runner_code=RunnerExitCode.AUTOMATON_RUN_COMPLETE,
                        source_name="automaton"
                    ),
                    name="automaton_runtime_task"
                )

                # Data collection tasks: they should NOT signal normal run completion.
                if should_sample_continuous_states:
                    continuous_state_sampler = ContinuousStateSampler(
                        sampling_rate=sample_rate_continuous_states
                    )
                    tg.create_task(
                        self._wrapped_task(
                            coro=continuous_state_sampler.activate(automaton_run_id=run_id['run_id'], ha=self.ha),
                            success_event=None,
                            source_name="continuous_state_sampler"
                        ),
                        name="sample_auxiliary_state_task"
                    )

                if should_sample_auxiliary_states:
                    auxiliary_state_sampler = AuxiliaryStateSampler(
                        sampling_rate=sample_rate_auxiliary_states
                    )
                    tg.create_task(
                        self._wrapped_task(
                            coro=auxiliary_state_sampler.activate(automaton_run_id=run_id['run_id'], ha=self.ha ),
                            success_event=None,
                            source_name="auxiliary_state_sampler"
                        ),
                        name="sample_auxiliary_state_task"
                    )

                if should_sample_control_input_states:
                    control_input_states_sampler = ControlInputStateSampler(
                        sampling_rate=sample_rate_control_input_states
                    )
                    tg.create_task(
                        self._wrapped_task(
                            coro=control_input_states_sampler.activate(automaton_run_id=run_id['run_id'], ha=self.ha),
                            success_event=None,
                            source_name="sample_control_input_states"
                        ),
                        name="sample_control_inputs_task"
                    )


                # Data injection tasks: injectors also should not signal run completion on normal exit.
                if should_inject_continuous_state:
                    if continuous_state_injection_fn is None:
                        raise ValueError("inject_continuous=True requires continuous_state_fn")

                    continuous_state_injector = ContinuousStateInjector(
                        continuous_state_injection_fn, 
                        continuous_states_injection_rate 
                    )
                    tg.create_task(
                        self._wrapped_task(
                            coro=continuous_state_injector.inject(self.ha),
                            success_event=None,
                            source_name="continuous_state_injector"
                        ),
                        name="continuous_state_injector_task"
                    )

                if should_inject_auxiliary_states:
                    if auxiliary_states_injection_fn is None:
                        raise ValueError("inject_auxiliary=True requires auxiliary_fn")
                    auxiliary_state_injector = AuxiliaryStateInjector(
                        fn=auxiliary_states_injection_fn, 
                        update_rate=auxiliary_states_injection_rate
                    )
                    tg.create_task(
                        self._wrapped_task(
                            coro=auxiliary_state_injector.inject(self.ha),
                            success_event=None,
                            source_name="auxiliary_injector"
                        ),
                        name="auxiliary_state_injector_task"
                    )

                if should_inject_control_states:
                    if control_states_injection_fn is None:
                        raise ValueError("inject_control=True requires control_fn")
                    control_states_injector = ControlInputInjector(
                        fn=control_states_injection_fn, 
                        update_rate=control_states_injection_rate
                    )
                    tg.create_task(
                        self._wrapped_task(
                            coro=control_states_injector.inject(self.ha),
                            success_event=None,
                            source_name="control_injector"
                        ),
                        name="control_inputs_injection_task"
                    )

                # Timeout monitor: if finite duration provided, this can finish the run.
                if np.isfinite(timeout_sec) and timeout_sec > 0:
                    tg.create_task(
                        self._wrapped_task(
                            coro=self._timeout_monitor(timeout_sec),
                            success_event=self._automaton_run_timeout,
                            event_runner_code=RunnerExitCode.AUTOMATON_RUN_TIMEOUT,
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
                'runner_exit_code': RunnerExitCode.AUTOMATON_RUN_EXCEPTION,
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
                automaton_name=self.ha.get_automaton_name(),
                automaton_version=self.ha.get_automaton_version(),
                run_id=run_id,
                runner_exit=RunnerExit(runner_code, runner_msg),
                automaton_exit=AutomatonExit(automaton_code, automaton_msg),
            )
        else:
            # Fallback if nothing meaningful was captured
            return AutomatonRunData(
                automaton_name=self.ha.get_automaton_name(),
                automaton_version=self.ha.get_automaton_version() ,
                run_id=run_id,
                runner_exit=RunnerExit(RunnerExitCode.AUTOMATON_NO_RUN, "No completion result captured")
            )

    async def _wrapped_task(self, coro, success_event: Optional[asyncio.Event], event_runner_code: RunnerExitCode = None, source_name: str = "<task>"):
        """
        Wrapper for every spawned coroutine:
          - If the coroutine raises, sets the _automaton_run_exception event (so supervisor notices)
          - If it returns successfully and a success_event is supplied, record that as the canonical completion result
            (only the first such success is recorded)
        - success_event: if provided, indicates that normal completion of this task should trigger run termination.
        - event_runner_code: RunnerExitCode value to associate with that success_event (optional).
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
                    'runner_exit_code': RunnerExitCode.AUTOMATON_RUN_EXCEPTION,
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
            runner_code = event_runner_code if event_runner_code is not None else RunnerExitCode.AUTOMATON_RUN_COMPLETE

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
        # Create tasks mapped to their RunnerExitCode for clarity.
        wait_map = {
            asyncio.create_task(self._automaton_run_complete.wait()): RunnerExitCode.AUTOMATON_RUN_COMPLETE,
            asyncio.create_task(self._automaton_run_timeout.wait()): RunnerExitCode.AUTOMATON_RUN_TIMEOUT,
            asyncio.create_task(self._automaton_run_exception.wait()): RunnerExitCode.AUTOMATON_RUN_EXCEPTION,
            asyncio.create_task(self._automaton_run_stop_requested.wait()): RunnerExitCode.AUTOMATON_RUN_STOP_REQUESTED,
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




