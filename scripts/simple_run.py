from hybrid_automaton import Automaton, State, Transition
import asyncio
import time

def main():
    """
    Traffic Light Controller - A hybrid automaton example
    
    States: RED -> GREEN -> YELLOW -> RED (cycle)
    
    Continuous state: elapsed_time in each state
    Transitions occur based on time thresholds
    """
    
    # Guard functions - check if enough time has elapsed
    def red_to_green_guard(x, aux_x, u, ctx, dt):
        """Transition from RED to GREEN after 5 seconds"""
        return ctx.elapsed_time_since_last_transition >= 5.0
    
    def green_to_yellow_guard(x, aux_x, u, ctx, dt):
        """Transition from GREEN to YELLOW after 8 seconds"""
        return ctx.elapsed_time_since_last_transition >= 8.0
    
    def yellow_to_red_guard(x, aux_x, u, ctx, dt):
        """Transition from YELLOW to RED after 3 seconds"""
        return ctx.elapsed_time_since_last_transition >= 3.0
    
    # Reset functions - reset the timer and update any state
    def reset_timer(x, aux_x, u, ctx, dt):
        """Reset the timer when transitioning"""
        new_ctx = ctx
        new_ctx.elapsed_time_since_last_transition = 0.0
        return x, new_ctx
    
    # State entry callbacks
    def on_enter_red():
        print("🔴 RED LIGHT - Stop!")
    
    def on_enter_green():
        print("🟢 GREEN LIGHT - Go!")
    
    def on_enter_yellow():
        print("🟡 YELLOW LIGHT - Caution!")
    
    # Define states
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
    
    # Add transitions
    red_state.add_transition(
        Transition(
            name="red_to_green",
            to_state=green_state,
            guards=[red_to_green_guard],
            reset=reset_timer,
            priority=1
        )
    )
    
    green_state.add_transition(
        Transition(
            name="green_to_yellow",
            to_state=yellow_state,
            guards=[green_to_yellow_guard],
            reset=reset_timer,
            priority=1
        )
    )
    
    yellow_state.add_transition(
        Transition(
            name="yellow_to_red",
            to_state=red_state,
            guards=[yellow_to_red_guard],
            reset=reset_timer,
            priority=1
        )
    )
    
    # Create the automaton
    traffic_light = Automaton(
        name="Traffic Light Controller",
        real_time_mode=True,
        states=[red_state, green_state, yellow_state],
        dt=0.1
    )
    
    # Initialize continuous state (empty dict for this example)
    x0 = {}
    
    # Activate the automaton
    traffic_light.activate(x0=x0)
    
    print("=" * 50)
    print("Traffic Light Automaton Started")
    print("=" * 50)
    print()
    
    # Simulate traffic light for 20 seconds
    simulation_time = 20.0
    current_time = 0.0
    dt = 0.1
    
    while current_time < simulation_time:
        # Update the context timer manually (since we're in real-time mode)
        traffic_light._ctx.elapsed_time_since_last_transition += dt
        traffic_light._ctx.elapsed_time_active += dt
        
        # Step the automaton
        step_result = traffic_light.step()
        
        if step_result and step_result.transition_taken:
            print(f"  ⚡ Transition: {step_result.transition_taken.name}")
            print(f"  → Current state: {traffic_light.q.name}")
            print()
        
        # Sleep to simulate real-time
        time.sleep(dt)
        current_time += dt
    
    print("=" * 50)
    print("Simulation Complete")
    print(f"Final state: {traffic_light.q.name}")
    print(f"Total time active: {traffic_light._ctx.elapsed_time_active:.1f}s")
    print("=" * 50)

if __name__ == "__main__":
    main()