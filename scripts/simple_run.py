from hybrid_automaton import HybridAutomaton, HybridState, HybridTransition
import asyncio

def main():
    def guard(*args, **kwargs):
        return True

    state_1 = HybridState(
        name="start",
        value=0,
        initial=True
    )


    state_2 = HybridState(
        name = "end",
        value=1,
        final=True
    )
    state_1.add_transition(
        HybridTransition(
            name="transition_1",
            value=1,
            to_state=state_2,
            guards=[guard],
        )
    )
    state_1.add_transition(
        HybridTransition(
                name="transition_1",
                value=2,
                to_state=state_2,
                guards=[guard],
                priority=2
            )
    )
    ha = HybridAutomaton(
        name="tb3 automaton",
        value=0,
        real_time_mode=True,
        states=[state_1, state_2],
    )
    import numpy as np
    # position [x, y, z] and quaternion [qx, qy, qz, qw]
    x_t0 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    x_u0 = None
    ctx_t0 = {
        'waypoint': np.array([0.0, 0.0]),
        'virtual_waypoint': np.array([0.0, 0.0])
    }
    dt = 0.1  # Adjusted to a small positive value for time step



    


    # import threading

    # thread_1 = threading.Thread(
    #     target=asyncio.run(
    #         ha.evluation_loop_worker(x_t0, x_u0, ctx_t0, dt)
    #     )
    # ).start()

    # thread_2 = threading.Thread(
    #     target=asyncio.run(
    #         ha.evluation_loop_worker(x_t0, x_u0, ctx_t0, dt)
    #     )
    # ).start()

    # import time
    # time.sleep(10.0)

if __name__ == '__main__':
    main()
