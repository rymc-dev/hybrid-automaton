# conftest.py
import pytest
import numpy as np
from hybrid_automaton import Automaton, State, Transition


@pytest.fixture
def automaton_mock():
    """
    Default fixture: creates a mock automaton with:
        x0 = {"heading": 1.0}
        real_time = True
    Tests may override fields as needed.
    """

    q1 = State(name="cruise")
    q2 = State(name="avoid")


    return Automaton(
        name="vessel_automaton",
        states=[q1, q2]
    )
