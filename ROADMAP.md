# Roadmap / Known Limitations

Tracking notes for known gaps and follow-up work identified during the v1.0.0
release pass, kept out of that release deliberately (either because fixing
them touches core runtime semantics this late before a release, or because
they were incomplete features not worth shipping half-finished). Pulled out
here so they don't get lost.

## Runtime

- **Context sharing on reactivation doesn't work.** `Automaton.deactivate()` /
  `_Runtime.deactivate()` (`src/hybrid_automaton/_runtime.py`, see the `TODO`
  on `_Runtime.deactivate`) sets the deactivate event on `self._ctx` if one
  exists, but there's no supported way to reactivate an automaton with a
  shared/carried-over context afterwards. Needs a real design pass, not a
  quick fix.

- **A state with `flow=None` silently zeroes the continuous state when
  integration is enabled.** `State.continuous_dynamics()` returns
  `np.array([])` when no `flow` is set. If `enable_self_integration=True`,
  that empty array gets integrated against the current continuous state
  (`x + dt * xdot`), and numpy's broadcasting rules silently collapse the
  result to an empty array instead of raising - the continuous state is
  gone from that point on. All four shipped example automatons avoid this by
  giving every state an explicit flow (even a `return np.array([0.0, ...])`
  no-op), but nothing stops a user from hitting this. Found while writing
  the v1.0.0 test suite (`tests/conftest.py` has a comment on the same
  footgun). Worth either raising a clear error when integrating an empty
  `xdot`, or documenting the "always give every state a flow" requirement
  explicitly.

## Evaluation / visualization (`hybrid_automaton_evaluation`)

These were stubbed out or left unimplemented pre-1.0 and were deliberately
removed from the public API for the v1.0.0 release rather than shipped
broken (see `git log` around the v1.0.0 tidy-up for the removal commit).
Each has a `# TODO(v1.1)` marker at its former location in source:

- `auxiliary_states_over_time_fig()` and `control_inputs_over_time_fig()` in
  `hybrid_automaton_evaluation/visualization/figure_generator.py` - analogous
  to the working `continuous_states_over_time_fig()`, just never implemented.
- `chattering_statistics()` (was in
  `hybrid_automaton_evaluation/mode_choreography_analysis/transition_stats.py`)
  - a summary-stats wrapper around `self_loop_detection()`; removed entirely
    since it never returned in its main branch.
- Guard activation timeline/rate figures (were commented out in
  `figure_generator.py`) - depend on guard-activation-event data that isn't
  currently captured anywhere in the runtime's logs.
- `guard_and_event_metrics` subpackage - was an empty stub with no content;
  removed. Reserve this name if/when real guard/event metrics land.

## Docs

- `docs/architecture/hierarchy_chart.mmd` and 3 placeholder diagrams under
  `docs/diagrams/automaton/` were removed (stale/never-authored) rather than
  redrawn. Worth redrawing against the current `_automaton.py`/`_runtime.py`
  structure if the architecture docs are revisited.
