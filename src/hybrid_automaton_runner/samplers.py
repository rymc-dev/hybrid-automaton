"""Data collectors for hybrid automaton state monitoring."""
import asyncio
from typing import List, Any, Optional
from hybrid_automaton import Automaton
import os
import csv
import json
import numpy as np
import sys

# TODO: should have a function for run 

class StateSampler:
    """Base class for state collectors."""
    FILE_EXTENSION = "csv"
    _last_automaton_run_id_sampled: str = None
    _last_automaton_run_id_sampled_time_complete: int = None
    _last_automaton_run_id_sampled: int = None
    output_dir = "./log_hybrid_automaton"
     
    def _create_file(self, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True) 
        with open(file_path, "w") as f: 
            writer = csv.writer(f)
            writer.writerow(["timestamp", "state"])
    
    def __init__(
        self, 
        sampling_rate: float = 0.01,
        file_name: str = "state",
        samples_per_write: int = 1000
    ):
        """
        Args:
            sampling_rate: Time between samples in seconds (default 0.01 = 100 Hz)
        """
        self._file_name = file_name
        
        self._file_path = os.path.join(self.output_dir, f"{file_name}.{self.FILE_EXTENSION}")
        self._sampling_rate = sampling_rate
        self._samples_per_write = samples_per_write
        self._samples_collected = 0
        self._samples: List[List[Any]] = []
        
        self._dump_samples_event = asyncio.Event()
        self._active_event = asyncio.Event()
        
        self._create_file(self._file_path)        

    async def activate(self, automaton_run_id: str, ha: Automaton):
        
        try: 
            self._active_event.set() 
            await asyncio.gather(
                self._state_sampler(ha),        # call the coroutine
                self._watch_for_state_dump_event()  # another coroutine or awaitable
            )
        except asyncio.CancelledError():
            pass
        finally:
            self._post_run_hook(automaton_run_id)
    
    def _post_run_hook(self, automaton_run_id): 
        self._dump_samples()
        self._samples = 0
        self._last_automaton_run_id_sampled = automaton_run_id 
        
    async def deactivate(self): 
        self._active_event.clear()

    async def _state_sampler(self, ha: Automaton):
        try:
            next_sample_time = ha.get_runtime_time_elapsed() + self._sampling_rate

            while self._active_event.is_set():
                now = ha.get_runtime_time_elapsed()
                drift = max(0, next_sample_time - now)
                await asyncio.sleep(drift)

                if not self._dump_samples_event.is_set():
                    state_data = self._get_state_sample(ha)
                    self._samples.append([ha.get_runtime_time_elapsed(), state_data])
                    self._samples_collected += 1

                    if self._samples_collected >= self._samples_per_write:
                        self._dump_samples_event.set()

                # schedule next sample
                next_sample_time += self._sampling_rate

        except asyncio.CancelledError:
            print("State sampler cancelled")
            raise
        except Exception as e:
            print(f"State sampler exception: {e}")

                
    def _get_state_sample(self, ha: Automaton) -> Any: 
        raise NotImplementedError("Collect method must be implemented by subclasses.")
    
    async def _watch_for_state_dump_event(self):
        """
        Coroutine that watches for the dump-to-file event indefinitely.
        When _dump_samples_event is set, writes current samples to file 
        and clears the event.
        """
        try:
            while self._active_event.is_set():
                # Wait until _dump_samples_event is set or task is cancelled
                await self._dump_samples_event.wait()

                # Dump samples to file
                self._dump_samples()

                # Clear the event for next round
                self._dump_samples_event.clear()

        except asyncio.CancelledError as e:
            # Handle graceful cancellation
            raise e
            
    def _dump_samples(self):
        def to_serializable(obj):
            """Recursively convert np arrays to lists so JSON can handle them."""
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: to_serializable(v) for k, v in obj.items()}
            else:
                return obj

        # append data from samples to file
        with open(self._file_path, "a", newline="") as f:
            writer = csv.writer(f)
            for timestamp, state in self._samples:
                writer.writerow([str(timestamp), json.dumps(to_serializable(state))])
        
        # clear data in struct 
        self._samples.clear() 
       
    def is_active(self):
        return True if self._active_event.is_set() else False
           
    def get_sampler_metadata(self) -> json:
        """return metadata regarding the sampler, including previous run ID, time, file_path associated with it"""
        return json.dump({
            'file_path': f'{self._file_path}',
            'last_automaton_run_id_sampled': f'{self._last_automaton_run_id_sampled}' 
        })     
    
class ContinuousStateSampler(StateSampler):
    """Collects continuous states over time."""
    
    def __init__(self, sampling_rate = 0.01, samples_per_write = 1000):
        super().__init__(sampling_rate, "continuous_state", samples_per_write)
    
    def _get_state_sample(self, ha: Automaton):
        """Collect continuous states from hybrid automaton."""
        try:
            return ha.get_runtime_continuous_state().latest()
        except Exception as e:
            return None

class AuxiliaryStateSampler(StateSampler):
    """Collects auxiliary states over time."""

    def __init__(self, sampling_rate = 0.01, samples_per_write = 1000):
        super().__init__(sampling_rate, "auxiliary_state", samples_per_write)
    
    def _get_state_sample(self, ha: Automaton):
        """
        Collect auxiliary states from hybrid automaton.
        
        Args:
            ha: Hybrid automaton instance
            get_auxiliary_fn: Optional function to get auxiliary state
        """
        try:
            return ha.get_runtime_auxiliary_state()
        except Exception as e: 
            return None

class ControlInputStateSampler(StateSampler):
    """Collects control inputs over time."""
    
    def __init__(self, sampling_rate = 0.01, samples_per_write = 1000):
        super().__init__(sampling_rate, "control_input_state", samples_per_write)
        
    def _get_state_sample(self, ha: Automaton):
        try:
            return ha.get_runtime_control_input().latest()
        except Exception as e: 
            return None

# class AutomatonCoreStateSampler(StateSampler):
#     """
#     collects core state data from the automaton run
#     This includes: 
#         discrete state/mode
#         time
        
#     """
    
#     def __init__(self, sampling_rate = 0.01, samples_per_write = 1000):
#         super().__init__(sampling_rate, "automaton_core_states", samples_per_write)
    
#     def _get_state_sample(self, ha: Automaton):
#         """Collect automaton states from hybrid automaton."""
#         return {
#             "discrete state/mode: ": ha.get_runtime_active_discrete_state()[1], 
#         }