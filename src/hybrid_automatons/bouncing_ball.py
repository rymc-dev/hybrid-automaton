"""
sample implementation using v0.0.4 of the hybrid automaton package for a bouncing ball
"""

from hybrid_automaton import Automaton, State, Transition
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

    def flying_flow(x, aux_x, u, cfg, clk):
        """Free fall: x = [y, v], dx/dt = [v, g]."""
        y, v = x.get_continous_state()
        return np.array([v, cfg['gravity']])


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
        new_state = np.array([0.0, -v * cfg['restitution']])
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