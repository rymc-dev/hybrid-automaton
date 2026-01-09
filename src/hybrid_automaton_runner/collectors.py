"""Data collectors for hybrid automaton state monitoring."""
import asyncio
from typing import List, Any, Optional
from hybrid_automaton import Automaton


class StateCollector:
    """Base class for state collectors."""
    
    def __init__(self, sampling_rate: float = 0.01):
        """
        Args:
            sampling_rate: Time between samples in seconds (default 0.01 = 100 Hz)
        """
        self.sampling_rate = sampling_rate
        self.data: List[List[Any]] = []
        
    async def collect(self, ha: Automaton): 
        raise NotImplementedError("Collect method must be implemented by subclasses.")
    
    def clear(self):
        """Clear collected data."""
        self.data.clear()
    
    def get_data(self):
        """Return collected data."""
        return self.data


class ContinuousStateCollector(StateCollector):
    """Collects continuous states over time."""
    
    async def collect(self, ha: Automaton):
        """Collect continuous states from hybrid automaton."""
        while True:
            await asyncio.sleep(self.sampling_rate)
            try:
                self.data.append([ha.get_runtime_time_elapsed(), ha.get_runtime_continuous_state().latest()])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in continuous state collector: {e}")


class AuxiliaryStateCollector(StateCollector):
    """Collects auxiliary states over time."""
    
    async def collect(self, ha: Automaton, get_auxiliary_fn: Optional[callable] = None):
        """
        Collect auxiliary states from hybrid automaton.
        
        Args:
            ha: Hybrid automaton instance
            get_auxiliary_fn: Optional function to get auxiliary state
        """
        while True:
            await asyncio.sleep(self.sampling_rate)
            try:
                aux_value = get_auxiliary_fn() if get_auxiliary_fn else None
                self.data.append([ha.get_runtime_time_elapsed(), aux_value])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in auxiliary state collector: {e}")


class ControlInputCollector(StateCollector):
    """Collects control inputs over time."""
    
    async def collect(self, ha: Automaton, get_control_fn: Optional[callable] = None):
        """
        Collect control inputs from hybrid automaton.
        
        Args:
            ha: Hybrid automaton instance
            get_control_fn: Optional function to get control input
        """
        while True:
            await asyncio.sleep(self.sampling_rate)
            try:
                control_value = get_control_fn() if get_control_fn else None
                self.data.append([ha.get_runtime_time_elapsed(), control_value])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in control input collector: {e}")


class AutomatonStateCollector(StateCollector):
    """Collects automaton discrete states over time."""
    
    async def collect(self, ha: Automaton):
        """Collect automaton states from hybrid automaton."""
        while True:
            await asyncio.sleep(self.sampling_rate)
            try:
                self.data.append([ha.get_runtime_time_elapsed(), ha.get_runtime_active_discrete_state()[1]])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in automaton state collector: {e}")


class TransitionTimeCollector(StateCollector):
    """Collects time since last transition over time."""
    
    async def collect(self, ha: Automaton):
        """Collect time since last transition from hybrid automaton."""
        while True:
            await asyncio.sleep(self.sampling_rate)
            try:
                self.data.append([
                    ha.get_runtime_active_discrete_state(),
                    ha.get_runtime_time_elapsed_since_transition()
                ])
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in transition time collector: {e}")