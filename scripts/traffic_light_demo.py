# ! /bin/python

import sys
import os
import asyncio
import numpy as np
import matplotlib.pyplot as plt
 
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from hybrid_automatons import traffic_lights
from hybrid_automaton import Automaton
from hybrid_automaton_evaluation.figure_generator import generate_time_since_last_transition_over_time

traffic_lights_ha: Automaton = traffic_lights(
    time_in_green=8.0,
    time_in_yellow=3.0,
    time_in_red=5.0
)

x = []
time_since_last_transition = []

async def runner():
    async def store_continous_state_data(): 
        asyncio.sleep(0.01)
        while True:
            try: 
                x.append([traffic_lights_ha.get_active_elapsed_time(), traffic_lights_ha.get_continous_state()])
            except Exception as e: 
                print (e)

            await asyncio.sleep(0.01)

    async def store_automaton_state(): 
        asyncio.sleep(0.01)
        while True:
            try: 
                time_since_last_transition.append(
                    [traffic_lights_ha.get_active_elapsed_time(), traffic_lights_ha.get_activate_elapsed_time_since_last_transition()]
                )
            except Exception as e: 
                print (str(e))
        
            await asyncio.sleep(0.001)

    async def deactivate_after_10_seconds(*tasks): 
        await asyncio.sleep(1.0)
        for t in tasks:
            t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        print ('tasks completed')
        
    t1 =  asyncio.create_task(traffic_lights_ha.activate(x0=None, real_time_mode=False, integrate=False))
    t2 = asyncio.create_task(store_continous_state_data())
    t3 = asyncio.create_task(store_automaton_state())
    
    await asyncio.create_task(deactivate_after_10_seconds(t1, t2, t3))
    

    
    times = np.array([row[0] for row in time_since_last_transition])
    time_since_last_transitions = np.array([row[1] for row in time_since_last_transition])

    fig = generate_time_since_last_transition_over_time(times, time_since_last_transition)

    plt.show()
    
    import time
    
    time.sleep(10.0)

asyncio.run(runner())