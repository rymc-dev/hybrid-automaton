import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))



from hybrid_automaton import Automaton, State, Transition
import numpy as np
import time

GRAVITY = -9.81
RESTITUTION = 0.8  # Energy loss coefficient


def flying_flow(x, aux_x, u, ctx):
    """Free fall dynamics - x = [y, v]"""
    # dx/dt = [v, g]
    return np.array([x[1], GRAVITY])

def ground_flow(x, aux_x, u, ctx):
    """On ground (stationary)"""
    return np.array([0.0, 0.0])

def hits_ground(x, aux_x, u, ctx):
    """Ball hits the ground"""
    return x[0] <= 0.0 and x[1] < 0  # y <= 0 and v < 0

def bounces_up(x, aux_x, u, ctx):
    """Ball has velocity to bounce"""
    return abs(x[1]) > 0.1  # Threshold for bouncing

def stops_bouncing(x, aux_x, u, ctx):
    """Ball has too little energy to bounce"""
    return abs(x[1]) <= 0.1

def bounce_reset(x, aux_x, u, ctx):
    """Reverse velocity with energy loss"""
    x_new = np.array([0.0, -x[1] * RESTITUTION])
    return x_new, ctx


def bounce_reset(x, aux_x, u, ctx):
    """Reverse velocity with energy loss"""
    x_new = np.array([0.0, -x[1] * RESTITUTION])
    return x_new, ctx
    
def stop_reset(x, aux_x, u, ctx):
    """Stop the ball"""
    x_new = np.array([0.0, 0.0])
    return x_new, ctx


# States
flying = State(name="FLYING", initial=True, flow=flying_flow, on_enter=lambda: print('Enter Flying Mode'))
ground = State(name="GROUND", flow=ground_flow, on_enter=lambda: print('enter on ground.'))

# Transitions
flying.add_transition(Transition("hit_ground", ground, guards=[hits_ground], 
                                reset=bounce_reset, priority=1))
ground.add_transition(Transition("bounce_up", flying, guards=[bounces_up], priority=1))
ground.add_transition(Transition("stop", ground, guards=[stops_bouncing], priority=2))

# Create automaton
ball = Automaton(name="Bouncing Ball", states=[flying, ground])

# Drop from 5 meters: x = [y, v]
x0 = np.array([5.0, 0.0])
import asyncio

asyncio.run(ball.activate(x0=x0, dt=0.001))
print ('time completed')