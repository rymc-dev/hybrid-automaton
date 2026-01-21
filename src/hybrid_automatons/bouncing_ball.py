"""
sample implementation using v0.0.4 of the hybrid automaton package for a bouncing ball
"""

import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from hybrid_automaton import Automaton, State, Transition
from hybrid_automaton.automaton_runtime import Context
from hybrid_automaton.automaton_annotations import guard, reset, invariant, continuous_dynamics
from hybrid_automaton_runner.run_data import AutomatonRunData
import time
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
        """Ball resting on the ground momentarily (contact dynamics)."""
        return np.array([0.0, 0.0])

    @continuous_dynamics
    def resting_flow(ctx: Context) -> np.ndarray:
        """Ball at complete rest - no dynamics."""
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
        return abs(v) > 0.1  # Check the velocity AFTER bounce


    @guard
    def no_more_bounce(ctx: Context) -> bool:
        """Ball has lost all bounce energy."""
        y, v = ctx.x.latest()
        return abs(v) <= 0.1


    # ============================
    #   Reset maps
    # ============================
    @reset
    def bounce_reset(ctx: Context) -> Context:
        """Apply bounce: set y=0, reverse velocity with restitution."""
        y, v = ctx.x.latest()
        new_v = -v * ctx.cfg['restitution']
        ctx.x.set_continuous_state(np.array([0.0, new_v]))
        return ctx

    @reset
    def stop_reset(ctx: Context) -> Context:
        """Final rest: position 0, velocity 0."""
        ctx.x.set_continuous_state(np.array([0.0, 0.0]))
        return ctx


    # ============================ 
    #  Invariants
    # ============================

    @invariant
    def failing_invariant(ctx: Context) -> bool: 
        return False


    # ============================
    #   States
    # ============================

    flying = State(
        name="FLYING",
        initial=True,
        flow=flying_flow,
        on_enter=lambda: print(f"[{time.time()}] [ENTER] FLYING"),
        on_exit=lambda: print(f"[{time.time()}] [EXIT] FLYING"),
    )

    ground = State(
        name="GROUND",
        flow=ground_flow,
        on_enter=lambda: print(f"[{time.time()}] [ENTER] GROUND"),
        on_exit=lambda: print(f"[{time.time()}] [EXIT] GROUND"),
    )

    resting = State(
        name="RESTING",
        flow=resting_flow,
        final=True,
        invariants=[failing_invariant],
        on_enter=lambda: print(f"[{time.time()}] [ENTER] RESTING (ball has stopped)"),
        on_exit=lambda: print(f"[{time.time()}] [EXIT] RESTING"),
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
            priority=2
        )
    )

    # GROUND → RESTING (final rest - no more bouncing)
    ground.add_transition(
        Transition(
            "come_to_rest",
            resting,
            guards=[no_more_bounce],
            reset=stop_reset,
            priority=1  # only after bounce_up is no longer possible
        )
    )


    # ============================
    #   Build automaton
    # ============================

    return Automaton(
        name="Bouncing Ball",
        version="0.0.1",
        states=[flying, ground, resting],
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
    from typing import Tuple, Optional
    from hybrid_automaton.exit_codes import ExitCode
    ha_runner: AutomatonRunner = AutomatonRunner(hybrid_automaton=ha)
    async def main(): 
        try:         
            results: AutomatonRunData = await ha_runner.activate(
                initial_continuous_state=np.array([5.0, 5.0]),
                should_sample_continuous_states=True,
                enable_real_time_mode=False,
                sample_rate_continuous_states=0.01,
                should_integrate=True,
                delta_time=0.001,
                timeout_sec=30.0,
                output_dir = "./log_hybrid_automaton/bouncing_ball/"
            )
        except Exception as e:
            print(f"Exception: Automaton execution terminated with exception: {e}")
            sys.exit(1)
            
        print (results.automaton_exit)
            
        # results.print_summary()
        # # results = ha_runner.get_results()
        # from matplotlib import pyplot as plt
        # from hybrid_automaton_evaluation.visualization import  automaton_states_over_time, continuous_states_over_time_fig, transitions_times_over_time_fig
        # fig1 = continuous_states_over_time_fig(results['continuous_states'], state_labels=['Height (m)', 'Velocity (m/s)'])
        # # fig2 = transitions_times_over_time_fig(results['transition_times']) # TODO: Need to fix this
        # fig5 = automaton_states_over_time(results['automaton_states'])
        # plt.show()

    asyncio.run(main())