import os
import asyncio
import numpy as np
from typing import Optional, Dict, List, Tuple
from .automaton_clock import Clock
from .automaton_runtime_context import Context, AuxiliaryState, ContinuousState, ControlInput
from .automaton_definition import Definition
from .automaton_state import State
from .automaton_transition import Transition
from .exit_codes import ExitCode
from .automaton_exit import AutomatonExit
from dataclasses import dataclass
from enum import Enum, auto
from datetime import timezone, time, datetime
import uuid

class StepResultCode(Enum): 
    STEP_NORMAL = auto()
    """standard operation inside a discrete mode, continuous dynamics evolve,
    invariants hold, guards all evaluated as false"""
    STEP_TRANSITION = auto()
    """guard/(s) satisfied during evaluation, transition selected, reset(s) applied if there are any
    for the transition new discrete mode entered  
    """
    CONTINUOUS_FLOW_EXCEPTION = auto()
    """continuous flow exception evaluation raised during integration
    """
    
    STEP_SELF_INTEGRATION_EXCEPTION = auto()
    """exception occured integration continuous dynamics generated for step
    """
    
    STEP_TRANSITION_EXCEPTION = auto()
    """an exception occured while attempting a discrete state jump
    """
    # NOTE: ENABLED_TRANSITION_CONFLICT ignored, handled by automaton definition requirements of non conflicting 
    # discrete mode priorities when defining discrete state transiitons
    # TIME BLOCK should not occur either, we check transitions have destinations 
    # on definition initialization, but as for the automaton flow, lack of flow may be a design
    # choice so there s no way for me to validate this, it's up to designer to determine through the 
    # automaton results if time blocks occur.  JUNMPS ALWAYS possible, 
    # but no continuous flow of dynamic not a worry of framework as may be intentional  
    STEP_INVARIANT_VIOLATION = auto()
    """invariant(s) bitwise ~| evaluated as without valid transition from current 
    discrete mode being available therefore leaving automaton in a semantically invalid state
    in an invalid state so run should stop
    """
    
    STEP_TERMINAL_REACHED = auto()
    """Entered a designated terminal / accepting discrete mode
       no further evolution intended therefore automaton run complete
       auto deactivate. 
       in this automaton final mode is declared, when invariant violation occurs
       and we are in a designated definition final state this is returned
    """  

    STEP_AUTOMATON_CANCELLED = auto()
    """signifies that the automaton has been manually cancelled by the client 
    """

class StepSeverity(Enum): 
    STEP_OK = auto()
    """ step worked as expected, continue normal operation as expected
    """
    STEP_WARNING = auto()
    """ a non critical issue during step, just need to prompt the end user of this
    """
    STEP_ERROR = auto()
    """ error raised, these are typically critical related to the automaton definition being mishandled,
    when raised should close automaton handle and raise exception to stop the run
    """
    STEP_FATAL = auto()
    """ fatal raised, this is an unexpected exception most likely related to code implementations, 
        when this occurs something has went fatally wrong with the code, for evaluation_step 
        should contact the developer if this severity occurs
    """
    
@dataclass
class StepResult:
    """
    a struct for returning information regarding evaluation steps
    in the runtime.
    """
    
    severity: StepSeverity
    result: StepResultCode = None
    message: str = ""

class RunResultCode(Enum): 
    SUCCESS = auto()
    FAILURE = auto()

@dataclass
class RunResult:
    """   
    a return obj for showing results of the runtime
    """ 
    exit_result: RunResultCode = RunResultCode.SUCCESS
    reason: StepResult = None # if failure then returns previous step result which caused
    message: str = ""
    
