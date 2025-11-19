from typing import Optional, List, Callable, Any, Tuple

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
        to_state: Any,
        guards: Optional[List[Callable]] = None,
        reset: Optional[Callable] = None,
        priority: int = 0
    ):
        if not isinstance(name, str):
            raise ValueError('')
        # if not isinstance(to_state, HybridState):
        #     raise ValueError('')
        # TODO: should validate guard and reset are following
        # guard blueprint and reset blueprint

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
    def priority(self): 
        return self._priority
    
    @property
    def value(self): 
        return self._value
    
    @property
    def to_state(self):
        return self._to_q
    
    @property
    def guards(self): 
        return self._G
    
    @property
    def reset(self):
        return self._R

    def is_enabled(self, x: Any, aux_x: Optional[Any] = None, 
        u: Optional[Any] = None, ctx: Optional[Any] = None, 
        dt: Optional[float] = 0.1) -> bool:
        """
        apply guard to continous state and/or auxielary context 
        to see if transition is enabled or not

        Args: 
            x: Any
                continous state information representation
            u: Optional[Any]
                control input
            ctx: Optional[Any]
                auxilary information for the hybrid automaton model
            dt: Optional[float]
                the delta time for calculating future states

        Outputs: 
            boolean: represents if transition is enabled
        """
        if self._G is None:
            return True # pass through guard, always true if guard not given
        
        return all(g(x, aux_x, u, ctx, dt) for g in self._G)
    
    def apply_reset(self, x: Any, aux_x: Optional[Any] = None, 
        u: Optional[Any] = None, ctx: Optional[Any] = None, 
        dt: Optional[float] = 0.1) ->  Tuple[Any, Any]: 
        """
        apply reset to continous states and/or auxielary context information 
        for the hybrid automaton model

        Args: 
            x: Any
                continous state information
            aux_x: Optional[Any]
                auxielary continous state information
            u: Optional[Any]
                control input
            ctx: Optional[Any]
                auxielary context information represenation the for hybrid automaton
            dt: Optional[float]
                delta time

        Outputs:
            Tuple[x, aux_x]: represents new continous states and continous auxielary states
        """
        if self._R is None: 
            return x, aux_x # pass through, reset just returns the x and ctx
        return self._R(x, aux_x, u, ctx, dt)
    
    def execute(self, x: Any, aux_x: Optional[Any] = None, u: Optional[Any] = None, ctx: Optional[Any] = None, dt: Optional[float] = 0.1) -> Tuple[Any, Any, Any]:
        """ 
        execute applies resets to the current contious and auxielary states
        utilzing information regarding the automaton and also return the next state

        Args: 
            x: Any
                continous state representation
            aux_x: Optional[Any]
                auxialary continous state information
            u: Optional[Any]
                external inputs
            ctx: Optional[Any]
                auxiarly context of automaton
            dt: Optional[float] = 0.1
                the delta time in seconds
        """
        new_x, new_aux_x = self.apply_reset(x, aux_x, u, ctx, dt)
        return self._to_q, new_x, new_aux_x
    
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
