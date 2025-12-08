import pytest
from unittest.mock import Mock
from hybrid_automaton.automaton_state import State
from hybrid_automaton.automaton_transition import Transition

# --- Helper functions for testing ---
def dummy_flow(x, aux_x=None, u=None, cfg=None, clk=None):
    return x + 1

def dummy_invariant(x, aux_x=None, u=None, cfg=None, clk=None):
    return x < 10

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
    results = s.evaluate_transitions(x=5)
    assert len(results) == 1
    trans, enabled, exc = results[0]
    assert trans == sample_transition
    assert enabled is True
    assert exc is None

def test_evaluate_transitions_exception():
    t = Mock(spec=Transition)
    t.is_enabled.side_effect = Exception("Guard error")
    s = State(transitions=[t])
    results = s.evaluate_transitions(x=0)
    trans, enabled, exc = results[0]
    assert enabled is False
    assert isinstance(exc, Exception)
    assert str(exc) == "Guard error"

def test_continuous_dynamics():
    s = State(flow=dummy_flow)
    assert s.continuous_dynamics(5) == 6

    s2 = State()  # No flow
    assert s2.continuous_dynamics(5) == 5
    assert s2.continuous_dynamics(None) == []

def test_check_invariants():
    s = State(invariants=[dummy_invariant])
    assert s.check_invariants(5) is True
    assert s.check_invariants(15) is False

    s_no_inv = State()
    assert s_no_inv.check_invariants(5) is True  # Not final, no invariants
    s_final = State(final=True)
    assert s_final.check_invariants(5) is False

def test_repr_and_str(sample_transition):
    s = State(name="S5", transitions=[sample_transition], flow=dummy_flow, invariants=[dummy_invariant])
    r = repr(s)
    st = str(s)
    assert "HybridState" in r
    assert "State 'S5'" in st
    assert "flow" in st
    assert "invariants" in st
    assert "transitions" in st


if __name__ == '__main__': 
    pytest.main([__file__])