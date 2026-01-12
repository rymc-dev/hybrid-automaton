import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))

import pytest
from unittest.mock import Mock
from hybrid_automaton.automaton_state import State
from hybrid_automaton.automaton_runtime_context import Context
from hybrid_automaton.automaton_transition import Transition

import numpy as np


# --- Helper functions for testing ---
def dummy_flow(ctx: Context):
    return ctx.x.latest() + 1
    

def dummy_invariant(ctx: Context):
    return ctx.x.latest() < 10

# --- Fixtures ---
@pytest.fixture
def sample_transition():
    t = Mock(spec=Transition)
    t.name = "T1"
    t.is_enabled.return_value = True
    t._to_q = Mock(name="TargetState")
    return t

# --- Tests ---

def test_state_creation():
    s = State(name="S1", initial=True, final=False, flow=dummy_flow, invariants=[dummy_invariant])
    assert s.name == "S1"
    assert s._is_init is True
    assert s._is_final is False
    assert s.flow == dummy_flow
    assert s.get_invariants() == [dummy_invariant]
    assert isinstance(s.get_state_id(), int)

def test_add_and_remove_transition(sample_transition):
    s = State(name="S2")
    s.add_transition(sample_transition)
    assert sample_transition in s.get_transitions()
    
    s.remove_transition(sample_transition)
    assert sample_transition not in s.get_transitions()

def test_add_transitions_multiple(sample_transition):
    s = State(name="S3")
    t2 = Mock(spec=Transition)
    s.add_transitions([sample_transition, t2])
    assert sample_transition in s.get_transitions()
    assert t2 in s.get_transitions()

def test_evaluate_transitions_enabled(sample_transition):
    s = State(name="S4", transitions=[sample_transition])
    ctx = Context(clk=None, x0=0)
    ctx.x = 5
    results = s.evaluate_transitions(ctx)
    assert len(results) == 1
    trans, enabled, exc = results[0]
    assert trans == sample_transition
    assert enabled is True
    assert exc is None

def test_evaluate_transitions_exception():
    t = Mock(spec=Transition)
    t.is_enabled.side_effect = Exception("Guard error")
    s = State(transitions=[t])
    ctx = Context(clk=None, x0=0)
    ctx.x = 5
    results = s.evaluate_transitions(ctx)
    trans, enabled, exc = results[0]
    # NO NEED TO TEST TRANS
    assert not enabled
    assert isinstance(exc, Exception)
    assert str(exc) == "Guard error"

def test_continuous_dynamics():
    s = State(flow=dummy_flow)
    ctx = Context(clk = None, x0 = 5)
    assert s.continuous_dynamics(ctx) == 6

    s2 = State()  # No flow
    assert np.array_equal(s2.continuous_dynamics(ctx), np.array([], dtype=float)) # TODO: FIGURE OUT WHY THIS COMPARISON IS NOT WORKING ALTHOUGH IT SHOULD. 
    # They are both np.array([], dtype=float)
    # assert s2.continuous_dynamics(None) == []

def test_check_invariants():
    s = State(invariants=[dummy_invariant])
    ctx = Context(clk = None, x0=5)
    assert s.check_invariants(ctx) is True
    ctx.x = 15
    assert s.check_invariants(ctx) is False

if __name__ == '__main__': 
    pytest.main([__file__])