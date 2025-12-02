from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio
import time
import numpy as np

from .state import State


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

        def __init__(
            self, 
            name: str, 
            states: List[State], 
            configuration: Dict[str, Any] = {},
            on_entry: Optional[Callable] = None, 
            on_exit: Optional[Callable] = None
        ): 
            self.name = name
            self.id = Automaton.Definition._id_counter
            Automaton.Definition._id_counter += 1

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
            if self._on_entry is not None:
                return 
            
            self._on_entry()

        def on_exit(self):
            if self._on_exit is not None:
                return
            
            self._on_exit()

        def get_configuration(self) -> Dict:
            return self._configuration

        def to_mermaid(self):
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
                inv = ", ".join(g.__name__ for g in state.get_invariants()) if state.get_invariants() else ""
                if inv:
                    lines.append(f"    note right of {state.name}: invariant = {inv}")

            return "\n".join(lines)

        def __repr__(self):
            """string represnetaion for devs, this outputs the amdl format"""
            return self.to_mermaid()

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

                    guard_list = ", ".join(g.__name__ for g in t.guards)
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
                invariants_list = ", ".join(g.__name__ for g in t.guards)
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
            def __init__(self, name: str, state_t0: np.array, expected_dt: float = 0.1): 
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

            def __init__(self, name: str, state_t0: np.array, expected_dt: float = 0.1): 
                self.name = name
                self.state_t0: np.array = state_t0
                self.state: np.array = self.state_t0

                self.avg_dt: float = expected_dt
                self.timestep: int = 0

            def set_continous_state(self, x: np.array):
                self.state = x
                # TODO: Timestamp and calc avg dt
                self.timestep += 1

            def get_continous_state(self) -> np.array:
                return self.state

            def integrate(self, xdot: np.array, dt: float): 
                if self._integration_function is not None: 
                    self.set_continous_state(self._integration_function(self.state, xdot, dt))
                else: 
                    self.set_continous_state(self.state + xdot * dt)

        class ControlInput: 
            
            def __init__(self, name: str, state_t0: np.array): 
                self.name = name
                self.state_t0: np.array = state_t0
                self.state: np.array = self.state_t0

            def set_control_input(self, u: np.array): 
                self.state = u
            
            def get_control_input(self) -> np.array:
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

        class Clock:

            def __init__(self, dt: float, real_time_mode: bool):
                self._real_time_mode: bool = real_time_mode
                self._dt: float = dt

                self._global_time: float = 0.0
                self._global_time_start: float = 0.0
                self._time_elapsed_active: float = 0.0
                self._time_elapsed_since_last_transition: float = 0.0
                self._last_transition_time: float = 0.0

                self._running: bool = False  # Add running flag for start/stop

            def step_dt(self):
                if self._real_time_mode:
                    raise SystemError(
                    "trying to step `dt` when we are in real time mode."
                    )
                self._time_elapsed_active += self._dt
                self._time_elapsed_since_last_transition += self._dt

            async def sleep_for_dt(self):
                await asyncio.sleep(self._dt)

            def get_dt(self) -> float: 
                return self._dt
            
            def get_time_elapsed_active(self): 
                return self._time_elapsed_active
            
            def get_time_elapsed_since_last_transition(self):
                return self._time_elapsed_since_last_transition
            
            def is_real_time(self): 
                return self._real_time_mode

            def ping_transition(self):
                """
                Call this method whenever a transition occurs to reset the
                time elapsed since last transition.
                """
                if self._real_time_mode:
                    now = time.perf_counter()
                    self._last_transition_time = now
                    self._time_elapsed_since_last_transition = 0.0
                else:
                    self._time_elapsed_since_last_transition = 0.0

            async def start(self): 
                if not self._real_time_mode:
                    raise SystemError(
                    "Attempted to start clock in simulation mode, which is invalid."
                    )

                self._global_time_start = time.perf_counter()
                self._time_elapsed_active = 0.0
                self._time_elapsed_since_last_transition = 0.0
                self._last_transition_time = self._global_time_start

                self._running = True
                while self._running: 
                    await asyncio.sleep(0.001)
                    now = time.perf_counter()
                    self._global_time = now
                    self._time_elapsed_active = now - self._global_time_start
                    self._time_elapsed_since_last_transition = now - self._last_transition_time

            def stop(self):
                """Stops the clock timer loop."""
                self._running = False

        def __init__(
                self,
                automaton_definition: 'Automaton.Definition',
                x0: np.array,
                aux_x0: Dict[str, np.array] = {},
                u0: Dict[str, np.array] = {},
                real_time_mode: Optional[bool] = False,
                integrate: Optional[bool] = True,
                dt: Optional[float] = 0.1

        ): 
            self._active: bool = False
            self._is_completed: bool = False
            self._integrate: bool = integrate

            self._automaton_definition: Automaton.Definition = automaton_definition
            self._mode: State = automaton_definition.state_t0 

            self._continous_state: Automaton.Runtime.ContinousState = Automaton.Runtime.ContinousState(name='agent_state', state_t0=x0)
            self._auxilary_states: Dict[str, Automaton.Runtime.AuxiliaryState] = {k: Automaton.Runtime.AuxiliaryState(name=k, state_t0=v) for k, v in aux_x0.items()} if aux_x0 is not None else {}
            self._control_inputs: Dict[str, Automaton.Runtime.ControlInput] = {k: Automaton.Runtime.ControlInput(name=k, state_t0=v) for k, v in u0.items()} if u0 is not None else []

            self._runtime_clock: Automaton.Runtime.Clock = Automaton.Runtime.Clock(dt=dt, real_time_mode=real_time_mode)

            self._xdot: List = None


        def get_active_mode(self) -> Tuple[int, str]: 
            return (self._mode.get_state_id(), self._mode.name) 


        def get_continous_dynamics(self) -> List:
            # returns a vector representing the continous dynamics 
            return self._xdot

        def get_continous_state(self) -> 'Automaton.Runtime.ContinousState':
            return self._continous_state

        def get_auxilary_state(self) -> Dict[str, 'Automaton.Runtime.AuxiliaryState']: 
            return self._auxilary_states
        
        def get_control_input(self) -> Dict[str, 'Automaton.Runtime.ControlInput']:
            if self._runtime_clock is None: 
                raise SystemError(
                    "Attempted to get control input but automaton is not active. Call `activate() first."
                )

            return self._control_inputs

        def get_active_elapsed_time(self):
            if self._runtime_clock is None: 
                raise SystemError( 
                    "Attempted to get runtime clock is not there"
                )

            return self._runtime_clock.get_time_elapsed_active()
                
        def get_active_elapsed_time_since_last_transition(self) -> float:
            if self._runtime_clock is None: 
                raise SystemError()

            return self._runtime_clock.get_time_elapsed_since_last_transition()

        def set_continous_state(self, x: np.array): 
            """updates the current continous state"""
            self._continous_state.set_continous_state(x)

        def set_auxilary_state(self, aux_x: Dict[str, np.array]):
            """updates the current auxilary state"""
            for key, value in aux_x.items():
                self._auxilary_states[key].set_auxiliary_state(value)

        def set_control_input(self, u: Dict[str, np.array]):
            """updates the control input"""
            for key, value in u.items():
                self._control_inputs[key].set_control_input(value)

        def _evaluation_step(self) -> StepResult:
            """
            Perform one timestep evaluation of the hybrid automaton.
            this is a purely syncronis function.
            """
            if not self._active:
                print(f"can't step, automaton '{self._automaton_definition.name}' is not active.")
                return None
            
            if not self._is_completed: 
                # ---------------------------------------------------------
                # 1️⃣ Continuous dynamics
                # ---------------------------------------------------------
                self._xdot = self._mode.continuous_dynamics( # TODO: need to change this function to use new class attribute reprensetations instead of dicts
                    x = self._continous_state, 
                    aux_x = self._auxilary_states, 
                    u = self._control_inputs, 
                    cfg = self._automaton_definition.get_configuration(), 
                    clk = self._runtime_clock
                )

                # NOTE: Integrate `x` continous state if in simulation mode.
                # if not self._runtime_clock.is_real_time() and (self._xdot is not None):
                #     self._continous_state.integrate(self._xdot, self._runtime_clock.get_dt()) 

                if self._integrate and (self._xdot is not None) and (self._continous_state.state_t0 is not None):
                    self._continous_state.integrate(self._xdot, self._runtime_clock.get_dt()) 
                
                # ---------------------------------------------------------
                # 2️⃣ Guard transitions - (Evaluate and Execute discrete
                #  Transition if 1 guard or more are active)
                # ---------------------------------------------------------
                self._guard_evaluations = self._mode.evaluate_transitions(
                    x=self._continous_state, 
                    aux_x=self._auxilary_states, 
                    u=self._control_inputs, 
                    cfg=self._automaton_definition.get_configuration(), 
                    clk=self._runtime_clock
                )
                active_guards = [item[0] for item in self._guard_evaluations if item[1] is True]

                if active_guards:
                    if len(active_guards) == 1:
                        d = active_guards[0]
                    else:
                        d = min(active_guards, key=lambda t: t.priority)

                    # Execute transition
                    new_mode, new_states = d.execute(
                        x=self._continous_state, 
                        aux_x=self._auxilary_states, 
                        u=self._control_inputs, 
                        cfg=self._automaton_definition.get_configuration(), 
                        clk=self._runtime_clock
                    )
                    self._runtime_clock.ping_transition()

                    if self._mode.on_exit:
                        self._mode.on_exit()

                    # Update state
                    self._mode = new_mode
                    self._continous_state = new_states[0] 
                    self._auxilary_states = new_states[1]
                    self._control_inputs = new_states[2]

                    # State entry callback
                    if self._mode.on_enter:
                        self._mode.on_enter()

                    return None

                    # return Automaton.Runtime.StepResult(
                    #     q=new_mode, aux_x=self._auxilary_states, x=new_states[0], ctx={},
                    #     transition_taken=d,
                    #     invariants_ok=True
                    # )

                # ---------------------------------------------------------
                # 3️⃣ No transition → invariant check
                # ---------------------------------------------------------
                invariant_holds = self._mode.check_invariants(
                    x = self._continous_state, 
                    aux_x = self._auxilary_states, 
                    u = self._control_inputs, 
                    cfg = self._automaton_definition.get_configuration(),
                    clk = self._runtime_clock
                )

                if not invariant_holds and self._mode._is_final:
                    print('automaton completed')
                    self._is_completed = True
                    self._active = False
                elif not invariant_holds: 
                    raise SystemError('Invairants failed to hold and not in final mode')
                
                return None
                # return Automaton.Runtime.StepResult(
                #     q=self._mode, aux_x=self._auxilary_states, x=self._continous_state, ctx={}, 
                #     transition_taken=None,
                #     invariants_ok=invariant_holds
                # )
            else: 
                print(f"{self._automaton_definition.name} has completed attemped an evaluation step but can't as we "
                      "have discretely completed")
                return None

        async def _automaton_loop_worker(self):
            """ 
            async evaluation loop worker for running the automaton
            instance, either in real time mode or simulation mode.
            assumes that the automaton has already been activated
            and that there is no other current automaton loops running.
            """

            print (f"automaton '{self._automaton_definition.name}' evaluation loop worker starting.")
            is_real_time = self._runtime_clock.is_real_time()
            
            if is_real_time: 
                clock_task = asyncio.create_task(self._runtime_clock.start())

            while self._active and not self._is_completed:
                # step_result: Automaton.Runtime.StepResult = self._evaluation_step() # TODO: Need to determine if I need a return from this evaluation_step 
                _ = self._evaluation_step()

                if is_real_time: 
                    await self._runtime_clock.sleep_for_dt()
                else:
                    # NOTE: simulation mode
                    self._runtime_clock.step_dt()
                    await asyncio.sleep(0.001)
            
            if is_real_time: 
                clock_task.cancel()

            print (f"automaton '{self._automaton_definition.name}' evaluation loop worker exiting.")

        async def run(self): 
            #   start the tasks for updating elapsed time, time_since_last_transition and automaton_loop_worker
            main_runner_task = asyncio.create_task(self._automaton_loop_worker())
            # elapsed_time_active_task = asyncio.create_task(self._update_elapsed_time_worker())
            # elapsed_time_since_last_transition_task = asyncio.create_task(self._update_time_since_last_transition_worker()) 
            self._active = True
            await main_runner_task

        def deactivate(self): 
            self._active = False


    def __init__(
        self, 
        name: str,
        states: List[State],  # Fixed: was Transition, should be State
        configuration: Dict = {},
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        integration_function: Optional[Callable] = None
    ):
        """ 
        
        """
        self._definition: Automaton.Definition = Automaton.Definition(
            name=name,
            states=states,
            configuration=configuration,
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

    def get_active_mode(self) -> Tuple[int, str]: 
        if self._runtime is None: 
            raise SystemError(
                "Attempted to get current mode `q` but the automaton is not active. Call `activate()` first."
            )

        return self._runtime.get_active_mode()


    def get_continous_state(self) -> np.array:
        if self._runtime is None:
            raise SystemError(
                "Attempted to get continous state 'x' but the automaton is not active. Call `activate()` first."
            )

        return self._runtime.get_continous_state().get_continous_state()
    
    def get_continous_dynamics(self): 
        """ 
        utilized for retrieving the current continous dynamics if there are any continous dynamics to get
        """
        if not self._active: 
            raise SystemError(
                "Attempted to get continous dynamics `xdot` but the automaton is not active. Call `activate()` first."
            )
        
        return self._runtime.get_continous_dynamics()
    
    def get_active_elapsed_time(self):
        if self._runtime is None:
            raise SystemError(
                "Attempted to get active elapsed time but the automaton is active. is not None Call `activate()` first."
            )
   
        return self._runtime.get_active_elapsed_time()
    
    def get_activate_elapsed_time_since_last_transition(self):
        if self._runtime is None:
            raise SystemError(
                "Attempted to get active elapsed time since last transition but the automaton is not active. Call `activate` first."
            )

        return self._runtime.get_active_elapsed_time_since_last_transition()

    """ === setter function for when active === """

    def set_continous_state(self, x: np.array): # NOTE: This setter should only be avialable if real_time hybrid automaton.
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

    def set_auxilary_continous_states(self, aux_x: Dict[str, np.array]):
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

    def set_control_input(self, u: Dict[str, np.array]): 
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
        x0: np.array,
        aux_x0: Optional[Dict[str, np.array]] = {},
        u0: Optional[Dict[str, np.array]] = {},
        real_time_mode: Optional[bool] = False,
        integrate: Optional[bool] = True,
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

        self._runtime: Automaton.Runtime = Automaton.Runtime(
            automaton_definition=self._definition,
            x0=x0,
            aux_x0=aux_x0,
            u0=u0,
            real_time_mode=real_time_mode,
            integrate=integrate,
            dt=dt
        )
        self._active = True

        await self._runtime.run()

        print (f"automaton '{self._definition.name}' deactived.")

    def deactivate(self): 
        """deactives the automaton"""
        if self._runtime is None or not self._runtime._active:
            raise SystemError(f"can't deactivate automaton '{self._definition.name}', it's not active.")

        self._runtime.deactivate()
        print (f"automaton '{self._definition.name}' deactived.")

    """ === string representations of the class === """

    def __repr__(self):
        """ developer string representation of instance"""
        return repr(self._definition)

    def __str__(self): 
        """user friendly represnetaiton of instance"""
        return str(self._definition)
