import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from hybrid_automaton import Automaton, State, Transition
from hybrid_automaton.automaton_runtime_context import Context
from hybrid_automaton.automaton_annotations import guard, continuous_dynamics
import numpy as np

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
    def too_cold(ctx: Context) -> bool: 
        return ctx.x.latest()[0] < ctx.cfg['too_cold_threshold']  # ← FIX: Use [0] not [-1]
    
    @guard
    def too_hot(ctx: Context) -> bool: 
        return ctx.x.latest()[0] > ctx.cfg['too_hot_threshold']  # ← FIX: Use [0] not [-1]
    
    @guard
    def temp_comfortable(ctx: Context) -> bool: 
        temp = ctx.x.latest()[0]  # ← FIX: Get the actual temperature value
        return ctx.cfg['too_cold_threshold'] <= temp <= ctx.cfg['too_hot_threshold']
    
    # ===============
    # Continuous Dynamics
    # ===============
    @continuous_dynamics
    def heating_dynamics(ctx: Context) -> np.ndarray: 
        return np.array([2.0])  # ← FIX: Must be array with brackets
    
    @continuous_dynamics
    def cooling_dynamics(ctx: Context) -> np.ndarray: 
        return np.array([-1.5])  # ← FIX: Must be array with brackets
    
    @continuous_dynamics
    def idle_dynamics(ctx: Context) -> np.ndarray: 
        temp = ctx.x.latest()[0]  
        ambient = ctx.cfg['ambient_temp']  
        drift_rate = ctx.cfg['drift_rate']
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
        states=[heating, cooling, idle],
        configuration={
            'too_cold_threshold': too_cold_threshold,
            'too_hot_threshold': too_hot_threshold,
            'ambient_temp': ambient_temp, 
            'drift_rate': drift_rate
        }
    )
    
if __name__ == '__main__': 

    ha = thermostat(
        too_cold_threshold=18.0,
        too_hot_threshold=22.0,
        ambient_temp=20.0,
        drift_rate=0.5
    )
    print (ha)
    print (repr(ha))
    
    from hybrid_automaton_runner import AutomatonRunner
    import asyncio
    ha_runner: AutomatonRunner = AutomatonRunner(hybrid_automaton=ha, sampling_rate=0.001)
    async def main(): 
        await ha_runner.run(
            x0 = np.array([25.0]), 
            real_time_mode=False, 
            integrate=True, 
            duration=30.0, 
            dt=0.01, 
            collect_automaton=True,
            collect_continuous=True,
            collect_transitions=True,
            collect_control=False, 
            collect_auxiliary=False
        )
        
        ha_runner.print_summary()
        results = ha_runner.get_results()
        from matplotlib import pyplot as plt
        from hybrid_automaton_evaluation.visualization import  automaton_states_over_time, continuous_states_over_time_fig, transitions_times_over_time_fig
        fig1 = continuous_states_over_time_fig(results['continuous_states'], state_labels=['temperature (c)'])
        # fig2 = transitions_times_over_time_fig(results['transition_times']) # TODO: Need to fix this
        fig5 = automaton_states_over_time(results['automaton_states'])
        plt.show()

    asyncio.run(main())