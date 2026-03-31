import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np

from hybrid_automaton import Automaton
from hybrid_automaton.definition import State
from hybrid_automaton.definition import Transition
from hybrid_automaton.definition import guard
from hybrid_automaton import RuntimeContext

 
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
    def red_to_green_guard(ctx: RuntimeContext) -> bool: 
        return ctx.clock.get_time_elapsed_since_transition() >= ctx.configuration['time_in_red']

    @guard
    def green_to_yellow_guard(ctx: RuntimeContext) -> bool:
        return ctx.clock.get_time_elapsed_since_transition() >= ctx.configuration['time_in_green']
    
    @guard
    def yellow_to_red_guard(ctx: RuntimeContext) -> bool: 
        return ctx.clock.get_time_elapsed_since_transition() >= ctx.configuration['time_in_yellow']
    
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
        version="0.0.1",
        states=[red_state, green_state, yellow_state],
        configuration={
            'time_in_red': time_in_red,
            'time_in_yellow': time_in_yellow,
            'time_in_green': time_in_green
        }
    )
    
  
async def main(): 
    try:
        results = await ha.activate(
            initial_continuous_state = None, 
            enable_real_time_mode=False, 
            enable_self_integration=False, 
            timeout_sec=5.0, 
            delta_time=0.01, 
            continuous_state_sampler_enabled=True,
            continuous_state_sampler_rate=0.01,
            control_input_states_sampler_enabled=True,
            control_input_states_sampler_rate=1, 
        ) 
    except Exception as e: 
        print (str(e))
        sys.exit(1)
    
    print ("Complete!")
    print (results)
  
if __name__ == '__main__': 

    ha = traffic_lights(
        time_in_green = 8.0, 
        time_in_red = 5.0, 
        time_in_yellow = 3.0
    )
    print (ha)
    print (repr(ha))
    
    import asyncio
    asyncio.run(main())