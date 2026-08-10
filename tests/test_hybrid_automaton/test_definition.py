# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT
import numpy as np
import pytest

from hybrid_automaton._runtime import _Runtime
from hybrid_automaton.definition import (
    State,
    Transition,
    guard,
    invariant,
    reset,
    continuous_dynamics,
    auxiliary_state_provider,
    control_input_states_provider,
)


def _dummy_context():
    # _Annotation.__call__ (which guard/invariant/continuous_dynamics/
    # provider decorators wrap functions in) requires a real
    # _Runtime.Context instance - a plain None or dict won't pass its
    # isinstance() check.
    return _Runtime.Context(initial_state=State(name="X", initial=True))


class TestState:
    def test_defaults(self):
        s = State(name="IDLE")
        assert s.name == "IDLE"
        assert s._is_init is False
        assert s._is_final is False
        assert s.integration_method is None

    def test_integration_method_kwarg(self):
        # Regression test: the constructor kwarg used to be misspelled
        # `integartion_method`; it must be `integration_method`.
        fn = lambda x, xdot, dt: x + dt * xdot
        s = State(name="IDLE", integration_method=fn)
        assert s.integration_method is fn

    def test_check_invariants_true_when_no_invariants_and_not_final(self):
        s = State(name="IDLE")
        assert s.check_invariants(ctx=None) is True

    def test_check_invariants_false_when_no_invariants_and_final(self):
        # A final state with no invariants reports its invariant as violated,
        # which the runtime interprets as "terminal state reached" (see
        # _runtime.py's _evaluation_step). This is intentional, not a bug.
        s = State(name="DONE", final=True)
        assert s.check_invariants(ctx=None) is False


class TestTransition:
    def test_basic_construction(self):
        target = State(name="TARGET")
        t = Transition("go", target, priority=2)
        assert t.name == "go"
        assert t.to_state is target
        assert t.priority == 2
        assert t.guards is None
        assert t.reset is None

    def test_is_enabled_with_no_guards_defaults_true(self):
        target = State(name="TARGET")
        t = Transition("go", target)
        assert t.is_enabled(ctx=None) is True

    def test_is_enabled_requires_all_guards(self):
        target = State(name="TARGET")
        t = Transition("go", target, guards=[lambda ctx: True, lambda ctx: False])
        assert t.is_enabled(ctx=None) is False

    def test_repr_and_str_do_not_raise(self):
        # Regression test: __repr__/__str__ used to reference a
        # non-existent `self._value` attribute (and __str__ referenced
        # `self.to_q` instead of `self._to_q`), so both always raised
        # AttributeError.
        target = State(name="TARGET")
        t = Transition("go", target, priority=1)
        assert "go" in repr(t)
        assert "TARGET" in repr(t)
        assert "go" in str(t)
        assert "TARGET" in str(t)

    def test_execute_applies_reset_and_returns_target(self):
        target = State(name="TARGET")

        # @reset-decorated functions must return a _Runtime.Context instance
        # (enforced by the decorator itself), so exercise it with a real one
        # rather than a plain dict.
        @reset
        def bump(ctx):
            ctx.transitions_count += 1
            return ctx

        t = Transition("go", target, reset=bump)
        ctx = _dummy_context()
        next_state, new_ctx = t.execute(ctx=ctx)
        assert next_state is target
        assert new_ctx.transitions_count == 1


class TestDecorators:
    def test_guard_wraps_and_calls_function(self):
        @guard
        def always_true(ctx) -> bool:
            return True

        assert always_true(_dummy_context()) is True
        assert always_true.name == "always_true"

    def test_invariant_wraps_and_calls_function(self):
        @invariant
        def always_true(ctx) -> bool:
            return True

        assert always_true(_dummy_context()) is True

    def test_continuous_dynamics_wraps_and_calls_function(self):
        @continuous_dynamics
        def flow(ctx) -> np.ndarray:
            return np.array([1.0])

        assert np.array_equal(flow(_dummy_context()), np.array([1.0]))

    def test_auxiliary_state_provider_returns_wrapped_function_without_annotation(self):
        # Regression test: this decorator used to only `return
        # _Annotation(...)` inside the "has a return annotation" branch,
        # so an undecorated (no `-> Dict`) function was silently replaced
        # with None instead of being wrapped.
        @auxiliary_state_provider
        def provide(ctx):
            return {"aux": 1.0}

        assert provide is not None
        assert provide(_dummy_context()) == {"aux": 1.0}

    def test_control_input_states_provider_returns_wrapped_function_without_annotation(self):
        @control_input_states_provider
        def provide(ctx):
            return {"u": 1.0}

        assert provide is not None
        assert provide(_dummy_context()) == {"u": 1.0}

    def test_auxiliary_state_provider_rejects_wrong_return_annotation(self):
        with pytest.raises(TypeError):
            @auxiliary_state_provider
            def provide(ctx) -> bool:
                return True
