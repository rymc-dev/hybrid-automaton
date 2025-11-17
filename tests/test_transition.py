import pytest
from hybrid_automaton import HybridState
from hybrid_automaton import HybridTransition
from unittest.mock import Mock


class TestHybridTransition: 
    """ === valid test case paths === """
    @pytest.mark.parametrize(
        'kwargs',
        [
            {'name': 't', 'value': 0, 'to_state': Mock(spec=HybridState)},
            {'name': 't', 'value': 0, 'to_state': Mock(spec=HybridState), 'priority': 1},
            {'name': 't', 'value': 0, 'to_state': Mock(spec=HybridState), 'guards': [Mock()], 'priority': 1},
            {'name': 't', 'value': 0, 'to_state': Mock(spec=HybridState), 'guards': [Mock()], 'reset': Mock(), 'priority': 1},
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
            t = HybridTransition(**kwargs)
            assert isinstance(t, HybridTransition)
        except AssertionError:
            pytest.fail(f"Test failed: {request.node.callspec.id}")

    @pytest.mark.parametrize(
            "guards, expected",
            [
                (None, True),
                ([lambda x, aux_x, u, ctx, dt: False], False),
                ([lambda x, aux_x, u, ctx, dt: output for output in [True,False]], False),
                ([lambda x, aux_x, u, ctx, dt: output for output in [True,True,True]], True)
            ],
            ids=[
                "T1: no guards, should auto pass through enabled",
                "T2: single guard that always fails",
                "T3: one guard active another not, therefore union of guards is false",
                "T4: all guard functions returned true therefore all of true"
            ]
    )
    def test_valid_is_enabled(self, guards, expected): 
        mock_hybrid_transition = HybridTransition(
            name='t1',
            value=1,
            to_state=Mock(spec=HybridState),
            guards=guards,
            priority=0
        )
        # expect enabled when no guards, otherwise all guards must return True
        actual = mock_hybrid_transition.is_enabled(None, None, None, None) 
        assert actual == expected
    
    @pytest.mark.parametrize(
        "input_kwargs, reset_func, expected_output",
        [
            (
                {"x": [10.0, 10.0], "aux_x": [40, 40], "u": None, "ctx": None, "dt": 0.1},
                lambda x, aux_x, u, ctx, dt: (x, aux_x),
                ([10.0, 10.0], [40.0, 40.0])
            )
        ],
        ids=["T1"]
    )
    def test_apply_rest(self, input_kwargs, reset_func, expected_output):
        t = HybridTransition(
            name='t1',
            value=1,
            to_state=Mock(spec=HybridState),
            guards=None,
            reset=reset_func,
            priority=0
        )
        output = t.apply_reset(input_kwargs['x'], input_kwargs['aux_x'], input_kwargs['u'], input_kwargs['ctx'], input_kwargs['dt'])
        assert output == expected_output

    @pytest.mark.parametrize(
        "reset_func, input_kwargs, expected_output",
        [
            # T1: reset function modifies states
            (
                lambda x, aux_x, u, ctx, dt: ([xi + 1 for xi in x], [ai + 2 for ai in aux_x]),
                {"x": [1, 2], "aux_x": [10, 20], "u": None, "ctx": None, "dt": 0.1},
                ([2, 3], [12, 22])
            ),
            # T2: no reset function, should pass through
            (
                None,
                {"x": [5, 5], "aux_x": [50, 50], "u": None, "ctx": None, "dt": 0.1},
                ([5, 5], [50, 50])
            ),
        ],
        ids=["T1: reset modifies states", "T2: no reset, pass-through"]
    )
    def test_execute(self, reset_func, input_kwargs, expected_output):
        mock_to_state = Mock(spec=HybridState)
        t = HybridTransition(
            name="t_execute",
            value=1,
            to_state=mock_to_state,
            guards=None,
            reset=reset_func,
            priority=0
        )
        
        to_state, new_x, new_aux_x = t.execute(
            input_kwargs['x'],
            input_kwargs['aux_x'],
            input_kwargs['u'],
            input_kwargs['ctx'],
            input_kwargs['dt']
        )

        # Check next state matches the mock
        assert to_state == mock_to_state
        # Check new x and aux_x match expected
        assert new_x == expected_output[0]
        assert new_aux_x == expected_output[1]


if __name__ == '__main__':
    pytest.main([__file__])