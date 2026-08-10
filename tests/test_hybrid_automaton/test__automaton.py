# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT
import numpy as np
import pytest

from hybrid_automaton import Automaton, RunResult
from tests.conftest import build_two_state_automaton


class TestAutomatonMetadata:
    def test_get_automaton_name(self, two_state_automaton):
        assert two_state_automaton.get_automaton_name() == "test_two_state_automaton"

    def test_get_automaton_version(self, two_state_automaton):
        assert two_state_automaton.get_automaton_version() == "1.0.0"

    def test_get_automaton_id_is_unique_per_instance(self):
        a = build_two_state_automaton()
        b = build_two_state_automaton()
        assert a.get_automaton_id() != b.get_automaton_id()

    def test_requires_exactly_one_initial_state(self):
        # _Definition enforces exactly one initial=True state; building an
        # Automaton with zero initial states must fail fast rather than
        # silently pick one.
        from hybrid_automaton.definition import State

        with pytest.raises(ValueError):
            Automaton(
                name="no_initial_state",
                version="1.0.0",
                states=[State(name="A"), State(name="B", final=True)],
            )


class TestAutomatonActivateLifecycle:
    async def test_activate_reaches_terminal_state_in_simulation_mode(self, two_state_automaton, initial_state):
        results: RunResult = await two_state_automaton.activate(
            initial_continuous_state=initial_state,
            enable_real_time_mode=False,
            enable_self_integration=True,
            delta_time=0.01,
            timeout_sec=5.0,
            should_write_logs=False,
        )

        assert results.was_successful()
        assert results.final_discrete_state == "DONE"
        assert results.termination_code.name == "TERMINAL_REACHED"
        assert results.transitions_count == 1
        assert results.final_continuous_state is not None
        assert results.final_continuous_state[0] >= 0.05

    async def test_activate_times_out_when_threshold_unreachable(self, initial_state):
        # threshold higher than what a short timeout can integrate up to
        ha = build_two_state_automaton(threshold=1_000_000.0)

        results: RunResult = await ha.activate(
            initial_continuous_state=initial_state,
            enable_real_time_mode=False,
            enable_self_integration=True,
            delta_time=0.01,
            timeout_sec=0.05,
            should_write_logs=False,
        )

        assert results.status.name == "TIMEOUT"
        assert not results.was_successful()

    async def test_deactivate_before_activate_does_not_raise(self, two_state_automaton):
        # deactivate() reads self._ctx, which is None until activate() has
        # run at least once; it must be a safe no-op, not an AttributeError.
        two_state_automaton.deactivate()
