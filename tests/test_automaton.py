import pytest
from hybrid_automaton import Automaton, State, Transition

    # ha = Automaton(
    #     name="thermostat",
    #     states=[q1, q2],
    #     real_time_mode=True
    #     dt = 0.1
    # )

def test_initialization():

    too_hot_threshold = 25
    too_cold_threshold = 20
    integration_method = lambda flow, x, aux_x, u, ctx, dt: x + flow(x, aux_x, u, ctx, dt) * dt

    q1 = State(
        name="warm up",
        initial=True,
        flow=lambda x, aux_x, u, ctx, dt: x + 1.0 * dt,   # temperature increases
        integration_method=integration_method
    )

    q2 = State(
        name="cool down",
        initial=False,
        flow=lambda x, aux_x, u, ctx, dt: x - 1.0 * dt   # temperature decreases
    )

    d1 = Transition(
        name="too hot",
        to_state=q2,
        guards=[lambda x, aux_x, u, ctx, dt: x > too_hot_threshold]
    )

    d2 = Transition(
        name="too cold",
        to_state=q1,
        guards=[lambda x, aux_x, u, ctx, dt: x < too_cold_threshold]
    )

    q1.add_transition(d1)
    q2.add_transition(d2)


    h = Automaton(
        name='thermostate', 
        states=[q1, q2],
        real_time_mode=True,
        integration_method=integration_method,
        dt=0.1
    )