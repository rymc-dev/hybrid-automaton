from typing import List, Tuple, Dict, Set
from collections import defaultdict, Counter

from hybrid_automaton import RunResult
from hybrid_automaton_evaluation.mode_choreography_analysis import extract_mode_transitions, transition_stats 
from hybrid_automaton_evaluation.mode_choreography_analysis.transition_stats import transition_count_between_modes

def find_repeating_sequences(run_result: RunResult, min_length: int = 2, max_length: int = 5) -> Dict[Tuple[str, ...], int]:
    """
    Find repeating mode sequences of varying lengths.
    
    Args:
        min_length: Minimum sequence length to detect (default 2)
        max_length: Maximum sequence length to detect (default 5)
    
    Returns:
        Dictionary mapping mode sequences to their occurrence count.
        Example: {('FLYING', 'GROUND'): 3, ('FLYING', 'GROUND', 'FLYING'): 2}
    """
    mode_transitions = extract_mode_transitions(run_result)
    modes = [mode for mode, _ in mode_transitions]
    
    sequence_counts = defaultdict(int)
    
    for length in range(min_length, max_length + 1):
        for i in range(len(modes) - length + 1):
            sequence = tuple(modes[i:i + length])
            sequence_counts[sequence] += 1
    
    # Filter out sequences that only occur once
    return {seq: count for seq, count in sequence_counts.items() if count > 1}


def detect_periodic_behavior(run_result: RunResult, tolerance: float = 0.1) -> List[Dict]:
    """
    Detect periodic/cyclic behavior in mode transitions.
    
    Args:
        tolerance: Time tolerance for considering cycles periodic (seconds)
    
    Returns:
        List of detected periodic patterns with their properties.
        Example: [
            {
                'cycle': ('FLYING', 'GROUND'),
                'occurrences': 3,
                'periods': [1.814, 1.813, 1.454],
                'mean_period': 1.694,
                'is_periodic': True
            }
        ]
    """
    mode_transitions = extract_mode_transitions(run_result)
    modes = [mode for mode, _ in mode_transitions]
    times = [time for _, time in mode_transitions]
    
    # Find repeating sequences
    repeating = find_repeating_sequences(run_result, min_length=2, max_length=4)
    
    periodic_patterns = []
    
    for sequence, count in repeating.items():
        if count < 2:
            continue
        
        # Find all occurrences of this sequence
        periods = []
        last_occurrence_time = None
        
        for i in range(len(modes) - len(sequence) + 1):
            if tuple(modes[i:i + len(sequence)]) == sequence:
                current_time = times[i]
                if last_occurrence_time is not None:
                    periods.append(current_time - last_occurrence_time)
                last_occurrence_time = current_time
        
        if periods:
            mean_period = sum(periods) / len(periods)
            # Check if periods are consistent (periodic)
            is_periodic = all(abs(p - mean_period) <= tolerance for p in periods)
            
            periodic_patterns.append({
                'cycle': sequence,
                'occurrences': count,
                'periods': periods,
                'mean_period': mean_period,
                'std_dev': (sum((p - mean_period) ** 2 for p in periods) / len(periods)) ** 0.5 if len(periods) > 1 else 0.0,
                'is_periodic': is_periodic
            })
    
    return periodic_patterns


def longest_mode_sequence(run_result: RunResult) -> Dict[str, Dict]:
    """
    Find the longest continuous stay in each mode.
    
    Returns:
        Dictionary mapping mode names to their longest continuous duration.
        Example: {
            'FLYING': {'duration': 1.813, 'start_time': 1.642, 'end_time': 3.455},
            'GROUND': {'duration': 0.001, 'start_time': 1.641, 'end_time': 1.642}
        }
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    longest_stays = {}
    
    for i in range(len(mode_transitions) - 1):
        mode, start_time = mode_transitions[i]
        end_time = mode_transitions[i + 1][1]
        duration = end_time - start_time
        
        if mode not in longest_stays or duration > longest_stays[mode]['duration']:
            longest_stays[mode] = {
                'duration': duration,
                'start_time': start_time,
                'end_time': end_time
            }
    
    return longest_stays


def mode_transition_graph(run_result: RunResult) -> Dict[str, Set[str]]:
    """
    Build a directed graph of all possible mode transitions.
    
    Returns:
        Dictionary mapping each mode to the set of modes it can transition to.
        Example: {'FLYING': {'GROUND'}, 'GROUND': {'FLYING'}}
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    graph = defaultdict(set)
    
    for i in range(len(mode_transitions) - 1):
        from_mode = mode_transitions[i][0]
        to_mode = mode_transitions[i + 1][0]
        graph[from_mode].add(to_mode)
    
    return {mode: transitions for mode, transitions in graph.items()}


