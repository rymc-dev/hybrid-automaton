import pytest
from typing import Any, Tuple
from hybrid_automaton import GuardFunction, ResetFunction, InvariantFunction, IntegrationFunction

class TestProtocols:

    def test_guard_function(self):
        def guard(x, aux_x, u, ctx, dt) -> bool:
            return True
        # Check it behaves like a GuardFunction
        result: bool = guard(0, None, None, None, 0.1)
        assert result is True

    def test_reset_function(self):
        def reset(x, aux_x, u, ctx, dt) -> Tuple[Any, Any]:
            return x, aux_x
        # Check it behaves like a ResetFunction
        new_x, new_aux_x = reset([1], [2], None, None, 0.1)
        assert new_x == [1]
        assert new_aux_x == [2]

    def test_invariant_function(self):
        def invariant(x, aux_x, u, ctx, dt) -> bool:
            return False
        # Check it behaves like an InvariantFunction
        result: bool = invariant([0], None, None, None, 0.1)
        assert result is False

    def test_integration_function(self):
        def integrate(x, aux_x, xdot, dt):
            return [xi + dxi*dt for xi, dxi in zip(x, xdot)]
        # Check it behaves like an IntegrationFunction
        new_x = integrate([1, 2], None, [0.1, 0.2], 1.0)
        assert new_x == [1.1, 2.2]
