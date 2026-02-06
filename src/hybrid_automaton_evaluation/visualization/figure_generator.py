import matplotlib.pyplot as plt
from typing import List, Tuple, Dict
import numpy as np
from hybrid_automaton import RunResult
import os
import csv
from hybrid_automaton_evaluation.mode_choreography_analysis import extract_mode_transitions, time_spent_in_each_mode, number_of_visits_per_mode
from hybrid_automaton_evaluation.mode_choreography_analysis import self_loop_detection
from hybrid_automaton_evaluation.mode_choreography_analysis.transition_stats import transition_count_between_modes, extract_mode_transitions
import ast

def continuous_states_over_time_fig(run_result: RunResult): 
    """  
    
    Args: 
        continous_states: 
            ...
            
    Output:
        pyplot.figure
    """
    #TODO: Add checks for invalid contiuous_states input and state labels, currently
    #      assumes valid logic, if no continuous states are provided exception will be thrown
    
    
    timestamps = []
    states = []
    with open(os.path.join(run_result.run_logs_dir_path, "continuous_state.csv"), newline="") as f:
        reader = csv.reader(f)
        header = next(reader) 
        
        for timestamp_str, state_str in reader:
            timestamp = float(timestamp_str)
            state = ast.literal_eval(state_str)
            
            timestamps.append(timestamp)
            states.append(state)
            
    
    states = np.array(states)
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each dimension separately
    num_dimensions = states.shape[1]
    for i in range(num_dimensions):
        ax.plot(timestamps, states[:, i], label=f'x[{i}]')
    
    ax.set_title(
        f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Continuous State Over Time",
        fontsize=16,
        y=1.02
    )

    ax.set_xlabel("Time Elapsed (seconds)", fontsize=12)
    ax.set_ylabel("Continuous State", fontsize=12)
    # if state_labels is not None: # TODO: UPDATE THIS 
    #     ax.legend(state_labels)
    # else:
        # ax.legend() 
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    return fig

def auxiliary_states_over_time_fig(run_result: RunResult):
    """  
    
    Args: 
        auxilary_states: 
            ...
    """
    ...
     
def control_inputs_over_time_fig(control_inputs: List):
    """   
    Args: 
        control_inputs: 
            ...
    """
    ...

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from typing import List, Tuple, Dict
from hybrid_automaton import RunResult
import os

def mode_timeline_fig(run_result: RunResult):
    """
    Visualize mode transitions over time as a timeline/Gantt chart.
    
    Returns:
        pyplot.figure showing which mode was active at each time
    """
    mode_transitions = extract_mode_transitions(run_result)
    
    if not mode_transitions:
        return None
    
    # Get unique modes and assign them y-positions
    unique_modes = list(set([mode for mode, _ in mode_transitions]))
    mode_to_y = {mode: i for i, mode in enumerate(unique_modes)}
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Draw rectangles for each mode period
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_modes)))
    mode_colors = {mode: colors[i] for i, mode in enumerate(unique_modes)}
    
    for i in range(len(mode_transitions) - 1):
        mode, start_time = mode_transitions[i]
        end_time = mode_transitions[i + 1][1]
        duration = end_time - start_time
        
        y_pos = mode_to_y[mode]
        rect = Rectangle((start_time, y_pos - 0.4), duration, 0.8, 
                         facecolor=mode_colors[mode], edgecolor='black', linewidth=1)
        ax.add_patch(rect)
    
    # Handle the last mode (if there's a final timestamp or use last known time)
    if len(mode_transitions) > 0:
        last_mode, last_time = mode_transitions[-1]
        # Extend to show the final mode is still active
        final_duration = last_time * 0.1  # Show as 10% extension
        y_pos = mode_to_y[last_mode]
        rect = Rectangle((last_time, y_pos - 0.4), final_duration, 0.8,
                         facecolor=mode_colors[last_mode], edgecolor='black', 
                         linewidth=1, linestyle='--', alpha=0.5)
        ax.add_patch(rect)
    
    ax.set_yticks(range(len(unique_modes)))
    ax.set_yticklabels(unique_modes)
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("Mode", fontsize=12)
    ax.set_title(
        f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Mode Timeline",
        fontsize=16,
        y=1.02
    )
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, mode_transitions[-1][1] * 1.15)
    ax.set_ylim(-0.5, len(unique_modes) - 0.5)
    
    fig.tight_layout()
    return fig


