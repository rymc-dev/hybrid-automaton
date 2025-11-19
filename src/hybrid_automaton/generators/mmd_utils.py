# !/usr/bin/env python3
""" 
script contains utility functions for mermaid diagram generation
for a hybraut_ros2 model.
"""

from typing import List
from hybraut_models.core import ModeRegistry, TransitionRegistry, Mode, Transition


def add_initial_state(mermaid: List[str], init_mode: str) -> None:
    if isinstance(init_mode, int):
        mermaid += ["    %% Initial Mode", f"    [*] --> {init_mode}", ""]


def add_modes(
    mermaid: List[str], modes: ModeRegistry, transitions: TransitionRegistry
) -> None:
    if not modes:
        return
    mermaid.append("\t%% Modes")
    for mode_id in modes.get_mode_ids():
        mode: Mode = modes.get_mode(mode_id)
        mode_name = mode.get_name()
        invariants = mode.get_invariant_refs()
        dynamics = mode.get_dynamics_ref()
        description = mode.get_description()
        mermaid.append(f"\t%% {mode_name} Mode details")
        mermaid.append(f"    {mode_id} : {mode_id}.{mode_name}")
        if any([invariants, dynamics, description]):
            add_mode_note(
                mermaid, mode_name, mode_id, description, invariants, dynamics
            )
        mermaid.append("")
        mermaid.append(f"\t%% {mode_name} transitions.")
        if mode.get_transition_refs():
            for transition_ref in mode.get_transition_refs():
                transition: Transition = transitions.get_transition_by_name(
                    transition_ref
                )
                add_transition_edge(
                    mermaid,
                    transition.get_name(),
                    mode_id,
                    transition.get_priority(),
                    transition.get_target_mode(),
                    transition.get_guard_refs(),
                    transition.get_reset_refs(),
                )
            mermaid.append("")


def add_mode_note(
    mermaid: List[str],
    mode_name: str,
    mode_index: str,
    description: str,
    invariants: str,
    dynamics: str,
) -> None:
    mermaid.append(f"    note left of {mode_index}")
    if description:
        mermaid.append("        <b>description</b>")
    if invariants:
        mermaid.append(f"        <b>invariants</b>: {invariants}")
    if dynamics:
        mermaid.append(f"        <b>dynamics</b>: {dynamics}")
    mermaid.append("    end note")


def add_transition_edge(
    mermaid: List[str],
    transition_key: str,
    origin_mode: str,
    priority: int,
    target_mode: str,
    guard: str,
    reset: str,
) -> None:
    label = (
        f"<b>Transition {transition_key}</b>"
        f"[<b>guards</b> = {guard}, <b>resets</b> = {reset}, <b>priority</b> = {priority}]"
    )
    mermaid.append(f"    {origin_mode} --> {target_mode} : {label}")


def add_goal_states(mermaid: List[str], goal_modes: List[str]) -> None:
    if goal_modes:
        mermaid.append("    %% Goal Modes")
        for goal_mode in goal_modes:
            mermaid.append(f"    {goal_mode} --> [*]")
        mermaid.append("")