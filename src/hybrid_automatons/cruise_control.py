import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from hybrid_automaton import State, Transition, Automaton
from hybrid_automaton.automaton_runtime_context import Context
from hybrid_automaton.automaton_annotations import guard, continuous_dynamics, reset, invariant


def cruise_control(target_speed: float = 30.0, safe_distance: float = 50.0,
                   danger_close: float = 20.0, car_ahead_speed: float = 20.0) -> Automaton:
    """ 
    Args: 
        target_speed: float
            m/s speed target
        safe distance: float
            meters safe distance
        car_ahead_speed: float
            m/s speed of car ahead
    """
    
    # =========================
    #   Continuous Dynamics
    # =========================
    @continuous_dynamics
    def accelerate_flow(ctx: Context):
        """Accelerate at 2 m/s² - x = [v, dist]"""
        v = ctx.x.latest()[0]
        v_dot = 2.0 if v < ctx.cfg['target_speed'] else 0.0
        dist_dot = -(v - ctx.cfg['car_ahead_speed'])
        return np.array([v_dot, dist_dot])
    
    @continuous_dynamics
    def cruise_flow(ctx: Context) -> np.ndarray:
        """Maintain constant speed"""
        return np.array([0.0, -(ctx.x.latest()[0] - ctx.cfg['car_ahead_speed'])])
    
    @continuous_dynamics
    def brake_flow(ctx: Context) -> np.ndarray:
        """Gentle braking at -1.5 m/s²"""
        v = ctx.x.latest()[0]
        v_dot = -1.5 if v > 0 else 0.0
        return np.array([v_dot, -(v - ctx.cfg['car_ahead_speed'])])
    
    @continuous_dynamics
    def emergency_brake_flow(ctx: Context) -> np.ndarray:
        """Hard braking at -5 m/s²"""
        v = ctx.x.latest()[0]
        v_dot = -5.0 if v > 0 else 0.0
        return np.array([v_dot, -(v - ctx.cfg['car_ahead_speed'])])

    # ==========================
    #   Guards
    # ==========================
    @guard
    def reached_target_speed(ctx: Context) -> bool:
        return abs(ctx.x.latest()[0] - ctx.cfg['target_speed']) < 0.5
    
    @guard    
    def below_target_speed(ctx: Context) -> bool:
        return ctx.x.latest()[0] < ctx.cfg['target_speed'] - 1.0 and ctx.x.latest()[1] > ctx.cfg['safe_distance']
    
    @guard    
    def too_close(ctx: Context) -> bool:
        return ctx.x.latest()[1] < ctx.cfg['safe_distance']
    
    @guard    
    def dangerously_close(ctx: Context) -> bool:
        return ctx.x.latest()[1] < ctx.cfg['danger_close']
    
    @guard    
    def safe_distance_restored(ctx: Context) -> bool:
        return ctx.x.latest()[1] > ctx.cfg['safe_distance'] + 10.0
    
    # Callbacks
    def on_accelerate():
        print("🚗💨 ACCELERATE mode")
    
    def on_cruise():
        print("🚗➡️  CRUISE mode - Maintaining speed")
    
    def on_brake():
        print("🚗🟡 BRAKE mode - Slowing down")
    
    def on_emergency():
        print("🚗🔴 EMERGENCY BRAKE!")
    
    # States
    accelerate = State("ACCELERATE", initial=True, flow=accelerate_flow, on_enter=on_accelerate)
    cruise = State("CRUISE", flow=cruise_flow, on_enter=on_cruise)
    brake = State("BRAKE", flow=brake_flow, on_enter=on_brake)
    emergency = State("EMERGENCY_BRAKE", flow=emergency_brake_flow, on_enter=on_emergency)
    
    # Transitions
    accelerate.add_transition(Transition("reach_cruise", cruise, guards=[reached_target_speed], priority=1))
    accelerate.add_transition(Transition("acc_to_brake", brake, guards=[too_close], priority=2))
    accelerate.add_transition(Transition("acc_to_emergency", emergency, guards=[dangerously_close], priority=3))
    
    cruise.add_transition(Transition("cruise_to_brake", brake, guards=[too_close], priority=1))
    cruise.add_transition(Transition("cruise_to_emergency", emergency, guards=[dangerously_close], priority=2))
    cruise.add_transition(Transition("cruise_to_acc", accelerate, guards=[below_target_speed], priority=3))
    
    brake.add_transition(Transition("brake_to_emergency", emergency, guards=[dangerously_close], priority=1))
    brake.add_transition(Transition("brake_to_cruise", cruise, guards=[safe_distance_restored], priority=2))
    
    emergency.add_transition(Transition("emergency_to_brake", brake, guards=[safe_distance_restored], priority=1))
    
    # Create automaton
    car = Automaton(
        name="Cruise Control", 
        states=[accelerate, cruise, brake, emergency], 
        configuration={
            'target_speed': target_speed,
            'safe_distance': safe_distance,
            'car_ahead_speed': car_ahead_speed,
            'danger_close': danger_close
        },
        on_entry=lambda: print('>>> Starting Cruise Control'),
        on_exit=lambda:print(">>> Ending Cruise Control")
    )

    return car

if __name__ == '__main__': 
    ha = cruise_control()
    
    print (ha)
    print (repr(ha))
    from hybrid_automaton_runner import AutomatonRunner
    import asyncio
    ha_runner: AutomatonRunner = AutomatonRunner(hybrid_automaton=ha, sampling_rate=0.001)
    async def main(): 
        results = await ha_runner.run(
            x0=np.array([5.0, 0.0]), 
            collect_automaton=True, 
            collect_transitions=True, 
            collect_continuous=True, 
            collect_auxiliary=True, 
            collect_control=False, 
            real_time_mode=False, 
            integrate=True, 
            duration=100.0, 
            dt=0.01
        )
        
        print(results) 
        # ha_runner.print_summary()
        # results = ha_runner.get_results()
        from matplotlib import pyplot as plt
        # from hybrid_automaton_evaluation.visualization import  automaton_states_over_time, continuous_states_over_time_fig, transitions_times_over_time_fig
        # fig1 = continuous_states_over_time_fig(results['continuous_states'], state_labels=['Velocity (m/s)', 'Distance to car in front (m)'])
        # # fig2 = transitions_times_over_time_fig(results['transition_times']) # TODO: Need to fix this
        # fig5 = automaton_states_over_time(results['automaton_states'])
        # plt.show()

    asyncio.run(main())