# import sys
# import os

# sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))

# import numpy as np
# import asyncio
# import pytest
# from unittest.mock import MagicMock, AsyncMock, patch

# # Import your Runtime class
# from hybrid_automaton._runtime import Runtime

# # ----------------------
# # Mock dependencies
# # ----------------------
# class DummyState:
#     def __init__(self, state_id=0, name="initial", is_final=False):
#         self._state_id = state_id
#         self.name = name
#         self._is_final = is_final
#         self.on_enter = MagicMock()
#         self.on_exit = MagicMock()
    
#     def get_state_id(self):
#         return self._state_id
    
#     def continuous_dynamics(self, ctx):
#         return np.array([1.0, 2.0])
    
#     def evaluate_transitions(self, ctx):
#         return []
    
#     def check_invariants(self, ctx):
#         return True

# class DummyDefinition:
#     def __init__(self):
#         self.name = "dummy_automaton"
#         self.state_t0 = DummyState()
#         self.on_entry = MagicMock()
#         self.on_exit = MagicMock()
    
#     def get_configuration(self):
#         return {}

# class DummyClock:
#     def __init__(self, dt=0.1, real_time_mode=False):
#         self._time_elapsed = 0.0
#         self._dt = dt
#         self._real_time_mode = real_time_mode

#     def get_time_elapsed_active(self):
#         return self._time_elapsed
    
#     def get_time_elapsed_since_last_transition(self):
#         return self._time_elapsed
    
#     def get_dt(self):
#         return self._dt

#     def is_real_time(self):
#         return self._real_time_mode

#     async def activate(self):
#         return

#     async def sleep_for_dt(self):
#         await asyncio.sleep(0.001)

#     def step_dt(self):
#         self._time_elapsed += self._dt

#     def ping_transition(self):
#         pass

# class DummyContext:
#     def __init__(self):
#         self.clk = DummyClock()
#         self.x = MagicMock()
#         self.aux = {}
#         self.u = {}

# # ----------------------
# # Pytest fixtures
# # ----------------------
# @pytest.fixture
# def dummy_definition():
#     return DummyDefinition()

# @pytest.fixture
# def runtime(dummy_definition):
#     # Patch Context in Runtime to use DummyContext
#     with patch('hybrid_automaton.automaton_runtime.Context', return_value=DummyContext()):
#         rt = Runtime(dummy_definition, x0=np.array([0, 0]))
#         yield rt

# # ----------------------
# # Tests
# # ----------------------
# def test_initial_state(runtime):
#     state_id, state_name = runtime.get_active_discrete_state()
#     assert state_id == 0
#     assert state_name == "initial"

# def test_continuous_state_setter_getter(runtime):
#     arr = np.array([1.0, 2.0])
#     runtime.set_continuous_state(arr)
#     runtime._ctx.x.set_continous_state.assert_called_with(arr)

# def test_evaluation_step_no_transition(runtime):
#     runtime._active = True
#     runtime._evaluation_step()
#     np.testing.assert_array_equal(runtime._xdot, np.array([1.0, 2.0]))

# @pytest.mark.asyncio
# async def test_activate_deactivate(runtime, dummy_definition):
#     with patch.object(runtime, '_run_automaton_loop', new=AsyncMock()) as mock_loop:
#         await runtime.activate()
#         mock_loop.assert_awaited_once()
#         dummy_definition.on_entry.assert_called_once()
#         dummy_definition.on_exit.assert_called_once()
    
#     runtime.deactivate()
#     assert not runtime._active


# if __name__ == '__main__': 
#     pytest.main([__file__])