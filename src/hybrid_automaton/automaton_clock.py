import asyncio
import time

class Clock:
    """clock, runs a clock instance that is utilized
    for real-time/simulation time for the automaton runtime"""
    def __init__(self, dt: float, real_time_mode: bool):
        self._real_time_mode: bool = real_time_mode
        self._dt: float = dt

        self._global_time: float = 0.0
        self._global_time_start: float = 0.0
        self._time_elapsed_active: float = 0.0
        self._time_elapsed_since_last_transition: float = 0.0
        self._last_transition_time: float = 0.0

        self._running: bool = False  # Add running flag for start/stop

    def step_dt(self):
        if self._real_time_mode:
            raise SystemError(
            "trying to step `dt` when we are in real time mode."
            )
        self._time_elapsed_active += self._dt
        self._time_elapsed_since_last_transition += self._dt

    async def sleep_for_dt(self):
        await asyncio.sleep(self._dt)

    def get_dt(self) -> float: 
        return self._dt
    
    def get_time_elapsed_active(self): 
        return self._time_elapsed_active
    
    def get_time_elapsed_since_last_transition(self):
        return self._time_elapsed_since_last_transition
    
    def is_real_time(self): 
        return self._real_time_mode

    def ping_transition(self):
        """
        Call this method whenever a transition occurs to reset the
        time elapsed since last transition.
        """
        if self._real_time_mode:
            now = time.perf_counter()
            self._last_transition_time = now
            self._time_elapsed_since_last_transition = 0.0
        else:
            self._time_elapsed_since_last_transition = 0.0

    async def activate(self): 
        if not self._real_time_mode:
            raise SystemError(
            "Attempted to start clock in simulation mode, which is invalid."
            )

        self._global_time_start = time.perf_counter()
        self._time_elapsed_active = 0.0
        self._time_elapsed_since_last_transition = 0.0
        self._last_transition_time = self._global_time_start

        self._running = True
        while self._running: 
            await asyncio.sleep(0.001)
            now = time.perf_counter()
            self._global_time = now
            self._time_elapsed_active = now - self._global_time_start
            self._time_elapsed_since_last_transition = now - self._last_transition_time

    def deactivate(self):
        """Stops the clock timer loop."""
        self._running = False