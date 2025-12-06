import asyncio
import numpy as np
from typing import Optional, Dict, List, Tuple
from .automaton_clock import Clock
from .automaton_runtime_context import Context, AuxiliaryState, ContinousState, ControlInput
from .automaton_definition import Definition
from .automaton_state import State
from .automaton_transition import Transition

class Runtime: 
    """ 
    `Automaton.Runtime` is the class that takes
    and injection of a `Automaton.Definition` 
    it encapsulates this and utilizes the structure
    of the automaton to operate a runtime for the automaton
    this class handles the state space states of the automaton
    `continuous_state`, `auxiliary_states`, `control_inputs` and 
    utilizes these to evaluate transition guards, invariants and 
    execute transitions to different discrete modes if activated.
    It utilizies a coro async activation function to do this.
    
    Args: 
        automaton_definition: 'Automaton.Definition'
            the injected static representation of the automaton 
            structure for use by the runtime
        x0: Optional[np.array]
            A scalar/vector/matrix representation of the initial continous
            state of the agent the automaton is acting on optional as not 
            necessailty needed automaton can be created without the need
            for x values for example a traffic light system
        aux_x0: Optional[Dict[str, np.array]]
            A dicionary representation of key value: auxiliary state name 
            to scalar/vector/matrix represnetsation of the state of the 
            auxiliary state at time 0 when the runtime is started optional 
            as may not be needed
        u0: Optional[Dict[str, np.array]]
            A dictionary reprensetaion of the key value: control input name
            to scalra/vector/matrix representation of the state of the 
            control input at time 0 when the rutnime is started optional 
            as may not be needed
        real_time_mode: bool
            real time mode is a flag that tells the autoamton clock that 
            it should update time on each evaluation step at increments
            of dt, while true signifies that automaton should operate on real time
        integrate: bool
            a flag that tells the automaton runtime evaluation stepper that 
            the continous state of the automaton should have it's value integrated
            using the current discrete state generated continuous dynamics
        dt: float
            the delta time expected between evaluation time steps, in real time mode
            we use dt to control the rate at which the evaluation stepper executes
            while in integration mode we run evaluation steps continously each evaluation step
            incrementing time by dt

        
    functions: 
        get_active_discrete_state
        get_previous_transition_name
        get_continuous_state
        get_auxiliary_states
        get_control_inputs
        get_continuous_dynamics
        get_elapsed_time
        get_elapsed_time_since_transition
        set_continuous_state
        set_auxiliary_states
        set_control_inputs
        
        _evaluation_step
        _run_automaton_loop
        
        activate
        deactivate    
    """

    def __init__(
            self,
            automaton_definition: Definition,
            x0: Optional[np.array] = np.array(),
            aux0: Optional[Dict[str, np.array]] = {},
            u0: Optional[Dict[str, np.array]] = {},
            real_time_mode: bool = True,
            integrate: bool = True,
            dt: float = 0.1
    ): 
        self._active: bool = False
        self._is_completed: bool = False
        self._integrate: bool = integrate

        self._automaton_definition: Definition = automaton_definition
        self._discrete_state: State = automaton_definition.state_t0 

        self._ctx: Context = Context(
            clk=Clock(dt=dt, real_time_mode=real_time_mode),
            x0=x0,
            aux0=aux0,
            u0=u0,
            cfg=automaton_definition.get_configuration()
        )
        self._xdot: List = None

    def get_active_discrete_state(self) -> Tuple[int, str]: 
        return (self._discrete_state.get_state_id(), self._discrete_state.name) 
    
    def get_previous_transition_name(self) -> str: 
        ...
    
    def get_continuous_state(self) -> ContinousState:
        return self._ctx.x

    def get_auxiliary_states(self) -> Dict[str, AuxiliaryState]: 
        return self._ctx.aux
    
    def get_control_inputs(self) -> Dict[str, ControlInput]:
        return self._ctx.u

    def get_continuous_dynamics(self) -> List:
        # returns a vector representing the continous dynamics 
        return self._xdot

    def get_elapsed_time(self):
        return self._ctx.clk.get_time_elapsed_active()
            
    def get_elapsed_time_since_transition(self) -> float:
        return self._ctx.clk.get_time_elapsed_since_last_transition()

    def set_continuous_state(self, x: np.array): 
        """updates the current continous state"""
        self._ctx.x.set_continous_state(x)

    def set_auxiliary_states(self, aux_x: Dict[str, np.array]):
        """updates the current auxilary state"""
        for key, value in aux_x.items():
            self._ctx.aux[key].set_auxiliary_state(value)

    def set_control_inputs(self, u: Dict[str, np.array]):
        """updates the control input"""
        for key, value in u.items():
            self._ctx.u[key].set_control_input(value)

    def _evaluation_step(self):
        """
        Perform one timestep evaluation of the hybrid automaton.
        this is a purely syncronis function.
        """
        if not self._is_completed and self._active: 
            # ---------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # ---------------------------------------------------------
            self._xdot = self._discrete_state.continuous_dynamics( # TODO: need to change this function to use new class attribute reprensetations instead of dicts
                ctx=self._ctx
            )

            # NOTE: Integrate `x` continous state if in simulation mode.
            # if not self._runtime_clock.is_real_time() and (self._xdot is not None):
            #     self._continous_state.integrate(self._xdot, self._runtime_clock.get_dt()) 

            if self._integrate and (self._xdot is not None) and (self._ctx.x.state_t0 is not None):
                self._ctx.x.integrate(self._xdot, self._ctx.clk.get_dt()) 
            
            # ---------------------------------------------------------
            # 2️⃣ Guard transitions - (Evaluate and Execute discrete
            #  Transition if 1 guard or more are active)
            # ---------------------------------------------------------
            self._guard_evaluations = self._discrete_state.evaluate_transitions(
                ctx=self._ctx
            )
            active_guards = [item[0] for item in self._guard_evaluations if item[1] is True]

            if active_guards:
                if len(active_guards) == 1:
                    d = active_guards[0]
                else:
                    d: Transition = min(active_guards, key=lambda t: t.priority)

                # Execute transition
                new_mode, new_states = d.execute(
                    ctx = self._ctx
                )
                self._ctx.clk.ping_transition()

                if self._discrete_state.on_exit:
                    self._discrete_state.on_exit()

                # Update state
                self._mode = new_mode
                self._ctx.x = new_states[0] 
                self._ctx.aux = new_states[1]
                self._ctx.u = new_states[2]

                # State entry callback
                if self._discrete_state.on_enter:
                    self._discrete_state.on_enter()
                return

            # ---------------------------------------------------------
            # 3️⃣ No transition → invariant check
            # ---------------------------------------------------------
            invariant_holds = self._discrete_state.check_invariants(
                ctx=self._ctx
            )

            if not invariant_holds and self._discrete_state._is_final:
                self._is_completed = True
                self._active = False
            elif not invariant_holds: 
                raise SystemError('Invairants failed to hold and not in final mode')
        
    async def _run_automaton_loop(self):
        """ 
        async evaluation loop worker for running the automaton
        instance, either in real time mode or simulation mode.
        assumes that the automaton has already been activated
        and that there is no other current automaton loops running.
        """
        is_real_time = self._ctx.clk.is_real_time()
        
        if is_real_time: 
            clock_task = asyncio.create_task(self._ctx.clk.activate())

        while self._active and not self._is_completed:
            self._evaluation_step()

            if is_real_time: 
                await self._ctx.clk.sleep_for_dt()
            else:
                self._ctx.clk.step_dt()
                await asyncio.sleep(0.001)
        
        if is_real_time: 
            clock_task.cancel() # should maybe use deactivate here instead of cancel for the task? 

        print (f"automaton '{self._automaton_definition.name}' evaluation loop worker exiting.")

    async def activate(self): 
        """interface for activation of the automaton"""
        self._automaton_definition.on_entry()
        main_runner_task = asyncio.create_task(self._run_automaton_loop())
        self._active = True
        await main_runner_task
        self._automaton_definition.on_exit()

    def deactivate(self): 
        self._active = False
