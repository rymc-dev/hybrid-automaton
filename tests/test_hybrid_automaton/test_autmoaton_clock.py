import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))

import asyncio
import time
import pytest
from hybrid_automaton.automaton_clock import Clock

DT = 1.3

@pytest.fixture(scope="class")
def real_time_clock(): 
    return Clock(real_time_mode=True, dt=DT)

@pytest.fixture(scope="class")
def simulation_time_clock(): 
    return Clock(real_time_mode=False, dt=DT)


@pytest.mark.usefixtures("real_time_clock")
class TestRealTimeClock: 

    def test_is_real_time(self, real_time_clock: Clock):
        assert real_time_clock.is_real_time()
    
    def test_step_dt_raises(self, real_time_clock: Clock): 
        with pytest.raises(SystemError): 
            real_time_clock.step_dt()
        
    def test_get_dt(self, real_time_clock: Clock): 
        assert real_time_clock.get_dt() == DT
    
    @pytest.mark.asyncio
    async def test_sleep_for_dt(self, real_time_clock: Clock): 
        start_stamp = time.perf_counter_ns()
        await real_time_clock.sleep_for_dt()
        after_stamp = time.perf_counter_ns()
        
        delta_seconds = (after_stamp - start_stamp) / 1e9
        assert abs(delta_seconds - DT) < 0.01
        
    def test_get_elapsed_time_active_initial(self, real_time_clock: Clock): 
        assert real_time_clock.get_elapsed_time_active() == 0.0
    
    def test_get_time_elapsed_since_transition_initial(self, real_time_clock: Clock): 
        assert real_time_clock.get_time_elapsed_since_transition() == 0.0
        
    def test_ping_transition(self, real_time_clock: Clock): 
        real_time_clock.ping_transition()
        assert real_time_clock.get_time_elapsed_since_transition() == 0.0
    
    @pytest.mark.asyncio
    async def test_activate_and_deactivate(self, real_time_clock: Clock): 
        async def run_and_stop():
            # schedule deactivate after short delay
            await asyncio.sleep(3.0)
            real_time_clock.deactivate()

        activate_task = asyncio.create_task(real_time_clock.activate())
        stop_task = asyncio.create_task(run_and_stop())

        await asyncio.gather(activate_task, stop_task)

        assert real_time_clock._running is False
        assert real_time_clock.get_elapsed_time_active() > 0.0


@pytest.mark.usefixtures("simulation_time_clock")
class TestSimulationTimeClock:

    def test_is_real_time(self, simulation_time_clock: Clock):
        assert not simulation_time_clock.is_real_time()
    
    def test_get_dt(self, simulation_time_clock: Clock): 
        assert simulation_time_clock.get_dt() == DT
    
    def test_step_dt_updates(self, simulation_time_clock: Clock): 
        before_elapsed = simulation_time_clock.get_elapsed_time_active()
        before_since_transition = simulation_time_clock.get_time_elapsed_since_transition()

        simulation_time_clock.step_dt()

        after_elapsed = simulation_time_clock.get_elapsed_time_active()
        after_since_transition = simulation_time_clock.get_time_elapsed_since_transition()

        assert after_elapsed == pytest.approx(before_elapsed + DT)
        assert after_since_transition == pytest.approx(before_since_transition + DT)
    
    @pytest.mark.asyncio
    async def test_sleep_for_dt(self, simulation_time_clock: Clock): 
        start_stamp = time.perf_counter_ns()
        await simulation_time_clock.sleep_for_dt()
        after_stamp = time.perf_counter_ns()
        delta_seconds = (after_stamp - start_stamp) / 1e9
        assert abs(delta_seconds - DT) < 0.01
        
    def test_get_elapsed_time_active_initial(self, simulation_time_clock: Clock): 
        assert simulation_time_clock.get_elapsed_time_active() == DT
    
    def test_get_time_elapsed_since_transition_initial(self, simulation_time_clock: Clock): 
        assert simulation_time_clock.get_time_elapsed_since_transition() == DT
        
    def test_ping_transition(self, simulation_time_clock: Clock): 
        simulation_time_clock.ping_transition()
        assert simulation_time_clock.get_time_elapsed_since_transition() == 0.0


if __name__ == '__main__':
    pytest.main([__file__])