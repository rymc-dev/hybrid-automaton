from hybrid_automaton import State
from hybrid_automaton import Transition
import pytest

def test_add_transition(): 
    x = State()
    d = Transition("t", 1, None, None, None, 0)
    assert x._D == []

    x.add_transition(d)

    assert len(x._D) == 1
    assert x._D[-1] == d

def test_add_transitions():
    x = State()
    d1 = Transition("t1", 1, None, None, None, 0)
    d2 = Transition("t2", 2, None, None, None, 0)
    assert x._D == []

    x.add_transitions([d1, d2])

    assert len(x._D) == 2
    assert x._D[0] == d1
    assert x._D[1] == d2

# def test_remove_transition():
#     d = Transition("t", 1, None, None, None, 0)
#     x = State(transitions=[d])
#     d = Transition("t", 1, None, None, None, 0)
#     assert len(x._D) == 1 

#     x.remove_transition(d)

#     assert len(x._D) == 0


def test_evaluate_transitions():
    d1 = Transition("t1", 1, None, None, None, 0)
    d2 = Transition("t2", 2, None, None, None, 0)
    x = State(transitions=[d1, d2])

    results = x.evaluate_transitions(None)
    print (results)

def test_continous_dynamics():
    x = State(
        name="blah blah ", 
        flow=lambda x, aux_x, u, ctx, dt: [0.5, 5.0]
    )
    continous_dynamics = x.continuous_dynamics(None)
    assert continous_dynamics == [0.5, 5.0]


def test_check_invariants():

    x = State(
        invariants=[
            lambda x, aux_x, u, ctx, dt: True,
            lambda x, aux_x, u, ctx, dt: True
        ]
    )

    holds = x.check_invariants(None)

    assert holds == True


if __name__ == '__main__':
    pytest.main([__file__])