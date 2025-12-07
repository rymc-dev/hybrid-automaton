from hybrid_automaton.automaton_clock import Clock
import pytest
import pytest_asyncio
import time
import asyncio

DT = 1.3

@pytest.fixture(scope="class")
def real_time_clock(): 
    return Clock(
        real_time_mode=True,
        dt=DT
    )

@pytest.fixture(scope="class")
def simulation_time_clock_fixture():
    return Clock(
        real_time_mode=False,
        dt=DT
    )

@pytest.mark.usefixtures("real_time_clock")
class TestRealTimeClock: 
    def test_is_real_time(self, real_time_clock: Clock):
        assert real_time_clock.is_real_time()
    
    def test_step_dt(self, real_time_clock: Clock): 
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
        dt = real_time_clock.get_dt()
        tolerance = 0.002
        assert abs((delta_seconds) - dt) < tolerance
        
    def test_get_elapsed_time_active(self, real_time_clock: Clock): 
        real_time_clock.get_elapsed_time_active() == 0.0
    
    def test_get_time_elapsed_since_transition(self, real_time_clock: Clock): 
        real_time_clock.get_elapsed_time_active() == 0.0
        
    def test_ping_transition(self, real_time_clock: Clock): 
        real_time_clock.ping_transition()
    
    @pytest.mark.ascynio
    async def test_activate(self, real_time_clock: Clock): 
        t1 = asyncio.create_task(real_time_clock.activate)  
        
        async def assert_time_updates():
            assert True
            
        async def sleep_till_deactivate(*tasks, timeout_sec: float = 2.0):
            await asyncio.sleep(timeout_sec)
            real_time_clock.deactivate()
            assert real_time_clock._running == False
            

        t2 = asyncio.create_task(assert_time_updates)
        t3 = asyncio.create_task(lambda tasks: sleep_till_deactivate(tasks))
        
        
        asyncio.gather(
            t1, t2, t3
        )
            
        assert True
        
        
    @pytest.mark.ascynio
    def test_deactivate(self):
        ...
    
# class TestSimulationTimeClock:
#     ...

if __name__ == '__main__':
    pytest.main([__file__])