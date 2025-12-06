from typing import Optional, Callable, List, Any, Tuple
import asyncio
from .automaton_transition import Transition

class State:
    """ 
    HybridState is a discrete state represeting a control mode the hybrid
    automaton can be in. 

    Args: 
        name: str
            A human-readable representation of the state. Default is derived
            from the value
        value: int
            A specific value for representation of the state for retrieval/storage of it
        initial: Optional[bool]
            Set ``True`` if the state is the inital one, There must only be one
            state ever at a time, defaults to ``False``
        final: Optional[bool] 
            Set ``True`` to represent a final state. FIle states have no :ref: to transition
            starting from it, Defaults to ``False``
        flow: Optional[Callbable] 
            flow function utilized for calculation of continous state of the hybrid automaton, 
            defaults to ``none`` meaning continous dynamics return nothing
        invariants: Optional[List[Callable]] 
            invariant function utilzied while inside hybrid automaton state, can evaluate continous
            state and auxielary context of the environment and generate true/false values based on whether
            we should be in this state.
        transitions: Optional[HybridTransition]
            A list of HybridTransitions associated with this hybrid automaton state
        integration_method: Optional[Callable] 
            This is an optional function for continous dynamic simulation it is required if 
            automaton is simulation otherwise not if real time because continous state will be generated 
            by sensors and external data
        on_enter: Optional[Callable]
            One or more action callbacks assigned to be exectued when the state is activated
        on_exit: Optional[Callable] 
            One or more action callbacks assigned to be executed when the state is being exectued


    Functions: 
        evaluate_transitions(x: Any, ctx: Any) -> ...: 
            a coro async function for evaluation of transitions within for this state.#

        continous_dynamics(x: Any, Optional[Any])
    """

    _id_counter = 0


    def __init__(
        self,
        name: str = "",
        initial: bool = False,
        final: bool = False,
        flow: Optional[Callable] = None,
        invariants: Optional[List[Callable]] = None,
        transitions: Optional[List['Transition']] = None,
        integartion_method: Optional[Callable] = None,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None
    ):
        self.name = name
        self._id = State._id_counter
        State._id_counter += 1
        self.flow = flow
        self._Inv = invariants
        self._D = [] if transitions == None else transitions
        self.integration_method = integartion_method
        self._is_init = initial
        self._is_final = final
        self.on_enter = on_enter
        self.on_exit = on_exit

    def get_state_id(self): 
        return self._id
    
    def get_transitions(self):
        return self._D
    
    def get_invariants(self):
        return self._Inv

    def get_continous_dynamics(self):
        return self.flow

    def add_transition(self, d: Transition): 
        """function for adding transition post HybridState obj creation"""
        self._D.append(d)

    def add_transitions(self, D: List[Transition]):
        """add several transitions to the state"""
        [self._D.append(d) for d in D]

    def remove_transition(self, d: Transition):
        """remove a transition from transitions"""
        self._D.remove(d)

    def evaluate_transitions(
        self,
        x: Any,
        aux_x: Any = None,
        u: Optional[Any] = None,
        cfg: Optional[Any] = {},
        clk: Optional[Any] = None
    ) -> List[Tuple[Transition, bool, Optional[Exception]]]:
        """
        Synchronously evaluate guards for each Transition.

        Returns a list of tuples (transition, enabled, exception). If an exception
        occurred while evaluating a guard, `enabled` will be False and `exception`
        contains the caught exception.

        Args:
            x: continuous state
            ctx: auxiliary context for this Hybrid Automaton
        """

        if not self._D:
            return []

        results = []
        for d in self._D:
            try:
                enabled = bool(d.is_enabled(x, aux_x, u, cfg, clk))
                results.append((d, enabled, None))
            except Exception as e:
                results.append((d, False, e))

        return results

    def continuous_dynamics(self, x: Any, aux_x: Optional[Any] = None, u: Optional[Any] = None,  cfg: Optional[Any] = None, clk: Optional[Any] = None) -> Any:
        """
        Process continuous dynamics using current state and context.
        Synchronous function.

        Args: 
            x: Any  
                continous dynamics representation for this model
            u: Optional[Any]
                optional command inputs like rudder, thrust, etc....
            ctx: Optional[Any]
                auxielary contexts like goal waypoints, or some other params for the continous dynamics.
        """
        if self.flow is None:
            return x if x is not None else []
        return self.flow(x, aux_x, u, cfg, clk)

    def check_invariants(self, x, aux_x=None, u=None, cfg=None, clk=None) -> bool:
        if not self._Inv:
            return False if self._is_final else True

        for i in self._Inv:
            try:
                if not bool(i(x, aux_x, u, cfg, clk)):
                    return False
            except Exception:
                return False

        return True
    
    def __repr__(self):
        """Developer representation: unambiguous string useful for debugging."""
        transitions_repr = None if not self._D else [
            getattr(d, "name", repr(d)) for d in self._D
        ]
        flow_repr = None if self.flow is None else getattr(self.flow, "__name__", repr(self.flow))
        invariants_repr = None if not self._Inv else [
            getattr(i, "__name__", repr(i)) for i in self._Inv
        ]
        return (
            f"HybridState(name={self.name}, id={self._id}, "
            f"flow={flow_repr}, invariants={invariants_repr}, "
            f"transitions={transitions_repr})"
        )

    def __str__(self):
        """User-facing string: shows state, flags, flow, invariants and transitions (with guards/resets)."""
        # Flags
        flags = []
        if self._is_init:
            flags.append("initial")
        if self._is_final:
            flags.append("final")
        flags_str = ", ".join(flags) if flags else "normal"

        # Flow function
        flow_str = getattr(self.flow, "__name__", repr(self.flow)) if self.flow is not None else "None"

        # Invariants
        Inv_str = "None" if not self._Inv else ", ".join(
            getattr(i, "__name__", repr(i)) for i in self._Inv
        )

        # Transitions (safe: print target state names only)
        if not self._D:
            D_str = "None"
        else:
            D_str_list = []
            for d in self._D:
                # Only show the target state's name or id to avoid recursion
                to_name = getattr(d._to_q, "name", f"<State id={id(d._to_q)}>")
                guards_list = [getattr(g, "__name__", repr(g)) for g in (d._G or [])]
                reset_name = getattr(d._R, "__name__", repr(d._R)) if d._R else "None"
                D_str_list.append(f"{d._name} -> {to_name}, guards={guards_list}, reset={reset_name}")
            D_str = "; ".join(D_str_list)

        return (
            f"State '{self.name}' (id={self._id}, {flags_str})\n"
            f"  flow: {flow_str}\n"
            f"  invariants: [{Inv_str}]\n"
            f"  transitions: [{D_str}]"
        )
