import pytest
from hybrid_automaton import Automaton, State, Transition
import numpy as np
from unittest.mock import Mock

    # ha = Automaton(
    #     name="thermostat",
    #     states=[q1, q2],
    #     real_time_mode=True
    #     dt = 0.1
    # )

# class TestInitialization: 
#     ... 

# def test_initialization():
#     too_hot_threshold = 25
#     too_cold_threshold = 20
#     integration_method = lambda flow, x, aux_x, u, ctx, dt: x + flow(x, aux_x, u, ctx, dt) * dt

#     q1 = State(
#         name="warm up",
#         initial=True,
#         flow=lambda x, aux_x, u, ctx, dt: x + 1.0 * dt,   # temperature increases
#         integration_method=integration_method
#     )

#     q2 = State(
#         name="cool down",
#         initial=False,
#         flow=lambda x, aux_x, u, ctx, dt: x - 1.0 * dt   # temperature decreases
#     )

#     d1 = Transition(
#         name="too hot",
#         to_state=q2,
#         guards=[lambda x, aux_x, u, ctx, dt: x > too_hot_threshold]
#     )

#     d2 = Transition(
#         name="too cold",
#         to_state=q1,
#         guards=[lambda x, aux_x, u, ctx, dt: x < too_cold_threshold]
#     )

#     q1.add_transition(d1)
#     q2.add_transition(d2)


#     h = Automaton(
#         name='thermostate', 
#         states=[q1, q2],
#         real_time_mode=True,
#         integration_method=integration_method,
#         dt=0.1
#     )

import pytest
import numpy as np


class TestSetContinuousState:

    @pytest.fixture
    def automaton_mock_real_time(self):
        """Fixture returns a function so tests can choose x0/is_real_time easily."""
        q = Mock(spec=State)
        q._is_init = True
        return Automaton(
            name="continous_state_test",
            states=[q],
            real_time_mode=True
        )
    
    @pytest.fixture
    def automaton_mock_sim_time(self):
        """Fixture returns a function so tests can choose x0/is_real_time easily."""
        q = Mock(spec=State)
        q._is_init = True
        return Automaton(
            name="continous_state_test",
            states=[q],
            real_time_mode=False
        )
    
    def test_fails_when_not_active(self, automaton_mock_real_time: Automaton):
        ha = automaton_mock_real_time
        with pytest.raises(SystemError):
            ha.set_continous_state({"heading": 2.0})

    def test_fails_when_not_real_time(self, automaton_mock_sim_time):
        ha = automaton_mock_sim_time
        ha.activate(
            {"heading": 1.0}
        )
        with pytest.raises(SystemError):
            ha.set_continous_state({"heading": 2.0})

    def test_fails_on_wrong_dict_keys(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(
            x0={"heading": 1.0}
        )
        with pytest.raises(ValueError):
            ha.set_continous_state({"hdg": 2.0})

    def test_fails_on_wrong_type(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(
            x0={"heading": 1.0}
        )
        with pytest.raises(ValueError):
            ha.set_continous_state([1.0])

    def test_list_length_mismatch(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(x0=[1.0, 2.0])
        with pytest.raises(ValueError):
            ha.set_continous_state([1.0])

    def test_numpy_shape_mismatch(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(
            x0=np.zeros((2, 2))
        )
        with pytest.raises(ValueError):
            ha.set_continous_state(np.zeros((3, 3)))

    def test_successful_update_dict(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(
            x0={"heading": 1.0}
        )
        ha.set_continous_state({"heading": 2.0})
        assert ha._x == {"heading": 2.0}

    def test_successful_update_list(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(
            x0=[1.0, 2.0]
        )
        new = [3.0, 4.0]
        ha.set_continous_state(new)
        assert ha._x == new

    def test_successful_update_numpy(self, automaton_mock_real_time):
        ha = automaton_mock_real_time
        ha.activate(
            x0=np.zeros((2, 2))
        )
        new = np.ones((2, 2))
        ha.set_continous_state(new)
        assert np.array_equal(ha._x, new)


if __name__ == '__main__':
    pytest.main([__file__])