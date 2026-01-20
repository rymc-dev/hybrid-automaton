import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))
import pytest
from hybrid_automaton_runner.samplers import (
    StateCollector,
    ContinuousStateCollector,
    AuxiliaryStateCollector,
    ControlInputCollector,
    AutomatonStateCollector,
    TransitionTimeCollector
)
from hybrid_automaton.automaton import Automaton
import asyncio
from unittest.mock import MagicMock



# class TestStateCollector:  # base class
#     def test_init(self): 
#         state_collector = StateCollector()
#         assert state_collector.data == []
#         assert state_collector.sampling_rate == 0.01
        
#         state_collector = StateCollector(sampling_rate=0.1)
#         assert state_collector.sampling_rate == 0.1
    
#     def test_collect(self): 
#         with pytest.raises(NotImplementedError): 
#             state_collector = StateCollector()
#             asyncio.run(state_collector.collect(None))
    
#     def test_clear(self): 
#         state_collector = StateCollector()
#         state_collector.data = [[0, [1, 2, 3]], [0.01, [1, 2, 4]]]
#         state_collector.clear()
#         assert state_collector.data == []
    
#     def test_get_data(self): 
#         state_collector = StateCollector()
#         state_collector.data = [[0, [1, 2, 3]], [0.01, [1, 2, 4]]]
#         data = state_collector.get_data()
#         assert data == [[0, [1, 2, 3]], [0.01, [1, 2, 4]]]

class TestMockStateCollector: 
    class MockStateCollector(StateCollector): 
        def __init__(self, sampling_rate = 0.01, dir_path = "./tests", sample_write_interval = 1000):
            super().__init__(sampling_rate, dir_path, "test_state", sample_write_interval)
            
        def _collect(self, ha):
            while True: 
                await asyncio.sleep()
            
            
    @pytest.mark.ascynio
    async def test_mock_state_collector(self): 
        collector = TestMockStateCollector.MockStateCollector()
        import os
        assert os.path.isfile(collector._file_path)            
        import csv
        with open(collector._file_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            assert header == ['timestamp', 'state']
            with pytest.raises(Exception):
                next(reader)

        mock_automaton: Automaton = MagicMock(spec=Automaton)
        await collector.run(mock_automaton)
        
        
                
        
                
        

# class TestContinuousStateCollector:
#     @pytest.mark.asyncio
#     async def test_collect(self, mocker):
#         # Create collector with faster sampling for testing
#         collector = ContinuousStateCollector(sampling_rate=0.01)
        
#         # Create mock automaton
#         ha = mocker.Mock(spec=Automaton)
        
#         # Mock the methods that will be called
#         time_values = [0.0, 0.01, 0.02, 0.03]
#         state_values = [[1.0, 2.0], [1.1, 2.1], [1.2, 2.2], [1.3, 2.3]]
        
#         ha.get_runtime_time_elapsed.side_effect = time_values
#         ha.get_runtime_continuous_state.side_effect = state_values
        
#         # Run collector for a short time then cancel
#         task = asyncio.create_task(collector.collect(ha))
#         await asyncio.sleep(0.05)  # Let it collect a few samples
#         task.cancel()
        
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass
        
#         # Verify data was collected
#         assert len(collector.data) > 0
#         assert len(collector.data) <= len(time_values)
        
#         # Check structure of collected data
#         for entry in collector.data:
#             assert len(entry) == 2
#             assert isinstance(entry[0], float)  # time
#             assert isinstance(entry[1], list)   # state


# class TestAuxiliaryStateCollector:
#     @pytest.mark.asyncio
#     async def test_collect(self, mocker):
#         collector = AuxiliaryStateCollector(sampling_rate=0.01)
        
#         ha = mocker.Mock(spec=Automaton)
        
#         # Mock time and auxiliary function
#         time_values = [0.0, 0.01, 0.02, 0.03]
#         aux_values = [10.0, 10.5, 11.0, 11.5]
        
#         ha.get_runtime_time_elapsed.side_effect = time_values
#         get_aux_fn = mocker.Mock(side_effect=aux_values)
        
#         # Run collector
#         task = asyncio.create_task(collector.collect(ha, get_auxiliary_fn=get_aux_fn))
#         await asyncio.sleep(0.05)
#         task.cancel()
        
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass
        
#         # Verify data was collected
#         assert len(collector.data) > 0
        
#         for entry in collector.data:
#             assert len(entry) == 2
#             assert isinstance(entry[0], float)  # time


# class TestControlInputCollector:
#     @pytest.mark.asyncio
#     async def test_collect(self, mocker):
#         collector = ControlInputCollector(sampling_rate=0.01)
        
#         ha = mocker.Mock(spec=Automaton)
        
#         # Mock time and control function
#         time_values = [0.0, 0.01, 0.02, 0.03]
#         control_values = [5.0, 5.1, 5.2, 5.3]
        
#         ha.get_runtime_time_elapsed.side_effect = time_values
#         get_control_fn = mocker.Mock(side_effect=control_values)
        
#         # Run collector
#         task = asyncio.create_task(collector.collect(ha, get_control_fn=get_control_fn))
#         await asyncio.sleep(0.05)
#         task.cancel()
        
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass
        
#         # Verify data was collected
#         assert len(collector.data) > 0
        
#         for entry in collector.data:
#             assert len(entry) == 2
#             assert isinstance(entry[0], float)  # time


# class TestAutomatonStateCollector:
#     @pytest.mark.asyncio
#     async def test_collect(self, mocker):
#         collector = AutomatonStateCollector(sampling_rate=0.01)
        
#         ha = mocker.Mock(spec=Automaton)
        
#         # Mock time and discrete state
#         time_values = [0.0, 0.01, 0.02, 0.03]
#         state_values = [(0, "state_a"), (0, "state_a"), (1, "state_b"), (1, "state_b")]
        
#         ha.get_runtime_time_elapsed.side_effect = time_values
#         ha.get_runtime_active_discrete_state.side_effect = state_values
        
#         # Run collector
#         task = asyncio.create_task(collector.collect(ha))
#         await asyncio.sleep(0.05)
#         task.cancel()
        
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass
        
#         # Verify data was collected
#         assert len(collector.data) > 0
        
#         for entry in collector.data:
#             assert len(entry) == 2
#             assert isinstance(entry[0], float)   # time
#             assert isinstance(entry[1], str)     # discrete state name


# class TestTransitionTimeCollector:
#     @pytest.mark.asyncio
#     async def test_collect(self, mocker):
#         collector = TransitionTimeCollector(sampling_rate=0.01)
        
#         ha = mocker.Mock(spec=Automaton)
        
#         # Mock discrete state and time since transition
#         discrete_states = [(0, "state_a"), (0, "state_a"), (1, "state_b"), (1, "state_b")]
#         transition_times = [0.0, 0.01, 0.0, 0.01]
        
#         ha.get_runtime_active_discrete_state.side_effect = discrete_states
#         ha.get_runtime_time_elapsed_since_transition.side_effect = transition_times
        
#         # Run collector
#         task = asyncio.create_task(collector.collect(ha))
#         await asyncio.sleep(0.05)
#         task.cancel()
        
#         try:
#             await task
#         except asyncio.CancelledError:
#             pass
        
#         # Verify data was collected
#         assert len(collector.data) > 0
        
#         for entry in collector.data:
#             assert len(entry) == 2
#             assert isinstance(entry[0], tuple)   # discrete state tuple
#             assert isinstance(entry[1], float)   # time since transition
            
            
if __name__ == '__main__': 
    pytest.main([__file__])