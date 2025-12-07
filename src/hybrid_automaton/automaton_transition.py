from typing import Optional, List, Callable, Any, Tuple
from .automaton_runtime_context import Context
from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from hybrid_automaton.automaton_state import State

class Transition:
    """ 
    Defines the transition logic for a hybrid automaton model.

    Args: 
        name: str
            human readable transition name for huamn viewing
        value: int 
            a simple storage/retrieval represenation of this transition, should be unique 
            for a hybrid automaton model
        to: HybridState
            a referece to a HybridState that this transition should transition to
        guard: Optional[Callable]
            an optional guard function that determines if guard is active or inactive
        reset: Optional[Callable]
            an optional reset function that determinal if reset is avaiable for during transition 


    Functions:
    """

    _id_counter = 0

    def __init__(
        self,
        name: str,
        to_state: "State",
        guards: Optional[List[Callable[[Context], bool]]] = None,
        reset: Optional[Callable[[Context], Context]] = None,
        priority: int = 0
    ):
        if not isinstance(name, str):
            raise ValueError('')
        if not isinstance(priority, int):
            raise ValueError('')

        self._name = name
        self._id = Transition._id_counter
        Transition._id_counter += 1
        self._to_q = to_state
        self._G = guards
        self._R = reset
        self._priority = priority
    
    @property
    def name(self):
        return self._name

    @property
    def id(self): 
        return self._id

    @property
    def priority(self): 
        return self._priority
    
    @property
    def to_state(self):
        return self._to_q
    
    @property
    def guards(self): 
        return self._G
    
    @property
    def reset(self):
        return self._R

    def is_enabled(self, ctx: Context) -> bool:
        """
        apply guard to continous state and/or auxielary context 
        to see if transition is enabled or not

        Args: 
            ctx: Context
                the runtime context for the automaton

        Outputs: 
            boolean: represents if transition is enabled
        """
        if self._G is None:
            return True # pass through guard, always true if guard not given
        
        return all(g(ctx) for g in self._G)
    
    def apply_reset(self, ctx: Context) -> Context: 
        """
        apply reset to continous states and/or auxielary context information 
        for the hybrid automaton model

        Args: 
            ctx: Context
                contains runtime context
        Outputs:
            returns the context after changes made
        """
        if self._R is None: 
            return ctx # pass through, reset just returns the x and ctx
        return self._R(ctx)
    
    def execute(self, ctx: Context) -> Tuple["State", Context]:
        """ 
        execute applies resets to the current contious and auxielary states
        utilzing information regarding the automaton and also return the next state

        Args: 
            ctx: Context
                contains the automaton runtime context

        Outputs: 
            Tuple[State, Context]
                returns the next state after transition execution and the update context
        """
        ctx = self.apply_reset(ctx)
        return self._to_q, ctx
    
    def __repr__(self): 
        """Developer representation: unambiguous string useful for debugging."""
        to_name = getattr(self._to_q, "name", repr(self._to_q))
        guards_repr = None if self._G is None else [getattr(g, "__name__", repr(g)) for g in self._G]
        reset_repr = None if self._R is None else getattr(self._R, "__name__", repr(self._R))
        return (
            f"HybridTransition(name={self._name!r}, value={self._value!r}, "
            f"to={to_name!r}, guards={guards_repr!r}, reset={reset_repr!r}, "
            f"priority={self._priority!r})"
        )
    
    def __str__(self): 
        """User-friendly string: shows target, guard names and reset name."""
        to_name = getattr(self._to_q, "name", repr(self.to_q))
        if self._G:
            guards_list = [getattr(g, "__name__", repr(g)) for g in self._G]
            guards_str = ", ".join(guards_list)
        else:
            guards_str = "None"
        reset_str = getattr(self._R, "__name__", repr(self._R)) if self._R is not None else "None"
        return (
            f"Transition '{self._name}' -> {to_name} (value={self._value}, priority={self._priority}, "
            f"guards=[{guards_str}], reset={reset_str})"
        )
