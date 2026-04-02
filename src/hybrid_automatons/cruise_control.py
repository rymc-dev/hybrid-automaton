import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np

from hybrid_automaton import RuntimeContext
from hybrid_automaton import Automaton
from hybrid_automaton.definition import State
from hybrid_automaton.definition import Transition
from hybrid_automaton.definition import guard 
from hybrid_automaton.definition import continuous_dynamics

ContinuousState = RuntimeContext.ContinuousState
AuxiliaryState = RuntimeContext.AuxiliaryState


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
    def accelerate_flow(ctx: RuntimeContext):
        """Accelerate at 2 m/s² - x = [v, dist]"""
        v = ctx.continuous_state.latest()[0]
        v_dot = 2.0 if v < ctx.configuration['target_speed'] else 0.0
        dist_dot = -(v - ctx.configuration['car_ahead_speed'])
        return np.array([v_dot, dist_dot])
    
    @continuous_dynamics
    def cruise_flow(ctx: RuntimeContext) -> np.ndarray:
        """Maintain constant speed"""
        return np.array([0.0, -(ctx.continuous_state.latest()[0] - ctx.configuration['car_ahead_speed'])])
    
    @continuous_dynamics
    def brake_flow(ctx: RuntimeContext) -> np.ndarray:
        """Gentle braking at -1.5 m/s²"""
        v = ctx.continuous_state.latest()[0]
        v_dot = -1.5 if v > 0 else 0.0
        return np.array([v_dot, -(v - ctx.configuration['car_ahead_speed'])])
    
    @continuous_dynamics
    def emergency_brake_flow(ctx: RuntimeContext) -> np.ndarray:
        """Hard braking at -5 m/s²"""
        v = ctx.continuous_state.latest()[0]
        v_dot = -5.0 if v > 0 else 0.0
        return np.array([v_dot, -(v - ctx.configuration['car_ahead_speed'])])

    # ==========================
    #   Guards
    # ==========================
    @guard
    def reached_target_speed(ctx: RuntimeContext) -> bool:
        return abs(ctx.continuous_state.latest()[0] - ctx.configuration['target_speed']) < 0.5
    
    @guard    
    def below_target_speed(ctx:RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[0] < ctx.configuration['target_speed'] - 1.0 \
            and ctx.continuous_state.latest()[1] > ctx.configuration['safe_distance']
    
    @guard    
    def too_close(ctx: RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[1] < ctx.configuration['safe_distance']
    
    @guard    
    def dangerously_close(ctx: RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[1] < ctx.configuration['danger_close']
    
    @guard    
    def safe_distance_restored(ctx:RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[1] > ctx.configuration['safe_distance'] + 10.0
    
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
    return Automaton(
        name="Cruise Control", 
        version="0.0.1",
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


async def main(): 
    result = await ha.activate(
            initial_continuous_state=ContinuousState(name="car", x0=np.array([5.0, 0.0]), x_labels=['velocity', 'distance']),
            initial_auxiliary_states=[
                AuxiliaryState(name="test_aux_state", aux0=[0.0, 0.0], aux_buffer_len=10, expected_update_hz=10),
                AuxiliaryState(name="dump state", aux0=np.array([10.0, 10.0]), aux_buffer_len=1, expected_update_hz=np.inf)
            ],
            continuous_state_sampler_enabled=True,
            continuous_state_sampler_rate=100,
            auxiliary_states_sampler_enabled=True,
            auxiliary_states_sampler_rate=10,
            enable_real_time_mode=False,
            enable_self_integration=True,
            timeout_sec=30.0,
            delta_time=0.01,
            output_dir="log_hybrid_automaton/cruise_control/"
    )
    print (result)

if __name__ == '__main__': 
    ha = cruise_control()
    
    print (ha)
    print (repr(ha))
    import asyncio
    asyncio.run(main())