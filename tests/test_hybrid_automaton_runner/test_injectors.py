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

class TestInjector: 
    def test_init(self): 
        injector = Injector(lambda: {}, 0.001)
        assert callable(injector.aux_state_fn)
        assert injector.update_rate == 0.001    

    def test_inject(self): 
        with pytest.raises(NotImplementedError):
            injector = Injector(lambda: {}, 0.001)
            asyncio.run(injector.inject(None))

class TestContinuousStateInjector: 
    @pytest.mark.asyncio
    def test_inject(self, mocker): 
        injector = ContinuousStateInjector(lambda: {}, 0.001)
        
        ha = mocker.Mock(spec=Automaton)
        
        time_values = [0.0, 0.01, 0.02]
        state_values = [{'x': 1}, {'x': 2}, {'x': 3}]
        
        
    
class TestAuxiliaryStateInjector: 
    @pytest.mark.asyncio
    def test_inject(self): 
        ... 
    
class TestControlInputInjector:
    @pytest.mark.asyncio 
    def test_inject(self): 
        ...
    

if __name__ == "__main__": 
    pytest.main([__file__])    