def average_dwell_time_per_mode(run_result: RunResult) -> Dict[str, float]:
    """
    Calculate average time spent per visit to each mode.
    
    Returns:
        Dictionary mapping mode names to average dwell time.
        Example: {'FLYING': 1.089, 'GROUND': 0.0003}
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    mode_durations = defaultdict(list)
    
    for i in range(len(mode_transitions) - 1):
        mode, start_time = mode_transitions[i]
        end_time = mode_transitions[i + 1][1]
        duration = end_time - start_time
        mode_durations[mode].append(duration)
    
    return {
        mode: sum(durations) / len(durations)
        for mode, durations in mode_durations.items()
    }


def transition_sequence_entropy(run_result: RunResult) -> float:
    """
    Calculate Shannon entropy of transition sequences to measure predictability.
    Higher entropy = more unpredictable transitions.
    Lower entropy = more regular/predictable pattern.
    
    Returns:
        Entropy value (bits). 0 = completely predictable, higher = more random.
    """
    import math
    
    transition_counts = transition_count_between_modes(run_result)
    total_transitions = sum(transition_counts.values())
    
    if total_transitions == 0:
        return 0.0
    
    entropy = 0.0
    for count in transition_counts.values():
        probability = count / total_transitions
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy


def detect_mode_oscillations(run_result: RunResult, max_cycle_length: int = 10) -> List[Dict]:
    """
    Detect oscillating patterns between modes (A->B->A->B... or A->B->C->A->B->C...).
    
    Args:
        max_cycle_length: Maximum length of oscillation cycle to detect
    
    Returns:
        List of detected oscillation patterns.
    """
    mode_transitions = extract_mode_transitions(run_result)
    modes = [mode for mode, _ in mode_transitions]
    
    oscillations = []
    
    for cycle_len in range(2, max_cycle_length + 1):
        for start_idx in range(len(modes)):
            # Check if we have enough modes left
            if start_idx + cycle_len * 2 > len(modes):
                break
            
            # Extract potential cycle
            potential_cycle = modes[start_idx:start_idx + cycle_len]
            
            # Count how many times it repeats
            repeat_count = 1
            idx = start_idx + cycle_len
            
            while idx + cycle_len <= len(modes):
                if modes[idx:idx + cycle_len] == potential_cycle:
                    repeat_count += 1
                    idx += cycle_len
                else:
                    break
            
            # If it repeats at least twice, it's an oscillation
            if repeat_count >= 2:
                oscillations.append({
                    'pattern': tuple(potential_cycle),
                    'start_index': start_idx,
                    'start_time': mode_transitions[start_idx][1],
                    'repetitions': repeat_count,
                    'total_length': cycle_len * repeat_count
                })
    
    return oscillations


if __name__ == '__main__':
    run_results = RunResult(run_logs_dir_path="/home/ryan/hybrid-automaton/log_hybrid_automaton/bouncing_ball")
    
    print("Repeating sequences:")
    print(find_repeating_sequences(run_results))
    print()
    
    print("Periodic behavior:")
    for pattern in detect_periodic_behavior(run_results):
        print(f"  Cycle: {pattern['cycle']}")
        print(f"  Mean period: {pattern['mean_period']:.3f}s")
        print(f"  Is periodic: {pattern['is_periodic']}")
        print()
    
    print("Longest mode sequences:")
    print(longest_mode_sequence(run_results))
    print()
    
    print("Mode transition graph:")
    print(mode_transition_graph(run_results))
    print()
    
    print("Average dwell time per mode:")
    print(average_dwell_time_per_mode(run_results))
    print()
    
    print("Transition sequence entropy:")
    print(f"{transition_sequence_entropy(run_results):.3f} bits")
    print()
    
    print("Mode oscillations:")
    for osc in detect_mode_oscillations(run_results):
        print(f"  Pattern: {osc['pattern']}")
        print(f"  Repetitions: {osc['repetitions']}")
        print()