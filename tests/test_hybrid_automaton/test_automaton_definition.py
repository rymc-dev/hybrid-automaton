from hybrid_automaton.automaton_definition import Definition


import pytest
from unittest.mock import Mock
from hybrid_automaton.automaton_state import State
from hybrid_automaton.automaton_definition import Definition

# --- Helper functions ---
def dummy_flow(x, aux_x=None, u=None, cfg=None, clk=None):
    return x

def dummy_invariant(x, aux_x=None, u=None, cfg=None, clk=None):
    return True

# --- Fixtures ---
@pytest.fixture
def state_initial():
    s = Mock(spec=State)
    s.name = "InitState"
    s._is_init = True
    s._is_final = False
    s.get_transitions.return_value = []
    s.get_invariants.return_value = [dummy_invariant]
    s.get_continous_dynamics.return_value = dummy_flow
    return s

@pytest.fixture
def state_non_initial():
    s = Mock(spec=State)
    s.name = "NonInitState"
    s._is_init = False
    s._is_final = False
    s.get_transitions.return_value = []
    s.get_invariants.return_value = []
    s.get_continous_dynamics.return_value = None
    return s

# --- Tests ---
class TestDefinition:

    def test_definition_creation_valid(self, state_initial, state_non_initial):
        d = Definition(name="TestAutomaton", states=[state_initial, state_non_initial])
        assert d.name == "TestAutomaton"
        assert d.state_t0 == state_initial
        assert d.get_configuration() == {}
        assert isinstance(d.id, int)

    def test_definition_creation_invalid_no_initial(self, state_non_initial):
        with pytest.raises(ValueError, match="invalid HybridAutomaton initialization"):
            Definition(name="InvalidAutomaton", states=[state_non_initial])

    def test_definition_creation_invalid_multiple_initial(self, state_initial):
        another_initial = Mock(spec=State)
        another_initial.name = "AnotherInit"
        another_initial._is_init = True
        another_initial._is_final = False
        another_initial.get_transitions.return_value = []
        another_initial.get_invariants.return_value = []
        another_initial.get_continous_dynamics.return_value = None

        with pytest.raises(ValueError, match="invalid HybridAutomaton initialization"):
            Definition(name="InvalidAutomaton", states=[state_initial, another_initial])

    def test_on_entry_and_exit_hooks_called(self, state_initial):
        entry_hook = Mock()
        exit_hook = Mock()
        d = Definition(name="AutomatonWithHooks", states=[state_initial], on_entry=entry_hook, on_exit=exit_hook)

        d.on_entry()
        entry_hook.assert_called_once()

        d.on_exit()
        exit_hook.assert_called_once()

    # def test_mermaid_repr_contains_state_names(self, state_initial, state_non_initial):
    #     d = Definition(name="AutomatonMermaid", states=[state_initial, state_non_initial])
    #     rep = repr(d)
    #     assert "stateDiagram-v2" in rep
    #     assert state_initial.name in rep
    #     assert state_non_initial.name in rep

    # def test_str_contains_modes_and_transitions(self, state_initial, state_non_initial):
    #     # Add mock transition
    #     t = Mock()
    #     t.name = "T1"
    #     t.to_state = state_non_initial
    #     t.guards = []
    #     t.reset = None
    #     state_initial.get_transitions.return_value = [t]

    #     d = Definition(name="AutomatonStr", states=[state_initial, state_non_initial])
    #     s = str(d)
    #     assert "Hybrid Automaton Definition:" in s
    #     assert state_initial.name in s
    #     assert state_non_initial.name in s
    #     assert t.name in s

if __name__ == '__main__': 
    pytest.main([__file__])