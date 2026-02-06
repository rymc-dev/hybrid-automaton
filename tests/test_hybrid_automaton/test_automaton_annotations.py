# import sys
# import os

# sys.path.append(os.path.join(os.path.dirname(__file__), './../../src/'))


# import pytest
# import numpy as np
# from hybrid_automaton.automaton_annotations import guard, invariant, reset, continuous_dynamics, integration
# from hybrid_automaton.automaton_runtime_context import Context

# # Mock Context for testing
# class MockContext(Context):
#     def __init__(self, x=0, aux=None, cfg=None):
#         self.x = x
#         self.aux = aux or {}
#         self.cfg = cfg or {}

# # ----------------------------
# # Guard decorator tests
# # ----------------------------
# class TestGuard:

#     @guard
#     def positive_x(ctx) -> bool:
#         return ctx.x > 0

#     def test_guard_valid(self):
#         ctx = MockContext(x=5)
#         assert self.positive_x(ctx) is True

#     def test_guard_invalid_ctx(self):
#         with pytest.raises(TypeError):
#             self.positive_x("not a context")

#     def test_guard_wrong_annotation(self):
#         with pytest.raises(TypeError):
#             @guard
#             def f(ctx) -> int:
#                 return 1

# # ----------------------------
# # Invariant decorator tests
# # ----------------------------
# class TestInvariant:

#     @invariant
#     def x_less_than_ten(ctx) -> bool:
#         return ctx.x < 10

#     def test_invariant_valid(self):
#         ctx = MockContext(x=5)
#         assert self.x_less_than_ten(ctx) is True

#     def test_invariant_invalid_ctx(self):
#         with pytest.raises(TypeError):
#             self.x_less_than_ten("invalid ctx")

#     def test_invariant_wrong_annotation(self):
#         with pytest.raises(TypeError):
#             @invariant
#             def f(ctx) -> int:
#                 return 0

# # ----------------------------
# # Reset decorator tests
# # ----------------------------
# class TestReset:

#     @staticmethod
#     @reset
#     def copy_context(ctx):
#         # Return a new Context instance
#         return MockContext(x=ctx.x)

#     def test_reset_valid(self):
#         ctx = MockContext(x=2)
#         new_ctx = self.copy_context(ctx)
#         assert isinstance(new_ctx, Context)
#         assert new_ctx.x == ctx.x

#     def test_reset_invalid_return(self):
#         @reset
#         def bad_reset(ctx):
#             return "not a context"
#         ctx = MockContext()
#         with pytest.raises(TypeError):
#             bad_reset(ctx)

# # ----------------------------
# # Continuous Dynamics decorator tests
# # ----------------------------
# class TestContinuousDynamics:

#     @staticmethod
#     @continuous_dynamics
#     def dyn(ctx) -> np.ndarray:
#         return np.array([ctx.x, ctx.x * 2])

#     def test_continuous_valid(self):
#         ctx = MockContext(x=3)
#         out = self.dyn(ctx)
#         assert isinstance(out, np.ndarray)
#         assert np.array_equal(out, np.array([3, 6]))

#     def test_continuous_invalid_ctx(self):
#         with pytest.raises(TypeError):
#             self.dyn("invalid ctx")

#     def test_continuous_wrong_annotation(self):
#         with pytest.raises(TypeError):
#             @continuous_dynamics
#             def bad(ctx) -> list:
#                 return [1, 2]

#     def test_continuous_wrong_runtime_return(self):
#         @continuous_dynamics
#         def bad_runtime(ctx) -> np.ndarray:
#             return [1, 2]  # list instead of np.ndarray
#         ctx = MockContext()
#         with pytest.raises(TypeError):
#             bad_runtime(ctx)

# # ----------------------------
# # Integration decorator tests
# # ----------------------------
# class TestIntegration:
#     @staticmethod
#     @integration
#     def integrate(ctx) -> np.ndarray:
#         return np.array([ctx.x + 1])

#     def test_integration_valid(self):
#         ctx = MockContext(x=5)
#         out = self.integrate(ctx)
#         assert isinstance(out, np.ndarray)
#         assert np.array_equal(out, np.array([6]))

#     def test_integration_wrong_annotation(self):
#         with pytest.raises(TypeError):
#             @integration
#             def bad(ctx) -> list:
#                 return [1]

#     def test_integration_wrong_runtime_return(self):
#         @integration
#         def bad_runtime(ctx) -> np.ndarray:
#             return [1]  # list instead of np.ndarray
#         ctx = MockContext()
#         with pytest.raises(TypeError):
#             bad_runtime(ctx)


# if __name__ == '__main__': 
#     pytest.main([__file__])