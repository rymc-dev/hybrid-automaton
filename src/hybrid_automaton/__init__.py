# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT

from .automaton import Automaton
from .automaton_integration import IntegrationMethods
from .automaton_state import State
from .automaton_transition import Transition
from .automaton_annotations import guard, reset, invariant

__author__ = "Ryan McKee <R.McKee@liverpool.ac.uk>"
__version__ = "0.0.4"

__all__ = [
    "Automaton",
    "State",
    "Transition",
    "GuardFunction",
    "ResetFunction",
    "InvariantFunction",
    "IntegrationMethods",
    "IntegrationFunction",
    "ContinousDynamicsFunction",
    'guard',
    'reset',
    'invariant'
]
