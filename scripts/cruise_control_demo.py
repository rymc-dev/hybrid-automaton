# ! /bin/python

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from hybrid_automatons import cruise_control
from hybrid_automaton import Automaton
import numpy as np

cruise_control_ha: Automaton = cruise_control(
    target_speed=30.0,
    safe_distance=50.0,
    danger_close=20.0,
    car_ahead_speed=20.0
)

async def runner():
    await cruise_control_ha.activate(x0=np.array([20.0, 100.0]), real_time_mode=True, integrate=True, dt=1.0)
    
import asyncio 

asyncio.run(runner())