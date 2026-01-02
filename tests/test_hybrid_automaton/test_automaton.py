import os 
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))

import pytest
import numpy as np
from unittest.mock import MagicMock, AsyncMock, patch

from hybrid_automaton.automaton import Automaton

# ----------------------
# Fixtures
# ----------------------
@pytest.fixture
def dummy_state():
    # Dummy state with minimal attributes
    state = MagicMock()
    state.get_state_id.return_value = 0
    state.name = "initial"
    return state

@pytest.fixture
def automaton_definition_states(dummy_state):
    return [dummy_state]

@pytest.fixture
def automaton(automaton_definition_states):
    # Patch Runtime so that activation does not run the actual loop
    with patch('hybrid_automaton.automaton.Runtime', autospec=True) as MockRuntime:
        mock_runtime_instance = MockRuntime.return_value
        mock_runtime_instance.activate = AsyncMock()
        mock_runtime_instance._active = True
        mock_runtime_instance.get_active_discrete_state.return_value = (0, "initial")
        mock_runtime_instance.get_continuous_state.return_value = np.array([1.0, 2.0])
        mock_runtime_instance.get_auxiliary_states.return_value = {'aux': 5}
        mock_runtime_instance.get_control_inputs.return_value = {'u': 10}
        mock_runtime_instance.get_continuous_dynamics.return_value = np.array([0.1, 0.2])
        mock_runtime_instance.get_elapsed_time.return_value = 1.5
        mock_runtime_instance.get_elapsed_time_since_transition.return_value = 0.5
        mock_runtime_instance.get_previous_transition_name.return_value = "trans1"

        ha = Automaton(
            name="test_automaton",
            states=automaton_definition_states
        )
        yield ha, MockRuntime, mock_runtime_instance

# ----------------------
# Tests
# ----------------------
def test_automaton_name_id(automaton):
    ha, _, _ = automaton
    assert ha.get_automaton_name() == "test_automaton"
    # Definition id is likely auto-generated
    assert isinstance(ha.get_automaton_id(), int)

@pytest.mark.asyncio
async def test_activate_deactivate(automaton):
    ha, MockRuntime, mock_runtime_instance = automaton

    # Activate automaton
    await ha.activate(x0=np.array([0.0, 0.0]), aux_x0={'aux': 0}, u0={'u': 0})
    MockRuntime.assert_called_once()
    mock_runtime_instance.activate.assert_awaited_once()

    # Runtime is active after activation
    assert ha._runtime._active

    # Deactivate automaton
    ha.deactivate()
    mock_runtime_instance.deactivate.assert_called_once()

def test_runtime_getters(automaton):
    ha, _, mock_runtime_instance = automaton
    ha._runtime = mock_runtime_instance  # assign mock runtime

    assert ha.get_runtime_active_discrete_state() == (0, "initial")
    np.testing.assert_array_equal(ha.get_runtime_continuous_state(), np.array([1.0, 2.0]))
    assert ha.get_runtime_auxiliary_state() == {'aux': 5}
    assert ha.get_runtime_control_input() == {'u': 10}
    np.testing.assert_array_equal(ha.get_runtime_continous_dynamics(), np.array([0.1, 0.2]))
    assert ha.get_runtime_time_elapsed() == 1.5
    assert ha.get_runtime_time_elapsed_since_transition() == 0.5
    assert ha.get_runtime_previous_transition_name() == "trans1"

def test_runtime_setters(automaton):
    ha, _, mock_runtime_instance = automaton
    ha._runtime = mock_runtime_instance  # assign mock runtime

    # Continuous state
    ha.set_runtime_continuous_state(np.array([5.0, 6.0]))
    mock_runtime_instance.set_continuous_state.assert_called_once_with(np.array([5.0, 6.0]))

    # Auxiliary state
    ha.set_runtime_auxiliary_continuous_states({'aux': 10})
    mock_runtime_instance.set_auxiliary_states.assert_called_once_with({'aux': 10})

    # Control input
    ha.set_runtime_control_inputs({'u': 20})
    mock_runtime_instance.set_control_inputs.assert_called_once_with({'u': 20})


if __name__ == '__main__': 
    pytest.main([__file__])