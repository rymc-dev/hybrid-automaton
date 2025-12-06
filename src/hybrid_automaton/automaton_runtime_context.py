import numpy as np
from typing import Optional, Callable, List, Dict, Any
from .automaton_clock import Clock


class AuxiliaryState: 
    """auxiliary state wrapper class"""
    def __init__(self, name: str, state_t0: np.array, expected_dt: float = 0.1): 
        self.name = name
        self.state_t0 = state_t0
        self.state = self.state_t0

        self.avg_dt: float = expected_dt
        self.timestep: int = 0

    def set_auxiliary_state(self, aux_x: List): 
        self.state = aux_x
        # TODO: Calculate avg dt if in real time
        self.timestep += 1

class ContinousState: 
    """continous state representation"""
    _integration_function: Optional[Callable] = None

    def __init__(self, name: str, state_t0: np.array, expected_dt: float = 0.1): 
        self.name = name
        self.state_t0: np.array = state_t0
        self.state: np.array = self.state_t0

        self.avg_dt: float = expected_dt
        self.timestep: int = 0

    def set_continous_state(self, x: np.array):
        self.state = x
        # TODO: Timestamp and calc avg dt
        self.timestep += 1

    def get_continous_state(self) -> np.array:
        return self.state

    def integrate(self, xdot: np.array, dt: float): 
        if self._integration_function is not None: 
            self.set_continous_state(self._integration_function(self.state, xdot, dt))
        else: 
            self.set_continous_state(self.state + xdot * dt)

class ControlInput: 
    """control input represenation"""
    def __init__(self, name: str, state_t0: np.array): 
        self.name = name
        self.state_t0: np.array = state_t0
        self.state: np.array = self.state_t0

    def set_control_input(self, u: np.array): 
        self.state = u
    
    def get_control_input(self) -> np.array:
        return self.state

class Context: 
    
    def __init__(
        self,
        clk: Clock,
        x0: Optional[np.array] = np.array(),
        aux0: Optional[Dict[str, np.array]] = {},
        u0: Optional[Dict[str, np.array]] = {},
        cfg: Optional[Dict[str, Any]] = {}
    ):
        self.clk: Clock = clk
        self.x: ContinousState = ContinousState(name='agent_state', state_t0=x0)
        self.aux: Dict[str, AuxiliaryState] = {k:AuxiliaryState(name=k, state_t0=v) for k, v in aux0.items()} if aux0 is not None else {}
        self.u: Dict[str, ControlInput] = {k: ControlInput(name=k, state_t0=v) for k, v in u0.items()} if u0 is not None else {}
        self.cfg: Dict[str, Any] = cfg
