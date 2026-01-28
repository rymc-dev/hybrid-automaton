#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# standard library
import asyncio
import csv
import hashlib
import json
import os
import socket
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

# third-party
import numpy as np

# local imports
from .definition import State, Transition, _Definition


# environment info
PYTHON_VERSION = sys.version
HOST_NAME = socket.gethostname()
PID = os.getpid()

class _Runtime: 
    """ 
    `Automaton.Runtime` is the class that takes
    and injection of a `Automaton.Definition` 
    it encapsulates this and utilizes the structure
    of the automaton to operate a runtime for the automaton
    this class handles the state space states of the automaton
    `continuous_state`, `auxiliary_states`, `control_inputs` and 
    utilizes these to evaluate transition guards, invariants and 
    execute transitions to different discrete modes if activated.
    It utilizies a coro async activation function to do this.

    Args: 
        TODO: 
    """
    _VERSION = "0.0.1"
    
    class Logger: 
        """logs temporal data regarding the automaton 
        """
        def __init__(
            self,
            automaton_definition: _Definition,
            run_signature: "_Runtime.Signature",
            run_context: "_Runtime.Context", 
            should_write_logs_to_file: bool = True,
            log_dir: str = "./log_hybrid_automaton/", 
            file_name: str = "temporal_automaton.log", 
        ):
            self._automaton_definition = automaton_definition
            self._run_signature = run_signature
            self._run_context = run_context
            
            self._should_write_logs_to_file = should_write_logs_to_file
            import os
            self._file_path = os.path.join(log_dir, f"{file_name}")
            if self._should_write_logs_to_file: 
                self._create_file(self._file_path)
        
        def _create_file(self, file_path): 
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(
f"""# ------------------------------------------------------------
# Temporal log for hybrid automaton: '{self._automaton_definition.name}_v{self._automaton_definition.version}'
#
# Time reference:
#   t = 0.0
#   Clock: monotonic {'real' if self._run_context.clk.is_real_time() else 'simulation'} time
#   Units: seconds
#
# Log contents:
#   Temporal automaton events as they occur
#   Includes transition events, invariant violations, etc.
#   Format: [LEVEL] [timestamp]: [Event Type] [Details]
#   Events: 
#       - Transition: [FROM Discrete State] - [Transition Name] --> [TO Discrete State]
#       - Activation: automaton activated
#       - Deactivation: [reason]
#       - ...
#
# Execution:
#   Initial mode: {self._automaton_definition.state_t0.name}
#   Runner: hybrid_automaton.Runtime v{_Runtime._VERSION}
#   Run ID: {self._run_signature.run_id}
#  
# Environment: 
#   PID: {PID}
#   Python Version: {PYTHON_VERSION}
#   HOST: {HOST_NAME}
# ------------------------------------------------------------
                    """)

        def _write_to_file(self, msg: str): 
            with open(self._file_path, "a") as f:
                f.write(f"\n{msg}")
                
        def _gen_log_msg(self, fixture: str, condition: str, consequence: str): 
            return f"[{fixture}] [{self._run_context.clk.get_elapsed_time_active():.3f}]: [{condition}] {consequence}"
                
        def INFO(self, condition:str, consequence: str): 
            fixture = "INFO"
            msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
            if self._should_write_logs_to_file:
                self._write_to_file(msg)
            else:
                print (msg)
            
        def WARNING(self, condition: str, consequence: str): 
            fixture = "WARNING"
            msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
            if self._should_write_logs_to_file:
                self._write_to_file(msg)
            else:
                print (msg)
            
        def ERROR(self, condition:str, consequence: str): 
            fixture = "ERROR"
            msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
            if self._should_write_logs_to_file:
                self._write_to_file(msg)
            else:
                print (msg)

        def FATAL(self, condition:str, consequence: str): 
            fixture = "FATAL"
            msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
            if self._should_write_logs_to_file:
                self._write_to_file(msg)
            else:
                print (msg)

    class Signature: 
        def __init__(
            self, 
            automaton_definition: _Definition,
            timeout_sec: float,
            real_time_mode_enabled: bool,
            delta_time: float,
            should_integrate: bool
        ):
            self.model_name = automaton_definition.name
            self.model_version = automaton_definition.version
            self.model_hash = automaton_definition.get_definition_hash()
            self.run_configuration_hash = self._generate_run_configuration_hash(
                timeout_sec=timeout_sec,
                real_time_mode_enabled=real_time_mode_enabled,
                should_integrate=should_integrate,
                delta_time=delta_time
            )
            self.run_id = self._generate_run_id()
            
        def _generate_run_configuration_hash(self, timeout_sec: float, real_time_mode_enabled: bool, should_integrate: bool, delta_time: float): 
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

        def _generate_run_id(self): 
            return f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:6]}"
    
    class StepResultCode(Enum): 
        STEP_NORMAL = auto()
        """standard operation inside a discrete mode, continuous dynamics evolve,
        invariants hold, guards all evaluated as false"""
        STEP_TRANSITION = auto()
        """guard/(s) satisfied during evaluation, transition selected, reset(s) applied if there are any
        for the transition new discrete mode entered  
        """
        CONTINUOUS_FLOW_EXCEPTION = auto()
        """continuous flow exception evaluation raised during integration
        """
        
        STEP_SELF_INTEGRATION_EXCEPTION = auto()
        """exception occured integration continuous dynamics generated for step
        """
        
        STEP_TRANSITION_EXCEPTION = auto()
        """an exception occured while attempting a discrete state jump
        """
        # NOTE: ENABLED_TRANSITION_CONFLICT ignored, handled by automaton definition requirements of non conflicting 
        # discrete mode priorities when defining discrete state transiitons
        # TIME BLOCK should not occur either, we check transitions have destinations 
        # on definition initialization, but as for the automaton flow, lack of flow may be a design
        # choice so there s no way for me to validate this, it's up to designer to determine through the 
        # automaton results if time blocks occur.  JUNMPS ALWAYS possible, 
        # but no continuous flow of dynamic not a worry of framework as may be intentional  
        STEP_INVARIANT_VIOLATION = auto()
        """invariant(s) bitwise ~| evaluated as without valid transition from current 
        discrete mode being available therefore leaving automaton in a semantically invalid state
        in an invalid state so run should stop
        """
        
        STEP_TERMINAL_REACHED = auto()
        """Entered a designated terminal / accepting discrete mode
        no further evolution intended therefore automaton run complete
        auto deactivate. 
        in this automaton final mode is declared, when invariant violation occurs
        and we are in a designated definition final state this is returned
        """  

        STEP_AUTOMATON_CANCELLED = auto()
        """signifies that the automaton has been manually cancelled by the client 
        """

        class StepSeverity(Enum): 
            STEP_OK = auto()
            """ step worked as expected, continue normal operation as expected
            """
            STEP_WARNING = auto()
            """ a non critical issue during step, just need to prompt the end user of this
            """
            STEP_ERROR = auto()
            """ error raised, these are typically critical related to the automaton definition being mishandled,
            when raised should close automaton handle and raise exception to stop the run
            """
            STEP_FATAL = auto()
            """ fatal raised, this is an unexpected exception most likely related to code implementations, 
                when this occurs something has went fatally wrong with the code, for evaluation_step 
                should contact the developer if this severity occurs
            """
    
    class StepSeverity(Enum): 
        STEP_OK = auto()
        """ step worked as expected, continue normal operation as expected
        """
        STEP_WARNING = auto()
        """ a non critical issue during step, just need to prompt the end user of this
        """
        STEP_ERROR = auto()
        """ error raised, these are typically critical related to the automaton definition being mishandled,
        when raised should close automaton handle and raise exception to stop the run
        """
        STEP_FATAL = auto()
        """ fatal raised, this is an unexpected exception most likely related to code implementations, 
            when this occurs something has went fatally wrong with the code, for evaluation_step 
            should contact the developer if this severity occurs
        """
    
    @dataclass
    class StepResult:
        """
        a struct for returning information regarding evaluation steps
        in the runtime.
        """
        
        severity: "_Runtime.StepSeverity"
        result: "_Runtime.StepResultCode" = None
        message: str = ""
        
    class RunResultCode(Enum): 
        SUCCESS = auto()
        FAILURE = auto()

    @dataclass
    class RunResult:
        """   
        a return obj for showing results of the runtime
        """
        run_signature:AutomatonRuntime.Signature = None 
        result: RunResultCode = RunResultCode.SUCCESS
        reason: StepResult = None # if failure then returns previous step result which caused
        message: str = ""
        dwell_time: float = 0.0
        
    @dataclass
    class TaskResults: 
        runner_task_result = None
        timeout_watchdog_task_result = None
        continuous_state_sampler_task_result = None
        auxiliary_state_sampler_task_result = None
        control_inputs_state_sampler_task_result = None
        continuous_state_provider_task_result = None
        auxiliary_state_provider_task_result = None
        control_input_states_provider_task_result = None

    class Context: 
        class Clock:
            """clock, runs a clock instance that is utilized
            for real-time/simulation time for the automaton runtime"""
            def __init__(
                self, 
                dt: float, 
                real_time_mode: bool,
                timeout_event:asyncio.Event, # A reference to the context timeout event
                timeout_sec: float = np.inf
            ):
                self._real_time_mode: bool = real_time_mode
                self._dt: float = dt

                self._global_time: float = 0.0
                self._global_time_start: float = 0.0
                self._elapsed_time_active: float = 0.0
                self._time_elapsed_since_last_transition: float = 0.0
                self._last_transition_time: float = 0.0
                
                self._timeout_sec = timeout_sec
                self._timeout_event:asyncio.Event = timeout_event

                self._running: bool = False  # Add running flag for start/stop

            def step_dt(self):
                if self._real_time_mode:
                    raise SystemError(
                    "trying to step `dt` when we are in real time mode."
                    )
                self._elapsed_time_active += self._dt
                self._time_elapsed_since_last_transition += self._dt

            async def sleep_for_dt(self):
                await asyncio.sleep(self._dt)

            def get_dt(self) -> float: 
                return self._dt
            
            def get_elapsed_time_active(self): 
                return self._elapsed_time_active
            
            def get_time_elapsed_since_transition(self):
                return self._time_elapsed_since_last_transition
            
            def is_real_time(self): 
                return self._real_time_mode

            def ping_transition(self):
                """
                Call this method whenever a transition occurs to reset the
                time elapsed since last transition.
                """
                if self._real_time_mode:
                    now = time.perf_counter()
                    self._last_transition_time = now
                    self._time_elapsed_since_last_transition = 0.0
                else:
                    self._time_elapsed_since_last_transition = 0.0

            async def activate(self): 
                if not self._real_time_mode:
                    raise SystemError(
                    "Attempted to start clock in simulation mode, which is invalid."
                    )

                self._global_time_start = time.perf_counter()
                self._elapsed_time_active = 0.0
                self._time_elapsed_since_last_transition = 0.0
                self._last_transition_time = self._global_time_start

                self._running = True
                while self._running: 
                    await asyncio.sleep(0.001)
                    now = time.perf_counter()
                    self._global_time = now
                    self._elapsed_time_active = now - self._global_time_start
                    self._time_elapsed_since_last_transition = now - self._last_transition_time

            def deactivate(self):
                """Stops the clock timer loop."""
                self._running = False
              
            async def _timeout_watchdog(self):
                """Monitor automaton and set timeout if elapsed."""
                try:
                    while self.get_elapsed_time_active() < self._timeout_sec:
                        if self._run_completed_event.is_set() or self._deactivate_event.is_set():
                            return
                        await asyncio.sleep(0.05)
                    # Timeout triggered
                    self._timeout_event.set()
                except asyncio.CancelledError:
                    return  
                
        class ContinuousState:
            """Continuous state representation with time-buffering and integration."""

            def __init__(
                self, 
                name: str, 
                x0: np.ndarray, 
                buffer_len: int = 10,
                expected_update_hz: float = 10.0,
                integration_func: Optional[Callable] = None
            ):
                self.name = name
                self.x0 = x0

                # state buffers (just like AuxiliaryState)
                self.x_buffer = deque(maxlen=buffer_len)
                self.x_update_stamps = deque(maxlen=buffer_len)

                # timing stats
                self.expected_update_hz = expected_update_hz
                self.actual_update_hz = expected_update_hz
                self.last_update_stamp: float = None

                # integration
                self._integration_function = integration_func

                # bookkeeping
                self.input_step: int = 0

                # initialize
                self._add_state(x0)

            # ----------------------------------------------------------------------
            # Internal "aux-like" buffer update
            # ----------------------------------------------------------------------
            def _add_state(self, x: np.ndarray):
                """Add new state + timestamp, updating timing statistics."""
                now = time.perf_counter_ns()

                # compute dt and update actual Hz
                if len(self.x_update_stamps) > 0:
                    dt_ns = now - self.x_update_stamps[0]
                    dt_s = dt_ns / 1_000_000_000
                    if dt_s > 0:
                        self.actual_update_hz = 1.0 / dt_s

                # push into buffers
                self.x_buffer.appendleft(x)
                self.x_update_stamps.appendleft(now)

                # update time bookkeeping
                self.last_update_stamp = now / 1_000_000_000
                self.input_step += 1

            # ----------------------------------------------------------------------
            # Public API
            # ----------------------------------------------------------------------
            def latest(self) -> np.ndarray:
                """Return the latest continuous state."""
                return self.x_buffer[0]

            def get_state_buffer(self) -> deque:
                return self.x_buffer

            def last_update_dt(self) -> float:
                """Time since last update in seconds."""
                if self.last_update_stamp is None:
                    return float("inf")
                return time.perf_counter() - self.last_update_stamp

            def set_continuous_state(self, x: np.ndarray):
                """Directly set the continuous state."""
                self._add_state(x)

            # ----------------------------------------------------------------------
            # Integration
            # ----------------------------------------------------------------------
            def integrate(self, xdot: np.ndarray, dt: float):
                """Integrate using custom function or Euler fallback."""
                x_current = self.latest()

                if self._integration_function is not None:
                    x_next = self._integration_function(x_current, xdot, dt)
                else:
                    # Euler integration
                    x_next = x_current + xdot * dt

                self._add_state(x_next)

            # ----------------------------------------------------------------------
            def __repr__(self):
                return (
                    f"ContinuousState(name={self.name}, "
                    f"latest={self.latest()}, "
                    f"actual_update_hz={self.actual_update_hz:.2f}, "
                    f"timestep={self.timestep})"
                )

        class AuxiliaryState:
            """Auxiliary state wrapper class"""

            def __init__(
                self, 
                name: str, 
                aux0: np.ndarray, 
                aux_buffer_len: int = 10, 
                expected_update_hz: int = 1
            ):
                self.name = name
                self.aux0 = aux0

                self.aux_buffer = deque(maxlen=aux_buffer_len)
                self.aux_update_stamps = deque(maxlen=aux_buffer_len)

                self.expected_update_hz = expected_update_hz
                self.actual_update_hz = expected_update_hz  # start with expected

                self.last_update_stamp: float = None
                self.input_step: int = 0

                # initialize with aux0
                self.add(aux0)

            def get_aux_buffer(self) -> deque: 
                return self.aux_buffer

            def latest(self) -> np.ndarray:
                """Return the most recent auxiliary state."""
                return self.aux_buffer[0]

            def last_update_dt(self) -> float:
                """Return time since last update in seconds."""
                if self.last_update_stamp is None:
                    return float("inf")
                return time.perf_counter() - self.last_update_stamp

            def add(self, aux: np.ndarray):
                """Add a new auxiliary state and update timing stats."""
                now = time.perf_counter_ns()

                # Compute actual update frequency if this is not the first update
                if len(self.aux_update_stamps) > 0:
                    dt_ns = now - self.aux_update_stamps[0]
                    dt_s = dt_ns / 1_000_000_000  # convert to seconds
                    if dt_s > 0:
                        self.actual_update_hz = 1.0 / dt_s

                # Update buffers
                self.aux_buffer.appendleft(aux)
                self.aux_update_stamps.appendleft(now)

                self.last_update_stamp = now / 1_000_000_000  # store in seconds
                self.input_step += 1

            def __repr__(self):
                return (
                    f"AuxiliaryState(name={self.name}, "
                    f"latest={self.latest()}, "
                    f"actual_update_hz={self.actual_update_hz:.2f})"
                )

        class ControlInput:
            """Control input representation with buffered history and update tracking"""

            def __init__(
                self, 
                name: str, 
                u0: np.ndarray, 
                buffer_len: int = 10, 
                expected_update_hz: float = 10.0
            ):
                self.name = name
                self.u0 = u0

                # buffer for control inputs
                self.u_buffer = deque(maxlen=buffer_len)
                self.u_update_stamps = deque(maxlen=buffer_len)

                # timing stats
                self.expected_update_hz = expected_update_hz
                self.actual_update_hz = expected_update_hz
                self.last_update_stamp: float = None

                # bookkeeping
                self.input_step: int = 0

                # initialize
                self.add(u0)

            # ----------------------------------------------------------------------
            # Internal buffer update
            # ----------------------------------------------------------------------
            def _add_state(self, u: np.ndarray):
                now = time.perf_counter_ns()

                if len(self.u_update_stamps) > 0:
                    dt_ns = now - self.u_update_stamps[0]
                    dt_s = dt_ns / 1_000_000_000
                    if dt_s > 0:
                        self.actual_update_hz = 1.0 / dt_s

                self.u_buffer.appendleft(u)
                self.u_update_stamps.appendleft(now)

                self.last_update_stamp = now / 1_000_000_000
                self.input_step += 1

            # ----------------------------------------------------------------------
            # Public API
            # ----------------------------------------------------------------------
            def latest(self) -> np.ndarray:
                """Return the most recent control input."""
                return self.u_buffer[0]

            def get_input_buffer(self) -> deque:
                return self.u_buffer

            def last_update_dt(self) -> float:
                """Time since last update in seconds."""
                if self.last_update_stamp is None:
                    return float("inf")
                return time.perf_counter() - self.last_update_stamp

            def add(self, u: np.ndarray):
                """Add a new control input to the buffer."""
                self._add_state(u)

            def set_control_input(self, u: np.ndarray):
                """Alias for add, for backward compatibility."""
                self.add(u)

            # ----------------------------------------------------------------------
            def __repr__(self):
                return (
                    f"ControlInput(name={self.name}, "
                    f"latest={self.latest()}, "
                    f"actual_update_hz={self.actual_update_hz:.2f}, "
                    f"input_step={self.input_step})"
                ) 
                
        @dataclass
        class EventFlags: 
            # core control events
            timeout_event = asyncio.Event()
            deactivate_event = asyncio.Event()
            
            # step events
            transition_event: asyncio.Event = asyncio.Event()
            
            terminal_reached_event: asyncio.Event = asyncio.Event()
            
            warning_event: asyncio.Event = asyncio.Event()
            error_event: asyncio.Event = asyncio.Event()
            fatal_exception_event: asyncio.Event = asyncio.Event()
            
            
            
            # Coordination events
            error_event: asyncio.Event  = asyncio.Event()
                
            def is_event(self) -> bool:
                """validates if any events are active or not"""
                return any([
                    self.run_completed_event.is_set(),
                    self.timeout_event.is_set(),
                    self.deactivate_event.is_set(),
                    self.transition_event.is_set()
                ])
                
            def which_event(self) -> None:
                """  
                returns enum associated with the event
                """ 
                if self.run_completed_event.is_set(): 
                    return ... 
                elif self.timeout_event.is_set(): 
                    return ...
                elif self.deactivate_event.is_set(): 
                    return ...
                elif self.deactivate_event.is_set(): 
                    return ...
                else: 
                    None
        
        class Status(Enum): 
            ACTIVE = auto()
            INACTIVE = auto()
    
        def __init__(
            self,
            initial_state,
            initial_continuous_state: Optional[np.array] = None,
            initial_auxiliary_states: Optional[Dict[str, np.array]] = {},
            initial_control_input_states: Optional[Dict[str, np.array]] = {},
            delta_time: float = 0.001,
            real_time_mode: bool = False,
            configuration: Optional[Dict[str, Any]] = {},
            timeout_sec: Optional[float] = np.inf,
            should_integrate: bool = True 
        ):
            from .definition import State
            self.discrete_state: State = initial_state
            self.clock: _Runtime.Context.Clock = _Runtime.Context.Clock(
                dt=delta_time,
                real_time_mode=True
            ) 
            self.continuous_state: _Runtime.Context.ContinuousState = _Runtime.Context.ContinuousState(name='agent_state', x0=initial_continuous_state)
            self.auxiliary_states: Dict[str, _Runtime.Context.AuxiliaryState] = {k:_Runtime.Context.AuxiliaryState(name=k, aux0=v) for k, v in initial_auxiliary_states.items()} if initial_auxiliary_states is not None else {}
            self.control_input_states: Dict[str, _Runtime.Context.ControlInput] = {k: _Runtime.Context.ControlInput(name=k, u0=v) for k, v in initial_control_input_states.items()} if initial_control_input_states is not None else {}
            self.configuration: Dict[str, Any] = configuration | {
                "timeout_sec": timeout_sec,
                "should_integrate": should_integrate
            }
            
            self.status = _Runtime.Context.Status = _Runtime.Context.Status.ACTIVE
            self.events: _Runtime.Context.EventFlags = _Runtime.Context.EventFlags()
    
    class StateProvider: 

        class ContinuousStateProvider:
            """Injects continuous state updates for open-loop operation."""
            
            def __init__(self, fn: Callable[[], Dict[str, np.ndarray]], update_rate: float = 0.001): 
                self.fn = fn
                self.update_rate = update_rate
            
            async def inject(self, ha):
                """Continuously inject state updates while automaton is active."""
                while ha._runtime and ha._runtime._active:
                    try:
                        new_state = self.fn()
                        ha.set_runtime_continuous_state(new_state)
                    except Exception as e:
                        print(f"State injection error: {e}")
                        break
                    
                    await asyncio.sleep(self.update_rate)

        class AuxiliaryStateProvider:
            """Injects auxiliary state updates for open-loop operation."""
        
            def __init__(self, fn: Callable[[], Dict[str, np.ndarray]], update_rate: float = 0.001):
                self.fn = fn
                self.update_rate = update_rate 
    
            async def inject(self, ha):
                """Continuously inject auxiliary state updates while automaton is active."""
                while ha._runtime and ha._runtime._active:
                    try:
                        new_aux_state = self.fn()
                        ha.set_runtime_auxiliary_continuous_states(new_aux_state)
                    except Exception as e:
                        print(f"Auxiliary state injection error: {e}")
                        break
                    
                    await asyncio.sleep(self.update_rate)

        class ControlInputProvider:
            """Injects control input updates for open-loop operation."""
            def __init__(self, fn: Callable[[], Dict[str, np.ndarray]], update_rate: float = 0.001):
                self.fn = fn
                self.update_Rate = update_rate
            
            async def inject(self, ha):
                """Continuously inject control input updates while automaton is active."""
                while ha._runtime and ha._runtime._active:
                    try:
                        new_control = self.fn()
                        ha.set_runtime_control_inputs(new_control)
                    except Exception as e:
                        print(f"Control input injection error: {e}")
                        break
                    
                    await asyncio.sleep(self.update_rate)
    
    class StateSamplers:   
         
        class BaseStateSampler:
            FILE_EXTENSION = "csv"

            def __init__(
                self,
                name: str,
                sampling_rate: float,
                samples_per_write: int,
                output_dir: str,
            ):
                self._name = name
                self._sampling_rate = sampling_rate
                self._samples_per_write = samples_per_write
                self._output_dir = output_dir

                self._samples: List[List[Any]] = []
                self._samples_collected = 0

                self._dump_event = asyncio.Event()
                self._active_event = asyncio.Event()

                self._task_group: List[asyncio.Task] = []
                self._file_path: Optional[str] = None
                self._last_run_id: Optional[str] = None

            # ---------- lifecycle ----------

            async def activate(self, automaton_run_id: str, ha):
                self._last_run_id = automaton_run_id
                self._create_file(automaton_run_id)
                self._active_event.set()

                self._task_group = [
                    asyncio.create_task(self._state_sampler(ha)),
                    asyncio.create_task(self._watch_for_dump_event()),
                ]

            async def deactivate(self):
                self._active_event.clear()

                for task in self._task_group:
                    task.cancel()

                await asyncio.gather(*self._task_group, return_exceptions=True)
                self._dump_samples()

            # ---------- core logic ----------

            async def _state_sampler(self, ha):
                next_sample_time = ha.get_runtime_time_elapsed() + self._sampling_rate

                try:
                    while self._active_event.is_set():
                        now = ha.get_runtime_time_elapsed()
                        await asyncio.sleep(max(0, next_sample_time - now))

                        sample = self._get_state_sample(ha)
                        self._samples.append([ha.get_runtime_time_elapsed(), sample])
                        self._samples_collected += 1

                        if self._samples_collected >= self._samples_per_write:
                            self._dump_event.set()

                        next_sample_time += self._sampling_rate

                except asyncio.CancelledError:
                    pass

            async def _watch_for_dump_event(self):
                try:
                    while self._active_event.is_set():
                        await self._dump_event.wait()
                        self._dump_samples()
                        self._dump_event.clear()
                except asyncio.CancelledError:
                    pass

            # ---------- file handling ----------

            def _create_file(self, automaton_run_id: str):
                os.makedirs(self._output_dir, exist_ok=True)
                self._file_path = os.path.join(
                    self._output_dir,
                    f"{automaton_run_id}_{self._name}.{self.FILE_EXTENSION}",
                )

                with open(self._file_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp", "state"])

            def _dump_samples(self):
                if not self._samples or not self._file_path:
                    return

                def to_serializable(obj):
                    if isinstance(obj, np.ndarray):
                        return obj.tolist()
                    if isinstance(obj, dict):
                        return {k: to_serializable(v) for k, v in obj.items()}
                    return obj

                with open(self._file_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    for ts, state in self._samples:
                        writer.writerow([ts, json.dumps(to_serializable(state))])

                self._samples.clear()
                self._samples_collected = 0

            # ---------- override hook ----------

            def _get_state_sample(self, ha) -> Any:
                raise NotImplementedError
            
        class ContinuousStateSampler(BaseStateSampler):
            def _get_state_sample(self, ha):
                return ha.get_runtime_continuous_state().latest()

        class AuxiliaryStateSampler(BaseStateSampler):
            def _get_state_sample(self, ha):
                return ha.get_runtime_auxiliary_state()

        class ControlInputStateSampler(BaseStateSampler):
            def _get_state_sample(self, ha):
                return ha.get_runtime_control_input().latest()
              
        def __init__(
            self,
            *,
            continuous_enabled=False,
            continuous_sample_rate: int = 10,
            continuous_samples_per_write: int = 1000,
            auxiliary_enabled=False,
            auxiliary_sample_rate: int = 10,
            auxiliary_samples_per_write: int = 1000,
            control_enabled=False,
            control_sample_rate: int = 10,
            control_samples_per_write: int = 1000,
            output_dir="./log_hybrid_automaton",
        ):
            self._samplers: List[_Runtime.StateSamplers.BaseStateSampler] = []

            if continuous_enabled:
                self._samplers.append(
                    _Runtime.StateSamplers.ContinuousStateSampler(
                        name="continuous_state",
                        sampling_rate=(1.0 / continuous_sample_rate),
                        samples_per_write=continuous_samples_per_write,
                        output_dir=output_dir,
                    )
                )

            if auxiliary_enabled:
                self._samplers.append(
                    _Runtime.StateSamplers.AuxiliaryStateSampler(
                        name="auxiliary_state",
                        sampling_rate=(1.0/auxiliary_sample_rate),
                        samples_per_write=auxiliary_samples_per_write,
                        output_dir=output_dir,
                    )
                )

            if control_enabled:
                self._samplers.append(
                    _Runtime.StateSamplers.ControlInputStateSampler(
                        name="control_input_state",
                        sampling_rate=(1.0/control_sample_rate),
                        samples_per_write=control_samples_per_write,
                        output_dir=output_dir,
                    )
                )

        async def activate(self, automaton_run_id: str, ha):
            await asyncio.gather(
                *(s.activate(automaton_run_id, ha) for s in self._samplers)
            )

        async def deactivate(self):
            await asyncio.gather(*(s.deactivate() for s in self._samplers))

    def __init__(
            self,
            definition: _Definition,
            integration_fnc: Optional[callable] = None
    ): 
        # TODO: Make 'self._active' this a async event instead of just being a boolean  
        self._active_event = asyncio.Event()

        self._automaton_definition: _Definition = definition
        self._discrete_state: State = self._automaton_definition.state_t0 
        
        self._integration_fnc = integration_fnc
        
        self._ctx: _Runtime.Context = None
        self._xdot: List = None
    
    def _evaluation_step(self, logger: Logger, runtime_context: Context) -> StepResult:
        """
        Perform one timestep evaluation of the hybrid automaton.
        this is a purely syncronis function.
        
        return: 
            StepResult: A step code and msg
        """
        try: 
            # ---------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # ---------------------------------------------------------
            try:
                xdot = self._discrete_state.continuous_dynamics( # TODO: need to change this function to use new class attribute reprensetations instead of dicts
                    ctx=runtime_context
                )
            except Exception as e:
                return _Runtime.StepResult( 
                    result=_Runtime.StepResultCode.CONTINUOUS_FLOW_EXCEPTION,
                    severity=_Runtime.StepSeverityCode.STEP_ERROR,
                    message=f"'{self._automaton_definition.name}' exception occured duration continuous flow caused by: '{str(e)}'"
                )

            if runtime_context.should_integrate and (xdot is not None) and (runtime_context.x.x0 is not None):
                try:
                    runtime_context.x.integrate(xdot, runtime_context.clk.get_dt())
                except Exception as e: 
                    return _Runtime.StepResult(
                        result=_Runtime.StepResultCode.STEP_SELF_INTEGRATION_EXCEPTION,
                        severity=_Runtime.StepSeverity.STEP_ERROR,
                        message=f"'{self._automaton_definition.name}' exception occured during continuous dynamics integration caused by: '{str(e)}'"
                    ) 
            
            # ---------------------------------------------------------
            # 2️⃣ Guard transitions - (Evaluate and Execute discrete
            #  Transition if 1 guard or more are active)
            # ---------------------------------------------------------
            try:
                guard_evaluations = runtime_context.discrete_state.evaluate_transitions(
                    ctx=runtime_context
                )
                active_guards = [item[0] for item in guard_evaluations if item[1] is True]
                error_guards = [[item[0], item[2]] for item in guard_evaluations if item[2] is not None]
                if error_guards and len(error_guards) >= len(active_guards):
                    raise Exception("No valid guard evaluations could be performed, automaton may be stuck, please check guard function implementation.")
                if error_guards:
                    for g in error_guards:
                        print (f"Warning, evaluating guard ended in exception could be critical: '{g[0].name}': {g[1]}")
            except Exception as e:
                return _Runtime.StepResult( 
                    result=_Runtime.StepResultCode.STEP_TRANSITION_EXCEPTION, 
                    severity=_Runtime.StepSeverity.STEP_ERROR,
                    message=f"'{self._automaton_definition.name}' Guard Evaluation error: {str(e)}"
                )
            
            if active_guards:
                try:
                    old_mode = runtime_context.discrete_state.name
                    if len(active_guards) == 1:
                        d = active_guards[0]
                    else:
                        d: Transition = min(active_guards, key=lambda t: t.priority)

                    # Execute transition
                    new_mode, new_ctx = d.execute(
                        ctx = runtime_context
                    )
                    runtime_context = new_ctx
                    runtime_context.clk.ping_transition()

                    if runtime_context.discrete_state.on_exit:
                        runtime_context.discrete_state.on_exit()

                    # Update state
           
                    runtime_context.discrete_state = new_mode
                    runtime_context = runtime_context 

                    # State entry callback
                    if self._discrete_state.on_enter:
                        self._discrete_state.on_enter()
                    
                    return _Runtime.StepResult(
                        result=_Runtime.StepResultCode.STEP_TRANSITION,
                        severity=_Runtime.StepSeverity.STEP_OK,
                        message=f"'{old_mode}' - |{d.name}| -> '{self._discrete_state.name}'"
                    )
                except Exception as e: 
                    return _Runtime.StepResult( 
                        _Runtime.StepResultCode.STEP_TRANSITION_EXCEPTION, 
                        _Runtime.StepSeverity.STEP_ERROR,
                        message=f"'{self._automaton_definition.name}' discrete state jump (transition) exception occured: {str(e)}"
                    )

            # ---------------------------------------------------------
            # 3️⃣ No transition → invariant check
            # ---------------------------------------------------------
            try:
                invariant_holds = runtime_context.discrete_state.check_invariants(
                    ctx=runtime_context
                )
            except Exception as e: 
                return _Runtime.StepResult(
                    results=_Runtime.StepResultCode.STEP_INVARIANT_VIOLATION,
                    severity=_Runtime.StepSeverity.STEP_ERROR, 
                    message=f"'{self._automaton_definition.name}' has had an invariant violation caused by exception during evaluation check, this is a critical semantic error for the automaton which could lead to instability and false results therefore please fix: {str(e)}"
                )

            if invariant_holds:
                return _Runtime.StepResult(
                    result=_Runtime.StepResultCode.STEP_NORMAL,
                    severity=_Runtime.StepSeverity.STEP_OK
                )
            elif not invariant_holds and runtime_context.discrete_state._is_final:
                return _Runtime.StepResult(
                    result=_Runtime.StepResultCode.STEP_TERMINAL_REACHED, 
                    severity=_Runtime.StepSeverity.STEP_OK,
                    message=f"reached: '{runtime_context.discrete_state.name}'"
                )
            else: 
                return _Runtime.StepResult(
                    result=_Runtime.StepResultCode.STEP_INVARIANT_VIOLATION, 
                    severity=_Runtime.StepSeverity.STEP_ERROR,
                    message=f"'{self._automaton_definition.name}' invariant(s) bitwise 'or/~|' '{runtime_context.discrete_state._Inv}' \
                        has been violated, this is a critical semantic error for you automaton definition semantic."
                )
        except Exception as e: 
            return _Runtime.StepResult(
                severity=_Runtime.StepSeverity.STEP_FATAL,
                message=f"undefined fatal exception has occured during evaluation step, please raise issue in 'hybrid_automaton' github repo: {str(e)}"
            )
        
    async def _run(self, logger: Logger, run_context: Context) -> RunResult:
        """
        Main worker for running the automaton asynchronously.

        Handles evaluation steps, state transitions, timeouts, and real-time or simulation clocks.
        Ensures proper cleanup of all tasks and sets RunResult appropriately.
        """
        run_result = _Runtime.RunResult()

        clock_task = None
        if run_context.clock.is_real_time():
            # Real-time mode: start the clock
            clock_task = asyncio.create_task(run_context.clock.activate())

        try:
            while run_context.status is _Runtime.Context.Status.ACTIVE:
                # Handle timeout first
                # if run_context.events.timeout_event.is_set():
                #     logger.WARNING(condition="TIMEOUT", consequence=f"t > {run_context.timeout_sec:.3f}")
                #     run_result.result = RunResultCode.FAILURE
                #     run_result.reason = StepResult(
                #         severity=StepSeverity.STEP_ERROR,
                #         result=StepResultCode.STEP_INVARIANT_VIOLATION,
                #         message=f"Timeout exceeded {run_context.timeout_sec:.3f} seconds"
                #     )
                #     run_result.message = "Automaton terminated due to timeout."
                #     self._active_event.clear()
                #     run_context.events.run_completed_event.set()
                #     break
                # elif run_context.events.deactivate_event.is_set(): 
                #     logger.INFO(
                #         condition="MANUAL_STOP", 
                #         consequence="Automaton was manually stopped via external event."
                #     )
                #     run_result.result = RunResultCode.SUCCESS
                #     run_result.reason = StepResult(
                #         severity=StepSeverity.STEP_OK,
                #         result=-1
                #     )
                #     break

                
                # Evaluate the next step
                step_result: _Runtime.StepResult = self._evaluation_step(runtime_context=run_context)

                # Handle step severities
                match step_result.severity:
                    case _Runtime.StepSeverity.STEP_OK:
                        match step_result.result:
                            case _Runtime.StepResultCode.STEP_NORMAL:
                                pass  # continue
                            case _Runtime.StepResultCode.STEP_TRANSITION:
                                logger.INFO(condition="Transition", consequence=f"{step_result.message}")
                            case _Runtime.StepResultCode.STEP_TERMINAL_REACHED:
                                logger.INFO(condition="Terminal Reached", consequence=f"{step_result.message}")
                                run_result.result = _Runtime.RunResultCode.SUCCESS
                                run_result.reason = step_result.result
                                run_result.message = step_result.message
                                self._active_event.clear()
                                self._run_completed_event.set()
                                break
                            case _Runtime.StepResultCode.STEP_AUTOMATON_CANCELLED:
                                logger.INFO(condition="Automaton Cancelled", consequence=f"{step_result.message}")
                                run_result.result = _Runtime.RunResultCode.SUCCESS
                                run_result.reason = step_result.result 
                                run_result.message = step_result.message
                                self._active_event.clear()
                                self._run_completed_event.set()
                                break
                    case _Runtime.StepSeverity.STEP_WARNING:
                        logger.WARNING(condition="Step Warning", consequence=f"{step_result.result}: {step_result.message}")
                    case _Runtime.StepSeverity.STEP_ERROR:
                        # Log error and terminate loop
                        logger.ERROR(condition="Step Error", consequence=f"{step_result.result}: {step_result.message}")
                        run_result.result = _Runtime.RunResultCode.FAILURE
                        run_result.reason = step_result.result
                        run_result.message = step_result.message
                        self._active_event.clear()
                        self._run_completed_event.set()
                        break
                    case _Runtime.StepResultCode.STEP_FATAL:
                        logger.FATAL(condition="Fatal Step Error", consequence=f"{step_result.result}: {step_result.message}")
                        run_result.result = _Runtime.RunResultCode.FAILURE
                        run_result.reason = step_result.result
                        run_result.message = step_result.message
                        self._active_event.clear()
                        self._run_completed_event.set()
                        break
                    case _:
                        logger.FATAL(condition="Unknown Step Severity", consequence=f"{step_result.result}: {step_result.message}")
                        run_result.result = _Runtime.RunResultCode.FAILURE
                        run_result.reason = step_result.result
                        run_result.message = "Unknown step severity encountered"
                        self._active_event.clear()
                        self._run_completed_event.set()
                        break

                # Advance the clock
                if run_context.clock.is_real_time():
                    await run_context.clock.sleep_for_dt()
                else:
                    run_context.clock.step_dt()
                    await asyncio.sleep(0.001)

        except asyncio.CancelledError as e:
            # Clear active state and propagate cancellation
            logger.WARNING(condition="Cancelled", consequence="Automaton run cancelled externally")
            self._active_event.clear()
            self._run_completed_event.set()
            raise
        except Exception as e:
            # Unexpected exception
            logger.FATAL(condition="Runtime Exception", consequence=str(e))
            run_result.exit_result = _Runtime.RunResultCode.FAILURE
            run_result.reason = -1
            run_result.message = f"Fatal exception during runtime: {str(e)}"
            self._active_event.clear()
            self._run_completed_event.set()
        finally:
            # Cleanup real-time clock if running
            if clock_task and not clock_task.cancelled():
                clock_task.cancel()
                
                try:
                    await clock_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

        return run_result
    
    async def activate(
        self,
        initial_continuous_state: Optional[np.ndarray] = None,
        initial_auxiliary_states: Optional[Dict[str, np.ndarray]] = None,
        initial_control_input_states: Optional[Dict[str, np.ndarray]] = None,
        enable_real_time_mode: Optional[bool] = False,
        enable_self_integration: Optional[bool] = True,
        delta_time: Optional[float] = 0.01,
        timeout_sec: Optional[float] = np.inf,
        continuous_state_sampler_enabled: bool = False,
        continuous_state_sampler_rate: Optional[int] = 1,
        continuous_state_sampler_samples_per_write: Optional[int] = 1000,
        auxiliary_states_sampler_enabled: bool = False,
        auxiliary_states_sampler_rate: Optional[int] = 1,
        auxiliary_states_sampler_samples_per_write: Optional[int] = 1000,
        control_input_states_sampler_enabled: bool = False,
        control_input_states_sampler_rate: Optional[int] = 1,
        control_input_states_samplers_per_write: Optional[int] = 1000,
        continuous_state_provider: Optional[Callable] = None,
        continuous_state_provision_rate: Optional[int] = None,
        auxiliary_states_provider: Optional[Callable] = None,
        auxiliary_states_provision_rate: Optional[int] = None,
        control_input_states_provider: Optional[Callable] = None,
        control_input_states_provision_rate: Optional[int] = None,
        should_write_logs: bool = True,
        output_dir: str = "./log_hybrid_automaton/"
    ) -> RunResult:
        """Activate the automaton asynchronously with optional timeout."""
        run_signature:_Runtime.Signature = _Runtime.Signature(
            self._automaton_definition,
            timeout_sec=timeout_sec,
            delta_time=delta_time,
            real_time_mode_enabled=enable_real_time_mode,
            should_integrate = enable_self_integration
        )
        run_context:_Runtime.Context = _Runtime.Context( # TODO: Need to find a way to move EventFlags into run context
            initial_state=self._automaton_definition.state_t0,
            initial_continuous_state=initial_continuous_state,
            initial_auxiliary_states=initial_auxiliary_states,
            initial_control_input_states=initial_control_input_states,
            clock=_Runtime.Context.Clock(
                dt=delta_time,
                real_time_mode=enable_real_time_mode
            ),
            configuration=self._automaton_definition._configuration, # TODO: Need to update this, configuration should not be referenced through context when being used
            timeout_sec=timeout_sec,
            should_integrate=enable_self_integration
        )
        run_logger:_Runtime.Logger = _Runtime.Logger(
            automaton_definition=self._automaton_definition,
            run_signature=run_signature,
            run_context=run_context,
            should_write_logs_to_file=should_write_logs,
            log_dir=output_dir,
            file_name="temporal_automaton.log"
        )
        
        try:
            # Start Automaton
            run_logger.INFO(condition="ACTIVATION", consequence="automaton activated successfully.")
            self._automaton_definition.on_entry()
            
            task_results: _Runtime.TaskResults = _Runtime.TaskResults()
            
            async with asyncio.TaskGroup() as tg: 
                # Runner Task
                task_results.runner_task_result = tg.create_task(
                    self._run(logger=run_logger, run_context=run_context), # TODO: pass run ID which should contain cfg hash and custom id and automaton name for logging
                    name="runner_task"
                )
               
                # timeout task
                if not (timeout_sec==np.inf): 
                    task_results.timeout_watchdog_task_result = tg.create_task(
                        self._timeout_watchdog(run_context, timeout_sec),
                        name="timeout_watchdog"
                    ) 
                # samplers
                if continuous_state_sampler_enabled:
                    continuous_state_sampler = _Runtime.StateSampler.ContinuousStateSampler(
                        sampling_rate=(1.0/continuous_state_sampler_rate),
                        samples_per_write=continuous_state_sampler_samples_per_write
                    )
                    task_results.continuous_state_sampler_task_result = tg.create_task(
                        continuous_state_sampler.activate(run_signature.run_id, self._automaton_definition),
                        name="continuous_states_sampler"
                    )
                
                if auxiliary_states_sampler_enabled:
                    auxiliary_states_sampler = AuxiliaryStateSampler(
                        sampling_rate=auxiliary_states_sampler_rate,
                        samples_per_write=auxiliary_states_sampler_samples_per_write 
                    )
                    task_results.auxiliary_state_sampler_task_result = tg.create_task(
                        auxiliary_states_sampler.activate(
                            run_signature.run_id,
                            self._automaton_definition
                        )
                    )
                # if control_input_states_sampler_enabled:
                #     control_inputs_state_sampler = ControlInputStateSampler(
                #         sampling_rate = (1.0 / control_input_states_sampler_rate), 
                #         samples_per_write=control_input_states_samplers_per_write 
                #     )
                #     control_inputs_state_sampler_task_result = tg.create_task(
                #         control_inputs_state_sampler.activate(
                #             automaton_run_id=run_signature.run_id,
                #             ha=self._automaton_definition
                #         ),
                #         name="control_inputs_state_sampler"
                #     )
                # # providers 
                # if continuous_state_provider is not None: 
                #     continuous_state_provider: ContinuousStateInjector = ContinuousStateInjector(
                #         fn=continuous_state_provider,
                #         update_rate=(1.0/continuous_state_provision_rate)
                #     )
                #     tg.create_task(
                #         continuous_state_provider.inject(self._automaton_definition),
                #         name="continuous_state_injection"
                #     )           
                # if auxiliary_states_provider is not None: 
                #     auxiliary_states_provider: AuxiliaryStateInjector = AuxiliaryStateInjector(
                #         fn=auxiliary_states_provider,
                #         update_rate=(1.0/auxiliary_states_provision_rate)
                #     )
                #     tg.create_task(
                #         auxiliary_states_provider.inject(ha=self._automaton_definition),
                #         name="auxiliary_state_injection"
                #     )              
                # if control_input_states_provider is not None:
                #     control_input_states_provider: ControlInputInjector = ControlInputInjector(
                #         fn=control_input_states_provider,
                #         update_rate=(1.0 / control_input_states_provision_rate)        
                #     )
                #     tg.create_task(
                #         control_input_states_provider.inject( # TODO: SHould just inject the context instead of automaton definition or something else
                #             fn=control_input_states_provider.inject(self._automaton_definition),
                            
                #         )
                #     )

            run_logger.INFO(condition="DEACTIVATION", consequence="automaton deactivated successfully.")
            self._automaton_definition.on_exit()
            
            print (task_results.runner_task_result)
            
            return task_results.runner_task_result.result() if task_results.runner_task_result.result() else RunResult()
        except Exception as e:
            run_logger.ERROR("FATAL Exception", str(e))
            raise e
        

 
    def deactivate(self): 
        print ("Client deactivation request received!") 
        self._active_event.clear()