def mode_duration_pie_chart_fig(run_result: RunResult):
    """
    Pie chart showing fraction of time spent in each mode.
    
    Returns:
        pyplot.figure with pie chart
    """
    time_in_mode = time_spent_in_each_mode(run_result)
    
    if not time_in_mode:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    modes = list(time_in_mode.keys())
    durations = list(time_in_mode.values())
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(modes)))
    
    wedges, texts, autotexts = ax.pie(durations, labels=modes, autopct='%1.1f%%',
                                        colors=colors, startangle=90,
                                        textprops={'fontsize': 12})
    
    # Make percentage text bold
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')
        autotext.set_fontsize(11)
    
    ax.set_title(
        f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Time Distribution Across Modes",
        fontsize=16,
        y=1.02
    )
    
    fig.tight_layout()
    return fig


def mode_visit_count_bar_chart_fig(run_result: RunResult):
    """
    Bar chart showing number of visits to each mode.
    
    Returns:
        pyplot.figure with bar chart
    """
    visit_counts = number_of_visits_per_mode(run_result)
    
    if not visit_counts:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    modes = list(visit_counts.keys())
    counts = list(visit_counts.values())
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(modes)))
    
    bars = ax.bar(modes, counts, color=colors, edgecolor='black', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_xlabel("Mode", fontsize=12)
    ax.set_ylabel("Number of Visits", fontsize=12)
    ax.set_title(
        f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Mode Visit Frequency",
        fontsize=16,
        y=1.02
    )
    ax.grid(True, alpha=0.3, axis='y')
    
    fig.tight_layout()
    return fig


def transition_matrix_heatmap_fig(run_result: RunResult):
    """
    Heatmap showing transition counts between modes.
    
    Returns:
        pyplot.figure with heatmap
    """
    transition_counts = transition_count_between_modes(run_result)
    
    if not transition_counts:
        return None
    
    # Get all unique modes
    all_modes = set()
    for (from_mode, to_mode) in transition_counts.keys():
        all_modes.add(from_mode)
        all_modes.add(to_mode)
    all_modes = sorted(list(all_modes))
    
    # Build transition matrix
    n = len(all_modes)
    matrix = np.zeros((n, n))
    
    for (from_mode, to_mode), count in transition_counts.items():
        from_idx = all_modes.index(from_mode)
        to_idx = all_modes.index(to_mode)
        matrix[from_idx, to_idx] = count
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Transition Count', fontsize=11)
    
    # Set ticks and labels
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(all_modes)
    ax.set_yticklabels(all_modes)
    
    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add text annotations
    for i in range(n):
        for j in range(n):
            if matrix[i, j] > 0:
                text = ax.text(j, i, int(matrix[i, j]),
                             ha="center", va="center", color="black", fontsize=11, fontweight='bold')
    
    ax.set_xlabel("To Mode", fontsize=12)
    ax.set_ylabel("From Mode", fontsize=12)
    ax.set_title(
        f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Transition Matrix",
        fontsize=16,
        y=1.02
    )
    
    fig.tight_layout()
    return fig


# def guard_activation_timeline_fig(run_result: RunResult):
#     """
#     Timeline showing when each guard was activated.
    
#     Returns:
#         pyplot.figure with guard activation events
#     """
#     transition_events = extract_transition_events(run_result)
    
#     if not transition_events:
#         return None
    
#     # Get unique guards
#     unique_guards = sorted(list(set([event['guard_name'] for event in transition_events])))
#     guard_to_y = {guard: i for i, guard in enumerate(unique_guards)}
    
#     fig, ax = plt.subplots(figsize=(14, 6))
    
#     colors = plt.cm.Set2(np.linspace(0, 1, len(unique_guards)))
#     guard_colors = {guard: colors[i] for i, guard in enumerate(unique_guards)}
    
#     # Plot vertical lines for each activation
#     for event in transition_events:
#         guard = event['guard_name']
#         timestamp = event['timestamp']
#         y_pos = guard_to_y[guard]
        
#         ax.plot([timestamp, timestamp], [y_pos - 0.3, y_pos + 0.3], 
#                color=guard_colors[guard], linewidth=3, marker='o', markersize=6)
    
#     ax.set_yticks(range(len(unique_guards)))
#     ax.set_yticklabels(unique_guards)
#     ax.set_xlabel("Time (seconds)", fontsize=12)
#     ax.set_ylabel("Guard", fontsize=12)
#     ax.set_title(
#         f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Guard Activation Timeline",
#         fontsize=16,
#         y=1.02
#     )
#     ax.grid(True, alpha=0.3, axis='x')
#     ax.set_ylim(-0.5, len(unique_guards) - 0.5)
    
#     fig.tight_layout()
#     return fig


# def guard_activation_rate_bar_chart_fig(run_result: RunResult):
#     """
#     Bar chart showing activation rate for each guard.
    
#     Returns:
#         pyplot.figure with bar chart
#     """
#     activation_rates = guard_activation_rate(run_result)
    
#     if not activation_rates:
#         return None
    
#     fig, ax = plt.subplots(figsize=(10, 6))
    
#     guards = list(activation_rates.keys())
#     rates = list(activation_rates.values())
    
#     colors = plt.cm.Set2(np.linspace(0, 1, len(guards)))
    
#     bars = ax.bar(guards, rates, color=colors, edgecolor='black', linewidth=1.5)
    
#     # Add value labels on top of bars
#     for bar in bars:
#         height = bar.get_height()
#         ax.text(bar.get_x() + bar.get_width()/2., height,
#                 f'{height:.3f}',
#                 ha='center', va='bottom', fontsize=10, fontweight='bold')
    
#     ax.set_xlabel("Guard", fontsize=12)
#     ax.set_ylabel("Activation Rate (activations/second)", fontsize=12)
#     ax.set_title(
#         f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Guard Activation Rates",
#         fontsize=16,
#         y=1.02
#     )
#     ax.grid(True, alpha=0.3, axis='y')
    
#     fig.tight_layout()
#     return fig


def chattering_detection_fig(run_result: RunResult):
    """
    Visualize chattering events (A->B->A patterns) on timeline.
    
    Returns:
        pyplot.figure highlighting chattering events
    """
    mode_transitions = extract_mode_transitions(run_result)
    chattering_events = self_loop_detection(run_result)
    
    if not mode_transitions:
        return None
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot all transitions as points
    modes = [mode for mode, _ in mode_transitions]
    times = [time for _, time in mode_transitions]
    unique_modes = sorted(list(set(modes)))
    mode_to_y = {mode: i for i, mode in enumerate(unique_modes)}
    
    # Plot normal transitions
    for mode, time in mode_transitions:
        y_pos = mode_to_y[mode]
        ax.plot(time, y_pos, 'o', color='blue', markersize=8, alpha=0.5)
    
    # Highlight chattering events
    for event in chattering_events:
        start_time = event['start_time']
        duration = event['duration']
        mode_a = event['pattern'][0]
        y_pos = mode_to_y[mode_a]
        
        # Draw red rectangle around chattering region
        rect = Rectangle((start_time, y_pos - 0.4), duration, 0.8,
                         facecolor='red', edgecolor='darkred', 
                         linewidth=2, alpha=0.3)
        ax.add_patch(rect)
        
        # Add annotation
        ax.annotate(f'{duration:.4f}s', 
                   xy=(start_time + duration/2, y_pos),
                   xytext=(0, 20), textcoords='offset points',
                   ha='center', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    ax.set_yticks(range(len(unique_modes)))
    ax.set_yticklabels(unique_modes)
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("Mode", fontsize=12)
    ax.set_title(
        f"{run_result.run_signature.model_name} v{run_result.run_signature.model_version} — Run {run_result.run_signature.run_id}: Chattering Detection (A→B→A patterns)",
        fontsize=16,
        y=1.02
    )
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_ylim(-0.5, len(unique_modes) - 0.5)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='blue', alpha=0.5, label='Mode Transitions'),
        Patch(facecolor='red', alpha=0.3, edgecolor='darkred', label='Chattering Detected')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    fig.tight_layout()
    return fig


if __name__ == '__main__':
    from hybrid_automaton._runtime import _Runtime
    from hybrid_automaton.definition import _Definition
    from unittest.mock import MagicMock 
    
    definition = MagicMock(spec=_Definition)
    definition.name = "Bouncing Ball"
    definition.version = "1.0"
    Signaure = _Runtime.Signature
    run_results = RunResult(
        run_signature=Signaure(
            timeout_sec=10,
            real_time_mode_enabled=True,
            should_integrate=True,
            delta_time=0.01,
            automaton_definition=definition
        ),
        run_logs_dir_path="/home/ryan/hybrid-automaton/log_hybrid_automaton/bouncing_ball"
    )
    
    # Generate all figures
    fig1 = mode_timeline_fig(run_results)
    fig2 = mode_duration_pie_chart_fig(run_results)
    fig3 = mode_visit_count_bar_chart_fig(run_results)
    fig4 = transition_matrix_heatmap_fig(run_results)
    # fig5 = guard_activation_timeline_fig(run_results)
    # fig6 = guard_activation_rate_bar_chart_fig(run_results)
    fig7 = chattering_detection_fig(run_results)
    
    plt.show()