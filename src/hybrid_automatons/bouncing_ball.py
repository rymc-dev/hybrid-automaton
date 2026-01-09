"""
sample implementation using v0.0.4 of the hybrid automaton package for a bouncing ball
"""

import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from hybrid_automaton import Automaton, State, Transition
from hybrid_automaton.automaton_runtime import Context
from hybrid_automaton.automaton_annotations import guard, reset, invariant, continuous_dynamics
import numpy as np

def bouncing_ball(gravity: float = -9.81, restitution: float = 0.8):
    """ 
    sample bouncing_ball hybrid automaton

    Args: 
        gravity: float
            gravity force applied to ball
        restitution: float
            velocity loss on bounce

    Output: 
        Automaton
    """

    # ============================
    #   Continuous dynamics
    # ============================
    @continuous_dynamics
    def flying_flow(ctx: Context) -> np.ndarray:
        """Free fall: x = [y, v], dx/dt = [v, g]."""
        y, v = ctx.x.latest()
        return np.array([v, ctx.cfg['gravity']])

    @continuous_dynamics
    def ground_flow(ctx: Context) -> np.ndarray:
        """Ball resting on the ground."""
        return np.array([0.0, 0.0])


    # ============================
    #   Guards
    # ============================

    @guard
    def hits_ground(ctx: Context) -> bool:
        """Ball contacts ground while moving downward."""
        y, v = ctx.x.latest()
        return y <= 0.0 and v < 0

    @guard
    def bounce_possible(ctx: Context) -> bool:
        """Ball has upward rebound velocity after impact."""
        y, v = ctx.x.latest()
        return abs(v) > 0.1  # threshold to determine if bounce energy remains

    @guard
    def no_more_bounce(ctx: Context) -> bool:
        """Ball has lost all bounce energy."""
        y, v = ctx.x.latest()
        return abs(v) <= 0.1   # small velocity → stop bouncing


    # ============================
    #   Reset maps
    # ============================
    @reset
    def bounce_reset(ctx: Context) -> Context:
        """Apply bounce: set y=0, reverse velocity with restitution."""
        y, v = ctx.x.latest()
        new_state = np.array([0.0, -v * ctx.cfg['restitution']])
        ctx.x.set_continuous_state(new_state)
        return ctx

    @reset
    def stop_reset(ctx: Context) -> Context:
        """Final rest: position 0, velocity 0."""
        ctx.x.set_continuous_state(np.array([0.0, 0.0]))
        return ctx


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

    return Automaton(
        name="Bouncing Ball",
        states=[flying, ground],
        configuration= {
            'gravity': gravity,
            'restitution': restitution 
        },
        on_entry=lambda: print(">>> Starting bouncing ball"),
        on_exit=lambda: print(">>> Ending bouncing ball"),
    )
    
if __name__ == '__main__': 
    ha = bouncing_ball()
    
    print (ha)
    print (repr(ha))
    from hybrid_automaton_runner import AutomatonRunner
    import asyncio
    ha_runner: AutomatonRunner = AutomatonRunner(hybrid_automaton=ha, sampling_rate=0.001)
    async def main(): 
        await ha_runner.run(
            x0=np.array([5.0, 0.0]), collect_automaton=False, collect_transitions=False, collect_continuous=False, collect_auxiliary=False, collect_control=False, real_time_mode=False, integrate=True, duration=30.0, dt=0.01
        )
        ha_runner.print_summary()

    asyncio.run(main())