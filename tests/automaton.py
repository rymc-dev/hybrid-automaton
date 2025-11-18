import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'hybrid_automaton'))

import pytest
from hybrid_automaton import Transition
from hybrid_automaton import State
from unittest.mock import Mock
import pytest


class TestTransition: 
    """ === valid test case paths === """
    @pytest.mark.parametrize(
        'kwargs',
        [
            {'name': 't', 'value': 0, 'to_state': Mock(spec=State)},
            {'name': 't', 'value': 0, 'to_state': Mock(spec=State), 'priority': 1},
            {'name': 't', 'value': 0, 'to_state': Mock(spec=State), 'guards': [Mock()], 'priority': 1},
            {'name': 't', 'value': 0, 'to_state': Mock(spec=State), 'guards': [Mock()], 'reset': Mock(), 'priority': 1},
        ],
        ids=[
            'T1: Minimal initialization',
            'T2: Minimal intiialization w/ priority',
            'T3: initialization w/ guards', 
            'T4: intiialization w/ guards and reset'     
        ]
    )
    def test_valid_initialization(self, kwargs, request):
        try:
            t = Transition(**kwargs)
            assert isinstance(t, Transition)
        except AssertionError:
            pytest.fail(f"Test failed: {request.node.callspec.id}")

    @pytest.mark.parametrize(
            "guards, expected",
            [
                (None, True),
                ([lambda x, u, ctx, dt: False], False),
                ([lambda x, u, ctx, dt: output for output in [True,False]], False),
                ([lambda x, u, ctx, dt: output for output in [True,True,True]], True)
            ],
            ids=[
                "T1: no guards, should auto pass through enabled",
                "T2: single guard that always fails",
                "T3: one guard active another not, therefore union of guards is false",
                "T4: all guard functions returned true therefore all of true"
            ]
    )
    def test_valid_is_enabled(self, guards, expected): 
        mock_hybrid_transition = Transition(
            name='t1',
            value=1,
            to_state=Mock(spec=State),
            guards=guards,
            priority=0
        )
        # expect enabled when no guards, otherwise all guards must return True
        actual = mock_hybrid_transition.is_enabled(None, None, None, None) 
        assert actual == expected

    @pytest.mark.parametrize(
        "reset, result",
        [
            ()
        ],
        ids=[

        ]
    )
    def test_valid_apply_reset(self, reset, result):
        """ do something here, blah blah """
        pass

    @pytest.mark.parametrize(
        "reset, result",
        [
            (),
        ],
        ids=[
            "T1",
        ]
    )
    def test_valid_execute():
        ...

    """ === invalid test case paths === """
    
    # def test_is_enabled(): 
    #     assert True

    # def test_apply_reset():
    #     assert True

    # def test_execute(): 
    #     assert True

if __name__ == '__main__': 
    pytest.main([__file__])
