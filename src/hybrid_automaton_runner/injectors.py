"""Injector classes for hybrid automaton simulations."""
import asyncio
from typing import Callable, Dict
import numpy as np
from hybrid_automaton import Automaton


class Injector: 
    def __init__(self, fn: Callable[[], Dict[str, np.ndarray]], update_rate: float = 0.001):
        """
        Initialize auxiliary state injector.
        
        Args:
            fn: Function that returns the updated state for injectable.
            update_rate: Rate at which to inject updates (seconds)
        """
        self.fn = fn
        self.update_rate = update_rate

    async def inject(self, ha: Automaton):
        raise NotImplementedError("Inject method must be implemented by subclasses.")

class ContinuousStateInjector(Injector):
    """Injects continuous state updates for open-loop operation."""
    
    async def inject(self, ha: Automaton):
        """Continuously inject state updates while automaton is active."""
        while ha._runtime and ha._runtime._active:
            try:
                new_state = self.fn()
                ha.set_runtime_continuous_state(new_state)
            except Exception as e:
                print(f"State injection error: {e}")
                break
            
            await asyncio.sleep(self.update_rate)

class AuxiliaryStateInjector(Injector):
    """Injects auxiliary state updates for open-loop operation."""
   
    async def inject(self, ha: Automaton):
        """Continuously inject auxiliary state updates while automaton is active."""
        while ha._runtime and ha._runtime._active:
            try:
                new_aux_state = self.fn()
                ha.set_runtime_auxiliary_continuous_states(new_aux_state)
            except Exception as e:
                print(f"Auxiliary state injection error: {e}")
                break
            
            await asyncio.sleep(self.update_rate)

class ControlInputInjector(Injector):
    """Injects control input updates for open-loop operation."""

    async def inject(self, ha: Automaton):
        """Continuously inject control input updates while automaton is active."""
        while ha._runtime and ha._runtime._active:
            try:
                new_control = self.fn()
                ha.set_runtime_control_inputs(new_control)
            except Exception as e:
                print(f"Control input injection error: {e}")
                break
            
            await asyncio.sleep(self.update_rate)