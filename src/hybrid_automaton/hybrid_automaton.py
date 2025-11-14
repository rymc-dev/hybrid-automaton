""" 
Hybrid Automaton is a model which models real-time and simulated 
tactical decision for navigating complex scenarios, This package implements
several classes, HybridTransition defines components of a transition 
for a hybrid automaton which is composed of guards and resets, 
Hybrid State contains transitions invariants and flow functions for 
calculation of continous dynamics which can be utilized by real world 
controllers or internally for simulating next states.
"""

import os
import sys

import time
sys.path.append(os.path.dirname(__file__))

from typing import Optional, Callable, List, Any, Tuple, Dict
import asyncio
from typing import Protocol

class GuardFunction(Protocol):
    def __call__(self, x, u, ctx, dt) -> bool: 
        ...

class ResetFunction(Protocol): 
    def __call__(self, x, u, ctx, dt) -> Tuple[Any, Any]: 
        ...

class InvariantFunction(Protocol): 
    def __call__(self, x, u, ctx, dt) -> bool: 
        ...

class IntegrationMethods: 
    def default_integration(self, x, xdot, dt):
        return x + xdot * dt
    
class HybridTransition:
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

    def __init__(
        self,
        name: str,
        value: int,
        to_state: "HybridState",
        guards: Optional[List[Callable]] = None,
        reset: Optional[Callable] = None,
        priority: int = 0
    ):
        if not isinstance(name, str):
            raise ValueError('')
        if not isinstance(value, int):
            raise ValueError('')
        if not isinstance(to_state, HybridState):
            raise ValueError('')
        # TODO: should validate guard and reset are following
        # guard blueprint and reset blueprint

        if not isinstance(priority, int):
            raise ValueError('')


        self.name = name
        self.value = value
        self.to_q = to_state
        self.G = guards
        self.R = reset
        self.priority = priority

    def is_enabled(self, x: Any, u: Optional[Any], ctx: Optional[Any] = None, dt: Optional[float] = 0.1) -> bool:
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
        if self.G is None:
            return True # pass through guard, always true if guard not given
        
        return all(g(x, u, ctx, dt) for g in self.G)
    
    def apply_reset(self, x: Any, u: Optional[Any], ctx: Optional[Any] = None, dt: Optional[float] = 0.1) ->  Tuple[Any, Any]: 
        """
        apply reset to continous states and/or auxielary context information 
        for the hybrid automaton model

        Args: 
            x: Any
                continous state information repesentation
            u: Optional[Any]
                control input
            ctx: Optional[Any]
                auxielary context information represenation the for hybrid automaton
            dt: Optional[float]
                delta time

        Outputs:
            Tuple[x, ctx]: represents new continous states and auxielary states
        """
        if self.R is None: 
            return x, ctx # pass through, reset just returns the x and ctx
        return self.R(x, u, ctx, dt)
    
    def execute(self, x: Any, u: Optional[Any] = None, ctx: Optional[Any] = None, dt: Optional[float] = 0.1) -> Tuple[Any, Any, Any]:
        """ 
        execute applies resets to the current contious and auxielary states
        utilzing information regarding the automaton and also return the next state

        Args: 
            x: Any
                continous states representation
            u: Optional[Any]
                external inputs
            ctx: Optional[Any]
                auxiarly context of automaton
            dt: Optional[float] = 0.1
                the delta time in seconds
        """
        new_x, new_ctx = self.apply_reset(x, u, ctx, dt)
        return self.to_q, new_x, new_ctx
    
    def __repr__(self): 
        """Developer representation: unambiguous string useful for debugging."""
        to_name = getattr(self.to_q, "name", repr(self.to_q))
        guards_repr = None if self.G is None else [getattr(g, "__name__", repr(g)) for g in self.G]
        reset_repr = None if self.R is None else getattr(self.R, "__name__", repr(self.R))
        return (
            f"HybridTransition(name={self.name!r}, value={self.value!r}, "
            f"to={to_name!r}, guards={guards_repr!r}, reset={reset_repr!r}, "
            f"priority={self.priority!r})"
        )
    
    def __str__(self): 
        """User-friendly string: shows target, guard names and reset name."""
        to_name = getattr(self.to_q, "name", repr(self.to_q))
        if self.G:
            guards_list = [getattr(g, "__name__", repr(g)) for g in self.G]
            guards_str = ", ".join(guards_list)
        else:
            guards_str = "None"
        reset_str = getattr(self.R, "__name__", repr(self.R)) if self.R is not None else "None"
        return (
            f"Transition '{self.name}' -> {to_name} (value={self.value}, priority={self.priority}, "
            f"guards=[{guards_str}], reset={reset_str})"
        )

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

    def add_transition(self, transition: HybridTransition): 
        """function for adding transition post HybridState obj creation"""
        self._D.append(transition)

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

    async def continuous_dynamics(self, x: Any, u: Optional[Any] = None,  ctx: Optional[Any] = None, dt: Optional[float] = None) -> Any:
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

    async def check_invariants(self, x: Any, u: Optional[Any] = None, ctx: Optional[Any] = None, dt: float = 0.1) -> bool:
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

