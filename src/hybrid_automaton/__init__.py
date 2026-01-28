# SPDX-FileCopyrightText: 2025-present Ryan McKee <ryanmckee47@icloud.com>
#
# SPDX-License-Identifier: MIT

from ._automaton import Automaton
from ._runtime import _Runtime

RuntimeContext = _Runtime.Context

__author__ = "Ryan McKee <R.McKee@liverpool.ac.uk>"
__version__ = "0.0.6"

__all__ = [
   'Automaton', 
   'RuntimeContext'
]
