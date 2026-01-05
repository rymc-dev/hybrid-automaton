import pytest


from hybrid_automaton.automaton import Automaton

from hybrid_automaton_runner.runner import AutomatonRunner

@pytest.fixture
def simple_automaton(mocker): 
    ha = mocker.Mock(spec=Automaton)
    return ha



# TODO: This is a complex object, need to figure out testing strategy
@pytest.mark.usefixtures("simple_automaton")
class TestAutomatonRunner: 
    def test_init(self): 
        
        runner = AutomatonRunner(
            hybrid_automaton=self.simple_automaton,
            sampling_rate=0.02
        )
        
        assert runner.ha == self.simple_automaton
        assert runner.sampling_rate == 0.02   
        assert hasattr(runner, 'continuous_collector')
        assert hasattr(runner, 'auxiliary_collector')
        assert hasattr(runner, 'control_collector')
        assert hasattr(runner, 'automaton_collector')
        assert hasattr(runner, 'transition_collector')
        
        assert runner._tasks == []
        assert runner._stop_requested is False
        
        
    def run_defaults(self): 
        runner = AutomatonRunner(
            hybrid_automaton=self.simple_automaton
        )
        
        assert runner.sampling_rate == 0.01
    
    
    
if __name__ == '__main__':
    import os
    import sys
    
    sys.path.insert() 
    pytest.main([__file__])