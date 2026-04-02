# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT

from ._automaton import Automaton
from ._runtime import _Runtime 

RuntimeContext = _Runtime.Context
RunResult = _Runtime.RunResult
ContinuousState = RuntimeContext.ContinuousState
AuxiliaryState = RuntimeContext.AuxiliaryState
ControlState = RuntimeContext.ControlInput
IntegrationFunction = ContinuousState.IntegrationFcn

__author__ = "Ryan McKee <R.McKee@liverpool.ac.uk>"
__version__ = "0.0.7"

__all__ = [
   'Automaton', 
   'RuntimeContext',
   'RunResult',
   'ContinuousState',
   'AuxiliaryState',
   'ControlState',
   'IntegrationFunction'
]
