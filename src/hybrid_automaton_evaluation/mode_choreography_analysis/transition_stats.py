""" 
evaluation stats for transition statistics, transition counting be4tween modes,
 transition frequency per unit time
 and self loop detection (chattering detector (A -> B -> A))
"""

from typing import List, Tuple, Dict
from collections import defaultdict

from hybrid_automaton import RunResult
from hybrid_automaton_evaluation.mode_choreography_analysis.mode_occupancy import extract_mode_transitions

def transition_count_between_modes(run_result: RunResult) -> Dict[Tuple[str, str], int]:
    """
    Count transitions between each pair of modes.
    
    Returns:
        Dictionary mapping (from_mode, to_mode) tuples to transition count.
        Example: {('FLYING', 'GROUND'): 3, ('GROUND', 'FLYING'): 3}
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    transition_counts = defaultdict(int)
    for i in range(len(mode_transitions) - 1):
        from_mode = mode_transitions[i][0]
        to_mode = mode_transitions[i + 1][0]
        transition_counts[(from_mode, to_mode)] += 1
    
    return dict(transition_counts)


def transition_frequency_per_unit_time(run_result: RunResult) -> Dict[Tuple[str, str], float]:
    """
    Calculate transition frequency (transitions per second) between each pair of modes.
    
    Returns:
        Dictionary mapping (from_mode, to_mode) tuples to frequency (transitions/second).
        Example: {('FLYING', 'GROUND'): 0.599, ('GROUND', 'FLYING'): 0.599}
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    if len(mode_transitions) < 2:
        return {}
    
    # Get total mission time
    total_time = mode_transitions[-1][1] - mode_transitions[0][1]
    
    if total_time == 0:
        return {}
    
    # Get transition counts
    transition_counts = transition_count_between_modes(run_result)
    
    # Calculate frequency
    transition_frequency = {
        transition: count / total_time 
        for transition, count in transition_counts.items()
    }
    
    return transition_frequency


def self_loop_detection(run_result: RunResult, window: int = 2) -> List[Dict]:
    """
    Detect chattering: rapid transitions back to the same state (A -> B -> A pattern).
    
    Args:
        window: Number of transitions to look back (default 2 for A->B->A pattern)
    
    Returns:
        List of dictionaries containing chattering events with details.
        Example: [
            {
                'pattern': ('FLYING', 'GROUND', 'FLYING'),
                'timestamps': [1.641, 1.642],
                'duration': 0.001,
                'start_time': 1.641
            }
        ]
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    chattering_events = []
    
    # Look for A -> B -> A patterns
    for i in range(len(mode_transitions) - 2):
        mode_a = mode_transitions[i][0]
        mode_b = mode_transitions[i + 1][0]
        mode_c = mode_transitions[i + 2][0]
        
        time_a = mode_transitions[i][1]
        time_b = mode_transitions[i + 1][1]
        time_c = mode_transitions[i + 2][1]
        
        # Check if we return to the same mode (A -> B -> A)
        if mode_a == mode_c and mode_a != mode_b:
            chattering_events.append({
                'pattern': (mode_a, mode_b, mode_c),
                'timestamps': [time_a, time_b, time_c],
                'duration': time_c - time_a,
                'start_time': time_a,
                'intermediate_mode': mode_b
            })
    
    return chattering_events


# NOTE: a chattering_statistics() summary function (counts/total time/patterns on
# top of self_loop_detection above) is planned for a future release but not
# implemented yet.


if __name__ == '__main__':
    run_results = RunResult(run_logs_dir_path="./log_hybrid_automaton/bouncing_ball")

    print ('\n')
    print (transition_count_between_modes(run_result=run_results))
    print ('\n')
    print (transition_frequency_per_unit_time(run_result=run_results))
    print ('\n')
    print (self_loop_detection(run_result=run_results))
