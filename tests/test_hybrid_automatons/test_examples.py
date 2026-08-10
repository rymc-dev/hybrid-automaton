# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT
"""
Smoke tests for the shipped example automatons in `hybrid_automatons`.

These are not physics-accuracy tests - parameters are tuned for test speed,
not realism. The goal is to catch regressions in the public API surface
(construction + activate()) across every shipped example, since none of
them had any test coverage before. A run is considered healthy if it
completes without an internal error (CONTINUOUS_FLOW_ERROR,
INTEGRATION_ERROR, TRANSITION_ERROR, GUARD_EVALUATION_ERROR, ...) - reaching
a terminal state (SUCCESS) or simply running out of time (TIMEOUT) are both
acceptable outcomes, since several of these automatons (thermostat,
cruise_control, traffic_lights) have no final state at all and are designed
to run indefinitely.
"""
import numpy as np
import pytest

from hybrid_automaton import RunResult, RuntimeContext
from hybrid_automatons import bouncing_ball, cruise_control, thermostat, traffic_lights

ContinuousState = RuntimeContext.ContinuousState
AuxiliaryState = RuntimeContext.AuxiliaryState

HEALTHY_STATUSES = {"SUCCESS", "TIMEOUT"}


def assert_healthy_run(results: RunResult):
    assert isinstance(results, RunResult)
    assert results.status.name in HEALTHY_STATUSES
    assert results.total_steps > 0


class TestBouncingBallSmoke:
    async def test_runs_without_internal_errors(self):
        ha = bouncing_ball(gravity=-9.81, restitution=0.5)
        results = await ha.activate(
            initial_continuous_state=ContinuousState(
                "bouncing_ball_state", x0=np.array([2.0, 0.0]), x_labels=["height", "velocity"]
            ),
            enable_real_time_mode=False,
            enable_self_integration=True,
            delta_time=0.02,
            timeout_sec=2.0,
            should_write_logs=False,
        )
        assert_healthy_run(results)


class TestCruiseControlSmoke:
    async def test_runs_without_internal_errors(self):
        ha = cruise_control(target_speed=30.0, safe_distance=50.0, danger_close=20.0, car_ahead_speed=20.0)
        results = await ha.activate(
            initial_continuous_state=ContinuousState(name="car", x0=np.array([5.0, 60.0]), x_labels=["velocity", "distance"]),
            initial_auxiliary_states=[
                AuxiliaryState(name="test_aux_state", aux0=[0.0, 0.0], aux_buffer_len=10, expected_update_hz=10),
            ],
            enable_real_time_mode=False,
            enable_self_integration=True,
            delta_time=0.02,
            timeout_sec=2.0,
            should_write_logs=False,
        )
        assert_healthy_run(results)


class TestThermostatSmoke:
    async def test_runs_without_internal_errors(self):
        ha = thermostat(too_cold_threshold=18.0, too_hot_threshold=22.0, ambient_temp=20.0, drift_rate=0.5)
        results = await ha.activate(
            initial_continuous_state=ContinuousState(name="temperature_state", x0=np.array([25.0]), x_labels=["temperature"]),
            enable_real_time_mode=False,
            enable_self_integration=True,
            delta_time=0.02,
            timeout_sec=2.0,
            should_write_logs=False,
        )
        assert_healthy_run(results)


class TestTrafficLightsSmoke:
    async def test_runs_without_internal_errors(self):
        ha = traffic_lights(time_in_green=0.2, time_in_red=0.1, time_in_yellow=0.1)
        results = await ha.activate(
            initial_continuous_state=None,
            enable_real_time_mode=False,
            enable_self_integration=False,
            delta_time=0.02,
            timeout_sec=2.0,
            should_write_logs=False,
        )
        assert_healthy_run(results)
        # Unlike the others, traffic lights loop on a clock, not continuous
        # dynamics - with a 2s timeout and ~0.4s per RED->GREEN->YELLOW->RED
        # cycle, several transitions should have actually fired.
        assert results.transitions_count > 0
