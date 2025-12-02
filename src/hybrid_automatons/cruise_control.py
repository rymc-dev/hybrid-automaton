import numpy as np
from hybrid_automaton import State, Transition, Automaton

def cruise_control(target_speed: float = 30.0, safe_distance: float = 50.0,
                   danger_close: float = 20.0, car_ahead_speed: float = 20.0) -> Automaton:
    """ 
    Args: 
        target_speed: float
            m/s speed target
        safe distance: float
            meters safe distance
        car_ahead_speed: float
            m/s speed of car ahead
    """
    TARGET_SPEED = 30.0  # m/s (108 km/h)
    SAFE_DISTANCE = 50.0  # meters
    CAR_AHEAD_SPEED = 20.0  # m/s
    
    # =========================
    #   Continous Dynamics
    # =========================

    def accelerate_flow(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        """Accelerate at 2 m/s² - x = [v, dist]"""
        v_dot = 2.0 if x.get_continous_state()[0] < cfg['target_speed'] else 0.0
        dist_dot = -(x.get_continous_state()[0] - cfg['car_ahead_speed'])
        return np.array([v_dot, dist_dot])
    
    def cruise_flow(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        """Maintain constant speed"""
        return np.array([0.0, -(x.get_continous_state()[0] - cfg['car_ahead_speed'])])
    
    def brake_flow(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        """Gentle braking at -1.5 m/s²"""
        v_dot = -1.5 if x.get_continous_state()[0] > 0 else 0.0
        return np.array([v_dot, -(x[0] - cfg['car_ahead_speed'])])
    
    def emergency_brake_flow(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        """Hard braking at -5 m/s²"""
        v_dot = -5.0 if x.get_continous_state()[0] > 0 else 0.0
        return np.array([v_dot, -(x.get_continous_state()[0] - cfg['car_ahead_speed'])])
    
    # ==========================
    #   Guards
    # ==========================
    def reached_target_speed(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        return abs(x.get_continous_state()[0] - cfg['target_speed']) < 0.5
    
    def below_target_speed(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        return x.get_continous_state()[0] < cfg['target_speed'] - 1.0 and x.get_continous_state()[1] > cfg['safe_distance']
    
    def too_close(x: Automaton.Runtime.ContinousState, aux_x, u, cfg, clk):
        return x[1] < cfg['safe_distance']
    
    def dangerously_close(x, aux_x, u, cfg, clk):
        return x[1] < cfg['danger_close']
    
    def safe_distance_restored(x, aux_x, u, cfg, clk):
        return x[1] > cfg['safe_distance'] + 10.0
    
    # Callbacks
    def on_accelerate():
        print("🚗💨 ACCELERATE mode")
    
    def on_cruise():
        print("🚗➡️  CRUISE mode - Maintaining speed")
    
    def on_brake():
        print("🚗🟡 BRAKE mode - Slowing down")
    
    def on_emergency():
        print("🚗🔴 EMERGENCY BRAKE!")
    
    # States
    accelerate = State("ACCELERATE", initial=True, flow=accelerate_flow, on_enter=on_accelerate)
    cruise = State("CRUISE", flow=cruise_flow, on_enter=on_cruise)
    brake = State("BRAKE", flow=brake_flow, on_enter=on_brake)
    emergency = State("EMERGENCY_BRAKE", flow=emergency_brake_flow, on_enter=on_emergency)
    
    # Transitions
    accelerate.add_transition(Transition("reach_cruise", cruise, guards=[reached_target_speed], priority=1))
    accelerate.add_transition(Transition("acc_to_brake", brake, guards=[too_close], priority=2))
    accelerate.add_transition(Transition("acc_to_emergency", emergency, guards=[dangerously_close], priority=3))
    
    cruise.add_transition(Transition("cruise_to_brake", brake, guards=[too_close], priority=1))
    cruise.add_transition(Transition("cruise_to_emergency", emergency, guards=[dangerously_close], priority=2))
    cruise.add_transition(Transition("cruise_to_acc", accelerate, guards=[below_target_speed], priority=3))
    
    brake.add_transition(Transition("brake_to_emergency", emergency, guards=[dangerously_close], priority=1))
    brake.add_transition(Transition("brake_to_cruise", cruise, guards=[safe_distance_restored], priority=2))
    
    emergency.add_transition(Transition("emergency_to_brake", brake, guards=[safe_distance_restored], priority=1))
    
    # Create automaton
    car = Automaton(
        name="Cruise Control", 
        states=[accelerate, cruise, brake, emergency], 
        configuration={
            'target_speed': target_speed,
            'safe_distance': safe_distance,
            'car_ahead_speed': car_ahead_speed,
            'danger_close': danger_close
        },
        on_entry=lambda: print('>>> Starting Cruise Control'),
        on_exit=lambda:print(">>> Ending Cruise Control")
    )

    return car
    