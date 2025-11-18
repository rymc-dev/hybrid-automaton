from hybrid_automaton import HybridState
from hybrid_automaton import HybridTransition
import pytest

def test_add_transition(): 
    x = HybridState()
    d = HybridTransition("t", 1, None, None, None, 0)
    assert x._D == []

    x.add_transition(d)

    assert len(x._D) == 1
    assert x._D[-1] == d

def test_add_transitions():
    x = HybridState()
    d1 = HybridTransition("t1", 1, None, None, None, 0)
    d2 = HybridTransition("t2", 2, None, None, None, 0)
    assert x._D == []

    x.add_transitions([d1, d2])

    assert len(x._D) == 2
    assert x._D[0] == d1
    assert x._D[1] == d2

# def test_remove_transition():
#     d = HybridTransition("t", 1, None, None, None, 0)
#     x = HybridState(transitions=[d])
#     d = HybridTransition("t", 1, None, None, None, 0)
#     assert len(x._D) == 1 

#     x.remove_transition(d)

#     assert len(x._D) == 0


def test_evaluate_transitions():
    d1 = HybridTransition("t1", 1, None, None, None, 0)
    d2 = HybridTransition("t2", 2, None, None, None, 0)
    x = HybridState(transitions=[d1, d2])

    results = x.evaluate_transitions(None)
    print (results)

def test_continous_dynamics():
    x = HybridState(
        name="blah blah ", 
        flow=lambda x, aux_x, u, ctx, dt: [0.5, 5.0]
    )
    continous_dynamics = x.continuous_dynamics(None)
    assert continous_dynamics == [0.5, 5.0]


def test_check_invariants():

    x = HybridState(
        invariants=[
            lambda x, aux_x, u, ctx, dt: True,
            lambda x, aux_x, u, ctx, dt: True
        ]
    )

    holds = x.check_invariants(None)

    assert holds == True


if __name__ == '__main__':
    pytest.main([__file__])