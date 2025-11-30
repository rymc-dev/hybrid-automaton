from .transition import Transition
from .state import State
from typing import List, Optional, Callable, Any, Dict
import time
import asyncio



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

    class Definition: 
        """ 
        Definition class for the Automaton, 
        contains static information about the automaton.

        Class Attributes: 
            _id_counter: int
                class level id counter for assigning unique ids to automaton definitions

        Args: 
            name: str
            states: List[State]
                list of states for the automaton
            on_entry: Optional[Callable]
                on entry callback function for when automaton is activated
            on_exit: Optional[Callable] 
                on exit callback function for when automaton is deactivated
        """
        _id_counter: int = 0

        def __init__(self, name: str, states: List[State], 
                     on_entry: Optional[Callable] = None, on_exit: Optional[Callable] = None): 
            self.name = name
            self.id = Automaton.Definition._id_counter
            Automaton.Definition._id_counter += 1

            self.states = states
            init_idx = [i for i, s in enumerate(self.states) if getattr(s, "_is_init", False)]
            cnt_init = len(init_idx)
            if cnt_init > 1 or cnt_init == 0: 
                raise ValueError(f"invalid HybridAutomaton initialization, need 1 initial state, got {cnt_init}")
            
            self.state_t0 = self.states[init_idx[0]]

            self.on_entry = on_entry
            self.on_exit = on_exit

    class Runtime: 
        """ 
        Runtime class for the Automaton, contains dynamic information
        about the automaton during execution.
        """

        # NOTE: Both auxiliary state and continous state are 
        #       mathmatically continous, however in simulation/real_time
        #       implementation they are treated differently as, 
        #       continous represents the agent for the automaton hence
        #       it in simulation mode especially the continous dynamics 
        #       in each state/mode are utilized to integrate for next state

        class AuxiliaryState: 
            def __init__(self, name: str, state_t0: List, expected_dt: float = 0.1): 
                self.name = name
                self.state_t0 = state_t0
                self.state = self.state_t0

                self.avg_dt: float = expected_dt
                self.timestep: int = 0

            def set_auxiliary_state(self, aux_x: List): 
                self.state = aux_x
                # TODO: Timestamp and calc avg dt
                self.timestep += 1

        class ContinousState: 
            
            _integration_function: Optional[Callable] = None

            def __init__(self, name: str, state_t0: Any, expected_dt: float = 0.1): 
                self.name = name
                self.state_t0: Any = state_t0
                self.state: Any = self.state_t0

                self.avg_dt: float = expected_dt
                self.timestep: int = 0

            def set_continous_state(self, x: Any):
                self.state = x
                # TODO: Timestamp and calc avg dt
                self.timestep += 1

            def get_continous_state(self) -> List:
                return self.state

            def integrate(self, xdot: Any, dt: float) -> Any: 
                if self._integration_function is not None: 
                    self.state = self._integration_function(self.state, xdot, dt)
                else: 
                    self.state = self.state + xdot * dt
                
                self.set_continous_state(self.state)

        class ControlInput: 
            
            def __init__(self, name: str, state_t0: Any): 
                self.name = name
                self.state_t0: Any = state_t0
                self.state: Any = self.state_t0

            def set_control_input(self, u: Any): 
                self.state = u
            
            def get_control_input(self) -> Any:
                return self.state

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


        def __init__(
                self,
                automaton_definition: 'Automaton.Definition',
                x0: List,
                aux_x0: Dict = None,
                u0: Dict = None,
                real_time_mode: Optional[bool] = False,
                dt: Optional[float] = 0.1

        ): 

            self._automaton_definition: Automaton.Definition = automaton_definition
            self._mode: State = automaton_definition.state_t0 

            self._continous_state: Automaton.Runtime.ContinousState = Automaton.Runtime.ContinousState(name='agent_state', state_t0=x0)
            self._auxilary_states: List[Automaton.Runtime.AuxiliaryState] = [Automaton.Runtime.AuxiliaryState(name=k, state_t0=v) for k, v in aux_x0.items()] if aux_x0 is not None else []
            self._control_inputs: List[Automaton.Runtime.ControlInput] = [Automaton.Runtime.ControlInput(name=k, state_t0=v) for k, v in u0.items()] if u0 is not None else []

            self._time_elapsed_active: float = 0.0
            self._time_elapsed_since_last_transition: float = 0.0

            self._real_time_mode: bool = real_time_mode
            self._dt = dt
            self.is_completed: bool = False
            self._xdot: List = None
            self._active: bool = False
            self._is_completed: bool = False

        def get_continous_dynamics(self) -> List:
            # returns a vector representing the continous dynamics 
            return self._xdot

        def get_continous_state(self) -> 'Automaton.Runtime.ContinousState':
            return self._continous_state

        def get_auxilary_state(self) -> List['Automaton.Runtime.AuxiliaryState']: 
            return self._auxilary_states
        
        def get_control_input(self) -> List['Automaton.Runtime.ControlInput']:
            return self._control_inputs

        def set_continous_state(self, x: List): 
            # setting the continous state directly means we pass in the list of values 
            self._continous_state = x

        def set_auxilary_state(self, aux_x: Dict):
            # setting the auxilary state directly means we pass in the dict of values 
            self.set_auxilary_state = aux_x

        def set_control_input(self, u: Dict):
            # setting the control input directly means we pass in the dict of values
            # TODO: Need to do validation on input
            self.set_control_input = u

        def _evaluation_step(self) -> StepResult:
            """
            Perform one hybrid automaton evaluation step the current state 
            of the hybrid automaton.
            This is pure logic — no loops, no sleeping.
            """
            if not self._active:
                print(f"can't step, automaton '{self._automaton_definition.name}' is not active.")
                return None
            
            if not self._is_completed: 
                # ---------------------------------------------------------
                # 1️⃣ Continuous dynamics
                # ---------------------------------------------------------
                xdot = self._mode.continuous_dynamics( # TODO: need to change this function to use new class attribute reprensetations instead of dicts
                    self._continous_state.state, self._auxilary_states, self._control_inputs, {}# self._u, self._ctx
                )
                self._xdot = xdot

                # Integrate if in simulation mode
                if not self._real_time_mode and (xdot is not None):
                    self._continous_state.integrate(xdot, self._dt) 
                # ---------------------------------------------------------
                # 2️⃣ Guard transitions
                # ---------------------------------------------------------
                D_eval = self._mode.evaluate_transitions(
                    self._continous_state.state, self._auxilary_states, {}, {}# TODO: self._u, self._ctx
                )

                active_guards = [item[0] for item in D_eval if item[1] is True]

                if active_guards:
                    if len(active_guards) == 1:
                        d = active_guards[0]
                    else:
                        d = min(active_guards, key=lambda t: t.priority)

                    # Execute transition
                    new_q, new_x, new_aux_x = d.execute(
                        self._continous_state.state, self._auxilary_states, {}, {} #TODO:  self._u, self._ctx
                    )

                    # Update state
                    self._mode = new_q
                    self._continous_state.state = new_x
                    self._auxilary_states = new_aux_x

                    # State entry callback
                    if self._mode.on_enter:
                        self._mode.on_enter()

                    return Automaton.Runtime.StepResult(
                        q=new_q, aux_x=self._auxilary_states, x=new_x, ctx={},
                        transition_taken=d,
                        invariants_ok=True
                    )

                # ---------------------------------------------------------
                # 3️⃣ No transition → invariant check
                # ---------------------------------------------------------
                invariants_ok = self._mode.check_invariants(
                    self._continous_state.state, self._auxilary_states, {}, {} # TODO: self._u, self._ctx
                )

                if not invariants_ok and self._mode._is_final:
                    print('automaton completed')
                    self._is_completed = True
                    self._active = False

                return Automaton.Runtime.StepResult(
                    q=self._mode, aux_x=self._auxilary_states, x=self._continous_state, ctx={}, 
                    transition_taken=None,
                    invariants_ok=invariants_ok
                )
            else: 
                print("automaton completed, can't step")
                return None

        async def _automaton_loop_worker(self):
            """ 
            async evaluation loop worker for running the automaton
            instance, either in real time mode or simulation mode.
            assumes that the automaton has already been activated
            and that there is no other current automaton loops running.
            """

            print (f"automaton '{self._automaton_definition.name}' evaluation loop worker starting.")
            is_real_time = self._real_time_mode
            
            if is_real_time: 
                self.start_timestamp = time.perf_counter()
            else:
                self.start_timestamp = 0.0 # simulation time starts at 0.0

            while self._active and not self._is_completed:
                if is_real_time: 
                    step_start_time = time.perf_counter()

                step_result: Automaton.Runtime.StepResult = self._evaluation_step() # NOTE: not sure what to do with step result yet.

                if is_real_time: 
                    # real-time mode
                    step_end_time = time.perf_counter()
                    time_elapsed_in_step = step_end_time - step_start_time
                    time_to_wait = self._dt - time_elapsed_in_step
                    if time_to_wait > 0:
                        await asyncio.sleep(time_to_wait)
                else:
                    # simulation mode
                    # Need to update timestamp for this
                    # TOOD: Update time stamp here somehow
                    self._time_elapsed_active += self._dt
                    await asyncio.sleep(0.01) # yield control to event loop for short period to stop race conditions

            print (f"automaton '{self._name}' evaluation loop worker exiting.")

        async def run(self): 
            #   start the tasks for updating elapsed time, time_since_last_transition and automaton_loop_worker
            main_runner_task = asyncio.create_task(self._automaton_loop_worker())
            # elapsed_time_active_task = asyncio.create_task(self._update_elapsed_time_worker())
            # elapsed_time_since_last_transition_task = asyncio.create_task(self._update_time_since_last_transition_worker()) 
            self._active = True
            await main_runner_task

        def deactive(self): 
            self._active = False


    def __init__(
        self, 
        name: str,
        states: List[State],  # Fixed: was Transition, should be State
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        integration_function: Optional[Callable] = None
    ):
        """ 
        
        """
        self._definition: Automaton.Definition = Automaton.Definition(
            name=name,
            states=states,
            on_entry=on_entry,
            on_exit=on_exit
        )
        self._runtime: Automaton.Runtime = None # by default while not active therefore not initializaed
        # set the integration function for the continous state which is a class attribute
        Automaton.Runtime.ContinousState._integration_function = integration_function

    """ === property getters === """
    @property
    def name(self) -> str: 
        return self._definition.name

    @property
    def id(self) -> int:
        return self._definition.id

    """ === getter for when active === """
    def get_continous_dynamics(self): 
        """ 
        utilized for retrieving the current continous dynamics if there are any continous dynamics to get
        """
        if not self._active: 
            raise SystemError(
                "Attempted to get continous dynamics `xdot` but the automaton is not active. Call `activate()` first."
            )
        
        return self._runtime.get_continous_dynamics()
    
    """ === setter function for when active === """

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
        # 1. Must be in active and real-time mode
        # -------------------------------
        if self._runtime is None:
            raise SystemError(
                "Automaton runtime is not initialized. Ensure the automaton is activated."
            )
        else: 
            if not self._runtime._active: 
                raise SystemError(
                    "Attempted to update continuous state `x` but the automaton "
                    "is not active. Call `activate()` first."
                )
            if self._runtime._real_time_mode is False: 
                raise SystemError(
                    "Attempted to manually update continuous state while in simulation mode. "
                    "In simulation mode, `x` must be advanced only by the integration method."
                )

        try: 
            self._runtime.set_continous_state(x)
        except Exception as e:
            raise ValueError(
                f"Failed to set continuous state `x`: {str(e)}"
            ) from e

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

        """ 
            1. automaton must be active
        """
        if self._runtime is None:
            raise SystemError(
                "Automaton runtime is not initialized. Ensure the automaton is activated."
            )
        else: 
            if not self._runtime._active: 
                raise SystemError(
                    "Attempted to update auxielary state `x` but the automaton "
                    "is not active. Call `activate()` first."
                )
        
        try: 
            self._runtime.set_auxilary_state(aux_x)
        except Exception as e: 
            raise Exception(
                f"Failed to set auxiliary continuous state `aux_x`: {str(e)}"
            ) from e 

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

        if self._runtime is None:
            raise SystemError(
                "Automaton runtime is not initialized. Ensure the automaton is activated."
            )
        else: 
            if not self._runtime._active: 
                raise SystemError(
                    "Attempted to update control input `x` but the automaton "
                    "is not active. Call `activate()` first."
                )
        
        try: 
            self._runtime.set_control_input(u)
        except Exception as e: 
            raise ValueError(
                f"Failed to set control input `u`: {str(e)}"
            ) from e

    """ === toggle active / deactive functions === """

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

        if self._runtime is not None: 
            if self._runtime._active:
                raise SystemError(f"can't activate automaton '{self._definition.name}', it's already active.")

        # should probably validate x0, aux_x0, u0 here

        print (f"activating automaton '{self._definition.name}'...")

        runner = Automaton.Runtime(
            automaton_definition=self._definition,
            x0=x0,
            aux_x0=aux_x0,
            real_time_mode=real_time_mode,
            dt=dt
        )
        self._active = True

        await runner.run()

        print (f"automaton '{self._name}' deactived.")

    def deactivate(self): 
        """deactives the automaton"""
        if not self._active:
            raise SystemError(f"can't deactivate automaton '{self._name}', it's not active.")

        self._active = False    
        print (f"automaton '{self._definition.name}' deactived.")

    """ === string representations of the class === """

    def __repr__(self):
        """ developer string representation of instance"""
        ... 

    def __str__(self): 
        """user friendly represnetaiton of instance"""
        ...
