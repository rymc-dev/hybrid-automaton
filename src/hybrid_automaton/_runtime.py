#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import csv
import hashlib
import json
import os
import socket
import sys
import time
from collections import deque
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

import numpy as np

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
    axecute transitions to different discrete modes if activated.
    It utilizies a coro async activation function to do this.

    Args: 
        TODO: 
    """
    _VERSION = "0.0.3"
    
    class Logger: 
        """logs temporal data regarding the automaton 
        """
        def __init__(
            self,
            *,
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
#   Clock: monotonic {'real' if self._run_context.clock.is_real_time() else 'simulation'} time
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
            return f"[{fixture}] [{self._run_context.clock.get_elapsed_time_active():.3f}]: [{condition}] {consequence}"
                
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
            *,
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
     
    # =========================================================================
    # IMPROVED STATUS CODES AND RESULTS
    # =========================================================================
    
    class StepResultCode(Enum):
        """
        Codes representing the outcome of a single evaluation step.
        Streamlined to remove redundancy and improve clarity.
        """
        # Normal operation
        NORMAL = auto()
        """Standard operation: continuous dynamics evolve, invariants hold, no active guards"""
        
        # Successful transitions
        TRANSITION = auto()
        """Guard satisfied, transition executed, new discrete mode entered"""
        
        # Terminal states
        TERMINAL_REACHED = auto()
        """Entered a designated terminal/accepting state - run complete"""
        
        CANCELLED = auto()
        """Automaton manually cancelled by client"""
        
        # Semantic violations
        INVARIANT_VIOLATION = auto()
        """Invariant violated without valid transition - invalid automaton state"""
        
        # Exceptions during evaluation
        CONTINUOUS_FLOW_ERROR = auto()
        """Exception during continuous dynamics evaluation"""
        
        INTEGRATION_ERROR = auto()
        """Exception during integration of continuous dynamics"""
        
        TRANSITION_ERROR = auto()
        """Exception during discrete state transition execution"""
        
        GUARD_EVALUATION_ERROR = auto()
        """Exception during guard evaluation"""

    class StepSeverity(Enum):
        """Severity level of a step result"""
        OK = auto()
        """Step executed successfully"""
        
        WARNING = auto()
        """Non-critical issue that doesn't stop execution"""
        
        ERROR = auto()
        """Critical error - automaton should terminate"""
        
        FATAL = auto()
        """Unexpected fatal error - indicates code bug"""

    @dataclass
    class EvalStepResult:
        """Result of a single evaluation step"""
        code: "_Runtime.StepResultCode"
        severity: "_Runtime.StepSeverity"
        message: str = ""
        
        def is_ok(self) -> bool:
            """Check if step was successful"""
            return self.severity == _Runtime.StepSeverity.OK
        
        def is_terminal(self) -> bool:
            """Check if step reached a terminal condition"""
            return self.code in [
                _Runtime.StepResultCode.TERMINAL_REACHED,
                _Runtime.StepResultCode.CANCELLED
            ]
        
        def should_terminate(self) -> bool:
            """Check if this result should terminate the run"""
            return self.severity in [
                _Runtime.StepSeverity.ERROR,
                _Runtime.StepSeverity.FATAL
            ] or self.is_terminal()

    class RunStatus(Enum):
        """Overall status of the automaton run"""
        SUCCESS = auto()
        """Run completed successfully (terminal state reached or cancelled cleanly)"""
        
        FAILURE = auto()
        """Run failed due to error or violation"""
        
        TIMEOUT = auto()
        """Run exceeded timeout limit"""

    @dataclass
    class RunResult:
        """
        Complete result of an automaton run.
        Provides comprehensive information about execution outcome.
        """
        # Identification
        run_signature: '_Runtime.Signature' = None
        
        # Status
        status: '_Runtime.RunStatus' = None

        run_logs_dir_path: str = ""
        
        # Termination details
        termination_code: '_Runtime.StepResultCode' = None
        termination_message: str = ""
        
        # Final state information
        final_discrete_state: str = ""
        final_continuous_state: Optional[np.ndarray] = None
        
        # Timing
        total_runtime_sec: float = 0.0
        total_steps: int = 0
        transitions_count: int = 0
        
        # Statistics
        step_statistics: Dict[str, int] = None
        
        def __post_init__(self):
            if self.step_statistics is None:
                self.step_statistics = {}
        
        def was_successful(self) -> bool:
            """Check if run completed successfully"""
            return self.status == _Runtime.RunStatus.SUCCESS
        
        def summary(self) -> str:
            """Generate human-readable summary"""
            lines = [
                f"{'='*60}",
                f"Automaton Run Summary",
                f"{'='*60}",
                f"Run ID: {self.run_signature.run_id if self.run_signature else 'N/A'}",
                f"Status: {self.status.name if self.status else 'UNKNOWN'}",
                f"logs directory: {self.run_logs_dir_path}",
                f"",
                f"Termination:",
                f"  Code: {self.termination_code.name if self.termination_code else 'N/A'}",
                f"  Message: {self.termination_message}",
                f"  Final State: {self.final_discrete_state}",
                f"",
                f"Execution Metrics:",
                f"  Total Runtime: {self.total_runtime_sec:.3f}s",
                f"  Total Steps: {self.total_steps}",
                f"  Transitions: {self.transitions_count}",
                f"",
            ]
            
            if self.step_statistics:
                lines.append("Step Statistics:")
                for code, count in self.step_statistics.items():
                    lines.append(f"  {code}: {count}")
            
            lines.append(f"{'='*60}")
            return "\n".join(lines)
        
        def __str__(self): 
            return self.summary()
    
    # =========================================================================
    # CONTEXT AND STATE MANAGEMENT
    # =========================================================================
    
    class Context: 
        class Clock:
            """clock, runs a clock instance that is utilized
            for real-time/simulation time for the automaton runtime"""
            def __init__(
                self, 
                dt: float, 
                real_time_mode: bool,
                timeout_event:asyncio.Event,
                deactivate_event:asyncio.Event,
                timeout_sec: float = np.inf
            ):
                self._real_time_mode: bool = real_time_mode
                self._dt: float = dt
                self._deactivate_event:asyncio.Event = deactivate_event
                self._global_time: float = 0.0
                self._global_time_start: float = 0.0
                self._elapsed_time_active: float = 0.0
                self._time_elapsed_since_last_transition: float = 0.0
                self._last_transition_time: float = 0.0
                
                self._timeout_sec = timeout_sec
                self._timeout_event:asyncio.Event = timeout_event

                self._running: bool = False

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

            async def activate(
                self
            ): 
                tasks = []
                if self._real_time_mode:
                    tasks.append(self._clock_task())
                    
                if self._timeout_sec != np.inf: 
                    tasks.append(
                        self._timeout_watchdog()
                    )
                    
                     
                if len(tasks) == 0: 
                    return None
                else:
                    return await asyncio.gather(
                        *tasks
                    )
            
            def deactivate(self):
                """Stops the clock timer loop."""
                self._running = False
              
            async def _clock_task(self): 
                """Clock task for real-time mode."""
                try:
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
                except asyncio.CancelledError:
                    return
             
            async def _timeout_watchdog(self):
                """Monitor automaton and set timeout if elapsed."""
                try:
                    while self.get_elapsed_time_active() < self._timeout_sec:
                        if self._deactivate_event.is_set(): 
                            return
                        await asyncio.sleep(0.05)
                    # Timeout triggered
                    self._timeout_event.set()
                except asyncio.CancelledError:
                    return  
                
        class ContinuousState:
            """Continuous state representation with time-buffering and integration."""

            class IntegrationFcn(Enum): 
                @staticmethod
                def _euler(x, xdot, dt): 
                    return x + dt * xdot
                
                @staticmethod
                def _rk4(x, xdot, dt): 
                    k1 = xdot
                    k2 = xdot
                    k3 = xdot
                    k4 = xdot
                    return x + dt * (k1 + 2*k2 + 2*k3 + k4) / 6
                        
                EULER = _euler 
                RK4 = _rk4
                
                def __call__(self, *args, **kwargs): 
                    return self.value(*args, **kwargs)
                 
            def __init__(
                    self, 
                    name: str, 
                    x0: np.ndarray, 
                    x_labels: List,
                    buffer_len: int = 10,
                    expected_update_hz: float = 10.0,
                    integration_fnc: IntegrationFcn = IntegrationFcn.EULER
                ):
                    self.name = name
                    self.x0 = x0
                    self.x_labels = x_labels

                    # state buffers (just like AuxiliaryState)
                    self.x_buffer = deque(maxlen=buffer_len)
                    self.x_update_stamps = deque(maxlen=buffer_len)

                    # timing stats
                    self.expected_update_hz = expected_update_hz
                    self.actual_update_hz = expected_update_hz
                    self.last_update_stamp: float = None

                    # integration
                    self._integration_function: _Runtime.Context.ContinuousState.IntegrationFcn = integration_fnc

                    # bookkeeping
                    self.input_step: int = 0

                    # initialize
                    self._add_state(x0)

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

            def integrate(self, xdot: np.ndarray, dt: float):
                """Integration utilizing the integration function patched in"""
                x_current = self.latest()
                x_next = self._integration_function(x_current, xdot, dt)
                self._add_state(x_next)

            def __repr__(self):
                return (
                    f"ContinuousState(name={self.name}, "
                    f"latest={self.latest()}, "
                    f"actual_update_hz={self.actual_update_hz:.2f}, "
                    f"timestep={self.input_step})"
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
                self.actual_update_hz = expected_update_hz

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

                if len(self.aux_update_stamps) > 0:
                    dt_ns = now - self.aux_update_stamps[0]
                    dt_s = dt_ns / 1_000_000_000
                    if dt_s > 0:
                        self.actual_update_hz = 1.0 / dt_s

                self.aux_buffer.appendleft(aux)
                self.aux_update_stamps.appendleft(now)

                self.last_update_stamp = now / 1_000_000_000
                self.input_step += 1

            def pop(self): 
                self.aux_buffer.popleft()
            
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

                self.u_buffer = deque(maxlen=buffer_len)
                self.u_update_stamps = deque(maxlen=buffer_len)

                self.expected_update_hz = expected_update_hz
                self.actual_update_hz = expected_update_hz
                self.last_update_stamp: float = None

                self.input_step: int = 0

                self.add(u0)

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

            def __repr__(self):
                return (
                    f"ControlInput(name={self.name}, "
                    f"latest={self.latest()}, "
                    f"actual_update_hz={self.actual_update_hz:.2f}, "
                    f"input_step={self.input_step})"
                ) 
                
        @dataclass
        class EventFlags: 
            timeout_event: asyncio.Event = None
            deactivate_event: asyncio.Event = None
            terminal_reached_event: asyncio.Event = None
            error_event: asyncio.Event = None
            fatal_event: asyncio.Event = None
            
            def __post_init__(self):
                if self.timeout_event is None:
                    self.timeout_event = asyncio.Event()
                if self.deactivate_event is None:
                    self.deactivate_event = asyncio.Event()
                if self.terminal_reached_event is None:
                    self.terminal_reached_event = asyncio.Event()
                if self.error_event is None:
                    self.error_event = asyncio.Event()
                if self.fatal_event is None:
                    self.fatal_event = asyncio.Event()
                
            def is_any_event_set(self) -> bool:
                """Check if any termination event is set"""
                return any([
                    self.timeout_event.is_set(),
                    self.deactivate_event.is_set(),
                    self.terminal_reached_event.is_set(),
                    self.error_event.is_set(),
                    self.fatal_event.is_set()
                ])
                
            def get_active_event(self) -> Optional[str]:
                """Return name of first active event"""
                if self.timeout_event.is_set():
                    return "timeout"
                elif self.deactivate_event.is_set():
                    return "deactivate"
                elif self.terminal_reached_event.is_set():
                    return "terminal_reached"
                elif self.error_event.is_set():
                    return "error"
                elif self.fatal_event.is_set():
                    return "fatal"
                return None
        
        class Status(Enum): 
            ACTIVE = auto()
            INACTIVE = auto()
    
        def __init__(
            self,
            initial_state,
            initial_continuous_state: ContinuousState = None,
            initial_auxiliary_states: Optional[Dict[str, np.array]] = None,
            initial_control_input_states: Optional[Dict[str, np.array]] = None,
            delta_time: float = 0.001,
            real_time_mode: bool = False,
            configuration: Optional[Dict[str, Any]] = None,
            timeout_sec: Optional[float] = np.inf,
            should_integrate: bool = True 
        ):
            from .definition import State
            self.discrete_state: State = initial_state

            self.continuous_state: _Runtime.Context.ContinuousState = initial_continuous_state 
            
            self.auxiliary_states: Dict[str, _Runtime.Context.AuxiliaryState] = {
                k: _Runtime.Context.AuxiliaryState(name=k, aux0=v) 
                for k, v in (initial_auxiliary_states or {}).items()
            }
            
            self.control_input_states: Dict[str, _Runtime.Context.ControlInput] = {
                k: _Runtime.Context.ControlInput(name=k, u0=v) 
                for k, v in (initial_control_input_states or {}).items()
            }
            
            self.configuration: Dict[str, Any] = (configuration or {}) | {
                "should_integrate": should_integrate
            }
            
            self.status = _Runtime.Context.Status.ACTIVE
            self.events: _Runtime.Context.EventFlags = _Runtime.Context.EventFlags()
            self.clock: _Runtime.Context.Clock = _Runtime.Context.Clock(
                dt=delta_time,
                real_time_mode=real_time_mode,
                timeout_event=self.events.timeout_event,
                deactivate_event=self.events.deactivate_event,
                timeout_sec=timeout_sec
            )
            
            # Statistics tracking
            self.total_steps: int = 0
            self.transitions_count: int = 0
            self.step_counts: Dict[str, int] = {}
    
    # =========================================================================
    # STATE PROVIDERS AND SAMPLERS
    # =========================================================================
    
    class StateProviders: 
        
        class BaseStateProvider:
            def __init__(
                self,
                fn: Callable[[], Dict[str, np.ndarray]],
                update_rate: float,
            ):
                self._fn = fn
                self._update_rate = update_rate

                self._active_event = asyncio.Event()
                self._task: Optional[asyncio.Task] = None

            async def activate(self, ctx: '_Runtime.Context'):
                self._active_event.set()
                self._task = asyncio.create_task(self._inject_loop(ctx))

            async def deactivate(self):
                self._active_event.clear()

                if self._task:
                    self._task.cancel()
                    await asyncio.gather(self._task, return_exceptions=True)

            async def _inject_loop(self, ctx: '_Runtime.Context'):
                try:
                    while self._active_event.is_set():
                        try:
                            value = self._fn()
                            self._inject(ctx, value)
                        except Exception as e:
                            print(f"{self.__class__.__name__} injection error: {e}")
                            break

                        await asyncio.sleep(self._update_rate)

                except asyncio.CancelledError:
                    pass

            def _inject(self, ctx: '_Runtime.Context', value: Dict[str, np.ndarray]):
                raise NotImplementedError
            
        class ContinuousStateProvider(BaseStateProvider):
            def _inject(self, ctx: '_Runtime.Context', value):
                ctx.continuous_state = value

        class AuxiliaryStateProvider(BaseStateProvider):
            def _inject(self, ctx: '_Runtime.Context', value):
                ctx.auxiliary_states = value

        class ControlInputProvider(BaseStateProvider):
            def _inject(self, ctx: '_Runtime.Context', value):
                ctx.control_input_states = value

        def __init__(
            self,
            *,
            continuous_fn: Optional[Callable[[], Dict[str, np.ndarray]]] = None,
            continuous_update_rate: int = 10,
            auxiliary_fn: Optional[Callable[[], Dict[str, np.ndarray]]] = None,
            auxiliary_update_rate: int = 10,
            control_fn: Optional[Callable[[], Dict[str, np.ndarray]]] = None,
            control_update_rate: int = 10,
        ):
            self._providers: List[_Runtime.StateProviders.BaseStateProvider] = []

            if continuous_fn:
                self._providers.append(
                    _Runtime.StateProviders.ContinuousStateProvider(continuous_fn, (1.0/continuous_update_rate))
                )

            if auxiliary_fn:
                self._providers.append(
                    _Runtime.StateProviders.AuxiliaryStateProvider(auxiliary_fn, (1.0/auxiliary_update_rate))
                )

            if control_fn:
                self._providers.append(
                    _Runtime.StateProviders.ControlInputProvider(control_fn, (1.0/control_update_rate))
                )

        def is_providers(self): 
            return len(self._providers) > 0
        
        async def activate(self, ctx: '_Runtime.Context'):
            await asyncio.gather(*(p.activate(ctx) for p in self._providers))

        async def deactivate(self):
            await asyncio.gather(*(p.deactivate() for p in self._providers))

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

            async def activate(self, automaton_run_id: str, ctx: '_Runtime.Context'):
                self._last_run_id = automaton_run_id
                self._create_file(automaton_run_id)
                self._active_event.set()

                self._task_group = [
                    asyncio.create_task(self._state_sampler(ctx)),
                    asyncio.create_task(self._watch_for_dump_event()),
                ]

            async def deactivate(self):
                self._active_event.clear()

                for task in self._task_group:
                    task.cancel()

                await asyncio.gather(*self._task_group, return_exceptions=True)
                self._dump_samples()

            async def _state_sampler(self, ctx: '_Runtime.Context'):
                next_sample_time = ctx.clock.get_elapsed_time_active() + self._sampling_rate

                try:
                    while self._active_event.is_set():
                        now = ctx.clock.get_elapsed_time_active()
                        await asyncio.sleep(max(0, next_sample_time - now))

                        sample = self._get_state_sample(ctx)
                        self._samples.append([ctx.clock.get_elapsed_time_active(), sample])
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

            def _create_file(self, automaton_run_id: str):
                os.makedirs(self._output_dir, exist_ok=True)
                self._file_path = os.path.join(
                    self._output_dir,
                    f"{self._name}.{self.FILE_EXTENSION}",
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

            def _get_state_sample(self, ha) -> Any:
                raise NotImplementedError
            
        class ContinuousStateSampler(BaseStateSampler):
            def _get_state_sample(self, ctx: '_Runtime.Context'):
                return ctx.continuous_state.latest()

        class AuxiliaryStateSampler(BaseStateSampler):
            def _get_state_sample(self, ctx: '_Runtime.Context'):
                return ctx.auxiliary_states

        class ControlInputStateSampler(BaseStateSampler):
            def _get_state_sample(self, ctx: '_Runtime.Context'):
                return ctx.control_input_states
              
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

        def is_samplers(self) -> bool: 
            return len(self._samplers) > 0

        async def activate(self, automaton_run_id: str, ctx: '_Runtime.Context'):
            await asyncio.gather(
                *(s.activate(automaton_run_id, ctx) for s in self._samplers)
            )

        async def deactivate(self):
            await asyncio.gather(*(s.deactivate() for s in self._samplers))

    # =========================================================================
    # RUNTIME INITIALIZATION
    # =========================================================================
    
    def __init__(
            self,
            *,
            definition: _Definition,
            integration_fnc: Optional[callable] = None
    ): 
        self._active_event = asyncio.Event()

        self._automaton_definition: _Definition = definition
        self._discrete_state: State = self._automaton_definition.state_t0 
        
        self._integration_fnc = integration_fnc
        
        self._ctx: _Runtime.Context = None
        self._xdot: List = None
    
    # =========================================================================
    # EVALUATION STEP
    # =========================================================================
    
    def _evaluation_step(self, logger: Logger, runtime_context: Context) -> EvalStepResult:
        """
        Perform one timestep evaluation of the hybrid automaton.
        
        Returns:
            EvalStepResult: Result code, severity, and message
        """
        try: 
            # ---------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # ---------------------------------------------------------
            try:
                xdot = runtime_context.discrete_state.continuous_dynamics(
                    ctx=runtime_context
                )
            except Exception as e:
                return _Runtime.EvalStepResult( 
                    code=_Runtime.StepResultCode.CONTINUOUS_FLOW_ERROR,
                    severity=_Runtime.StepSeverity.ERROR,
                    message=f"Continuous flow exception in mode '{runtime_context.discrete_state.name}': {str(e)}"
                )

            if runtime_context.configuration['should_integrate'] and (xdot is not None) and (runtime_context.continuous_state.x0 is not None):
                try:
                    runtime_context.continuous_state.integrate(xdot, runtime_context.clock.get_dt())
                except Exception as e: 
                    return _Runtime.EvalStepResult(
                        code=_Runtime.StepResultCode.INTEGRATION_ERROR,
                        severity=_Runtime.StepSeverity.ERROR,
                        message=f"Integration exception in mode '{runtime_context.discrete_state.name}': {str(e)}"
                    ) 
            
            # ---------------------------------------------------------
            # 2️⃣ Guard transitions
            # ---------------------------------------------------------
            try:
                guard_evaluations = runtime_context.discrete_state.evaluate_transitions(
                    ctx=runtime_context
                )
                active_guards = [item[0] for item in guard_evaluations if item[1] is True]
                error_guards = [[item[0], item[2]] for item in guard_evaluations if item[2] is not None]
                
                if error_guards and len(error_guards) >= len(active_guards):
                    logger.WARNING("GUARD WARNING", f"guard evaluation exceptions occured - automaton may be stuck")
                     
                if error_guards:
                    for g in error_guards:
                        logger.WARNING("Guard Evaluation", f"Guard '{g[0].name}' raised exception: {g[1]}")
                        
            except Exception as e:
                return _Runtime.EvalStepResult( 
                    code=_Runtime.StepResultCode.GUARD_EVALUATION_ERROR, 
                    severity=_Runtime.StepSeverity.ERROR,
                    message=f"Guard evaluation error in mode '{runtime_context.discrete_state.name}': {str(e)}"
                )
            
            if active_guards:
                try:
                    old_mode = runtime_context.discrete_state.name
                    
                    # Select highest priority transition
                    transition: Transition = min(active_guards, key=lambda t: t.priority)

                    # Execute transition
                    new_mode, new_ctx = transition.execute(ctx=runtime_context)
                    runtime_context = new_ctx
                    runtime_context.clock.ping_transition()
                    runtime_context.transitions_count += 1

                    # Exit callback
                    if runtime_context.discrete_state.on_exit:
                        runtime_context.discrete_state.on_exit()

                    # Update state
                    runtime_context.discrete_state = new_mode

                    # Entry callback
                    if new_mode.on_enter:
                        new_mode.on_enter()
                    
                    return _Runtime.EvalStepResult(
                        code=_Runtime.StepResultCode.TRANSITION,
                        severity=_Runtime.StepSeverity.OK,
                        message=f"'{old_mode}' --[{transition.name}]--> '{new_mode.name}'"
                    )
                except Exception as e: 
                    return _Runtime.EvalStepResult( 
                        code=_Runtime.StepResultCode.TRANSITION_ERROR, 
                        severity=_Runtime.StepSeverity.ERROR,
                        message=f"Transition execution error: {str(e)}"
                    )

            # ---------------------------------------------------------
            # 3️⃣ No transition → invariant check
            # ---------------------------------------------------------
            try:
                invariant_holds = runtime_context.discrete_state.check_invariants(
                    ctx=runtime_context
                )
            except Exception as e: 
                return _Runtime.EvalStepResult(
                    code=_Runtime.StepResultCode.INVARIANT_VIOLATION,
                    severity=_Runtime.StepSeverity.ERROR, 
                    message=f"Invariant check exception in mode '{runtime_context.discrete_state.name}': {str(e)}"
                )

            if invariant_holds:
                return _Runtime.EvalStepResult(
                    code=_Runtime.StepResultCode.NORMAL,
                    severity=_Runtime.StepSeverity.OK
                )
            elif not invariant_holds and runtime_context.discrete_state._is_final:
                return _Runtime.EvalStepResult(
                    code=_Runtime.StepResultCode.TERMINAL_REACHED, 
                    severity=_Runtime.StepSeverity.OK,
                    message=f"Terminal state '{runtime_context.discrete_state.name}' reached"
                )
            else: 
                return _Runtime.EvalStepResult(
                    code=_Runtime.StepResultCode.INVARIANT_VIOLATION, 
                    severity=_Runtime.StepSeverity.ERROR,
                    message=f"Invariant violated in mode '{runtime_context.discrete_state.name}' with no valid transition available"
                )
                
        except Exception as e: 
            return _Runtime.EvalStepResult(
                code=_Runtime.StepResultCode.INVARIANT_VIOLATION,
                severity=_Runtime.StepSeverity.FATAL,
                message=f"Unexpected fatal exception during evaluation: {str(e)}"
            )
        
    # =========================================================================
    # MAIN RUN LOOP
    # =========================================================================
    
    async def _run(self, logger: Logger, run_context: Context) -> RunResult:
        """
        Main worker for running the automaton asynchronously.

        Handles evaluation steps, state transitions, timeouts, and real-time or simulation clocks.
        Ensures proper cleanup of all tasks and sets RunResult appropriately.
        """
        run_result = _Runtime.RunResult()
        start_time = time.perf_counter()

        clock_task = asyncio.create_task(run_context.clock.activate())

        try:
            while run_context.status is _Runtime.Context.Status.ACTIVE:
                # Check for external termination events
                if run_context.events.timeout_event.is_set():
                    logger.WARNING("TIMEOUT", f"Exceeded {run_context.clock._timeout_sec:.3f}s")
                    run_result.status = _Runtime.RunStatus.TIMEOUT
                    run_result.termination_code = _Runtime.StepResultCode.CANCELLED
                    run_result.termination_message = "Timeout exceeded"
                    self._active_event.clear()
                    break
                    
                if run_context.events.deactivate_event.is_set():
                    logger.INFO("MANUAL_STOP", "Automaton stopped by client")
                    run_result.status = _Runtime.RunStatus.SUCCESS
                    run_result.termination_code = _Runtime.StepResultCode.CANCELLED
                    run_result.termination_message = "Manually cancelled"
                    self._active_event.clear()
                    break
                
                # Evaluate step
                step_result: _Runtime.EvalStepResult = self._evaluation_step(
                    logger=logger, 
                    runtime_context=run_context
                )
                
                # Update statistics
                run_context.total_steps += 1
                step_code_name = step_result.code.name
                run_context.step_counts[step_code_name] = run_context.step_counts.get(step_code_name, 0) + 1

                # Handle step result
                if step_result.severity == _Runtime.StepSeverity.OK:
                    if step_result.code == _Runtime.StepResultCode.TRANSITION:
                        logger.INFO("Transition", step_result.message)
                    elif step_result.code == _Runtime.StepResultCode.TERMINAL_REACHED:
                        logger.INFO("Terminal", step_result.message)
                        run_result.status = _Runtime.RunStatus.SUCCESS
                        run_result.termination_code = step_result.code
                        run_result.termination_message = step_result.message
                        self._active_event.clear()
                        run_context.events.terminal_reached_event.set()
                        break
                        
                elif step_result.severity == _Runtime.StepSeverity.WARNING:
                    logger.WARNING(step_result.code.name, step_result.message)
                    
                elif step_result.severity == _Runtime.StepSeverity.ERROR:
                    logger.ERROR(step_result.code.name, step_result.message)
                    run_result.status = _Runtime.RunStatus.FAILURE
                    run_result.termination_code = step_result.code
                    run_result.termination_message = step_result.message
                    self._active_event.clear()
                    run_context.events.error_event.set()
                    break
                    
                elif step_result.severity == _Runtime.StepSeverity.FATAL:
                    logger.FATAL(step_result.code.name, step_result.message)
                    run_result.status = _Runtime.RunStatus.FAILURE
                    run_result.termination_code = step_result.code
                    run_result.termination_message = f"FATAL: {step_result.message}"
                    self._active_event.clear()
                    run_context.events.fatal_event.set()
                    break

                # Advance clock
                if run_context.clock.is_real_time():
                    await run_context.clock.sleep_for_dt()
                else:
                    run_context.clock.step_dt()
                    await asyncio.sleep(0.001)

        except asyncio.CancelledError:
            logger.WARNING("Cancelled", "Run cancelled externally")
            run_result.status = _Runtime.RunStatus.FAILURE
            run_result.termination_code = _Runtime.StepResultCode.CANCELLED
            run_result.termination_message = "Externally cancelled"
            self._active_event.clear()
            raise
            
        except Exception as e:
            logger.FATAL("Runtime Exception", str(e))
            run_result.status = _Runtime.RunStatus.FAILURE
            run_result.termination_code = _Runtime.StepResultCode.CONTINUOUS_FLOW_ERROR
            run_result.termination_message = f"Unexpected exception: {str(e)}"
            self._active_event.clear()
            run_context.events.fatal_event.set()
            
        finally:
            # Cleanup clock
            if clock_task and not clock_task.done():
                clock_task.cancel()
                try:
                    await clock_task
                except (asyncio.CancelledError, Exception):
                    pass
            
            # Populate final results
            run_result.total_runtime_sec = time.perf_counter() - start_time
            run_result.total_steps = run_context.total_steps
            run_result.transitions_count = run_context.transitions_count
            run_result.step_statistics = run_context.step_counts
            run_result.final_discrete_state = run_context.discrete_state.name
            run_result.final_continuous_state = run_context.continuous_state.latest() if run_context.continuous_state else None

        return run_result
    
    # =========================================================================
    # ACTIVATION
    # =========================================================================
        
    async def activate(
        self,
        *,
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
        control_input_states_samples_per_write: Optional[int] = 1000,
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
        
        # Setup
        run_signature = _Runtime.Signature(
            automaton_definition=self._automaton_definition,
            timeout_sec=timeout_sec,
            delta_time=delta_time,
            real_time_mode_enabled=enable_real_time_mode,
            should_integrate=enable_self_integration
        )
        
        run_context = _Runtime.Context(
            initial_state=self._automaton_definition.state_t0,
            initial_continuous_state=initial_continuous_state,
            initial_auxiliary_states=initial_auxiliary_states,
            initial_control_input_states=initial_control_input_states,
            real_time_mode=enable_real_time_mode,
            delta_time=delta_time,
            timeout_sec=timeout_sec,
            configuration=self._automaton_definition._configuration,
            should_integrate=enable_self_integration
        )
        self._ctx = run_context
         
        run_logger = _Runtime.Logger(
            automaton_definition=self._automaton_definition,
            run_signature=run_signature,
            run_context=run_context,
            should_write_logs_to_file=should_write_logs,
            log_dir=output_dir,
            file_name="temporal_automaton.log"
        )
        
        state_samplers = _Runtime.StateSamplers(
            continuous_enabled=continuous_state_sampler_enabled,
            continuous_sample_rate=continuous_state_sampler_rate,
            continuous_samples_per_write=continuous_state_sampler_samples_per_write,
            auxiliary_enabled=auxiliary_states_sampler_enabled,
            auxiliary_sample_rate=auxiliary_states_sampler_rate,
            auxiliary_samples_per_write=auxiliary_states_sampler_samples_per_write,
            control_enabled=control_input_states_sampler_enabled,
            control_sample_rate=control_input_states_sampler_rate,
            control_samples_per_write=control_input_states_samples_per_write,
            output_dir=output_dir
        )
        
        state_providers = _Runtime.StateProviders(
            continuous_fn=continuous_state_provider,
            continuous_update_rate=continuous_state_provision_rate,
            auxiliary_fn=auxiliary_states_provider,
            auxiliary_update_rate=auxiliary_states_provision_rate,
            control_fn=control_input_states_provider,
            control_update_rate=control_input_states_provision_rate 
        )
        
        try:
            # Activate automaton
            run_logger.INFO("ACTIVATION", "automaton activated")
            self._automaton_definition.on_entry()
            self._active_event.set()
            
            # Activate samplers and providers (starts background tasks)
            if state_samplers.is_samplers():
                await state_samplers.activate(
                    automaton_run_id=run_signature.run_id,
                    ctx=run_context
                )
            
            if state_providers.is_providers():
                await state_providers.activate(ctx=run_context)
            
            # Run the main automaton loop
            run_result: _Runtime.RunResult = await self._run(
                logger=run_logger, 
                run_context=run_context
            )
            run_result.run_signature = run_signature
            run_result.run_logs_dir_path = output_dir
            
            # CRITICAL: Deactivate samplers/providers (triggers final dump)
            if state_samplers.is_samplers():
                await state_samplers.deactivate()
            
            if state_providers.is_providers():
                await state_providers.deactivate()
            self._ctx = None
            
            # Final cleanup
            run_logger.INFO("DEACTIVATION", f"automaton deactivated - {run_result.status.name}")
            self._automaton_definition.on_exit()
            
            return run_result
            
        except Exception as e:
            run_logger.FATAL("Activation Error", str(e))
            # Ensure cleanup on error
            try:
                if state_samplers.is_samplers():
                    await state_samplers.deactivate()
                if state_providers.is_providers():
                    await state_providers.deactivate()
            except Exception:
                pass
            raise
        
    def deactivate(self): 
        """Request deactivation of the automaton"""
        if self._ctx: # TODO: Need to fixure out a way to share context because currently this does not work
            self._ctx.events.deactivate_event.set()
        self._active_event.clear()