class HybridAutomaton: 
    """ 
    model of the hybrid automaton 

    args: 
        name: str
            human readable representaiton of the hybrid automaton model
        value: int
            value respetnation of the hybrid automaton, clearly shows the model 
            for storage purposes in case you have sevelar models running at the same time
        states: List[HybridState]
            these are the Hybrid STates of the automaton, these represent the discrete modes
            of the automaton 

        real_time_mode: bool
            determines whether continous state should have simulated integration,
            (automation to compute xdot (continous dynamics) and integrate it with continous state
            on each internal loop), if true loop just uses whatever is provided for continous state via
            manual set_continous_state function which will be hooked up to sensors.

        on_entry: Optional[Callable]
            on entry callback function for when evaluation_loop_worker starts

        on_exit: Optional[Callable]
            on exit callback function for when evaluation_loop_worker completes

    
    
    functions:
        evaluation_loop_worker(self): 
            async coro worker for running the automaton 
            using asyncio

    
    """

    _q = None
    _x_t0 = None
    _x = None
    _aux_x_t0 = None
    _aux_x = None # auxielary continous state
    _u_t0 = None
    _u = None
    _ctx_t0 = None
    _ctx = None
    _dt = None
    _xdot = None
    _active = False
    _elapsed_time_active = None
    _elapsed_time_since_transition = None
    _elapsed_time_since_last_transition = None
    
    def __init__(
        self, 
        name: str, 
        value: int, 
        states: List[HybridTransition], 
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        real_time_mode: bool = False
    ):
        """ """
        
        self.NAME = name
        self.VALUE = value
        self.Q = states

        init_idx = [i for i, s in enumerate(self.Q) if getattr(s, "_is_init", False)]
        cnt_init = len(init_idx)
        if cnt_init == 0: 
            raise ValueError("invalid HybridAutomaton initialization, need 1 initial state, got 0.")
        if cnt_init > 1: 
            raise ValueError(f"invalid HybridAutomaton initialization, need 1 initial state, got {cnt_init}")
        
        self._real_time_mode = real_time_mode

        self._Q_T0 = self.Q[init_idx[0]]
        self._ON_ENTRY = on_entry
        self._ON_EXIT = on_exit

    """ === getters and setters === """
    @property
    def q(self): 
        return self._q

    @property
    def x(self): 
        return self._x
    
    @property
    def aux_x(self):
        return self._aux_x
    
    @property
    def u(self):
        return self._u

    @property
    def ctx(self):
        return self._ctx
    
    @property
    def dt(self):
        return self._dt

    @property
    def xdot(self): # NOTE: continous dynamics has not setter, becuase this is internally generated
        return self._xdot
    
    @property
    def elapsed_time_active(self): 
        return self._elapsed_time_active
    
    @property
    def elapsed_time_since_last_transition(self):
        return self._elapsed_time_since_last_transition
    
    def set_continous_state(self, new_continous_state: Any): # NOTE: This setter should only be avialable if real_time hybrid automaton.
        """explcit setter for the _x attribute value which is the continous state values of the hybrid automaton"""
        self._x = new_continous_state

    def set_auxilary_states(self, new_auxielary_states: Any):
        """explicit setting for the _aux_x value which is the values of auxelary continous states"""
        self._aux_x = new_auxielary_states

    def set_control_input(self, new_ctrl_input: Any): 
        """explicity setter for the internal _u control input vector"""
        self._u = new_ctrl_input
    
    def set_aux_context(self, new_aux_ctx: Dict[str, Any]):
        """explicit setter for the internal _ctx auxiliary context for the hybrid automaton""" 
        self._ctx = new_aux_ctx

    def set_dt(self, new_dt: float):
        """explicit setter for internal dt, used for timing of evalution loop and calculations"""
        self._dt = new_dt

    async def _elapsed_time_active_worker(self): 
        """a background worker for during the evaluation loop, for updating elapsed time active"""
        start = time.perf_counter()
        while True: 
            self._elapsed_time_active = time.perf_counter() - start
            await asyncio.sleep(0.01)

    async def _elapsed_time_since_last_transition_worker(self):
        q = self._q
        _start = time.perf_counter()
        while True:
            if q != self._q:
                q = self._q
                _start = time.perf_counter() 
            
            self._elapsed_time_since_last_transition = time.perf_counter() - _start
            await asyncio.sleep(0.01)


    async def evluation_loop_worker(
        self,
        x_t0: Any,
        u_t0: Optional[Any] = None,
        ctx_t0: Optional[Any] = None,
        dt: float = 0.1
    ):
        """ 
        Async evaluation loop worker for hybrid automaton.

        Args: 
            x_t0: initial continuous state value
            u_t0: initial input
            ctx_t0: auxiliary context for hybrid automaton
        """
        
        print(f"starting {self.NAME}")

        if self._ON_ENTRY is not None:
            self._ON_ENTRY()

        self.active = True
        elapsed_time_background_task = asyncio.create_task(self._elapsed_time_active_worker())
        elapsed_time_since_last_transition = asyncio.create_task(self._elapsed_time_since_last_transition_worker())
        
        self._q = self._Q_T0
        self._x   = x_t0
        self._u   = u_t0
        self._ctx = ctx_t0
        self._dt  = dt

        while self.active:

            # -------------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # -------------------------------------------------------------
            
            if not self._real_time_mode: # simulated
                self._xdot = await self._q.continuous_dynamics(
                    self._x, self._u, self._ctx, self._dt
                )
                if self._xdot is not None: 
                    self._x = self._x + self._xdot * self._dt # TODO: need to update this to use injectable Integrator function

            else: # real time 
                self._xdot = await self._q.continuous_dynamics(
                    self._x, self._u, self._ctx, self._dt
                )

            # TODO: check here if there is integration/ real_time param is set to true or false
            # for now assuming closed loop control with simulation, If it's not real time
            # we need here to do an update on the continous state.

            # -------------------------------------------------------------
            # 2️⃣ Check transitions (guards)
            # -------------------------------------------------------------
            D_eval = await self._q.evaluate_transitions(
                self._x, self._u, self._ctx, self._dt
            )

            # Collect all transitions whose guard evaluates to True
            D_active = [t[0] for t in D_eval if t[1] == True]

            if D_active:
                # Guard transitions have priority over invariants
                if len(D_active) == 1:
                    d = D_active[0]
                else:
                    def resolve_transition_priority(D_active):
                        to = None
                        lowest_priority = None
                        for t in D_active:
                            if lowest_priority is None:
                                lowest_priority = t.priority
                                to = t
                                continue

                            if lowest_priority > t.priority: 
                                lowest_priority = t.priority
                                to = t

                        return to

                    # TODO: implement priority logic if multiple guards active
                    d = resolve_transition_priority(D_active)

                # ---------------------------------------------------------
                # Execute transition (apply reset, change state)
                # ---------------------------------------------------------
                new_q, new_x, new_ctx = d.execute(
                    self._x, self._u, self._ctx, self._dt
                )

                # Update automaton state
                self._q = new_q
                self._x = new_x
                self._ctx = new_ctx

                # Invoke state entry callback
                if new_q.on_enter is not None:
                    new_q.on_enter()

                # Continue to next iteration (skip invariant check)
                continue

            # -------------------------------------------------------------
            # 3️⃣ No transition fired → check invariant of current state
            # -------------------------------------------------------------
            invariants_ok = await self._q.check_invariants(
                self._x, self._u, self._ctx, self._dt
            )
            self.invariants = invariants_ok
            # if not invariants_ok and !(invariants_ok == []):
            #     # Invariant violated → forced exit or error
            #     if self._q._is_final:
            #         # Proper termination
            #         print(f"{self.NAME} reached final state {self._q.name}")
            #         self.active = False
            #         break
            #     else:
            #         raise RuntimeError(
            #             f"Invariant violated in mode '{self._q.name}' "
            #             "with no valid outgoing transition."
            #         )

            # -------------------------------------------------------------
            # 4️⃣ Real-time pacing / cooperative async yielding
            # -------------------------------------------------------------
            await asyncio.sleep(self.dt)

        # -------------------------------------------------------------
        # On exit
        # -------------------------------------------------------------
        if self._ON_EXIT is not None:
            self._ON_EXIT()


