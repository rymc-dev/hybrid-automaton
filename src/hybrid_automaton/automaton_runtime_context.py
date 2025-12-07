import numpy as np
from typing import Optional, Callable, List, Dict, Any
from .automaton_clock import Clock
from collections import deque
import time

import time
import numpy as np
from collections import deque
from typing import Callable, Optional


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

class Context: 
    
    def __init__(
        self,
        clk: Clock,
        x0: Optional[np.array] = None,
        aux0: Optional[Dict[str, np.array]] = {},
        u0: Optional[Dict[str, np.array]] = {},
        cfg: Optional[Dict[str, Any]] = {}
    ):
        self.clk: Clock = clk
        self.x: ContinuousState = ContinuousState(name='agent_state', x0=x0)
        self.aux: Dict[str, AuxiliaryState] = {k:AuxiliaryState(name=k, aux0=v) for k, v in aux0.items()} if aux0 is not None else {}
        self.u: Dict[str, ControlInput] = {k: ControlInput(name=k, u0=v) for k, v in u0.items()} if u0 is not None else {}
        self.cfg: Dict[str, Any] = cfg
