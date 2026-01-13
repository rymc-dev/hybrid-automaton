import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from hybrid_automaton import Automaton, State, Transition, guard
from hybrid_automaton.automaton_runtime_context import Context
import numpy as np

def traffic_lights(time_in_green: float = 8.0, time_in_red: float = 5.0, time_in_yellow:float = 3.0) -> Automaton:
    """
    Docstring for traffic_lights
    
    :param time_in_green: Description
    :type time_in_green: float
    :param time_in_red: Description
    :type time_in_red: float
    :param time_in_yellow: Description
    :type time_in_yellow: float
    :return: Description
    :rtype: Automaton
    """
    
    # ================
    # Guards
    # ================
    @guard
    def red_to_green_guard(ctx: Context) -> bool: 
        return ctx.clk.get_time_elapsed_since_transition() >= ctx.cfg['time_in_red']

    @guard
    def green_to_yellow_guard(ctx: Context) -> bool:
        return ctx.clk.get_time_elapsed_since_transition() >= ctx.cfg['time_in_green']
    
    @guard
    def yellow_to_red_guard(ctx: Context) -> bool: 
        return ctx.clk.get_time_elapsed_since_transition() >= ctx.cfg['time_in_yellow']
    
    # ================
    # On entry hook functions
    # ================
    def on_enter_red():
        print("🔴 RED LIGHT - Stop!")

    def on_enter_green():
        print("🟢 GREEN LIGHT - Go!")

    def on_enter_yellow():
        print("🟡 YELLOW LIGHT - Caution!")  
    
    # ================
    # States and Transitions
    # ================
    
    red_state = State(
        name="RED",
        initial=True,
        on_enter=on_enter_red
    )

    green_state = State(
        name="GREEN",
        on_enter=on_enter_green
    )

    yellow_state = State(
        name="YELLOW",
        on_enter=on_enter_yellow
    )
    
    red_state.add_transition(
        Transition(
            name="red_to_green",
            to_state=green_state,
            guards=[red_to_green_guard],
            priority=1
        )
    )
    
    green_state.add_transition(
        Transition(
            name="green_to_yellow",
            to_state=yellow_state,
            guards=[green_to_yellow_guard],
            priority=1
        )
    )
    
    yellow_state.add_transition(
        Transition(
            name="yellow_to_red",
            to_state=red_state,
            guards=[yellow_to_red_guard],
            priority=1
        )
    )
    
    # Automaton Definition
    
    return Automaton(
        name="Traffic Light Automaton",
        states=[red_state, green_state, yellow_state],
        configuration={
            'time_in_red': time_in_red,
            'time_in_yellow': time_in_yellow,
            'time_in_green': time_in_green
        }
    )
    
  
if __name__ == '__main__': 

    ha = traffic_lights(
        time_in_green = 8.0, 
        time_in_red = 5.0, 
        time_in_yellow = 3.0
    )
    print (ha)
    print (repr(ha))
    
    from hybrid_automaton_runner import AutomatonRunner
    import asyncio
    ha_runner: AutomatonRunner = AutomatonRunner(hybrid_automaton=ha, sampling_rate=0.001)
    async def main(): 
        try:
            await ha_runner.run(
                x0 = None, 
                real_time_mode=False, 
                integrate=True, 
                duration=100.0, 
                dt=0.01, 
                collect_automaton=True,
                collect_continuous=True,
                collect_transitions=True,
                collect_control=False, 
                collect_auxiliary=False
            )
        except Exception as e: 
            print (str(e))
            sys.exit(1)
        
        ha_runner.print_summary()
        results = ha_runner.get_results()
        from matplotlib import pyplot as plt
        from hybrid_automaton_evaluation.visualization import  automaton_states_over_time, continuous_states_over_time_fig, transitions_times_over_time_fig
        # fig1 = continuous_states_over_time_fig(results['continuous_states'], state_labels=["traffic light state \{RED, GREEN, YELLOW \}"])
        # fig2 = transitions_times_over_time_fig(results['transition_times']) # TODO: Need to fix this
        fig5 = automaton_states_over_time(results['automaton_states'])
        plt.show()

    asyncio.run(main())