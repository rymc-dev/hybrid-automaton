#! /usr/bin/python3


from typing import Callable, Dict, List, Optional 

import numpy as np

from .definition import _Definition
from .definition import State
from ._runtime import _Runtime

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
        
    """

    def __init__(
        self,
        *, 
        name: str,
        version: str,
        states: List[State],
        configuration: Dict = {},
        on_entry: Optional[Callable] = None, 
        on_exit: Optional[Callable] = None,
        integration_function: Optional[Callable] = None
    ):
        """ 
        initialize the static details of the automaton
        """
        self._definition: _Definition = _Definition(
            name=name,
            version=version,
            states=states,
            configuration=configuration,
            on_entry=on_entry,
            on_exit=on_exit
        )
        self._runtime: _Runtime = _Runtime(
            definition=self._definition,
            integration_fnc=integration_function
        )
        # ContinuousState._integration_function = integration_function

    """ === property getters === """
    def get_automaton_name(self) -> str: 
        return self._definition.name
    
    def get_automaton_version(self) -> str:
        return self._definition.version

    def get_automaton_id(self) -> int:
        return self._definition.id

    """ === toggle active / deactive functions === """

    async def activate(
        self,
        *,
        initial_continuous_state: _Runtime.Context.ContinuousState = None,
        initial_auxiliary_states: Optional[Dict[str, np.ndarray]] = {},
        initial_control_input_states: Optional[Dict[str, np.ndarray]] = {},
        enable_real_time_mode: bool = False,
        enable_self_integration: bool = True,
        delta_time: float = 0.01,
        timeout_sec: float = np.inf,
        continuous_state_sampler_enabled: bool = False,
        continuous_state_sampler_rate: Optional[int] = 1,
        auxiliary_states_sampler_enabled: bool = False,
        auxiliary_states_sampler_rate: Optional[int] = 1,
        control_input_states_sampler_enabled: bool = False,
        control_input_states_sampler_rate: Optional[int] = 1,
        continuous_state_provider: Optional[Callable] = None,
        continuous_state_provision_rate: Optional[int] = None,
        auxiliary_states_provider: Optional[Callable] = None,
        auxiliary_states_provision_rate: Optional[int] = None,
        control_states_provider: Optional[Callable] = None,
        control_states_provision_rate: Optional[int] = None,
        should_write_logs: bool = True,
        output_dir: str = "./log_hybrid_automaton/"
    ):
        """
        # NOTE: THis has been updated to be a simple access point for the automaton runtime activate function
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
        results = await self._runtime.activate(
            # states at t0
            initial_continuous_state=initial_continuous_state,
            initial_auxiliary_states=initial_auxiliary_states,
            initial_control_input_states=initial_control_input_states,
            # run configuration
            enable_real_time_mode=enable_real_time_mode,
            enable_self_integration=enable_self_integration,
            delta_time=delta_time,
            timeout_sec=timeout_sec,
            # samplers
            continuous_state_sampler_enabled=continuous_state_sampler_enabled,
            continuous_state_sampler_rate=continuous_state_sampler_rate,
            auxiliary_states_sampler_enabled=auxiliary_states_sampler_enabled,
            auxiliary_states_sampler_rate=auxiliary_states_sampler_rate,
            control_input_states_sampler_enabled=control_input_states_sampler_enabled,
            control_input_states_sampler_rate=control_input_states_sampler_rate,
            # providers 
            continuous_state_provider=continuous_state_provider,
            continuous_state_provision_rate=continuous_state_provision_rate,
            auxiliary_states_provider=auxiliary_states_provider,
            auxiliary_states_provision_rate=auxiliary_states_provision_rate,
            control_input_states_provider=control_states_provider,
            control_input_states_provision_rate=control_states_provision_rate,
            # metadata and log outputs from run 
            should_write_logs=should_write_logs,
            output_dir=output_dir
        )
        return results
        
    def deactivate(self): 
        """deactives the automaton"""
        self._runtime.deactivate()

    """ === string representations of the class === """

    def __repr__(self):
        """ developer string representation of instance"""
        return repr(self._definition)

    def __str__(self): 
        """user friendly represnetaiton of instance"""
        return str(self._definition)
