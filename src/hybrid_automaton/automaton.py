from .transition import Transition
from .state import State
from typing import List, Optional, Callable, Any, Dict
import time
import asyncio

class StepResult:
    """Return container for one automaton step evaluation."""
    def __init__(
        self,
        q,
        x,
        aux_x,
        ctx,
        transition_taken=None,
        reset_applied=False,
        invariants_ok=True,
    ):
        self.q = q
        self.x = x
        self.aux_x = aux_x
        self.ctx = ctx

        self.transition_taken = transition_taken
        self.reset_applied = reset_applied
        self.invariants_ok = invariants_ok


class Automaton: 
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

    class Ctx: 
        active: bool = False 
        is_completed: bool = False
        elapsed_time_active: float = 0.0
        elapsed_time_since_last_transition: float = 0.0

    _name: str = ""
    _id: int = 0
    _id_counter: int = 0

    # 
    _Q: List[State] = []


    # Internal Context Values
    _active: bool = False
    _is_completed: bool = False

    _elapsed_time_active: float = None
    _elapsed_time_since_last_transition: float = None

    # Initial States inside automaton
    _q_t0: Any = None
    _x_t0: Any = None
    _aux_x_t0: Any = None
    _u_t0: Any = None
    _ctx_t0: Ctx = Ctx()

    # Current States inside automaton
    _q: Any = None
    _x: Any = None
    _aux_x: Any = None 
    _u: Any = None
    _ctx: Ctx = None

    _xdot: Any = None
    
    # on entry and on exit
    _on_entry: Callable = None
    _on_exit: Callable = None

    _real_time_mode = False
    _dt: float = 0.1
   

    
    def __init__(
        self, 
        name: str,
        states: List[Transition], 
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        real_time_mode: bool = False
    ):
        """ """
        
        self._name = name
        self._id = Automaton._id_counter
        Automaton._id_counter += 1

        # TODO: Validate states
        self._Q = states
        init_idx = [i for i, s in enumerate(self._Q) if getattr(s, "_is_init", False)]
        
        cnt_init = len(init_idx)
        if cnt_init == 0: 
            raise ValueError("invalid HybridAutomaton initialization, need 1 initial state, got 0.")
        if cnt_init > 1: 
            raise ValueError(f"invalid HybridAutomaton initialization, need 1 initial state, got {cnt_init}")
        
        self._q0 = self._Q[init_idx[0]]

        self._real_time_mode = real_time_mode
        
        self._on_entry = on_entry
        self._on_exit = on_exit

    """ === getters and setters === """

    @property
    def is_completed(self):
        return self._is_completed

    @property
    def id(self):
        return self._id

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

    def step(self) -> StepResult:
        """
        Perform one hybrid automaton evaluation step.
        This is pure logic — no loops, no sleeping.
        """
        if not self._is_completed: 
            # ---------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # ---------------------------------------------------------
            xdot = self._q.continuous_dynamics(
                self._x, self._aux_x, self._u, self._ctx, self._dt
            )
            self._xdot = xdot

            # Integrate if in simulation mode
            if not self._real_time_mode and (xdot is not None):
                self._x = self._x + xdot * self._dt

            # ---------------------------------------------------------
            # 2️⃣ Guard transitions
            # ---------------------------------------------------------
            D_eval = self._q.evaluate_transitions(
                self._x, self._aux_x, self._u, self._ctx, self._dt
            )

            active_guards = [item[0] for item in D_eval if item[1] is True]

            if active_guards:
                if len(active_guards) == 1:
                    d = active_guards[0]
                else:
                    d = min(active_guards, key=lambda t: t.priority)

                # Execute transition
                new_q, new_x, new_ctx = d.execute(
                    self._x, self._u, self._ctx, self._dt
                )

                # Update state
                self._q = new_q
                self._x = new_x
                self._ctx = new_ctx

                # State entry callback
                if new_q.on_enter:
                    new_q.on_enter()

                return StepResult(
                    q=new_q, aux_x=self.aux_x, x=new_x, ctx=new_ctx,
                    transition_taken=d,
                    invariants_ok=True
                )

            # ---------------------------------------------------------
            # 3️⃣ No transition → invariant check
            # ---------------------------------------------------------
            invariants_ok = self._q.check_invariants(
                self._x, self._aux_x, self._u, self._ctx, self._dt
            )

            return StepResult(
                q=self._q, aux_x=self._aux_x, x=self._x, ctx=self._ctx, 
                transition_taken=None,
                invariants_ok=invariants_ok
            )
        else: 
            print ("automaton completed, can't step")
            return None

    # async def evaluation_loop_worker(
    #     self,
    #     x_t0: Any,
    #     x_aux_t0: Any,
    #     u_t0: Optional[Any] = None,
    #     ctx_t0: Optional[Any] = None,
    #     dt: float = 0.1
    # ):
    #     print(f"starting {self.NAME}")

    #     if self._on_entry:
    #         self._on_entry()

    #     self._active = True
        
    #     self._dt = dt
    #     self._x = x_t0
    #     self._aux_x = aux
    #     self._u = u_t0
    #     self._ctx = ctx_t0
    #     self._q = self._q_t0

    #     # Background timers
    #     tasks = [
    #         asyncio.create_task(self._elapsed_time_active_worker()),
    #         asyncio.create_task(self._elapsed_time_since_last_transition_worker()),
    #     ]

    #     # Main eval loop
    #     while self._active:
    #         result = await self.step()

    #         # (Optional) handle invariant violation
    #         if not result.invariants_ok:
    #             if self._q._is_final:
    #                 print(f"{self.NAME} reached final state {self._q.name}")
    #                 self._active = False
    #                 break
    #             else:
    #                 raise RuntimeError(
    #                     f"Invariant violated in state {self._q.name} "
    #                     "with no available transition."
    #                 )

    #         # Cooperative yielding / real-time pacing
    #         await asyncio.sleep(self._dt)

    #     # Cleanup
    #     for task in tasks:
    #         task.cancel()

    #     if self._on_exit:
    #         self._on_exit()

