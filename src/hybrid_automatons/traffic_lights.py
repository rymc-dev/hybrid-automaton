from hybrid_automaton import Automaton, State, Transition

def traffic_lights(time_in_green: float = 8.0, time_in_red: float = 5.0, time_in_yellow:float = 3.0) -> Automaton: 
    def red_to_green_guard(x, aux_x, u, cfg, clk: Automaton.Runtime.Clock): 
        return clk.get_time_elapsed_since_last_transition() >= cfg['time_in_red']

    def green_to_yellow_guard(x, aux_x, u, cfg, clk):
        return clk.get_time_elapsed_since_last_transition() >= cfg['time_in_green']
    
    def yellow_to_red_guard(x, aux_x, u, cfg, clk): 
        return clk.get_time_elapsed_since_last_transition() >= cfg['time_in_yellow']
        
    def on_enter_red():
        print("🔴 RED LIGHT - Stop!")

    def on_enter_green():
        print("🟢 GREEN LIGHT - Go!")

    def on_enter_yellow():
        print("🟡 YELLOW LIGHT - Caution!")  
        
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
    
    return Automaton(
        name="Traffic Light Automaton",
        states=[red_state, green_state, yellow_state],
        configuration={
            'time_in_red': time_in_red,
            'time_in_yellow': time_in_yellow,
            'time_in_green': time_in_green
        }
    )