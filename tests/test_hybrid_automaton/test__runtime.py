# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT
import asyncio

import numpy as np
import pytest

from hybrid_automaton._runtime import _Runtime
from hybrid_automaton.definition import State, Transition, guard, continuous_dynamics, _Definition

ContinuousState = _Runtime.Context.ContinuousState


class TestRuntimeLogger:
    def _make_logger(self, tmp_path, should_write_logs_to_file):
        definition = _Definition(name="logger_test", version="1.0.0", states=[
            State(name="ONLY", initial=True, final=True)
        ])
        ctx = _Runtime.Context(initial_state=definition.state_t0)
        signature = _Runtime.Signature(
            automaton_definition=definition,
            timeout_sec=np.inf,
            real_time_mode_enabled=False,
            delta_time=0.01,
            should_integrate=False,
        )
        return _Runtime.Logger(
            automaton_definition=definition,
            run_signature=signature,
            run_context=ctx,
            should_write_logs_to_file=should_write_logs_to_file,
            log_dir=str(tmp_path),
        )

    def test_disabled_file_logging_does_not_write_to_disk(self, tmp_path):
        logger = self._make_logger(tmp_path, should_write_logs_to_file=False)
        logger.INFO("TEST", "no file should be written")
        assert list(tmp_path.iterdir()) == []

    def test_enabled_file_logging_creates_log_file(self, tmp_path):
        logger = self._make_logger(tmp_path, should_write_logs_to_file=True)
        logger.INFO("TEST", "a file should exist")
        log_file = tmp_path / "temporal_automaton.log"
        assert log_file.exists()
        contents = log_file.read_text()
        assert "TEST" in contents
        assert "no file should be written" not in contents


class TestRuntimeClock:
    def _clock(self, dt=0.1, real_time_mode=False, timeout_sec=np.inf):
        return _Runtime.Context.Clock(
            dt=dt,
            real_time_mode=real_time_mode,
            timeout_event=asyncio.Event(),
            deactivate_event=asyncio.Event(),
            timeout_sec=timeout_sec,
        )

    def test_init(self):
        clock = self._clock(dt=0.1, real_time_mode=True, timeout_sec=10)
        assert clock.get_dt() == 0.1
        assert clock.is_real_time() is True
        assert clock.get_elapsed_time_active() == 0.0

    @pytest.mark.parametrize("dt", [0.1, 0.2, 0.5])
    def test_step_dt_accumulates_elapsed_time(self, dt):
        clock = self._clock(dt=dt, real_time_mode=False)
        clock.step_dt()
        assert clock.get_elapsed_time_active() == pytest.approx(dt)
        clock.step_dt()
        assert clock.get_elapsed_time_active() == pytest.approx(2 * dt)

    def test_step_dt_raises_in_real_time_mode(self):
        clock = self._clock(real_time_mode=True)
        with pytest.raises(SystemError):
            clock.step_dt()

    def test_ping_transition_resets_time_since_transition(self):
        clock = self._clock(dt=0.1, real_time_mode=False)
        clock.step_dt()
        clock.step_dt()
        assert clock.get_time_elapsed_since_transition() == pytest.approx(0.2)
        clock.ping_transition()
        assert clock.get_time_elapsed_since_transition() == 0.0


class TestRuntimeContext:
    def test_defaults(self):
        state = State(name="ONLY", initial=True, final=True)
        ctx = _Runtime.Context(initial_state=state, delta_time=0.05, timeout_sec=1.0)

        assert ctx.discrete_state is state
        assert ctx.status == _Runtime.Context.Status.ACTIVE
        assert ctx.total_steps == 0
        assert ctx.transitions_count == 0
        assert ctx.configuration["should_integrate"] is True
        assert ctx.clock.get_dt() == 0.05

    def test_initial_continuous_state_is_carried_through(self):
        state = State(name="ONLY", initial=True, final=True)
        cs = ContinuousState("x", x0=np.array([1.0]), x_labels=["x"])
        ctx = _Runtime.Context(initial_state=state, initial_continuous_state=cs)
        assert ctx.continuous_state is cs
        assert ctx.continuous_state.latest()[0] == 1.0


class TestRuntime:
    def _build_runtime_and_ctx(self, threshold=0.05):
        @continuous_dynamics
        def constant_rate(ctx) -> np.ndarray:
            return np.array([1.0])

        @guard
        def reached_threshold(ctx) -> bool:
            return ctx.continuous_state.latest()[0] >= threshold

        start = State(name="START", initial=True, flow=constant_rate)
        done = State(name="DONE", final=True)
        start.add_transition(Transition("advance", done, guards=[reached_threshold]))

        definition = _Definition(name="runtime_test", version="1.0.0", states=[start, done])
        runtime = _Runtime(definition=definition, integration_fnc=None)

        cs = ContinuousState("x", x0=np.array([0.0]), x_labels=["x"])
        ctx = _Runtime.Context(
            initial_state=definition.state_t0,
            initial_continuous_state=cs,
            delta_time=0.01,
        )
        return runtime, ctx

    def test_evaluation_step_normal_when_no_guard_active(self):
        runtime, ctx = self._build_runtime_and_ctx(threshold=1.0)
        logger = _Runtime.Logger(
            automaton_definition=runtime._automaton_definition,
            run_signature=_Runtime.Signature(
                automaton_definition=runtime._automaton_definition,
                timeout_sec=np.inf,
                real_time_mode_enabled=False,
                delta_time=0.01,
                should_integrate=True,
            ),
            run_context=ctx,
            should_write_logs_to_file=False,
        )

        result = runtime._evaluation_step(logger=logger, runtime_context=ctx)

        assert result.code == _Runtime.StepResultCode.NORMAL
        assert result.severity == _Runtime.StepSeverity.OK
        assert ctx.continuous_state.latest()[0] == pytest.approx(0.01)

    def test_evaluation_step_transitions_when_guard_active(self):
        runtime, ctx = self._build_runtime_and_ctx(threshold=0.0)
        logger = _Runtime.Logger(
            automaton_definition=runtime._automaton_definition,
            run_signature=_Runtime.Signature(
                automaton_definition=runtime._automaton_definition,
                timeout_sec=np.inf,
                real_time_mode_enabled=False,
                delta_time=0.01,
                should_integrate=True,
            ),
            run_context=ctx,
            should_write_logs_to_file=False,
        )

        result = runtime._evaluation_step(logger=logger, runtime_context=ctx)

        assert result.code == _Runtime.StepResultCode.TRANSITION
        assert ctx.discrete_state.name == "DONE"

    def test_deactivate_is_safe_before_activate(self):
        definition = _Definition(name="deactivate_test", version="1.0.0", states=[
            State(name="ONLY", initial=True, final=True)
        ])
        runtime = _Runtime(definition=definition, integration_fnc=None)
        # self._ctx is None until activate() has run; deactivate() must not
        # raise (this is a known limitation - see _runtime.py's TODO on the
        # context-sharing mechanism for reactivation).
        runtime.deactivate()
