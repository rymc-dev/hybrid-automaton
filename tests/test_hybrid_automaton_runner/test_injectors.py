import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
import asyncio

from hybrid_automaton.automaton import Automaton

from hybrid_automaton_runner.injectors import Injector
from hybrid_automaton_runner.injectors import ContinuousStateInjector
from hybrid_automaton_runner.injectors import AuxiliaryStateInjector
from hybrid_automaton_runner.injectors import ControlInputInjector

from hybrid_automaton_runner.samplers import ContinuousStateCollector
from hybrid_automaton_runner import AutomatonRunner

import numpy as np

class TestInjector: 
    def test_init(self): 
        injector = Injector(lambda: {}, 0.001)
        assert callable(injector.fn)
        assert injector.update_rate == 0.001    

    def test_inject(self): 
        with pytest.raises(NotImplementedError):
            injector = Injector(lambda: {}, 0.001)
            asyncio.run(injector.inject(None))


# TODO: Need to figure out how I'm going to test these properly,
# since they require interaction with the automaton runtime.
# For now we just spy on the injected function to ensure it's called and returns
# the expected injectable side effect.
class TestContinuousStateInjector: 
    @pytest.mark.asyncio
    async def test_inject(self, mocker): 
        
        state_fnc = mocker.Mock()
        state_data = [
            np.array([0,0], dtype=float), 
            np.array([1.0, 1.0], dtype=float), 
            np.array([2.0, 2.0], dtype=float)
        ]
        state_fnc.side_effect = state_data
        
        collector = ContinuousStateCollector(0.01)
        injector = ContinuousStateInjector(
            lambda: state_fnc(), 
            0.01
        )
        
        ha = mocker.Mock(spec=Automaton)
        ha._runtime = mocker.Mock(spec=AutomatonRunner)
        ha._runtime._active = True
        
        injector_task = asyncio.create_task(injector.inject(ha))

        collector_task  = asyncio.create_task(collector.collect(ha))
        
        await asyncio.sleep(0.04)
        
        
        injector_task.cancel()
        collector_task.cancel()
        
        try:
            await collector_task
            await injector_task
        except asyncio.CancelledError:
            pass
        
        assert len(collector.data) == 3
        
        for idx, entry in enumerate(collector.data): 
            print (entry[1], state_data[idx])
            np.testing.assert_array_equal(entry, state_data[idx])
        
        
        
        
    
# class TestAuxiliaryStateInjector: 
#     @pytest.mark.asyncio
#     def test_inject(self): 
#         ... 
    
# class TestControlInputInjector:
#     @pytest.mark.asyncio 
#     def test_inject(self): 
#         ...
    

if __name__ == "__main__": 
    pytest.main([__file__])    