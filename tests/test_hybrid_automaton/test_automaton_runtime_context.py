# import sys
# import os

# sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))


# import numpy as np
# from collections import deque
# from hybrid_automaton.automaton_runtime_context import (
#     AuxiliaryState, 
#     ContinuousState, 
#     ControlInput,
#     Context
# )

# import pytest
# import time
# import numpy as np
# import pytest
# from collections import deque

# # import your class here
# # from your_module import ContinuousState

# class DummyClock:
#     """Simple mock clock for testing"""
#     def __init__(self):
#         self.time = 0.0

#     def tick(self, dt=1.0):
#         self.time += dt

#     def now(self):
#         return self.time


# class TestContinuousState:

#     def test_initialization(self):
#         x0 = np.array([1.0, 2.0])
#         cs = ContinuousState("test_state", x0, buffer_len=3)

#         assert cs.name == "test_state"
#         assert np.allclose(cs.latest(), x0)
#         assert isinstance(cs.get_state_buffer(), deque)
#         assert len(cs.get_state_buffer()) == 1
#         assert cs.input_step == 1

#     def test_direct_state_update(self):
#         cs = ContinuousState("cs", np.array([0.0]), buffer_len=3)

#         cs.set_continuous_state(np.array([5.0]))
#         assert np.allclose(cs.latest(), np.array([5.0]))
#         assert len(cs.x_buffer) == 2
#         assert cs.input_step == 2

#     def test_buffer_maxlen(self):
#         cs = ContinuousState("cs", np.zeros(1), buffer_len=2)

#         cs.set_continuous_state(np.array([1.0]))
#         cs.set_continuous_state(np.array([2.0]))

#         assert len(cs.x_buffer) == 2
#         assert np.allclose(cs.latest(), np.array([2.0]))
#         # ensure oldest state rolled off
#         assert not np.allclose(cs.x_buffer[-1], np.zeros(1))

#     def test_euler_integration(self):
#         cs = ContinuousState("cs", np.array([0.0]), buffer_len=3)

#         xdot = np.array([2.0])
#         dt = 0.5
#         cs.integrate(xdot, dt)

#         expected = 0.0 + 2.0 * 0.5
#         assert np.allclose(cs.latest(), np.array([expected]))
#         assert cs.input_step == 2

#     def test_custom_integration_function(self):
#         def custom_integrator(x, xdot, dt):
#             # integrate as x_next = x + 2 * xdot * dt
#             return x + 2 * xdot * dt

#         cs = ContinuousState(
#             "cs",
#             np.array([1.0]),
#             buffer_len=3,
#             integration_func=custom_integrator
#         )

#         cs.integrate(np.array([3.0]), 1.0)
#         expected = 1.0 + 2 * 3.0 * 1.0

#         assert np.allclose(cs.latest(), np.array([expected]))

#     def test_last_update_dt(self):
#         cs = ContinuousState("cs", np.zeros(1))
#         time.sleep(0.01)  # ensure measurable time delta
#         dt = cs.last_update_dt()

#         assert dt > 0
#         assert dt < 1  # sanity check: should not exceed 1 sec in test

#     def test_actual_update_hz_updates(self):
#         cs = ContinuousState("cs", np.zeros(1))

#         # simulate another update after a short delay
#         time.sleep(0.01)
#         cs.set_continuous_state(np.array([1.0]))

#         assert cs.actual_update_hz > 0


# class TestAuxiliaryState:

#     def test_initialization(self):
#         aux0 = np.array([1, 2])
#         aux = AuxiliaryState("test", aux0, aux_buffer_len=3, expected_update_hz=5)

#         assert aux.name == "test"
#         assert np.array_equal(aux.latest(), aux0)
#         assert isinstance(aux.get_aux_buffer(), deque)
#         assert len(aux.get_aux_buffer()) == 1
#         assert aux.actual_update_hz == 5   # starts at expected
#         assert aux.input_step == 1

#     def test_add_updates_buffer(self):
#         aux = AuxiliaryState("test", np.array([0]), aux_buffer_len=2)

#         aux.add(np.array([1]))

#         buf = aux.get_aux_buffer()
#         assert len(buf) == 2
#         assert np.array_equal(buf[0], np.array([1]))
#         assert np.array_equal(buf[1], np.array([0]))

#     def test_buffer_overflow_drops_oldest(self):
#         aux = AuxiliaryState("test", np.array([0]), aux_buffer_len=2)

#         aux.add(np.array([1]))
#         aux.add(np.array([2]))

#         buf = aux.get_aux_buffer()
#         assert list(buf) == [np.array([2]), np.array([1])]  # capacity = 2
#         assert len(buf) == 2

#     def test_latest_returns_front(self):
#         aux = AuxiliaryState("test", np.array([0]), aux_buffer_len=3)
#         aux.add(np.array([5]))

#         assert np.array_equal(aux.latest(), np.array([5]))

#     def test_aux_step_increments(self):
#         aux = AuxiliaryState("test", np.array([0]))
#         assert aux.input_step == 1

#         aux.add(np.array([1]))
#         aux.add(np.array([2]))

#         assert aux.input_step == 3

#     def test_actual_update_hz_updates(self):
#         aux = AuxiliaryState("test", np.array([0]))
        
#         # Add a new sample; dt > 0, so frequency should update
#         before = aux.actual_update_hz
#         aux.add(np.array([1]))
#         after = aux.actual_update_hz

#         # Should update to some positive value
#         assert after > 0
#         assert after != before  # changed from initial expected value

