import matplotlib.pyplot as plt
from typing import List, Tuple

def generate_mode_timeseries_figure(mode_data: List[Tuple[float, int]]):
    """  
    users time series and mode data from a hybrid automaton run 
    to plot mode over time.

    Args: 
        mode_data: List[Tuple[float, int]]
            float timestamp to mode id values over time

    Returns:
        matplotlib.figure.Figure: The created matplotlib figure.
    """ 
    timestamps = [mode_state[0] for mode_state in mode_data]
    mode_values = [mode_state[1] for mode_state in mode_data]
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(timestamps, mode_values, label='mode ID `q`')

    ax.set_title('Hybrid Automaton (v0.0.4- Automaton State Time Series Plot', fontsize=16, y=1.02)
    ax.set_xlabel("Time Activate (s)", fontsize=12)
    ax.set_ylabel("Mode (q)", fontsize=12)
    ax.grid(True, alpha=0.3)
    # Create a mapping from mode int values to string labels for the legend
    # mode_ids = sorted(set(mode_values))
    # # Example mapping, replace with your actual mapping if available
    # mode_labels = {0: "Idle", 1: "Running", 2: "Paused", 3: "Stopped"}
    # legend_labels = [f"{mode_id}: {mode_labels.get(mode_id, 'Unknown')}" for mode_id in mode_ids]
    # Show the mapping in the legend
    # ax.legend([', '.join(legend_labels)], title="Mode Mapping")
    fig.tight_layout()
    
    return fig
