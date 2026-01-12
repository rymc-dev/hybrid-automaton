import matplotlib.pyplot as plt
from typing import List, Tuple
import numpy as np
from typing import List


def continuous_states_over_time_fig(continuous_states: List[Tuple[float, np.array]], state_labels: List[str] = None): 
    """  
    
    Args: 
        continous_states: 
            ...
            
    Output:
        pyplot.figure
    """
    #TODO: Add checks for invalid contiuous_states input and state labels, currently
    #      assumes valid logic, if no continuous states are provided exception will be thrown
    timestamps = [continuous_state[0] for continuous_state in continuous_states]
    continuous_state_values = np.array([continuous_state[1] for continuous_state in continuous_states])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot each dimension separately
    num_dimensions = continuous_state_values.shape[1]
    for i in range(num_dimensions):
        ax.plot(timestamps, continuous_state_values[:, i], label=f'x[{i}]')
    
    ax.set_title('Hybrid Automaton <v0.0.4> - Continuous State Over Time', fontsize=16, y=1.02)
    ax.set_xlabel("Time Active Elapsed (s)", fontsize=12)
    ax.set_ylabel("Continuous State Values", fontsize=12)
    if state_labels is not None:
        ax.legend(state_labels)
    else:
        ax.legend() 
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    return fig

def transitions_times_over_time_fig(transition_times: List[Tuple[float, float]]):
    """
    
    Args: 
        transition_times: 
            ...
    """
    timestamps = [transition_time[0] for transition_time in transition_times]
    transition_times = [transition_time[1] for transition_time in transition_times]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(timestamps, transition_times, label=f'transition_time (s)')
    
    ax.set_title('Hybrid Automaton <v0.0.4> - transition times over time active elapsed', fontsize=16, y=1.02)
    ax.set_xlabel("time active elapsed (s)", fontsize=12)
    ax.set_ylabel("transition times (s)", fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    return fig

def auxiliary_states_over_time_fig(auxilary_states: List):
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

def automaton_states_over_time(automaton_states: List[Tuple[float, str]]):
    """  
    
    Args: 
        automaton_states: 
            List[Tuple[float, str]]
    """
    timestamps = [automaton_state[0] for automaton_state in automaton_states]
    states = [automaton_state[1] for automaton_state in automaton_states]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(timestamps, states, label=f'automaton state (q)')
    
    ax.set_title('Hybrid Automaton <v0.0.4> - automaton states over time active elapsed', fontsize=16, y=1.02)
    ax.set_xlabel("time active elapsed (s)", fontsize=12)
    ax.set_ylabel("Automaton State (q)", fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    return fig