#     def test_last_update_dt(self):
#         aux = AuxiliaryState("test", np.array([0]))

#         dt = aux.last_update_dt()
#         assert dt >= 0.0
#         assert isinstance(dt, float)

#     def test_repr_runs(self):
#         aux = AuxiliaryState("test", np.array([0]))
#         r = repr(aux)

#         assert "AuxiliaryState(" in r
#         assert aux.name in r


# class TestControlInput:

#     def test_initialization(self):
#         u0 = np.array([0.0, 1.0])
#         ci = ControlInput("throttle", u0, buffer_len=3)

#         assert ci.name == "throttle"
#         assert np.allclose(ci.latest(), u0)
#         assert isinstance(ci.get_input_buffer(), deque)
#         assert len(ci.get_input_buffer()) == 1
#         assert ci.input_step == 1
#         assert ci.actual_update_hz == 10.0  # starts at expected

#     def test_add_updates_buffer(self):
#         ci = ControlInput("rudder", np.array([0.0]), buffer_len=2)

#         ci.add(np.array([1.0]))
#         buf = ci.get_input_buffer()

#         assert len(buf) == 2
#         assert np.allclose(buf[0], np.array([1.0]))
#         assert np.allclose(buf[1], np.array([0.0]))
#         assert ci.input_step == 2

#     def test_set_control_input_alias(self):
#         ci = ControlInput("throttle", np.array([0.0]))
#         ci.set_control_input(np.array([2.0]))

#         assert np.allclose(ci.latest(), np.array([2.0]))
#         assert ci.input_step == 2

#     def test_buffer_maxlen_rollover(self):
#         ci = ControlInput("rudder", np.array([0.0]), buffer_len=2)

#         ci.add(np.array([1.0]))
#         ci.add(np.array([2.0]))

#         buf = ci.get_input_buffer()
#         assert len(buf) == 2
#         assert np.allclose(buf[0], np.array([2.0]))
#         assert np.allclose(buf[1], np.array([1.0]))

#     def test_last_update_dt(self):
#         ci = ControlInput("throttle", np.array([0.0]))
#         time.sleep(0.01)
#         dt = ci.last_update_dt()

#         assert dt > 0
#         assert dt < 1  # sanity check

#     def test_actual_update_hz_updates(self):
#         ci = ControlInput("rudder", np.array([0.0]))

#         time.sleep(0.01)
#         ci.add(np.array([1.0]))

#         assert ci.actual_update_hz > 0
#         assert ci.input_step == 2

#     def test_repr_runs(self):
#         ci = ControlInput("throttle", np.array([0.0]))
#         r = repr(ci)

#         assert "ControlInput(" in r
#         assert ci.name in r
        

# class TestContext:

#     def test_initialization_empty(self):
#         clk = DummyClock()
#         ctx = Context(clk)

#         # Clock reference
#         assert ctx.clk == clk

#         # Continuous state initialized with None
#         assert isinstance(ctx.x, ContinuousState)
#         assert ctx.x.latest() is None or np.allclose(ctx.x.latest(), np.array(None))  # if None handled

#         # Aux and control dicts should be empty
#         assert ctx.aux == {}
#         assert ctx.u == {}
#         assert ctx.cfg == {}

#     def test_initialization_with_data(self):
#         clk = DummyClock()
#         x0 = np.array([0.0, 1.0])
#         aux0 = {"wind": np.array([1.0, 2.0])}
#         u0 = {"throttle": np.array([0.5])}
#         cfg = {"param": 123}

#         ctx = Context(clk, x0=x0, aux0=aux0, u0=u0, cfg=cfg)

#         # Continuous state
#         assert isinstance(ctx.x, ContinuousState)
#         assert np.allclose(ctx.x.latest(), x0)

#         # Auxiliary state
#         assert isinstance(ctx.aux["wind"], AuxiliaryState)
#         assert np.allclose(ctx.aux["wind"].latest(), aux0["wind"])

#         # Control input
#         assert isinstance(ctx.u["throttle"], ControlInput)
#         assert np.allclose(ctx.u["throttle"].latest(), u0["throttle"])

#         # Config
#         assert ctx.cfg == cfg

#     def test_add_aux_and_control(self):
#         clk = DummyClock()
#         aux0 = {"wind": np.array([1.0])}
#         u0 = {"throttle": np.array([0.0])}
#         ctx = Context(clk, aux0=aux0, u0=u0)

#         # Add new aux value
#         ctx.aux["wind"].add(np.array([2.0]))
#         assert np.allclose(ctx.aux["wind"].latest(), np.array([2.0]))
#         assert ctx.aux["wind"].input_step == 2 or ctx.aux["wind"].aux_step == 2

#         # Add new control input
#         ctx.u["throttle"].add(np.array([1.0]))
#         assert np.allclose(ctx.u["throttle"].latest(), np.array([1.0]))
#         assert ctx.u["throttle"].input_step == 2

#     def test_continuous_state_update(self):
#         clk = DummyClock()
#         x0 = np.array([0.0])
#         ctx = Context(clk, x0=x0)

#         ctx.x.set_continuous_state(np.array([5.0]))
#         assert np.allclose(ctx.x.latest(), np.array([5.0]))
#         assert ctx.x.input_step == 2

#         # Integrate
#         ctx.x.integrate(np.array([2.0]), dt=1.0)
#         assert np.allclose(ctx.x.latest(), np.array([7.0]))  # 5 + 2*1
#         assert ctx.x.input_step == 3

        
# if __name__ == '__main__':
#     pytest.main([__file__])