def main():
    def guard(*args, **kwargs):
        return True

    state_1 = HybridState(
        name="start",
        value=0,
        initial=True
    )


    state_2 = HybridState(
        name = "end",
        value=1,
        final=True
    )


    state_1.add_transition(
        HybridTransition(
            name="transition_1",
            value=1,
            to_state=state_2,
            guards=[guard],
        )
    )
    state_1.add_transition(
        HybridTransition(
                name="transition_1",
                value=2,
                to_state=state_2,
                guards=[guard],
                priority=2
            )
    )


    ha = HybridAutomaton(
        name="tb3 automaton",
        value=0,
        real_time_mode=True,
        states=[state_1, state_2],
    )
    import numpy as np
    # position [x, y, z] and quaternion [qx, qy, qz, qw]
    x_t0 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    x_u0 = None
    ctx_t0 = {
        'waypoint': np.array([0.0, 0.0]),
        'virtual_waypoint': np.array([0.0, 0.0])
    }
    dt = 0.1  # Adjusted to a small positive value for time step


    import threading

    thread_1 = threading.Thread(
        target=asyncio.run(
            ha.evluation_loop_worker(x_t0, x_u0, ctx_t0, dt)
        )
    ).start()

    thread_2 = threading.Thread(
        target=asyncio.run(
            ha.evluation_loop_worker(x_t0, x_u0, ctx_t0, dt)
        )
    ).start()

    import time
    time.sleep(10.0)

if __name__ == '__main__':
    main()
