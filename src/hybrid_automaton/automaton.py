""" 
Automaton is a class for defining hybrid automaton, 
automaton contains both definition and runtime information,
in the runtime there are attributes which store information]
regarding the state space the automaton is operating during runtime
this includes continous states, auxiliary states, control inputs,
the definition contains the configuration of the automaton and te structure
the structure encompasses the formal definition transitions map, guards resets, 
invariants and so on.

...
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

from .automaton_definition import Definition
from .automaton_runtime import Runtime
from .automaton_state import State


class Automaton: 
    """ 
    Automaton is a class for modelling of a hybrid automaton,
    this class provides a framework for initialization of automaton
    utilizing a new DSL language for definition of mathmatical automaton
    programmatically I call AMDL (Automaton Model Definition Language)
    this is version 0.0.5 of this model

    args: 
        name: str
            human readable string representation of the of the automaton
        states: List[HybridState]
            states are a list of discrete states you have defined of type 
            Automaton.State, these discrete states contain the structure 
            of the automaton including the transition map with guards/resets
            and invariants per mode
        on_entry: Optional[Callable]
            on_entry hook callable which you can statically pass to the 
            instance of this class to have it run automatically 
            activation.
        on_exit: Optional[Callable]
            on_exit hook callable on automaton runtime
            completion
        integration_function: Optional[Callable]
            integration_function to be passed to the automaton definition
            for integrating continous state if you activate with integrate 
            == true. which signifies on each evaluation time step the 
            automaton should utilize the continous dynamics generated 
            by the current discrete state to integrate step the dynamics
            of the agent continous state by 1 

    functions:
        get_name 
        get_id
        get_continuous_state
        get_auxiliary_states
        get_continuous_dynamics
        get_runtime_time_elapsed
        get_runtime_last_transition_name
        get_runtime_time_elapsed_since_last_transition
        
    """


    def __init__(
        self, 
        name: str,
        states: List[State],
        configuration: Dict = {},
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        integration_function: Optional[Callable] = None
    ):
        """ 
        
        """
        self._definition: Definition = Definition(
            name=name,
            states=states,
            configuration=configuration,
            on_entry=on_entry,
            on_exit=on_exit
        )
        self._runtime: Runtime = None 
        # ContinuousState._integration_function = integration_function

    """ === property getters === """
    def get_automaton_name(self) -> str: 
        return self._definition.name

    def get_automaton_id(self) -> int:
        return self._definition.id

    """ === getter for when active === """

    def get_runtime_active_discrete_state(self) -> Tuple[int, str]: 
        if self._runtime is None: 
            raise SystemError(
                "Attempted to get current mode `q` but the automaton is not active. Call `activate()` first."
            )

        return self._runtime.get_active_discrete_state()

    def get_runtime_continous_state(self) -> np.array:
        """"""
        if self._runtime is None:
            raise SystemError(
                "Attempted to get continous state 'x' but the automaton is not active. Call `activate()` first."
            )

        return self._runtime.get_continuous_state()
    
    def get_runtime_auxiliary_state(self) -> Dict: 
        if self._runtime in None: 
            raise SystemError(
                "Attempted to get auxiliary state 'aux_x' but the automaton is not active. Call `activate()` first."
            )
        return self._runtime.get_auxiliary_states()
    
    def get_runtime_control_input(self) -> Dict: 
        if self._runtime is None: 
            raise SystemError(
                "Attempted to get control input `u` but the automaton is not active. Call `activate()` first"
            )
        return self._runtime.get_control_inputs()
    
    def get_runtime_continous_dynamics(self) -> Dict[str, 'Automaton.Runtime.ContinousDynamics']: 
        """ 
        utilized for retrieving the current continous dynamics if there are any continous dynamics to get
        """
        if not self._active: 
            raise SystemError(
                "Attempted to get continous dynamics `xdot` but the automaton is not active. Call `activate()` first."
            )
        
        return self._runtime.get_continuous_dynamics()
    
    def get_runtime_time_elapsed(self) -> float:
        if self._runtime is None:
            raise SystemError(
                "Attempted to get active elapsed time but the automaton is not active. Call `activate()` first."
            )
   
        return self._runtime.get_elapsed_time()
    
    def get_runtime_previous_transition_name(self) -> str: 
        if self._runtime is None: 
            raise SystemError("Attemped to get previous transition name but the automaton is not active, Call `activate()` first.")
        return self._runtime.get_previous_transition_name()
    
    def get_runtime_time_elapsed_since_transition(self) -> float:
        if self._runtime is None:
            raise SystemError(
                "Attempted to get active elapsed time since last transition but the automaton is not active. Call `activate` first."
            )

        return self._runtime.get_elapsed_time_since_transition()

    """ === setter function for when active === """

    def set_runtime_continuous_state(self, x: np.array):
        """
        Explicit setter for the continuous state `x` of the automaton.

        This updates the internal continuous state that is normally evolved by
        the active state's continuous dynamics (flow function) and integrated
        via the automaton's integration method. This setter is intended for
        real-time operation, where the continuous state comes from external
        sensors rather than simulation-based integration.

        This function may **only** be called while the automaton is active.

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
        """

        # -------------------------------
        # 1. Must be active
        # -------------------------------
        if self._runtime is None:
            raise SystemError(
                "Automaton runtime is not initialized. Ensure the automaton is activated."
            )
        
        if not self._runtime._active:
            raise SystemError(
                "Attempted to update continuous state `x` but the automaton "
                "is not active. Call `activate()` first."
            )
        
        # -------------------------------
        # 2. Check real-time mode (optional warning, but don't block)
        # -------------------------------
        # FIX: Access real_time_mode through the clock
        if not self._runtime._ctx.clk.is_real_time():
            # This is just a warning - we allow it for open-loop injection
            # in simulation mode (integrate=False)
            if self._runtime._integrate:
                print("Warning: Setting continuous state while integrate=True. "
                    "This may cause conflicts. Consider integrate=False for open-loop.")

        # -------------------------------
        # 3. Set the state
        # -------------------------------
        try:
            self._runtime.set_continuous_state(x)
        except Exception as e:
            raise ValueError(
                f"Failed to set continuous state `x`: {str(e)}"
            ) from e

    def set_runtime_auxiliary_continuous_states(self, aux_x: Dict[str, np.array]):
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
            self._runtime.set_auxiliary_states(aux_x)
        except Exception as e: 
            raise Exception(
                f"Failed to set auxiliary continuous state `aux_x`: {str(e)}"
            ) from e 

    def set_runtime_control_inputs(self, u: Dict[str, np.array]): 
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
            self._runtime.set_control_inputs(u)
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

        self._runtime: Runtime = Runtime(
            automaton_definition=self._definition,
            x0=x0,
            aux_x0=aux_x0,
            u0=u0,
            real_time_mode=real_time_mode,
            integrate=integrate,
            dt=dt
        )
        self._active = True
        await self._runtime.activate()
        
    def deactivate(self): 
        """deactives the automaton"""
        if self._runtime is None or not self._runtime._active:
            raise SystemError(f"can't deactivate automaton '{self._definition.name}', it's not active.")

        self._runtime.deactivate()

    """ === string representations of the class === """

    def __repr__(self):
        """ developer string representation of instance"""
        return repr(self._definition)

    def __str__(self): 
        """user friendly represnetaiton of instance"""
        return str(self._definition)
