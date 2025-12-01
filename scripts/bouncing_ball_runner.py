
from hybrid_automaton import Automaton, State, Transition
from typing import Dict, Tuple
import numpy as np
import time

GRAVITY = -9.81
RESTITUTION = 0.8  # Energy loss coefficient

def flying_flow(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock) -> np.array:
    """Free fall dynamics - x = [y, v]"""
    # dx/dt = [v, g]
    return np.array([x.get_continous_state()[0], GRAVITY])

def ground_flow(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock) -> np.array:
    """On ground (stationary)"""
    return np.array([0.0, 0.0])


def hits_ground(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock) -> bool:
    """Ball hits the ground"""
    return x.get_continous_state()[0] <= 0.0 and x[1] < 0  # y <= 0 and v < 0

def bounces_up(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock) -> bool:
    """Ball has velocity to bounce"""
    return abs(x.get_continous_state()[0]) > 0.1  # Threshold for bouncing

def stops_bouncing(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock) -> bool:
    """Ball has too little energy to bounce"""
    return abs(x.get_continous_state()[0]) <= 0.1

def bounce_reset(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock
                ) -> Tuple[np.array, Dict[str, Automaton.Runtime.AuxiliaryState], Dict[str, Automaton.Runtime.ControlInput]]:
    """Reverse velocity with energy loss"""
    x.set_continous_state(np.array([0.0, -x[1] * RESTITUTION]))
    return x, aux_x, u

def stop_reset(x: Automaton.Runtime.ContinousState, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], 
                u: Dict[str, Automaton.Runtime.ControlInput], cfg: Dict, clk: Automaton.Runtime.Clock
                ) -> Tuple[np.array, Dict[str, Automaton.Runtime.AuxiliaryState], Dict[str, Automaton.Runtime.ControlInput]]:
    """Stop the ball"""
    x.set_continous_state(np.array([0.0, 0.0]))
    return x, aux_x, u

# States
flying = State(name="FLYING", initial=True, flow=flying_flow)
ground = State(name="GROUND", flow=ground_flow)

# Transitions
flying.add_transition(Transition("hit_ground", ground, guards=[hits_ground], 
                                reset=bounce_reset, priority=1))
ground.add_transitions(
    [Transition("bounce_up", flying, guards=[bounces_up], priority=1), 
    Transition("stop", ground, guards=[stops_bouncing], priority=2)]
)


# Create automaton
ball = Automaton(
    name="Bouncing Ball", 
    states=[flying, ground], 
    integration_function=None, 
    on_entry=lambda: print('starting bouncing ball!'), 
    on_exit=lambda: print('ending bouncing ball')
)

# Drop from 5 meters: x = [y, v]
x0 = np.array([5.0, 0.0])

import asyncio
asyncio.run(ball.activate(x0=x0, real_time_mode=False, dt=0.1))