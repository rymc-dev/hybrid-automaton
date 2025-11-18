from hybrid_automaton import Automaton, State, Transition
import asyncio

def main():
    def guard(*args, **kwargs):
        return True
    
    def reset(*args, **kwargs):
        return None, None

    state_1 = State(
        name="start",
        initial=True
    )
    state_2 = State(
        name = "end",
        final=True
    )
    state_1.add_transition(
        Transition(
            name="transition_1",
            to_state=state_2,
            guards=[guard],
            reset=reset
        )
    )
    state_1.add_transition(
        Transition(
                name="transition_1",
                to_state=state_2,
                guards=[guard],
                priority=2
            )
    )
    ha = Automaton(
        name="Transition automaton",
        real_time_mode=True,
        states=[state_1, state_2],
    )

    step_result = ha.step()

    print (step_result)
    print(ha.q)
    
    step_result = ha.step()

    print (step_result)
    print (ha.q)
    # import numpy as np
    # # position [x, y, z] and quaternion [qx, qy, qz, qw]
    # x_t0 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    # x_u0 = None
    # ctx_t0 = {
    #     'waypoint': np.array([0.0, 0.0]),
    #     'virtual_waypoint': np.array([0.0, 0.0])
    # }
    # dt = 0.1  # Adjusted to a small positive value for time step
    # async def step():
    #     await ha.step()

    # asyncio.run(step())

    # print('here')

    


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
