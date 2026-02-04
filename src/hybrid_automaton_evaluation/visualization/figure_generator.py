import matplotlib.pyplot as plt
from typing import List, Tuple
import numpy as np
from typing import List
from hybrid_automaton import RunResult
import os
import csv
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

def automaton_states_over_time(run_result: RunResult):
    """  
    
    Args: 
        automaton_states: 
            List[Tuple[float, str]]
    """
    
    events = []
    with open(os.path.join(run_result.run_logs_dir_path, "temporal_automaton.log"), "r") as f:
        for line in f: 
            line = line.strip()
            if not line or line.startswith("#"): 
                continue
            events.append(line)
            
    # Parse the automaton events
    print (events) # TODO: Complete this
    
    # timestamps = [automaton_state[0] for automaton_state in automaton_states]
    # states = [automaton_state[1] for automaton_state in automaton_states]
    
    # fig, ax = plt.subplots(figsize=(12, 6))
    
    # ax.plot(timestamps, states, label=f'automaton state (q)')
    
    # ax.set_title('Hybrid Automaton <v0.0.4> - automaton states over time active elapsed', fontsize=16, y=1.02)
    # ax.set_xlabel("time active elapsed (s)", fontsize=12)
    # ax.set_ylabel("Automaton State (q)", fontsize=12)
    # ax.legend()
    # ax.grid(True, alpha=0.3)
    # fig.tight_layout()
    
    # return fig