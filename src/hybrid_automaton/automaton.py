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



class AutomatonContext: 
    active: bool = False 
    is_completed: bool = False
    start_timestamp: float = 0.0
    elapsed_time_active: float = 0.0
    elapsed_time_since_last_transition: float = 0.0
    dt: float = 0.1
    is_real_time: bool = False

    def update_elapsed_time_real_time(self, unix_timestamp: float):
        self.elapsed_time_active = time.perf_counter() - self.elapsed_time_active

    def dt_step(self):
        self.elapsed_time_active = self.elapsed_time_active + self.dt

    def update_dt(self, updated_dt: float):
        self.dt = updated_dt  

    def set_real_time(self, is_real_time: bool): 
        self.is_real_time = is_real_time

class Automaton: 
    """ 
    model of the hybrid automaton 

    args: 
        name: str
            human readable representaiton of the hybrid automaton model
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

        dt: Optional[float]
            mainly used for 'real_time_mode == False' for performing integration
            on continous x state based on this

    
    
    functions:
        evaluation_loop_worker(self): 
            async coro worker for running the automaton 
            using asyncio

        step(self): 
            synchronous function for performing one step in automaton 
            evalution (continous dynamics, integration if sim, check transitions
            , check if invariants hold for current state)

    
    """



    _name: str = ""
    _id: int = 0
    _id_counter: int = 0

    # set of potential states
    _Q: List[State] = []

    # Initial States inside automaton
    _q0: Any = None
    _x0: Any = None
    _aux_x0: Any = None
    _u0: Any = None

    # Current States inside automaton
    _q: Any = None
    _x: Any = None
    _aux_x: Any = None 
    _u: Any = None
    _ctx: AutomatonContext = AutomatonContext()

    _xdot: Any = None

    # integration method: this is used when automaton is in simulation 
    # mode for taking the derivative#s calculated by the flow function as input
    # then updated the x state accordingly based on that. 
    _integration_function: Optional[Callable] = None
    
    # on entry and on exit have allow the end user to add additional
    # on start functions on entry by default and on exit on default has a couple
    # functionalites associated with it by default, such as starting timers, ending them
    # updating the state of the automaton to deactived .....
    _on_entry: Optional[Callable] = None
    _on_exit: Optional[Callable] = None
   
    # Additional missing attributes
    _active: bool = False
    _is_completed: bool = False
    _real_time_mode: bool = False
    _x_t0: Any = None  # Store initial x for validation

    def __init__(
        self, 
        name: str,
        states: List[State],  # Fixed: was Transition, should be State
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        real_time_mode: bool = False,
        integration_function: Optional[Callable] = None
    ):
        """ """
        
        self._name = name
        self._id = Automaton._id_counter
        Automaton._id_counter += 1

        self._integration_function = integration_function
        self._real_time_mode = real_time_mode

        # TODO: Validate states
        self._Q = states
        init_idx = [i for i, s in enumerate(self._Q) if getattr(s, "_is_init", False)]
        
        cnt_init = len(init_idx)
        if cnt_init == 0: 
            raise ValueError("invalid HybridAutomaton initialization, need 1 initial state, got 0.")
        if cnt_init > 1: 
            raise ValueError(f"invalid HybridAutomaton initialization, need 1 initial state, got {cnt_init}")
        
        self._q0 = self._Q[init_idx[0]]

        self._ctx.is_real_time = real_time_mode
        
        self._on_entry = on_entry
        self._on_exit = on_exit

    """ === getters and setters === """
    @property
    def name(self):
        return self._name

    @property
    def is_completed(self):
        return self._is_completed

    @property
    def id(self):
        return self._id

    @property
    def q0(self):
        return self._q0

    @property
    def x0(self):
        return self._x0  # Fixed: was self.x0 (recursive)
    
    @property
    def aux_x0(self):
        return self._aux_x0  
    
    @property
    def u0(self):
        return self._u0 

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
    def xdot(self): # NOTE: continous dynamics has not setter, becuase this is internally generated
        return self._xdot

    @property
    def ctx(self):
        return self._ctx

    def set_continous_state(self, x: Any): # NOTE: This setter should only be avialable if real_time hybrid automaton.
        """
        Explicit setter for the continuous state `x` of the automaton.

        This updates the internal continuous state that is normally evolved by
        the active state's continuous dynamics (flow function) and integrated
        via the automaton's integration method. This setter is intended for
        real-time operation, where the continuous state comes from external
        sensors rather than simulation-based integration.

        This function may **only** be called while the automaton is active.

        Docs: 
            flowchart: 
                ...

        Args:
            x (Any):
                New continuous state value. The structure (e.g., dict keys,
                dimensionality) must match the structure provided during
                activation (`x0`).

        Raises:
            SystemError:
                If called when the automaton has not been activated or is not
                currently active.

            ValueError:
                If the provided value `x` does not match the format/structure of
                the initial continuous state defined at activation time.

        Examples:
            >>> ha = Automaton(name="vessel_controller", states=[q1, q2], dt=0.1)
            >>> ha.activate(x0={"heading": float(np.deg2rad(100))})
            >>> 
            >>> # Simulate sensor updates
            >>> ha.set_continous_state({"heading": float(np.deg2rad(101))})
            >>> time.sleep(0.1)
            >>> ha.set_continous_state({"heading": float(np.deg2rad(102))})
        """
        # -------------------------------
        # 1. Automaton must be active
        # -------------------------------
        if not getattr(self, "_active", False):
            raise SystemError(
                "Attempted to update continuous state `x` but the automaton "
                "is not active. Call `activate()` first."
            )

        # -------------------------------
        # 2. Must be in real-time mode
        # -------------------------------
        if not getattr(self._ctx, "is_real_time", False):
            raise SystemError(
                "Attempted to manually update continuous state while in simulation mode. "
                "In simulation mode, `x` must be advanced only by the integration method."
            )

        # -------------------------------
        # 3. Validate structure matches x0
        # -------------------------------
        x0 = self._x_t0

        if x0 is not None:
            if isinstance(x0, dict):
                if not isinstance(x, dict):
                    raise ValueError(
                        f"Invalid type for x. Expected dict with keys {list(x0.keys())}, "
                        f"got {type(x).__name__}."
                    )
                # Ensure keys match
                if set(x.keys()) != set(x0.keys()):
                    raise ValueError(
                        "Invalid structure for x. Keys do not match initial x0.\n"
                        f"Expected keys: {set(x0.keys())}\nGot keys: {set(x.keys())}"
                    )

            elif isinstance(x0, (list, tuple)):
                if not isinstance(x, type(x0)):
                    raise ValueError(
                        f"Invalid type for x. Expected {type(x0).__name__}, got {type(x).__name__}."
                    )
                if len(x) != len(x0):
                    raise ValueError(
                        f"Invalid structure for x. Expected length {len(x0)}, got {len(x)}."
                    )

            # Optional: numpy array shape check
            elif hasattr(x0, "shape"):
                if not hasattr(x, "shape") or x.shape != x0.shape:
                    raise ValueError(
                        f"Invalid array shape for x. Expected {x0.shape}, got {getattr(x, 'shape', None)}."
                    )

            # Otherwise assume opaque object → type must match
            else:
                if not isinstance(x, type(x0)):
                    raise ValueError(
                        f"Invalid type for x. Expected {type(x0).__name__}, got {type(x).__name__}."
                    )

        # -------------------------------
        # 4. Passed validation → assign
        # -------------------------------
        self._x = x

    def set_auxilary_continous_states(self, aux_x: Any):
        """
        explicity auxilary continous state setter

        Args: 
            aux_x: Any
                aux_x can be a list, dict or whatever else is required
                is's structure is defined by the aux_x0 representation 
                at time 0.

        Raises:
            SystemError: if you try set aux_x while the automaton is not active
            ValueError: if you try to set a aux_x which is invalid 

        """
        if not getattr(self, "_active", False):
            raise SystemError(
                "Attempted to update auxilary continuous state `aux_x` but the automaton "
                "is not active. Call `activate()` first."
            ) 
        
        # Validate structure matches aux_x0
        aux_x0 = self._aux_x0
        
        if aux_x0 is not None:
            if isinstance(aux_x0, dict):
                if not isinstance(aux_x, dict):
                    raise ValueError(
                        f"Invalid type for aux_x. Expected dict, got {type(aux_x).__name__}."
                    )
                if set(aux_x.keys()) != set(aux_x0.keys()):
                    raise ValueError(
                        f"Invalid structure for aux_x. Expected keys: {set(aux_x0.keys())}, "
                        f"got keys: {set(aux_x.keys())}"
                    )
            elif isinstance(aux_x0, (list, tuple)):
                if not isinstance(aux_x, type(aux_x0)):
                    raise ValueError(
                        f"Invalid type for aux_x. Expected {type(aux_x0).__name__}, "
                        f"got {type(aux_x).__name__}."
                    )
                if len(aux_x) != len(aux_x0):
                    raise ValueError(
                        f"Invalid structure for aux_x. Expected length {len(aux_x0)}, "
                        f"got {len(aux_x)}."
                    )

        self._aux_x = aux_x 

    def set_control_input(self, u: Any): 
        """
        explicity setter for the internal control input value
        this is a value that effects flow functions, can be heading
        offset or so on.

        Args:
            u: Any
                u can be a list, dict or whatever else is required 
                it's structure is defined by the u0 representation which
                is set on t0.

        Raises: 
            SystemError: if you try set control input state `u` but the automaton is not active
            ValueError: if you try to set `u` value but the structure is not the same as u0
        """
        if not getattr(self, "_active", False):
            raise SystemError(
                "Attempted to update control input `u` but the automaton "
                "is not active. Call `activate()` first."
            )
        
        # Validate structure matches u0
        u0 = self._u0
        
        if u0 is not None:
            if isinstance(u0, dict):
                if not isinstance(u, dict):
                    raise ValueError(
                        f"Invalid type for u. Expected dict, got {type(u).__name__}."
                    )
                if set(u.keys()) != set(u0.keys()):
                    raise ValueError(
                        f"Invalid structure for u. Expected keys: {set(u0.keys())}, "
                        f"got keys: {set(u.keys())}"
                    )
            elif isinstance(u0, (list, tuple)):
                if not isinstance(u, type(u0)):
                    raise ValueError(
                        f"Invalid type for u. Expected {type(u0).__name__}, "
                        f"got {type(u).__name__}."
                    )
                if len(u) != len(u0):
                    raise ValueError(
                        f"Invalid structure for u. Expected length {len(u0)}, "
                        f"got {len(u)}."
                    )
        
        self._u = u
    
    def set_dt(self, new_dt: float):
        """explicit setter for internal dt, used for timing of evalution loop and calculations"""
        if not isinstance(new_dt, (float, int)):
            raise ValueError(f"invalid type for dt, expected float got {type(new_dt)}")

        self._ctx.update_dt(float(new_dt))


    def step(self) -> StepResult:
        """
        Perform one hybrid automaton evaluation step.
        This is pure logic — no loops, no sleeping.
        """
        if not self._active:
            print(f"can't step, automaton '{self._name}' is not active.")
            return None
        
        if not self._is_completed: 
            # ---------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # ---------------------------------------------------------
            xdot = self._q.continuous_dynamics(
                self._x, self._aux_x, self._u, self._ctx
            )
            self._xdot = xdot

            # Integrate if in simulation mode
            if not self._real_time_mode and (xdot is not None):
                self._x = self._x + xdot * self._ctx.dt # TODO: Need to update this to use self._integration function instead

            # ---------------------------------------------------------
            # 2️⃣ Guard transitions
            # ---------------------------------------------------------
            D_eval = self._q.evaluate_transitions(
                self._x, self._aux_x, self._u, self._ctx
            )

            active_guards = [item[0] for item in D_eval if item[1] is True]

            if active_guards:
                if len(active_guards) == 1:
                    d = active_guards[0]
                else:
                    d = min(active_guards, key=lambda t: t.priority)

                # Execute transition
                new_q, new_x, new_aux_x = d.execute(
                    self._x, self._aux_x, self._u, self._ctx
                )

                # Update state
                self._q = new_q
                self._x = new_x
                self._aux_x = new_aux_x

                # State entry callback
                if new_q.on_enter:
                    new_q.on_enter()

                return StepResult(
                    q=new_q, aux_x=self._aux_x, x=new_x, ctx=self._ctx,
                    transition_taken=d,
                    invariants_ok=True
                )

            # ---------------------------------------------------------
            # 3️⃣ No transition → invariant check
            # ---------------------------------------------------------
            invariants_ok = self._q.check_invariants(
                self._x, self._aux_x, self._u, self._ctx
            )

            if not invariants_ok and self._q._is_final:
                print('automaton completed')
                self._is_completed = True
                self._active = False

            return StepResult(
                q=self._q, aux_x=self._aux_x, x=self._x, ctx=self._ctx, 
                transition_taken=None,
                invariants_ok=invariants_ok
            )
        else: 
            print("automaton completed, can't step")
            return None

    async def automaton_loop_worker(self):
        """ 
        async evaluation loop worker for running the automaton
        instance, either in real time mode or simulation mode.
        assumes that the automaton has already been activated
        and that there is no other current automaton loops running.
        """

        print (f"automaton '{self._name}' evaluation loop worker starting.")
        is_real_time = self._ctx.is_real_time
        
        if is_real_time: 
            self._ctx.start_timestamp = time.perf_counter()
        else:
            self._ctx.start_timestamp = 0.0 # simulation time starts at 0.0

        while self._active and not self._is_completed:
            if is_real_time: 
                step_start_time = time.perf_counter()

            step_result: StepResult = self.step() # NOTE: not sure what to do with step result yet.

            if is_real_time: 
                # real-time mode
                step_end_time = time.perf_counter()
                time_elapsed_in_step = step_end_time - step_start_time
                time_to_wait = self._ctx.dt - time_elapsed_in_step
                if time_to_wait > 0:
                    await asyncio.sleep(time_to_wait)
            else:
                # simulation mode
                self._ctx.dt_step()
                asyncio.sleep(0.01) # yield control to event loop for short period to stop race conditions

        print (f"automaton '{self._name}' evaluation loop worker exiting.")

        
    async def activate(
        self,
        x0: List,
        aux_x0: Optional[Dict] = {},
        u0: Optional[Dict] = {},
        real_time_mode: Optional[bool] = False,
        dt: Optional[float] = 0.1
    ):
        """
        Activate the hybrid automaton.

        This function initializes the automaton for execution. Activation defines the
        *runtime* initial conditions of the system, including the continuous state `x`,
        auxiliary continuous states `aux_x`, and the static control inputs `u`.

        It also sets the initial discrete state (the state marked `initial=True`)
        and prepares the internal context (ctx) for timing, real-time mode, and 
        other evaluation metadata.

        Notes:
            • The automaton must be activated before calling `step()` or 
            `evaluation_loop_worker()`.

            • `x0` represents the continuous state that will be updated over time
            through the state's flow() function and integrated using the provided 
            integration method (unless in real-time mode).

            • `aux_x0` represents auxiliary continuous variables that do not undergo
            automatic integration, but may be accessed by:
                – guard functions
                – invariant checks
                – reset maps
                – flow functions
            (Typical examples: temperature, waypoint position, agent metadata.)

            • `u0` contains static or piecewise-static control inputs that may be
            referenced by flow functions or guards. These are not integrated and
            are only updated externally via `set_control_input()`.

        Args:
            x0 (dict):
                Initial continuous state at activation time t₀. This is the state
                variable that will be advanced by the continuous dynamics of the
                active hybrid state.

            aux_x0 (Optional[dict]):
                Initial auxiliary continuous state at activation time t₀. These 
                values do *not* undergo automatic integration but participate as 
                additional inputs to transitions, invariants, and flow functions.

            u0 (Optional[dict]):
                Initial control inputs. These remain static unless updated by 
                `set_control_input()`.

            dt (Optional[float])
                Expected delta time between evaluation steps of automaton, defaults
                to `0.1`

        Example:
            >>> ha = Automaton(name="vessel_controller", states=[q1, q2], dt=0.1)
            >>> ha.activate(
            ...     x0={'heading': float(np.deg2rad(100)), 'speed': 5.0},
            ...     aux_x0={'waypoint': [100.0, 100.0]},
            ...     u0={'rudder_offset': -2.0},
            ...     dt=1.0
            ... )
        """
        
        print (f"activating automaton '{self._name}'")
        self._q = self._q0
        
        self._x0 = x0  # Store initial state
        self._x = self._x0

        self._aux_x0 = aux_x0
        self._aux_x = self._aux_x0
        
        self._u0 = u0
        self._u = u0
        
        self._ctx.update_dt(dt)
        self._ctx.set_real_time(real_time_mode)

        self._active = True
        self._is_completed = False

        automaton_runner = asyncio.create_task(self.automaton_loop_worker())
        await automaton_runner

        print (f"automaton '{self._name}' deactived.")

    def deactivate(self): 
        """deactives the automaton"""
        self._active = False    
        print (f"automaton '{self._name}' deactived.")


