#! /usr/bin/python3

""" 
automaton_definition.py

contains the definition object for defining the static
structure of a hybrid automaton in this package.
"""


from typing import List, Optional, Any, Dict, Callable,Tuple 
import hashlib
import json
import numpy as np
from typing import Tuple
# Definition Decorators

# TODO: Need to investigate if there is a point in the _ANNOTATION class
class _Annotation:
    def __init__(self, func: Callable, name=None, priority=0, description=""):
        self.func = func
        self.name = name or func.__name__
        self.priority = priority
        self.description = description

    def __call__(self, ctx):
        from ._runtime import _Runtime
        Context = _Runtime.Context
        if not isinstance(ctx, Context):
            raise TypeError(f"{self.name}: ctx must be a Context instance")
        return self.func(ctx)

def continuous_state_provider(func: Callable = None, *, name=None, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not None:
                raise TypeError(f"Continuous State provider:'{f.__name__}' must return none as this is an action class")
        return _Annotation(f, name="continuous_state_sampler", priority=-1, description=description)
    return wrapper(func) if func else wrapper

def auxiliary_state_provider(func: Callable = None, *, name=None, description=""):
    if hasattr(f, "__annotations__") and "return" in f.__annotations__:
        if f.__annotations__["return"] is not None:
            raise TypeError(f"Auxiliary States provider:'{f.__name__}' must return none as this is an action class")
        return _Annotation(f, name="auxiliary_states_provider", priority=-1, description=description)
    return wrapper(func) if func else wrapper 

def control_input_states_provider(func: Callable = None, *, name=None, description=""):
    if hasattr(f, "__annotations__") and "return" in f.__annotations__:
        if f.__annotations__["return"] is not None:
            raise TypeError(f"Control Inputs State provider:'{f.__name__}' must return none as this is an action class")
        return _Annotation(f, name="control_inputs_state_provider", priority=-1, description=description)
    return wrapper(func) if func else wrapper 

def guard(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Guard '{f.__name__}' must return bool")
        return _Annotation(f, name=name, priority=priority, description=description)
    return wrapper(func) if func else wrapper

def invariant(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Invariant '{f.__name__}' must return bool")
        return _Annotation(f, name=name, priority=priority, description=description)
    return wrapper(func) if func else wrapper

def reset(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        def inner(ctx):
            result = f(ctx)
            from ._runtime import _Runtime
            Context = _Runtime.Context
            if not isinstance(result, Context):
                raise TypeError(f"Reset '{f.__name__}' must return a Context instance")
            return result
        inner.__name__ = name or f.__name__
        inner.priority = priority
        inner.description = description
        return inner
    return wrapper(func) if func else wrapper

def continuous_dynamics(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not np.ndarray:
                raise TypeError(f"Continuous Dynamics '{f.__name__}' must return np.ndarray")
        
        def inner(ctx):
            # Validate context first
            from ._runtime import _Runtime
            Context = _Runtime.Context
            if not isinstance(ctx, Context):
                raise TypeError(f"Continuous Dynamics '{f.__name__}': ctx must be a Context instance")

            result = f(ctx)
            if not isinstance(result, np.ndarray):
                raise TypeError(f"Continuous Dynamics '{f.__name__}' must return np.ndarray")
            return result

        inner.__name__ = name or f.__name__
        inner.priority = priority
        inner.description = description
        return inner

    return wrapper(func) if func else wrapper

def integration(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not np.ndarray:
                raise TypeError(f"Integration '{f.__name__}' must return np.ndarray")
        def inner(ctx):
            result = f(ctx)
            if not isinstance(result, np.ndarray):
                raise TypeError(f"Integration '{f.__name__}' must return np.ndarray")
            return result
        inner.__name__ = name or f.__name__
        inner.priority = priority
        inner.description = description
        return inner
    return wrapper(func) if func else wrapper


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
        guards: Optional[List[Callable[[Any], bool]]] = None,
        reset: Optional[Callable[[Any], Any]] = None,
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

    def is_enabled(self, ctx) -> bool:
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
    
    def apply_reset(self, ctx) -> Any: 
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
        try:
            return self._R(ctx)
        except Exception as e:
            raise RuntimeError(f"Error applying reset function '{self._R.__name__}' for transition '{self._name}': {e}") from e
    
    def execute(self, ctx) -> Tuple["State", Any]:
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
        ctx: Any 
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
                enabled = bool(d.is_enabled(ctx))
                results.append((d, enabled, None))
            except Exception as e:
                results.append((d, False, e))

        return results

    def continuous_dynamics(self, ctx: Any) -> np.array:
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
            return np.array([])
        try:
            return self.flow(ctx)
        except Exception as e:
            raise Exception(f"Error in continuous dynamics of state '{self.name}': {str(e)}") from e

    def check_invariants(self, ctx: Any) -> bool:
        if not self._Inv:
            return False if self._is_final else True
        # TODO: IMprove through dynamic programming
        # try: return not any([i(ctx) for i in self.Inv]); except Exception: return False
        for i in self._Inv:
            try:
                if not bool(i(ctx)):
                    return False
            except Exception as e:
                raise Exception(f"Error in invariant check of state '{self.name}: {str(e)}") from e

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

class _Definition: 
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
        self.id = _Definition._id_counter
        _Definition._id_counter += 1

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
    
    def get_definition_hash(self, short: bool = True) -> str:
        """
        Return a deterministic hash of the automaton definition structure.
        This is suitable for use as a run signature component.
        """

        def state_repr(state: State) -> Dict[str, Any]:
            return {
                "name": state.name,
                "is_initial": state is self.state_t0,
                "invariants": sorted(i.name for i in state.get_invariants() or []),
                "continuous_dynamics": (
                    state.get_continous_dynamics().__name__
                    if state.get_continous_dynamics()
                    else None
                ),
                "transitions": sorted(
                    [
                        {
                            "name": t.name,
                            "to": t.to_state.name,
                            "guards": sorted(g.name for g in t.guards or []),
                            "reset": t.reset.__name__ if t.reset else None,
                        }
                        for t in state.get_transitions()
                    ],
                    key=lambda x: (x["name"], x["to"]),
                ),
            }

        definition_repr = {
            "name": self.name,
            "version": self.version,
            "configuration": self._configuration,
            "states": sorted(
                [state_repr(s) for s in self.states],
                key=lambda x: x["name"],
            ),
        }

        serialized = json.dumps(
            definition_repr,
            sort_keys=True,
            separators=(",", ":"),
        )

        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return digest[:12] if short else digest