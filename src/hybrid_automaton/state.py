from typing import Optional, Callable, List, Any, Tuple
import asyncio
from .transition import HybridTransition

class HybridState:
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

        continous_dynamics(x: Any, Optional[Any], dt)
    """

    def __init__(
        self,
        name: str = "",
        value: int = 0,
        initial: bool = False,
        final: bool = False,
        flow: Optional[Callable] = None,
        invariants: Optional[List[Callable]] = None,
        transitions: Optional[List['HybridTransition']] = None,
        integartion_method: Optional[Callable] = None,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None
    ):
        self.name = name
        self.value = value
        self.flow = flow
        self._Inv = invariants
        self._D = [] if transitions == None else transitions
        self.integration_method = integartion_method
        self._is_init = initial
        self._is_final = final
        self.on_enter = on_enter
        self.on_exit = on_exit

    def add_transition(self, d: HybridTransition): 
        """function for adding transition post HybridState obj creation"""
        self._D.append(d)

    def add_transitions(self, D: List[HybridTransition]):
        """add several transitions to the state"""
        [self._D.append(d) for d in D]

    def remove_transition(self, d: HybridTransition):
        """remove a transition from transitions"""
        self._D.remove(d)

    async def evaluate_transitions(self, x: Any, u: Optional[Any] = None, ctx: Optional[Any] = None, dt: float = 0.1) -> List[Tuple[HybridTransition, bool, Optional[Exception]]]:
        """
        Concurrently evaluate guards for each HybridTransition.

        Returns a list of tuples (transition, enabled, exception). If an exception
        occurred while evaluating a guard, `enabled` will be False and `exception`
        contains the caught exception.

        Args: 
            x: continous state
            ctx: auxielary context for this Hybrid Automaton to run
        """
        if not self._D:
            return []

        async def _eval(d: HybridTransition):
            try:
                enabled = bool(d.is_enabled(x, ctx))
                return (d, enabled, None)
            except Exception as e:
                return (d, False, e)

        coros = [_eval(d) for d in self._D]
        results = await asyncio.gather(*coros, return_exceptions=False)
        return results

    async def continuous_dynamics(self, x: Any, aux_x: Optional[Any] = None, u: Optional[Any] = None,  ctx: Optional[Any] = None, dt: Optional[float] = None) -> Any:
        """
        Process continuous dynamics using current state and context.
        Synchronous function.

        Args: 
            x: Any  
                continous dynamics representation for this model
            u: Optional[Any]
                optional command inputs like rudder, thrust, etc....
            dt: Optional[float]
                optional delta time for continous dynamics that required future predictions,
                dt represented in seconds
            ctx: Optional[Any]
                auxielary contexts like goal waypoints, or some other params for the continous dynamics.
        """
        if self.flow is None:
            return x if x is not None else []
        return self.flow(x, u, dt, ctx)

    async def check_invariants(self, x: Any, aux_x: Optional[Any] = None, u: Optional[Any] = None, ctx: Optional[Any] = None, dt: float = 0.1) -> bool:
        """
        a coro async function for checking invariants for this HybridState

        Args: 
            x: Optional[Any]
                continous state represntation
            ctx: Optional[Any]
                auxielary context information

        returns: 
        bool: True if invariant holds, else False
        """
    
        if not self._Inv:
            return True

        async def _eval(i: Callable):
            try:
                enabled = bool(i(x, ctx))
                return (i, enabled, None)
            except Exception as e:
                return (i, False, e)

        coros = [_eval(i) for i in self._Inv]
        results = await asyncio.gather(*coros, return_exceptions=False)
        return results
    
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
            f"HybridState(name={self.name}, value={self.value}, "
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
                to_name = getattr(d.to_q, "name", f"<State id={id(d.to_q)}>")
                guards_list = [getattr(g, "__name__", repr(g)) for g in (d.G or [])]
                reset_name = getattr(d.R, "__name__", repr(d.R)) if d.R else "None"
                D_str_list.append(f"{d.name} -> {to_name}, guards={guards_list}, reset={reset_name}")
            D_str = "; ".join(D_str_list)

        return (
            f"State '{self.name}' (value={self.value}, {flags_str})\n"
            f"  flow: {flow_str}\n"
            f"  invariants: [{Inv_str}]\n"
            f"  transitions: [{D_str}]"
        )
