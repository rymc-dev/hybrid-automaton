import os 
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))


import pytest
from hybrid_automaton.automaton_runtime_context import Context
from hybrid_automaton.automaton_transition import Transition

# Mock State for testing
class MockState:
    def __init__(self, name="MockState"):
        self.name = name

# Mock guard functions
def guard_true(ctx: Context) -> bool:
    return True

def guard_false(ctx: Context) -> bool:
    return False

# Mock reset functions
def reset_identity(ctx: Context) -> Context:
    return ctx

def reset_modify(ctx: Context) -> Context:
    ctx.x += 10
    return ctx

# Mock Context
class MockContext(Context):
    def __init__(self, x=0, aux=None, cfg=None):    
        self.x = x
        self.aux = aux or {}
        self.cfg = cfg or {}

# ----------------------------
# Transition construction tests
# ----------------------------
def test_transition_construction_minimal():
    s = MockState()
    t = Transition(name="t1", to_state=s)
    assert t.name == "t1"
    assert t.to_state is s
    assert t.guards is None
    assert t.reset is None
    assert t.priority == 0

def test_transition_construction_full():
    s = MockState()
    t = Transition(name="t2", to_state=s, guards=[guard_true], reset=reset_identity, priority=5)
    assert t.guards == [guard_true]
    assert t.reset == reset_identity
    assert t.priority == 5

def test_transition_invalid_name_priority():
    s = MockState()
    with pytest.raises(ValueError):
        Transition(name=123, to_state=s)
    with pytest.raises(ValueError):
        Transition(name="t", to_state=s, priority="high")

# ----------------------------
# Guard logic tests
# ----------------------------
def test_is_enabled_no_guards():
    s = MockState()
    t = Transition(name="t", to_state=s)
    ctx = MockContext()
    assert t.is_enabled(ctx) is True

def test_is_enabled_with_guards():
    s = MockState()
    t = Transition(name="t", to_state=s, guards=[guard_true, guard_true])
    ctx = MockContext()
    assert t.is_enabled(ctx) is True

    t2 = Transition(name="t2", to_state=s, guards=[guard_true, guard_false])
    assert t2.is_enabled(ctx) is False

# ----------------------------
# Reset logic tests
# ----------------------------
def test_apply_reset_no_reset():
    s = MockState()
    t = Transition(name="t", to_state=s)
    ctx = MockContext(x=5)
    result = t.apply_reset(ctx)
    assert result is ctx  # unchanged

def test_apply_reset_with_reset():
    s = MockState()
    t = Transition(name="t", to_state=s, reset=reset_modify)
    ctx = MockContext(x=2)
    result = t.apply_reset(ctx)
    assert result.x == 12

# ----------------------------
# Execution tests
# ----------------------------
def test_execute_no_reset():
    s = MockState(name="S1")
    t = Transition(name="t", to_state=s)
    ctx = MockContext(x=7)
    next_state, new_ctx = t.execute(ctx)
    assert next_state is s
    assert new_ctx is ctx

def test_execute_with_reset():
    s = MockState(name="S2")
    t = Transition(name="t", to_state=s, reset=reset_modify)
    ctx = MockContext(x=3)
    next_state, new_ctx = t.execute(ctx)
    assert next_state is s
    assert new_ctx.x == 13

# ----------------------------
# Edge case tests
# ----------------------------
def test_transition_with_multiple_guards_and_reset():
    s = MockState()
    t = Transition(
        name="t",
        to_state=s,
        guards=[guard_true, guard_true],
        reset=reset_modify
    )
    ctx = MockContext(x=0)
    assert t.is_enabled(ctx) is True
    new_ctx = t.apply_reset(ctx)
    assert new_ctx.x == 10
    next_state, ctx_after = t.execute(ctx)
    assert ctx_after.x == 20
    assert next_state is s

if __name__ == '__main__': 
    pytest.main([__file__])