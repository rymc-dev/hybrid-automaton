import sys

import numpy as np

from hybrid_automaton import Automaton
from hybrid_automaton.definition import State
from hybrid_automaton.definition import Transition
from hybrid_automaton.definition import guard
from hybrid_automaton.definition import continuous_dynamics
from hybrid_automaton import RuntimeContext

ContinuousState = RuntimeContext.ContinuousState


def thermostat(too_cold_threshold: float = 18.0, too_hot_threshold: float = 22.0, 
               ambient_temp: float = 20.0, drift_rate: float = 0.5) -> Automaton: 
    """ 
    Sample thermostat hybrid automaton
    Args: 
        too_cold_threshold: float - threshold value for being too cold
        too_hot_threshold: float - threshold value for being too hot
        ambient_temp: float - the ambient temperature
        drift_rate: float - drift rate toward ambient temp
    Output: 
        Automaton
    """
    
    # ================
    # Guards
    # ================
    @guard
    def too_cold(ctx: RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[0] < ctx.configuration['too_cold_threshold']

    @guard
    def too_hot(ctx: RuntimeContext) -> bool:
        return ctx.continuous_state.latest()[0] > ctx.configuration['too_hot_threshold']

    @guard
    def temp_comfortable(ctx: RuntimeContext) -> bool:
        temp = ctx.continuous_state.latest()[0]
        return ctx.configuration['too_cold_threshold'] <= temp <= ctx.configuration['too_hot_threshold']

    # ===============
    # Continuous Dynamics
    # ===============
    @continuous_dynamics
    def heating_dynamics(ctx: RuntimeContext) -> np.ndarray:
        return np.array([2.0])

    @continuous_dynamics
    def cooling_dynamics(ctx: RuntimeContext) -> np.ndarray:
        return np.array([-1.5])
    
    @continuous_dynamics
    def idle_dynamics(ctx: RuntimeContext) -> np.ndarray: 
        temp = ctx.continuous_state.latest()[0]  
        ambient = ctx.configuration['ambient_temp']  
        drift_rate = ctx.configuration['drift_rate']
        return np.array([drift_rate * (ambient - temp)]) 
    
    # ===============
    # On entry functions
    # ===============
    def on_enter_heating(): 
        print("🔥 HEATING - Turning heater ON")
    
    def on_enter_cooling():
        print("❄️  COOLING - Turning AC ON")
    
    def on_enter_idle():
        print("😌 IDLE - Systems off, maintaining temperature")
    
    # ===============
    # States
    # ===============
    heating = State(name="HEATING", flow=heating_dynamics, on_enter=on_enter_heating)
    cooling = State(name="COOLING", flow=cooling_dynamics, on_enter=on_enter_cooling)
    idle = State(name="IDLE", initial=True, flow=idle_dynamics, on_enter=on_enter_idle)
    
    # ===============
    # Transitions
    # ===============
    idle.add_transition(Transition("idle_to_heating", heating, guards=[too_cold], priority=1))
    idle.add_transition(Transition("idle_to_cooling", cooling, guards=[too_hot], priority=1))
    
    heating.add_transition(Transition("heating_to_idle", idle, guards=[temp_comfortable], priority=1))
    cooling.add_transition(Transition("cooling_to_idle", idle, guards=[temp_comfortable], priority=1))
    
    return Automaton(
        name="Thermostat",
        version="v0.0.1",
        states=[heating, cooling, idle],
        configuration={
            'too_cold_threshold': too_cold_threshold,
            'too_hot_threshold': too_hot_threshold,
            'ambient_temp': ambient_temp, 
            'drift_rate': drift_rate
        }
    )
    
async def main(): 
    try:
        async def timeout():
            await asyncio.sleep(5.0)
            ha.deactivate()
            
        results = await asyncio.gather(
            timeout(),
            ha.activate(
                initial_continuous_state=ContinuousState(name="temperature_state", x0 = np.array([25.0]), x_labels=["temperature"]),
                enable_real_time_mode=False,
                enable_self_integration=True,
                timeout_sec=30.0,
                delta_time=0.01,
                continuous_state_sampler_enabled=True,
                continuous_state_sampler_rate=100,
                output_dir='./log_hybrid_automaton/thermostat'
        ))
    except Exception as e:
        print (f"Caught a critical Exception in automaton run: {str(e)}")
        sys.exit(1)
        
    from matplotlib import pyplot as plt
    from hybrid_automaton_evaluation.visualization import continuous_states_over_time_fig

    print ("Complete!")
    print (results[1])
    continuous_states_over_time_fig(results[1])
    plt.show()
    
if __name__ == '__main__': 

    ha = thermostat(
        too_cold_threshold=18.0,
        too_hot_threshold=22.0,
        ambient_temp=20.0,
        drift_rate=0.5
    )
    print (ha)
    print (repr(ha))
    
    import asyncio
    asyncio.run(main())