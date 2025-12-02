from hybrid_automaton import Automaton, State, Transition
import numpy as np

def thermostat(too_cold_threshold: float = 18.0, too_hot_threshold: float = 22.0, ambient_temp: float = 20.0, drift_rate: float = 0.5) -> Automaton: 
    """ 
    sample thermostate hybrid automaton
    
    Args: 
        too_cold_threshold: float
            the threshold value for being too cold
        too_hot_threshold: float 
            the threshold value for being too hot
        ambient_temp: float
            the ambeint temperture
        drift_rate: float
            this is the drift rate of ambient temp
    
    Output: 
        Automaton
    """
    
    # ================
    # Guards
    # ================
    def too_cold(x, aux_x, u, cfg, clk) -> bool: 
        return x.get_continous_state()[-1] < cfg['too_cold_threshold']
    
    def too_hot(x, aux_x, u, cfg, clk) -> bool: 
        return x.get_continous_state()[-1] > cfg['too_hot_threshold']
    
    def temp_comfortable(x, aux_x, u, cfg, clk) -> bool: 
        return cfg['too_cold_threshold'] <= x <= cfg['too_hot_threshold']
    
    # ===============
    # Continous Dynamics
    # ===============
    
    def heating_dynamics(x, aux_x, u, cfg, clk): 
        return np.array(2.0)
    
    def cooling_dynamics(x, aux_x, u, cfg, clk): 
        return np.array(-1.5)
    
    def idle_dynamics(x, aux_x, u, cfg, clk): 
        ambient = cfg['ambient']
        drift_rate = cfg['drift_rate']
        
        return drift_rate * (ambient - x)
    
    # ===============
    # on entry functions
    # ==============
    
    def on_enter_heating(): 
        print("🔥 HEATING - Turning heater ON")
        
    def on_enter_cooling():
        print("❄️  COOLING - Turning AC ON")

    def on_enter_idle():
        print("😌 IDLE - Systems off, maintaining temperature")
        
    heating = State(name="HEATING", flow=heating_dynamics, on_enter=on_enter_heating)
    cooling = State(name="COOLING", flow=cooling_dynamics, on_enter=on_enter_cooling)
    idle = State(name="IDLE", initial=True, flow=idle_dynamics, on_enter=on_enter_idle)
        
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