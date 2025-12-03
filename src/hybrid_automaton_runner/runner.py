"""Main runner class for hybrid automaton simulations."""
import asyncio
import numpy as np
from typing import Optional, Dict, Any
from .collectors import (
    ContinuousStateCollector,
    AuxiliaryStateCollector,
    ControlInputCollector,
    AutomatonStateCollector,
    TransitionTimeCollector
)
from .utils import deactivate_after_timeout
from hybrid_automaton import Automaton


class AutomatonRunner:
    """Runner for hybrid automaton with data collection."""
    
    def __init__(self, hybrid_automaton: Automaton, sampling_rate: float = 0.01):
        """
        Initialize runner.
        
        Args:
            hybrid_automaton: The hybrid automaton instance to run
            sampling_rate: Sampling rate for data collection in seconds (default 0.01 = 100 Hz)
        """
        self.ha = hybrid_automaton
        self.sampling_rate = sampling_rate
        
        # Initialize collectors
        self.continuous_collector = ContinuousStateCollector(sampling_rate)
        self.auxiliary_collector = AuxiliaryStateCollector(sampling_rate)
        self.control_collector = ControlInputCollector(sampling_rate)
        self.automaton_collector = AutomatonStateCollector(sampling_rate)
        self.transition_collector = TransitionTimeCollector(sampling_rate)
        
        self._tasks = []
    
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
        inject_continuous: bool = False,  # NEW
        inject_auxiliary: bool = False,   # NEW
        inject_control: bool = False,     # NEW
        continuous_state_fn: Optional[callable] = None,
        auxiliary_fn: Optional[callable] = None,
        control_fn: Optional[callable] = None,
        injector_update_rate: float = 0.001,
    ) -> Dict[str, Any]:
        """
        Run the hybrid automaton simulation with data collection and/or injection.
        
        Args:
            x0: Initial continuous state
            aux_x0: Initial auxiliary continuous state
            u0: Initial control input state 
            duration: Simulation duration in seconds
            real_time_mode: Whether to run in real-time
            integrate: Whether to integrate continuous dynamics
            dt: Integration time step
            
            # Collection flags
            collect_continuous: Collect continuous states
            collect_auxiliary: Collect auxiliary states
            collect_control: Collect control inputs
            collect_automaton: Collect automaton discrete states
            collect_transitions: Collect time since transitions
            
            # Injection flags (for open-loop operation)
            inject_continuous: Inject continuous state updates from continuous_state_fn
            inject_auxiliary: Inject auxiliary state updates from auxiliary_fn
            inject_control: Inject control input updates from control_fn
            
            # Functions (dual-purpose: collection OR injection)
            continuous_state_fn: Function to get/provide continuous state
                                - For collection: () -> Any (samples external state)
                                - For injection: () -> np.ndarray (provides state to automaton)
            auxiliary_fn: Function to get/provide auxiliary state
                        - For collection: () -> Any
                        - For injection: () -> Dict[str, np.ndarray]
            control_fn: Function to get/provide control input
                    - For collection: () -> Any
                    - For injection: () -> Dict[str, np.ndarray]
            
            injector_update_rate: Update rate for injectors (seconds)
        
        Returns:
            Dictionary containing collected data
        """
        # Clear previous data
        self.clear_all_data()
        
        # Create tasks
        self._tasks = []
        
        # Main automaton task
        ha_task = asyncio.create_task(
            self.ha.activate(
                x0=x0, 
                aux_x0=aux_x0, 
                u0=u0, 
                real_time_mode=real_time_mode, 
                integrate=integrate, 
                dt=dt
            )
        )
        self._tasks.append(ha_task)
        
        # ============================================================
        # DATA COLLECTION TASKS (read from automaton)
        # ============================================================
        if collect_continuous:
            self._tasks.append(
                asyncio.create_task(self.continuous_collector.collect(self.ha))
            )
        
        if collect_auxiliary:
            self._tasks.append(
                asyncio.create_task(self.auxiliary_collector.collect(self.ha, auxiliary_fn))
            )
        
        if collect_control:
            self._tasks.append(
                asyncio.create_task(self.control_collector.collect(self.ha, control_fn))
            )
        
        if collect_automaton:
            self._tasks.append(
                asyncio.create_task(self.automaton_collector.collect(self.ha))
            )
        
        if collect_transitions:
            self._tasks.append(
                asyncio.create_task(self.transition_collector.collect(self.ha))
            )
        
        # ============================================================
        # DATA INJECTION TASKS (write to automaton)
        # ============================================================
        if inject_continuous:
            if continuous_state_fn is None:
                raise ValueError("inject_continuous=True requires continuous_state_fn")
            from .injectors import ContinuousStateInjector
            injector = ContinuousStateInjector(continuous_state_fn, injector_update_rate)
            self._tasks.append(
                asyncio.create_task(injector.inject(self.ha))
            )
        
        if inject_auxiliary:
            if auxiliary_fn is None:
                raise ValueError("inject_auxiliary=True requires auxiliary_fn")
            from .injectors import AuxiliaryStateInjector
            injector = AuxiliaryStateInjector(auxiliary_fn, injector_update_rate)
            self._tasks.append(
                asyncio.create_task(injector.inject(self.ha))
            )
        
        if inject_control:
            if control_fn is None:
                raise ValueError("inject_control=True requires control_fn")
            from .injectors import ControlInputInjector
            injector = ControlInputInjector(control_fn, injector_update_rate)
            self._tasks.append(
                asyncio.create_task(injector.inject(self.ha))
            )
        
        # Run with timeout
        await deactivate_after_timeout(duration, *self._tasks)
        
        # Return collected data
        return self.get_results()
        
    def get_results(self) -> Dict[str, Any]:
        """Get all collected data."""
        return {
            'continuous_states': self.continuous_collector.get_data(),
            'auxiliary_states': self.auxiliary_collector.get_data(),
            'control_inputs': self.control_collector.get_data(),
            'automaton_states': self.automaton_collector.get_data(),
            'transition_times': self.transition_collector.get_data(),
        }
        
    def clear_all_data(self):
        """Clear all collected data."""
        self.continuous_collector.clear()
        self.auxiliary_collector.clear()
        self.control_collector.clear()
        self.automaton_collector.clear()
        self.transition_collector.clear()
    
    def print_summary(self):
        """Print summary of collected data."""
        print(f"Collected {len(self.continuous_collector.data)} continuous state samples")
        print(f"Collected {len(self.auxiliary_collector.data)} auxiliary state samples")
        print(f"Collected {len(self.control_collector.data)} control input samples")
        print(f"Collected {len(self.automaton_collector.data)} automaton state samples")
        print(f"Collected {len(self.transition_collector.data)} transition time samples")