class TemporalAutomatonLogger: 
    """logs temporal data regarding the automaton 
    """
    FILE_EXTENSION = "log"
    def __init__(
        self,
        automaton_name: str,
        automaton_version: str,
        automaton_runner_version: str,
        automaton_initial_mode_name: str,
        is_real_time: bool,
        run_id: str,
        clk: Clock, 
        should_write_logs_to_file: bool = True,
        log_dir: str = "./log_hybrid_automaton/", 
        file_name: str = "temporal_automaton.log", 
    ):
        self._automaton_name = automaton_name
        self._automaton_version = automaton_version
        self._automaton_runner_version = automaton_runner_version
        self._automaton_initial_mode = automaton_initial_mode_name
        self._is_real_time = is_real_time
        self._run_id = run_id
        self._clk = clk
        self._is_write = should_write_logs_to_file
        import os
        self._file_path = os.path.join(log_dir, f"{file_name}.{self.FILE_EXTENSION}")
        if self._is_write: 
            self._create_file(self._file_path)
    
    def _create_file(self, file_path): 
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(
f"""# ------------------------------------------------------------
# Temporal log for hybrid automaton: '{self._automaton_name}_v{self._automaton_version}'
#
# Time reference:
#   t = 0.0
#   Clock: monotonic {'real' if self._is_real_time else 'simulation'} time
#   Units: seconds
#
# Log contents:
#   Temporal automaton events as they occur
#   Includes transition events, invariant violations, etc.
#   Format: [LEVEL] [timestamp]: [Event Type] [Details]
#   Events: 
#       - Transition: [FROM Discrete State] - [Transition Name] --> [TO Discrete State]
#       - Activation: automaton activated
#       - Deactivation: [reason]
#       - ...
#
# Execution:
#   Initial mode: {self._automaton_initial_mode}
#   Runner: hybrid_automaton.Runtime v{self._automaton_runner_version}
#   Run ID: {self._run_id}
#
# ------------------------------------------------------------
                """)


    def _write_to_file(self, msg: str): 
        with open(self._file_path, "a") as f:
            f.write(f"\n{msg}")
            
    def _gen_log_msg(self, fixture: str, condition: str, consequence: str): 
        return f"[{fixture}] [{self._clk.get_elapsed_time_active():.3f}]: [{condition}] {consequence}"
            
    def INFO(self, condition:str, consequence: str): 
        fixture = "INFO"
        msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
        if self._is_write:
            self._write_to_file(msg)
        else:
            print (msg)
        
    def WARNING(self, condition: str, consequence: str): 
        fixture = "WARNING"
        msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
        if self._is_write:
            self._write_to_file(msg)
        else:
            print (msg)
        
    def ERROR(self, condition:str, consequence: str): 
        fixture = "ERROR"
        msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
        if self._is_write:
            self._write_to_file(msg)
        else:
            print (msg)

    def FATAL(self, condition:str, consequence: str): 
        fixture = "FATAL"
        msg = self._gen_log_msg(fixture=fixture, condition=condition, consequence=consequence )
        if self._is_write:
            self._write_to_file(msg)
        else:
            print (msg)



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
    _VERSION = "0.0.1"

    def __init__(
            self,
            automaton_definition: Definition,
            x0: Optional[np.array] = np.array([]),
            aux0: Optional[Dict[str, np.array]] = {},
            u0: Optional[Dict[str, np.array]] = {},
            real_time_mode: bool = True,
            integrate: bool = True,
            dt: float = 0.1
    ): 
        # TODO: Make 'self._active' this a async event instead of just being a boolean  
        self._active_event = asyncio.Event()
        self._integrate: bool = integrate

        self._automaton_definition: Definition = automaton_definition
        self._discrete_state: State = automaton_definition.state_t0 

        
        self._timeout_event = asyncio.Event()
        self._deactivate_event = asyncio.Event()
        self._run_completed_event = asyncio.Event()
        
        self._ctx: Context = Context(
            clk=Clock(dt=dt, real_time_mode=real_time_mode),
            x0=x0,
            aux0=aux0,
            u0=u0,
            cfg=automaton_definition.get_configuration()
        )
        self._xdot: List = None

    def is_active(self) -> bool: 
        return self._active_event.is_set()
    
    def get_active_discrete_state(self) -> Tuple[int, str]: 
        return (self._discrete_state.get_state_id(), self._discrete_state.name) 
    
    def get_previous_transition_name(self) -> str: 
        ...
    
    def get_continuous_state(self) -> ContinuousState:
        return self._ctx.x

    def get_auxiliary_states(self) -> Dict[str, AuxiliaryState]: 
        return self._ctx.aux
    
    def get_control_inputs(self) -> Dict[str, ControlInput]:
        return self._ctx.u

    def get_continuous_dynamics(self) -> List:
        # returns a vector representing the continous dynamics 
        return self._xdot

    def get_elapsed_time(self):
        return self._ctx.clk.get_elapsed_time_active()
            
    def get_elapsed_time_since_transition(self) -> float:
        return self._ctx.clk.get_time_elapsed_since_transition()

    def set_continuous_state(self, x: np.array): 
        """updates the current continous state"""
        self._ctx.x.set_continuous_state(x)

    def set_auxiliary_states(self, aux_x: Dict[str, np.array]):
        """updates the current auxilary state"""
        for key, value in aux_x.items():
            self._ctx.aux[key].set_auxiliary_state(value)

    def set_control_inputs(self, u: Dict[str, np.array]):
        """updates the control input"""
        for key, value in u.items():
            self._ctx.u[key].set_control_input(value)

    def _evaluation_step(self) -> StepResult:
        """
        Perform one timestep evaluation of the hybrid automaton.
        this is a purely syncronis function.
        
        return: 
            StepResult: A step code and msg
        """
        try: 
            # ---------------------------------------------------------
            # 1️⃣ Continuous dynamics
            # ---------------------------------------------------------
            try:
                self._xdot = self._discrete_state.continuous_dynamics( # TODO: need to change this function to use new class attribute reprensetations instead of dicts
                    ctx=self._ctx
                )
            except Exception as e:
                return StepResult( 
                    result=StepResultCode.CONTINUOUS_FLOW_EXCEPTION,
                    severity=StepSeverity.STEP_ERROR,
                    message=f"'{self._automaton_definition.name}' exception occured duration continuous flow caused by: '{str(e)}'"
                )

            # NOTE: Integrate `x` continous state if in simulation mode.
            # if not self._runtime_clock.is_real_time() and (self._xdot is not None):
            #     self._continous_state.integrate(self._xdot, self._runtime_clock.get_dt()) 

            if self._integrate and (self._xdot is not None) and (self._ctx.x.x0 is not None):
                try:
                    self._ctx.x.integrate(self._xdot, self._ctx.clk.get_dt())
                except Exception as e: 
                    return StepResult(
                        result=StepResultCode.STEP_SELF_INTEGRATION_EXCEPTION,
                        severity=StepSeverity.STEP_ERROR,
                        message=f"'{self._automaton_definition.name}' exception occured during continuous dynamics integration caused by: '{str(e)}'"
                    ) 
            
            # ---------------------------------------------------------
            # 2️⃣ Guard transitions - (Evaluate and Execute discrete
            #  Transition if 1 guard or more are active)
            # ---------------------------------------------------------
            try:
                self._guard_evaluations = self._discrete_state.evaluate_transitions(
                    ctx=self._ctx
                )
                active_guards = [item[0] for item in self._guard_evaluations if item[1] is True]
                error_guards = [[item[0], item[2]] for item in self._guard_evaluations if item[2] is not None]
                if error_guards and len(error_guards) >= len(active_guards):
                    raise Exception("No valid guard evaluations could be performed, automaton may be stuck, please check guard function implementation.")
                if error_guards:
                    for g in error_guards:
                        print (f"Warning, evaluating guard ended in exception could be critical: '{g[0].name}': {g[1]}")
            except Exception as e:
                return StepResult( 
                    result=StepResultCode.STEP_TRANSITION_EXCEPTION, 
                    severity=StepSeverity.STEP_ERROR,
                    message=f"'{self._automaton_definition.name}' Guard Evaluation error: {str(e)}"
                )
            

            if active_guards:
                try:
                    old_mode = self._discrete_state.name
                    if len(active_guards) == 1:
                        d = active_guards[0]
                    else:
                        d: Transition = min(active_guards, key=lambda t: t.priority)

                    # Execute transition
                    new_mode, new_ctx = d.execute(
                        ctx = self._ctx
                    )
                    self._ctx.clk.ping_transition()

                    if self._discrete_state.on_exit:
                        self._discrete_state.on_exit()

                    # Update state
                    self._discrete_state = new_mode
                    self._ctx = new_ctx

                    # State entry callback
                    if self._discrete_state.on_enter:
                        self._discrete_state.on_enter()
                    
                    return StepResult(
                        result=StepResultCode.STEP_TRANSITION,
                        severity=StepSeverity.STEP_OK,
                        message=f"'{old_mode}' - |{d.name}| -> '{self._discrete_state.name}'"
                    )
                except Exception as e: 
                    return StepResult( 
                        StepResultCode.STEP_TRANSITION_EXCEPTION, 
                        StepSeverity.STEP_ERROR,
                        message=f"'{self._automaton_definition.name}' discrete state jump (transition) exception occured: {str(e)}"
                    )

            # ---------------------------------------------------------
            # 3️⃣ No transition → invariant check
            # ---------------------------------------------------------
            try:
                invariant_holds = self._discrete_state.check_invariants(
                    ctx=self._ctx
                )
            except Exception as e: 
                return StepResult(
                    results=StepResultCode.STEP_INVARIANT_VIOLATION,
                    severity=StepSeverity.STEP_ERROR, 
                    message=f"'{self._automaton_definition.name}' has had an invariant violation caused by exception during evaluation check, this is a critical semantic error for the automaton which could lead to instability and false results therefore please fix: {str(e)}"
                )

            if invariant_holds:
                return StepResult(
                    result=StepResultCode.STEP_NORMAL,
                    severity=StepSeverity.STEP_OK
                )
            elif not invariant_holds and self._discrete_state._is_final:
                return StepResult(
                    result=StepResultCode.STEP_TERMINAL_REACHED, 
                    severity=StepSeverity.STEP_OK,
                    message=f"reached: '{self._discrete_state.name}'"
                )
            else: 
                return StepResult(
                    result=StepResultCode.STEP_INVARIANT_VIOLATION, 
                    severity=StepSeverity.STEP_ERROR,
                    message=f"'{self._automaton_definition.name}' invariant(s) bitwise 'or/~|' '{self._discrete_state._Inv}' \
                        has been violated, this is a critical semantic error for you automaton definition semantic."
                )
        except Exception as e: 
            return StepResult(
                severity=StepSeverity.STEP_FATAL,
                message=f"undefined fatal exception has occured during evaluation step, please raise issue in 'hybrid_automaton' github repo: {str(e)}"
            )
        
    async def _run(self, logger: TemporalAutomatonLogger, timeout_sec: float = 1.0) -> RunResult:
        """
        Main worker for running the automaton asynchronously.

        Handles evaluation steps, state transitions, timeouts, and real-time or simulation clocks.
        Ensures proper cleanup of all tasks and sets RunResult appropriately.
        """
        run_result = RunResult()
        is_real_time = self._ctx.clk.is_real_time()
        self._active_event.set()  # mark automaton as active

        clock_task = None
        if is_real_time:
            # Real-time mode: start the clock
            clock_task = asyncio.create_task(self._ctx.clk.activate())

        try:
            while self._active_event.is_set():
                # Handle timeout first
                if self._timeout_event.is_set():
                    logger.WARNING(condition="Timeout", consequence=f"Automaton run timed out after {timeout_sec:.3f}s")
                    run_result.exit_result = RunResultCode.FAILURE
                    run_result.reason = StepResult(
                        severity=StepSeverity.STEP_ERROR,
                        result=StepResultCode.STEP_INVARIANT_VIOLATION,
                        message=f"Timeout exceeded {timeout_sec:.3f} seconds"
                    )
                    run_result.message = "Automaton terminated due to timeout."
                    self._active_event.clear()
                    self._run_completed_event.set()
                    break
                elif self._deactivate_event.is_set(): 
                    logger.INFO(
                        condition="MANUAL_STOP", 
                        consequence="Automaton was manually stopped via external event."
                    )
                    run_result.exit_result = RunResultCode.SUCCESS
                    run_result.reason = StepResult(
                        severity=StepSeverity.STEP_OK,
                        result=StepResultCode.STEP_
                    )

                # Evaluate the next step
                step_result: StepResult = self._evaluation_step()

                # Handle step severities
                match step_result.severity:
                    case StepSeverity.STEP_OK:
                        match step_result.result:
                            case StepResultCode.STEP_NORMAL:
                                pass  # continue
                            case StepResultCode.STEP_TRANSITION:
                                logger.INFO(condition="Transition", consequence=f"{step_result.message}")
                            case StepResultCode.STEP_TERMINAL_REACHED:
                                logger.INFO(condition="Terminal Reached", consequence=f"{step_result.message}")
                                run_result.exit_result = RunResultCode.SUCCESS
                                run_result.reason = step_result.result
                                run_result.message = step_result.message
                                self._active_event.clear()
                                self._run_completed_event.set()
                                break
                            case StepResultCode.STEP_AUTOMATON_CANCELLED:
                                logger.INFO(condition="Automaton Cancelled", consequence=f"{step_result.message}")
                                run_result.exit_result = RunResultCode.SUCCESS
                                run_result.reason = step_result.result 
                                run_result.message = step_result.message
                                self._active_event.clear()
                                self._run_completed_event.set()
                                break
                    case StepSeverity.STEP_WARNING:
                        logger.WARNING(condition="Step Warning", consequence=f"{step_result.result}: {step_result.message}")
                    case StepSeverity.STEP_ERROR:
                        # Log error and terminate loop
                        logger.ERROR(condition="Step Error", consequence=f"{step_result.result}: {step_result.message}")
                        run_result.exit_result = RunResultCode.FAILURE
                        run_result.reason = step_result.result
                        run_result.message = step_result.message
                        self._active_event.clear()
                        self._run_completed_event.set()
                        break
                    case StepSeverity.STEP_FATAL:
                        logger.FATAL(condition="Fatal Step Error", consequence=f"{step_result.result}: {step_result.message}")
                        run_result.exit_result = RunResultCode.FAILURE
                        run_result.reason = step_result.result
                        run_result.message = step_result.message
                        self._active_event.clear()
                        self._run_completed_event.set()
                        break
                    case _:
                        logger.FATAL(condition="Unknown Step Severity", consequence=f"{step_result.result}: {step_result.message}")
                        run_result.exit_result = RunResultCode.FAILURE
                        run_result.reason = step_result.result
                        run_result.message = "Unknown step severity encountered"
                        self._active_event.clear()
                        self._run_completed_event.set()
                        break

                # Advance the clock
                if is_real_time:
                    await self._ctx.clk.sleep_for_dt()
                else:
                    self._ctx.clk.step_dt()
                    await asyncio.sleep(0.001)

        except asyncio.CancelledError:
            # Clear active state and propagate cancellation
            logger.WARNING(condition="Cancelled", consequence="Automaton run cancelled externally")
            self._active_event.clear()
            self._run_completed_event.set()
            raise
        except Exception as e:
            # Unexpected exception
            logger.FATAL(condition="Runtime Exception", consequence=str(e))
            run_result.exit_result = RunResultCode.FAILURE
            run_result.reason = -1
            run_result.message = f"Fatal exception during runtime: {str(e)}"
            self._active_event.clear()
            self._run_completed_event.set()
        finally:
            # Cleanup real-time clock if running
            if clock_task and not clock_task.cancelled():
                clock_task.cancel()
                try:
                    await clock_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

        return run_result

    def _on_entry_hook(self, logger: TemporalAutomatonLogger):
        logger.INFO(condition="Automaton Activation", consequence="automaton has been activated")
        self._automaton_definition.on_entry()
        
    def _on_exit_hook(self, logger: TemporalAutomatonLogger):
        logger.INFO(condition="Automaton Complete", consequence="automaton completed!")
        self._automaton_definition.on_exit()

    async def activate(
        self,
        write_logs: bool = True,
        temporal_log_dir: str = "./log_hybrid_automaton",
        should_timeout: bool = False,
        timeout_sec: float = 100.0
    ) -> RunResult:
        """Activate the automaton asynchronously with optional timeout."""
        run_id = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:6]}"
        run_result: Optional[RunResult] = None
        timeout_task: Optional[asyncio.Task] = None
        main_runner_task: Optional[asyncio.Task] = None
        entered = False

        logger: Optional[TemporalAutomatonLogger] = None

        try:
            self._run_completed_event.clear()
            self._timeout_event.clear()
            self._deactivate_event.clear()

            # Initialize logger
            logger = TemporalAutomatonLogger(
                automaton_name=self._automaton_definition.name,
                automaton_version=self._automaton_definition.version,
                automaton_runner_version=self._VERSION,
                automaton_initial_mode_name=self._automaton_definition.state_t0.name,
                run_id=run_id,
                is_real_time=self._ctx.clk.is_real_time(),
                clk=self._ctx.clk,
                should_write_logs_to_file=write_logs,
                log_dir=temporal_log_dir,
                file_name="temporal_automaton.log"
            )

            self._on_entry_hook(logger)
            entered = True

            # Start main runner
            main_runner_task = asyncio.create_task(
                self._run(logger=logger, timeout_sec=timeout_sec), name="main_runner"
            )

            # Start timeout watcher if requested
            if should_timeout:
                timeout_task = asyncio.create_task(self._timeout_watchdog(timeout_sec), name="timeout_watchdog")

            tasks = [main_runner_task]
            if timeout_task:
                tasks.append(timeout_task)

            # Wait for the first task to finish
            done, pending = await asyncio.wait(
                tasks
            )

            # Cancel any remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Determine the finished task result safely
            finished_task = next((t for t in done if not t.cancelled()), None)
            if finished_task is not None:
                run_result = finished_task.result()
            else:
                # All tasks were cancelled (e.g., due to timeout)
                run_result = RunResult(
                    exit_result=RunResultCode.FAILURE,
                    reason=StepResult(
                        severity=StepSeverity.STEP_ERROR,
                        result=StepResultCode.STEP_INVARIANT_VIOLATION,
                        message="Automaton run was cancelled"
                    ),
                    message="All tasks were cancelled during activation."
                )

            # Handle timeout
            if self._timeout_event.is_set() and run_result.exit_result != RunResultCode.SUCCESS:
                run_result = RunResult(
                    exit_result=RunResultCode.FAILURE,
                    reason=StepResult(
                        severity=StepSeverity.STEP_ERROR,
                        result=StepResultCode.STEP_INVARIANT_VIOLATION,
                        message=f"Automaton run exceeded timeout of {timeout_sec:.3f} seconds."
                    ),
                    message="Timeout occurred during automaton activation."
                )
                if logger:
                    logger.WARNING("TIMEOUT", f"Automaton exceeded timeout of {timeout_sec:.3f}s")

        except Exception as e:
            run_result = RunResult(
                exit_result=RunResultCode.FAILURE,
                reason=StepResult(severity=StepSeverity.STEP_FATAL, message=str(e)),
                message=f"Exception occurred during activation: {str(e)}"
            )

        finally:
            # Ensure exit hook always runs
            if entered and logger:
                try:
                    self._on_exit_hook(logger)
                except Exception as e:
                    if logger:
                        logger.ERROR("ExitHookError", f"Exception during on_exit_hook: {str(e)}")

        return run_result


    async def _timeout_watchdog(self, timeout_sec: float):
        """Monitor automaton and set timeout if elapsed."""
        try:
            while self._ctx.clk.get_elapsed_time_active() < timeout_sec:
                if self._run_completed_event.is_set() or self._deactivate_event.is_set():
                    return
                await asyncio.sleep(0.05)
            # Timeout triggered
            self._timeout_event.set()
        except asyncio.CancelledError:
            return
 
    def deactivate(self): 
        print ("Client deactivation request received!") 
        self._active_event.clear()
