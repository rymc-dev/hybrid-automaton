""" 
metrics for calculating mode occupancy for analysis of an automaton
these metrics enable evaluation of time spent in each mode, 
fraction of mission in each mode
number of visits per mode

"""

from hybrid_automaton import RunResult
import os
from typing import List

from typing import List, Tuple, Dict
from collections import Counter


def extract_mode_transitions(run_result: RunResult) -> List[Tuple[str, float]]:
    """
    Extract discrete state changes with their exact timestamps.
    
    Returns:
        List of tuples (mode, timestamp) representing each state transition.
        Example: [('FLYING', 0.0), ('GROUND', 1.641), ('FLYING', 1.642), ...]
    """
    mode_transitions = []
    
    with open(os.path.join(run_result.run_logs_dir_path, 'temporal_automaton.log'), 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('#   Initial mode:'):
                mode = line.split(':')[1].strip()
                mode_transitions.append((mode, 0.0))
            
            if line.find("[Transition]") != -1:
                mode = line.split('>')[1].strip().replace("'", "")
                timestamp = float(line.split('[')[2].split(']')[0])
                mode_transitions.append((mode, timestamp))
    
    return mode_transitions

def time_spent_in_each_mode(run_result: RunResult) -> Dict[str, float]:
    """Calculate total time spent in each mode."""
    mode_events = []
    with open(os.path.join(run_result.run_logs_dir_path, 'temporal_automaton.log'), 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('#   Initial mode:'):
                mode_events.append((line.split(':')[1].strip(), 0.0))
            if line.find("[Transition]") != -1:
                mode = line.split('>')[1].strip().replace("'", "")
                time = float(line.split('[')[2].split(']')[0])
                mode_events.append((mode, time))
    
    # Calculate time spent in each mode
    time_in_mode = {}
    for i in range(len(mode_events) - 1):
        mode, start_time = mode_events[i]
        next_time = mode_events[i + 1][1]
        duration = next_time - start_time
        time_in_mode[mode] = time_in_mode.get(mode, 0) + duration
    
    return time_in_mode
    
def fraction_of_mission_in_each_mode(run_result: RunResult) -> Dict[str, float]:
    """
    Calculate the fraction of total mission time spent in each mode.
    
    Returns:
        Dictionary mapping mode names to fraction of total time (0.0 to 1.0).
        Example: {'FLYING': 0.643, 'GROUND': 0.357}
    """
    time_in_mode = time_spent_in_each_mode(run_result)
    total_time = sum(time_in_mode.values())
    
    if total_time == 0:
        return {mode: 0.0 for mode in time_in_mode.keys()}
    
    return {mode: duration / total_time for mode, duration in time_in_mode.items()}

def number_of_visits_per_mode(run_result: RunResult) -> Dict[str, int]:
    """
    Count the number of times each mode is visited.
    
    Returns:
        Dictionary mapping mode names to visit count.
        Example: {'FLYING': 3, 'GROUND': 3}
    """
    mode_transitions = extract_mode_transitions(run_result)
    modes = [mode for mode, _ in mode_transitions]
    
    return dict(Counter(modes))

    
if __name__ == '__main__':
    run_results = RunResult(run_logs_dir_path="/home/ryan/hybrid-automaton/log_hybrid_automaton/bouncing_ball")
    print (time_spent_in_each_mode(run_results))
    print (extract_mode_transitions(run_results))
    print (fraction_of_mission_in_each_mode(run_results))
    print (number_of_visits_per_mode(run_results)) 