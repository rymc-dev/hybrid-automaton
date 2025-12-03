from hybrid_automaton import Automaton, State, Transition
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
    def too_cold(x, aux_x, u, cfg, clk) -> bool: 
        return x.get_continous_state()[0] < cfg['too_cold_threshold']  # ← FIX: Use [0] not [-1]
    
    def too_hot(x, aux_x, u, cfg, clk) -> bool: 
        return x.get_continous_state()[0] > cfg['too_hot_threshold']  # ← FIX: Use [0] not [-1]
    
    def temp_comfortable(x, aux_x, u, cfg, clk) -> bool: 
        temp = x.get_continous_state()[0]  # ← FIX: Get the actual temperature value
        return cfg['too_cold_threshold'] <= temp <= cfg['too_hot_threshold']
    
    # ===============
    # Continuous Dynamics
    # ===============
    def heating_dynamics(x, aux_x, u, cfg, clk): 
        return np.array([2.0])  # ← FIX: Must be array with brackets
    
    def cooling_dynamics(x, aux_x, u, cfg, clk): 
        return np.array([-1.5])  # ← FIX: Must be array with brackets
    
    def idle_dynamics(x, aux_x, u, cfg, clk): 
        temp = x.get_continous_state()[0]  # ← FIX: Get current temperature
        ambient = cfg['ambient_temp']  # ← FIX: Was 'ambient', should be 'ambient_temp'
        drift_rate = cfg['drift_rate']
        return np.array([drift_rate * (ambient - temp)])  # ← FIX: Must be array
    
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
            'ambient_temp': ambient_temp,  # ← FIX: Consistent naming
            'drift_rate': drift_rate
        }
    )