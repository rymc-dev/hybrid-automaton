from typing import List, Optional, Any, Dict, Callable
from .automaton_state import State
import hashlib
import json

class Definition: 
    """ 
    Definition class for the Automaton, 
    contains static information about the automaton.

    Class Attributes: 
        _id_counter: int
            class level id counter for assigning unique ids to automaton definitions

    Args: 
        name: str
            string represneation of the automaton
        states: List[State]
            list of discrete states for the automaton
        on_entry: Optional[Callable]
            hook function when automaton runtime is started this is called
        on_exit: Optional[Callable] 
            hook function for when automaton runtime has completed
    """
    _id_counter: int = 0

    def __init__(
        self, 
        name: str, 
        version: str,
        states: List[State], 
        configuration: Dict[str, Any] = {},
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None
    ): 
        self.name = name
        self.version = version
        self.id = Definition._id_counter
        Definition._id_counter += 1

        self.states = states
        init_idx = [i for i, s in enumerate(self.states) if getattr(s, "_is_init", False)]
        cnt_init = len(init_idx)
        if cnt_init > 1 or cnt_init == 0: 
            raise ValueError(f"invalid HybridAutomaton initialization, need 1 initial state, got {cnt_init}")
        
        self._configuration = configuration
        self.state_t0 = self.states[init_idx[0]]

        self._on_entry = on_entry
        self._on_exit = on_exit

    def on_entry(self):
        if self._on_entry is None:
            return 
        
        self._on_entry()

    def on_exit(self):
        if self._on_exit is None:
            return
        
        self._on_exit()

    def get_configuration(self) -> Dict:
        return self._configuration
    
    def get_configuration_hash(self) -> Any:
        serialized = json.dumps(self._configuration, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return digest[:12]

    def _to_mermaid(self):
        """Return a Mermaid stateDiagram-v2 representation of the automaton."""

        lines = ["stateDiagram-v2"]

        lines.append(f"    direction LR")

        # ---------------------------------------------------------
        # Initial state arrow
        # ---------------------------------------------------------
        lines.append(f"    [*] --> {self.state_t0.name}")

        # ---------------------------------------------------------
        # Transitions
        # ---------------------------------------------------------
        for state in self.states:
            for t in state.get_transitions():
                lines.append(
                    f"    {state.name} --> {t.to_state.name}: {t.name}"
                )

        # ---------------------------------------------------------
        # Invariants (optional annotation)
        # ---------------------------------------------------------
        for state in self.states:
            inv = ", ".join(i.name for i in state.get_invariants()) if state.get_invariants() else ""
            if inv:
                lines.append(f"    note right of {state.name}: invariant = {inv}")

        return "\n".join(lines)

    def __repr__(self):
        """string represnetaion for devs, this outputs the amdl format"""
        return self._to_mermaid()

    def __str__(self):
        """String representation for end users."""

        # ---------------------------------------------------------
        # Transitions
        # ---------------------------------------------------------
        transition_lines = []
        for state in self.states:
            for t in state.get_transitions():
                transition_lines.append(
                    f"\t\t{state.name} --[{t.name}]--> {t.to_state.name}"
                )

        transitions_block = "\n".join(transition_lines) if transition_lines else "\t\t<none>"

        # ---------------------------------------------------------
        # Continuous Dynamics
        # ---------------------------------------------------------
        continous_dynamics_lines = []
        for state in self.states:
            dyn = state.get_continous_dynamics()
            dyn_name = dyn.__name__ if dyn else "<none>"
            continous_dynamics_lines.append(
                f"\t\t{state.name} -> {dyn_name}"
            )

        continous_dynamics_block = "\n".join(continous_dynamics_lines)

        # ---------------------------------------------------------
        # Guards
        # ---------------------------------------------------------
        guard_lines = []
        for state in self.states:
            for t in state.get_transitions():
                if not t.guards:
                    guard_lines.append(f"\t\t{t.name}: <none>")
                    continue

                guard_list = ", ".join(g.name for g in t.guards)
                guard_lines.append(f"\t\t{t.name}: [{guard_list}]")

        guards_block = "\n".join(guard_lines) if guard_lines else "\t\t<none>"

        # ---------------------------------------------------------
        # Resets
        # ---------------------------------------------------------
        reset_lines = []
        for state in self.states:
            for t in state.get_transitions():
                if not t.reset:
                    reset_lines.append(f"\t\t{t.name}: <none>")
                    continue
                else: 
                    reset_lines.append(f"\t\t{t.name}: {t.reset.__name__}")

        resets_block = "\n".join(reset_lines) if reset_lines else "\t\t<none>"

        invariant_lines = []

        for state in self.states:
            invariants_list = ", ".join(i.name for i in state.get_invariants()) if state.get_invariants() is not None else "<none>"
            invariant_lines.append(f"\t\t{state.name}: [{invariants_list}]")

        invariants_block = "\n".join(invariant_lines) if invariant_lines else "\t\t<none>"

        # ---------------------------------------------------------
        # Modes
        # ---------------------------------------------------------
        modes = ", ".join(s.name for s in self.states)

        # ---------------------------------------------------------
        # Final string return
        # ---------------------------------------------------------
        return (
            "Hybrid Automaton Definition:\n"
            f"\tname: {self.name}\n"
            f"\tid: {self.id}\n"
            f"\tinitial_mode: {self.state_t0.name}\n"
            f"\tmodes: [{modes}]\n"
            f"\ttransitions:\n{transitions_block}\n"
            f"\tguards:\n{guards_block}\n"
            f"\tresets:\n{resets_block}\n"
            f"\tinvariants:\n{invariants_block}\n"
            f"\tcontinous_dynamics:\n{continous_dynamics_block}\n"
        )

