# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT
"""
Shared fixtures for the hybrid-automaton test suite.
"""
import numpy as np
import pytest

from hybrid_automaton import Automaton, RuntimeContext
from hybrid_automaton.definition import State, Transition, guard, continuous_dynamics

ContinuousState = RuntimeContext.ContinuousState


def build_two_state_automaton(threshold: float = 0.05, version: str = "1.0.0") -> Automaton:
    """
    Build the minimal automaton used across the test suite:

        START (initial) --[reached_threshold]--> DONE (final)

    START integrates a continuous state at a constant rate of 1.0/s; once the
    state crosses `threshold` the guard fires and control moves to DONE, a
    final state with no invariants, which is reported as TERMINAL_REACHED on
    the very next evaluation step.
    """
    @continuous_dynamics
    def constant_rate(ctx: RuntimeContext) -> np.ndarray:
        return np.array([1.0])

    @continuous_dynamics
    def no_dynamics(ctx: RuntimeContext) -> np.ndarray:
        # NOTE: a state with flow=None makes continuous_dynamics() return
        # np.array([]), which numpy silently broadcasts against the
        # existing continuous state during integration, zeroing it out.
        # Give DONE an explicit zero flow (as the example automatons do)
        # to avoid that footgun rather than rely on it here.
        return np.array([0.0])

    @guard
    def reached_threshold(ctx: RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[0] >= threshold

    start = State(name="START", initial=True, flow=constant_rate)
    done = State(name="DONE", final=True, flow=no_dynamics)

    start.add_transition(Transition("advance", done, guards=[reached_threshold]))

    return Automaton(
        name="test_two_state_automaton",
        version=version,
        states=[start, done],
    )


@pytest.fixture
def two_state_automaton() -> Automaton:
    return build_two_state_automaton()


@pytest.fixture
def initial_state() -> ContinuousState:
    return ContinuousState("test_state", x0=np.array([0.0]), x_labels=["x"])
