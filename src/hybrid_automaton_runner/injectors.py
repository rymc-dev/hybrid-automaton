"""Injector classes for hybrid automaton simulations."""
import asyncio
from typing import Callable, Dict
import numpy as np
from hybrid_automaton import Automaton


class ContinuousStateInjector:
    """Injects continuous state updates for open-loop operation."""
    
    def __init__(self, state_fn: Callable[[], np.ndarray], update_rate: float = 0.001):
        """
        Initialize injector.
        
        Args:
            state_fn: Function that returns updated continuous state
            update_rate: Rate at which to inject state updates (seconds)
        """
        self.state_fn = state_fn
        self.update_rate = update_rate
    
    async def inject(self, ha: Automaton):
        """Continuously inject state updates while automaton is active."""
        while ha._runtime and ha._runtime._active:
            try:
                new_state = self.state_fn()
                ha.set_continous_state(new_state)
            except Exception as e:
                print(f"State injection error: {e}")
                break
            
            await asyncio.sleep(self.update_rate)


class AuxiliaryStateInjector:
    """Injects auxiliary state updates for open-loop operation."""
    
    def __init__(self, aux_state_fn: Callable[[], Dict[str, np.ndarray]], update_rate: float = 0.001):
        """
        Initialize auxiliary state injector.
        
        Args:
            aux_state_fn: Function that returns updated auxiliary states as dict
            update_rate: Rate at which to inject updates (seconds)
        """
        self.aux_state_fn = aux_state_fn
        self.update_rate = update_rate
    
    async def inject(self, ha: Automaton):
        """Continuously inject auxiliary state updates while automaton is active."""
        while ha._runtime and ha._runtime._active:
            try:
                new_aux_state = self.aux_state_fn()
                ha.set_auxilary_continous_states(new_aux_state)
            except Exception as e:
                print(f"Auxiliary state injection error: {e}")
                break
            
            await asyncio.sleep(self.update_rate)


class ControlInputInjector:
    """Injects control input updates for open-loop operation."""
    
    def __init__(self, control_fn: Callable[[], Dict[str, np.ndarray]], update_rate: float = 0.001):
        """
        Initialize control input injector.
        
        Args:
            control_fn: Function that returns updated control inputs as dict
            update_rate: Rate at which to inject updates (seconds)
        """
        self.control_fn = control_fn
        self.update_rate = update_rate
    
    async def inject(self, ha: Automaton):
        """Continuously inject control input updates while automaton is active."""
        while ha._runtime and ha._runtime._active:
            try:
                new_control = self.control_fn()
                ha.set_control_input(new_control)
            except Exception as e:
                print(f"Control input injection error: {e}")
                break
            
            await asyncio.sleep(self.update_rate)