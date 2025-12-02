import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
from hybrid_automatons import bouncing_ball
from hybrid_automaton_evaluation.figure_generator import generate_mode_timeseries_figure
import asyncio


ball = bouncing_ball()


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
    
    fig = generate_mode_timeseries_figure()

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
