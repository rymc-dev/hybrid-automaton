import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from hybrid_automaton import Automaton, State, Transition
from typing import Dict, Tuple
import numpy as np
import asyncio

# Physical constants
GRAVITY = -9.81
RESTITUTION = 0.8  # Velocity loss on bounce


# ============================
#   Continuous dynamics
# ============================

def flying_flow(x, aux_x, u, cfg, clk):
    """Free fall: x = [y, v], dx/dt = [v, g]."""
    y, v = x.get_continous_state()
    return np.array([v, GRAVITY])


def ground_flow(x, aux_x, u, cfg, clk):
    """Ball resting on the ground."""
    return np.array([0.0, 0.0])


# ============================
#   Guards
# ============================

def hits_ground(x, aux_x, u, cfg, clk):
    """Ball contacts ground while moving downward."""
    y, v = x.get_continous_state()
    return y <= 0.0 and v < 0


def bounce_possible(x, aux_x, u, cfg, clk):
    """Ball has upward rebound velocity after impact."""
    y, v = x.get_continous_state()
    return abs(v) > 0.1  # threshold to determine if bounce energy remains


def no_more_bounce(x, aux_x, u, cfg, clk):
    """Ball has lost all bounce energy."""
    y, v = x.get_continous_state()
    return abs(v) <= 0.1   # small velocity → stop bouncing


# ============================
#   Reset maps
# ============================

def bounce_reset(x, aux_x, u, cfg, clk):
    """Apply bounce: set y=0, reverse velocity with restitution."""
    y, v = x.get_continous_state()
    new_state = np.array([0.0, -v * RESTITUTION])
    x.set_continous_state(new_state)
    return x, aux_x, u


def stop_reset(x, aux_x, u, cfg, clk):
    """Final rest: position 0, velocity 0."""
    x.set_continous_state(np.array([0.0, 0.0]))
    return x, aux_x, u


# ============================
#   States
# ============================

flying = State(
    name="FLYING",
    initial=True,
    flow=flying_flow,
    on_enter=lambda: print("[ENTER] FLYING"),
    on_exit=lambda: print("[EXIT] FLYING"),
)

ground = State(
    name="GROUND",
    flow=ground_flow,
    on_enter=lambda: print("[ENTER] GROUND"),
    on_exit=lambda: print("[EXIT] GROUND"),
)


# ============================
#   Transitions
# ============================

# FLYING → GROUND (impact)
flying.add_transition(
    Transition(
        "hit_ground",
        ground,
        guards=[hits_ground],
        reset=bounce_reset,
        priority=1
    )
)

# GROUND → FLYING (bounce back up)
ground.add_transition(
    Transition(
        "bounce_up",
        flying,
        guards=[bounce_possible],
        priority=1
    )
)

# GROUND → GROUND (final rest)
ground.add_transition(
    Transition(
        "stop",
        ground,
        guards=[no_more_bounce],
        reset=stop_reset,
        priority=2  # only after bounce_up is no longer possible
    )
)


# ============================
#   Build automaton
# ============================

ball = Automaton(
    name="Bouncing Ball",
    states=[flying, ground],
    integration_function=None,
    on_entry=lambda: print(">>> Starting bouncing ball"),
    on_exit=lambda: print(">>> Ending bouncing ball"),
)


# ============================
#   Run simulation
# ============================

x0 = np.array([5.0, 0.0])  # initial drop height

x = []
automaton_state = []

async def runner(): 
    async def store_continous_state_data(): 
        asyncio.sleep(0.01)
        while True:
            try: 
                x.append([ball.get_active_elapsed_time(), ball.get_continous_state()])
            except Exception as e: 
                print (e)

            await asyncio.sleep(0.01)


    async def store_automaton_state(): 
        asyncio.sleep(0.01)
        while True:
            try: 
                automaton_state.append(
                    [ball.get_active_elapsed_time(), {'mode': ball.get_active_mode()}]
                )
            except Exception as e: 
                print (str(e))
        
            await asyncio.sleep(0.01)
    # async def store_automaton_state_data():
    #     asyncio.sleep(0.01)
    #     while True: 
    #         try: 


    async def deactivate_after_10_seconds(*tasks): 
        await asyncio.sleep(10.0)
        for t in tasks:
            t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        print ('tasks completed')

    t1 = asyncio.create_task(ball.activate(x0=x0, real_time_mode=True, integrate=True, dt=0.01))
    t2 = asyncio.create_task(store_continous_state_data())
    t3 = asyncio.create_task(store_automaton_state())

    # stopper = asyncio.create_task(store_)
    await asyncio.create_task(deactivate_after_10_seconds(t1, t2, t3))

    print (x)

    import matplotlib.pyplot as plt

    # plot continous state
    times = np.array([row[0] for row in x])
    x_vals = np.array([row[1][0] for row in x])
    y_vals = np.array([row[1][1] for row in x])

    plt.figure(figsize=(12, 6))

    plt.plot(times, x_vals, label="Height (m)")
    plt.plot(times, y_vals, label="Velocity (m/s)")

    # Main title + subtitle
    plt.suptitle(f"{ball.name} Hybrid Automaton – Continuous State Time Series", fontsize=16, y=1.02)
    plt.title("Generated using hybrid-automaton v0.0.4", fontsize=11, pad=10)

    plt.xlabel("Time Active (s)", fontsize=12)
    plt.ylabel("Value", fontsize=12)

    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.show()


    times = np.array([row[0] for row in x])
    mode_ids = np.array([row[1]['mode'][0] for row in automaton_state])

    plt.figure(figsize=(12, 6))

    plt.plot(times, mode_ids, label="mode ID `q`")

    # Main title + subtitle
    plt.suptitle(f"{ball.name} Hybrid Automaton – Automaton State Time Series", fontsize=16, y=1.02)
    plt.title("Generated using hybrid-automaton v0.0.4", fontsize=11, pad=10)

    plt.xlabel("Time Active (s)", fontsize=12)
    plt.ylabel("Value", fontsize=12)

    plt.grid(True, alpha=0.3)
    plt.legend()

    plt.tight_layout()
    plt.show()

asyncio.run(runner())
