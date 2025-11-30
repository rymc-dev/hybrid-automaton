import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'hybrid_automaton')) 

from hybrid_automaton import Transition
from hybrid_automaton import State
from hybrid_automaton import Automaton

import asyncio

if __name__ == '__main__':
    import numpy as np

    TARGET_SPEED = 30.0  # m/s (108 km/h)
    SAFE_DISTANCE = 50.0  # meters
    CAR_AHEAD_SPEED = 20.0  # m/s

    def accelerate_flow(x, aux_x, u, ctx):
        """Accelerate at 2 m/s² - x = [v, dist]"""
        v_dot = 2.0 if x[0] < TARGET_SPEED else 0.0
        dist_dot = -(x[0] - CAR_AHEAD_SPEED)
        return np.array([v_dot, dist_dot])

    def cruise_flow(x, aux_x, u, ctx):
        """Maintain constant speed"""
        return np.array([0.0, -(x[0] - CAR_AHEAD_SPEED)])

    def brake_flow(x, aux_x, u, ctx):
        """Gentle braking at -1.5 m/s²"""
        v_dot = -1.5 if x[0] > 0 else 0.0
        return np.array([v_dot, -(x[0] - CAR_AHEAD_SPEED)])

    def emergency_brake_flow(x, aux_x, u, ctx):
        """Hard braking at -5 m/s²"""
        v_dot = -5.0 if x[0] > 0 else 0.0
        return np.array([v_dot, -(x[0] - CAR_AHEAD_SPEED)])
    
    # Guards - x = [v, dist]
    def reached_target_speed(x, aux_x, u, ctx):
        return abs(x[0] - TARGET_SPEED) < 0.5

    def below_target_speed(x, aux_x, u, ctx):
        return x[0] < TARGET_SPEED - 1.0 and x[1] > SAFE_DISTANCE

    def too_close(x, aux_x, u, ctx):
        return x[1] < SAFE_DISTANCE

    def dangerously_close(x, aux_x, u, ctx):
        return x[1] < 20.0

    def safe_distance_restored(x, aux_x, u, ctx):
        return x[1] > SAFE_DISTANCE + 10.0
    
    # Callbacks
    def on_accelerate():
        print("🚗💨 ACCELERATE mode")

    def on_cruise():
        print("🚗➡️  CRUISE mode - Maintaining speed")

    def on_brake():
        print("🚗🟡 BRAKE mode - Slowing down")

    def on_emergency():
        print("🚗🔴 EMERGENCY BRAKE!")

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
    car = Automaton(name="Cruise Control", states=[accelerate, cruise, brake, emergency])

    # Initial: x = [velocity, distance_to_car_ahead]
    async def deactivate_after_10_seconds():
        await asyncio.sleep(10)
        car.deactivate()
        
    async def runner():
        x0 = np.array([20.0, 100.0])
        t1 = asyncio.create_task(car.activate(x0=x0, dt=0.1))
        t2 = asyncio.create_task(deactivate_after_10_seconds())
        await asyncio.gather(asyncio.gather(t1, t2))

    asyncio.run(runner())
    print ('task completed')