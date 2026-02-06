"""
sample implementation using v0.0.4 of the hybrid automaton package for a bouncing ball
"""
import os 
import sys
import time

import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from hybrid_automaton import Automaton
from hybrid_automaton import RuntimeContext 
from hybrid_automaton.definition import guard 
from hybrid_automaton.definition import reset 
from hybrid_automaton.definition import invariant 
from hybrid_automaton.definition import continuous_dynamics 
from hybrid_automaton.definition import State 
from hybrid_automaton.definition import Transition


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
    def flying_flow(ctx: RuntimeContext) -> np.ndarray:
        """Free fall: x = [y, v], dx/dt = [v, g]."""
        y, v = ctx.continuous_state.latest()
        return np.array([v, ctx.configuration['gravity']])

    @continuous_dynamics
    def ground_flow(ctx: RuntimeContext) -> np.ndarray:
        """Ball resting on the ground momentarily (contact dynamics)."""
        return np.array([0.0, 0.0])

    @continuous_dynamics
    def resting_flow(ctx: RuntimeContext) -> np.ndarray:
        """Ball at complete rest - no dynamics."""
        return np.array([0.0, 0.0])


    # ============================
    #   Guards
    # ============================

    @guard
    def hits_ground(ctx: RuntimeContext) -> bool:
        """Ball contacts ground while moving downward."""
        y, v = ctx.continuous_state.latest()
        return y <= 0.0 and v < 0

    @guard
    def bounce_possible(ctx: RuntimeContext) -> bool:
        """Ball has upward rebound velocity after impact."""
        y, v = ctx.continuous_state.latest()
        return abs(v) > 0.1  # Check the velocity AFTER bounce


    @guard
    def no_more_bounce(ctx: RuntimeContext) -> bool:
        """Ball has lost all bounce energy."""
        y, v = ctx.continuous_state.latest()
        return abs(v) <= 0.1


    # ============================
    #   Reset maps
    # ============================
    @reset
    def bounce_reset(ctx: RuntimeContext) -> RuntimeContext:
        """Apply bounce: set y=0, reverse velocity with restitution."""
        y, v = ctx.continuous_state.latest()
        new_v = -v * ctx.configuration['restitution']
        ctx.continuous_state.set_continuous_state(np.array([0.0, new_v]))
        return ctx

    @reset
    def stop_reset(ctx: RuntimeContext) -> RuntimeContext:
        """Final rest: position 0, velocity 0."""
        ctx.continuous_state.set_continuous_state(np.array([0.0, 0.0]))
        return ctx


    # ============================ 
    #  Invariants
    # ============================

    @invariant
    def failing_invariant(ctx: RuntimeContext) -> bool: 
        return False


    # ============================
    #   States
    # ============================

    flying = State(
        name="FLYING",
        initial=True,
        flow=flying_flow,
        on_enter=lambda: print(f"[ENTER] FLYING"),
        on_exit=lambda: print(f"[EXIT] FLYING"),
    )

    ground = State(
        name="GROUND",
        flow=ground_flow,
        on_enter=lambda: print(f"[ENTER] GROUND"),
        on_exit=lambda: print(f"[EXIT] GROUND"),
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
    
     
async def main():
    
    from hybrid_automaton import RunResult 
    try:        
        results: RunResult = await ha.activate(
            initial_continuous_state=np.array([5.0, 5.0]),
            enable_real_time_mode=False,
            continuous_state_sampler_enabled=True,
            continuous_state_sampler_rate=100,
            auxiliary_states_sampler_enabled=True,
            auxiliary_states_sampler_rate=1,
            control_input_states_sampler_enabled=True,
            control_input_states_sampler_rate=1,
            enable_self_integration=True,
            delta_time=0.001,
            timeout_sec=5.0,
            output_dir = "/home/ryan/hybrid-automaton/log_hybrid_automaton/bouncing_ball" # TODO: Have the
        ) 
    except Exception as e:
        print(f"Exception: Automaton execution terminated with exception: {e}")
        sys.exit(1)
        
    from matplotlib import pyplot as plt
    from hybrid_automaton_evaluation.visualization.figure_generator import continuous_states_over_time_fig, automaton_states_over_time
    
    fig1 = continuous_states_over_time_fig(results)
    fig2 = automaton_states_over_time(results) 
    plt.show()
    
    print (results)
    print ('Complete!')
    
if __name__ == '__main__': 
    import asyncio

    ha = bouncing_ball()
    print (ha)
    print (repr(ha))  
    asyncio.run(main())