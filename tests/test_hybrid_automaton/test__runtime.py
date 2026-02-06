import os
import sys

sys.path.append("/home/ryan/hybrid-automaton/src/hybrid_automaton")

import pytest
import asyncio


class TestRuntimeLogger: 
    ... 

class TestRuntimeClock:
    # @pytest.fixture  
    def clock(self, dt, real_time_mode, timeout_event, deactivate_event, timeout_sec): 
        from hybrid_automaton._runtime import _Runtime 
        Clock = _Runtime.Context.Clock
        return Clock(
            dt=dt,
            real_time_mode=real_time_mode,
            timeout_event=timeout_event,
            deactivate_event=deactivate_event,
            timeout_sec=timeout_sec
        )
     
    def test_init(self): 
        clock = self.clock(
            dt=0.1, 
            real_time_mode=True, 
            timeout_event=None, 
            deactivate_event=None, 
            timeout_sec=10
        )
        
        assert clock._dt == 0.1
        assert clock._real_time_mode == True
        assert clock._timeout_event == None
        assert clock._deactivate_event == None
        assert clock._timeout_sec == 10
         
    @pytest.mark.parametrize(
        "dt, expected_t", 
        [
            0.1, 
            0.2, 
            0.5
        ]
        
    )
    def test_step_dt(self, dt): 
        clock = self.clock(
            dt=dt
        )
        import time
        start_time = time.perf_counter_ns()
        clock.step_dt()
        duration = time.perf_counter_ns() - start_time
        duration_sec = duration / 1e9
        
        assert clock.get_elapsed_time_active() == dt
        assert abs(duration_sec - dt) < 0.05
        

class TestRuntimeContext:
    ...

class TestRuntime: 
    ... 
    
    
if __name__ == '__main__': 
    pytest.main([__file__])