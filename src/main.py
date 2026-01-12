"""
Bouncing Ball Hybrid Automaton - Open-Loop Mode with Injectors

This demonstrates:
1. External physics simulation generates continuous dynamics
2. Continuous state injector feeds x into automaton
3. Auxiliary injector provides environmental data (wind, ground height)
4. Automaton uses aux_x in guards/resets but does NOT integrate
"""

import asyncio
import numpy as np
import matplotlib.pyplot as plt
from hybrid_automaton import Automaton
from hybrid_automaton_runner import AutomatonRunner
from hybrid_automaton_evaluation.visualization import (
    continuous_states_over_time_fig, 
    transitions_times_over_time_fig, 
    automaton_states_over_time
)


# ============================================================
# External Physics Simulator (replaces automaton's integration)
# ============================================================
class BouncingBallPhysics:
    """External physics simulator that generates continuous dynamics."""
    
    def __init__(self, gravity=-9.81, dt=0.001):
        self.gravity = gravity
        self.dt = dt
        self.x = np.array([5.0, 0.0])  # [height, velocity]
        self.time = 0.0
        
    def compute_dynamics(self, wind_force=0.0):
        """Compute xdot based on current state and external forces."""
        height, velocity = self.x
        
        # Continuous dynamics: xdot = [v, g + wind]
        xdot = np.array([
            velocity,
            self.gravity + wind_force
        ])
        
        return xdot
    
    def integrate_step(self, xdot):
        """Integrate one step (Euler integration)."""
        self.x = self.x + xdot * self.dt
        self.time += self.dt
    
    def get_state(self):
        """Get current state (for injection into automaton)."""
        return self.x.copy()
    
    def set_state(self, x):
        """Set state (for reset from automaton)."""
        self.x = x.copy()


# ============================================================
# Environmental Simulator (generates auxiliary data)
# ============================================================
class Environment:
    """Simulates environmental conditions."""
    
    def __init__(self):
        self.time = 0.0
        self.dt = 0.001
        
    def get_auxiliary_state(self):
        """Generate time-varying environmental data."""
        # Sinusoidal wind (for demonstration)
        wind = 2.0 * np.sin(2 * np.pi * 0.2 * self.time)
        
        # Variable ground height (oscillating platform)
        ground_height = 0.5 * np.sin(2 * np.pi * 0.1 * self.time)
        
        return {
            'wind': np.array([wind]),
            'ground_height': np.array([ground_height])
        }
    
    def step(self):
        self.time += self.dt


# ============================================================
# Build Hybrid Automaton (uses aux_x, does NOT integrate)
# ============================================================
def bouncing_ball_open_loop(restitution=0.8):
    """
    Bouncing ball automaton for open-loop operation.
    
    - Continuous state x: [height, velocity] (injected externally)
    - Auxiliary state aux_x: {'wind', 'ground_height'} (injected externally)
    - Guard uses aux_x['ground_height'] for collision detection
    - Reset uses aux_x for coefficient of restitution
    """
    from hybrid_automaton import State, Transition
    
    # --------------------------------------------------------
    # State: Falling (no continuous dynamics - external!)
    # --------------------------------------------------------
    def falling_dynamics(x, aux_x, u, cfg, clk):
        # Return None - we're in open-loop mode
        # External simulator handles dynamics
        return None
    
    # --------------------------------------------------------
    # Guard: Check if ball hits ground (uses aux_x!)
    # --------------------------------------------------------
    def hit_ground_guard(x, aux_x, u, cfg, clk):
        height = x.state[0]
        ground = aux_x['ground_height'].state[0]
        velocity = x.state[1]
        
        # Hit ground if height <= ground and moving downward
        return height <= ground and velocity < 0
    
    # --------------------------------------------------------
    # Reset: Bounce with restitution (uses aux_x!)
    # --------------------------------------------------------
    def bounce_reset(x, aux_x, u, cfg, clk):
        height = x.state[0]
        velocity = x.state[1]
        ground = aux_x['ground_height'].state[0]
        
        # Reset height to ground level
        new_height = ground
        
        # Reverse velocity with energy loss
        new_velocity = -cfg['restitution'] * velocity
        
        new_x = x
        new_x.set_continous_state(np.array([new_height, new_velocity]))
        
        return new_x, aux_x, u
    
    # --------------------------------------------------------
    # Build automaton
    # --------------------------------------------------------
    falling_state = State(
        name="Falling",
        initial=True,
        final=False,
        flow=falling_dynamics
    )
    
    bounce_transition = Transition(
        name="bounce",
        to_state=falling_state,  # Transition back to self
        guards=[hit_ground_guard],
        reset=bounce_reset,
        priority=1
    )
    
    falling_state.add_transition(bounce_transition)
    
    return Automaton(
        name="BouncingBallOpenLoop",
        states=[falling_state],
        configuration={'restitution': restitution}
    )


# ============================================================
# Main Simulation with Injectors
# ============================================================
async def main():
    # Create external simulators
    physics = BouncingBallPhysics(gravity=-9.81, dt=0.001)
    environment = Environment()
    
    # Create hybrid automaton (open-loop mode)
    ha = bouncing_ball_open_loop(restitution=0.8)
    print(ha)
    
    # Create runner
    ha_runner = AutomatonRunner(hybrid_automaton=ha, sampling_rate=0.001)
    
    # --------------------------------------------------------
    # Define injector callbacks
    # --------------------------------------------------------
    def continuous_state_callback():
        """External physics generates continuous state."""
        # Compute dynamics
        wind = environment.get_auxiliary_state()['wind'][0]
        xdot = physics.compute_dynamics(wind_force=wind)
        
        # Integrate externally
        physics.integrate_step(xdot)
        
        # Return state for injection
        return physics.get_state()
    
    def auxiliary_callback():
        """Environment provides auxiliary data."""
        environment.step()
        return environment.get_auxiliary_state()
    
    # --------------------------------------------------------
    # Run with injection
    # --------------------------------------------------------
    await ha_runner.run(
        x0=np.array([5.0, 0.0]),
        aux_x0={'wind': np.array([0.0]), 'ground_height': np.array([0.0])},
        duration=10.0,
        real_time_mode=False,
        integrate=False,  # DON'T integrate - external simulator does it!
        dt=0.001,
        
        # Enable injectors
        inject_continuous=True,
        inject_auxiliary=True,
        continuous_state_fn=continuous_state_callback,
        auxiliary_fn=auxiliary_callback,
        injector_update_rate=0.001,
        
        # Collect data
        collect_continuous=True,
        collect_auxiliary=True,
        collect_automaton=True,
        collect_transitions=True
    )
    
    # --------------------------------------------------------
    # Visualize results
    # --------------------------------------------------------
    ha_runner.print_summary()
    results = ha_runner.get_results()
    
    fig1 = continuous_states_over_time_fig(results['continuous_states'])
    fig2 = transitions_times_over_time_fig(results['transition_times'])
    fig3 = automaton_states_over_time(results['automaton_states'])
    
    # Plot auxiliary states
    aux_data = results['auxiliary_states']
    if aux_data['data']:
        fig4, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        times = aux_data['times']
        
        wind = [d['wind'][0] for d in aux_data['data']]
        ground = [d['ground_height'][0] for d in aux_data['data']]
        
        ax1.plot(times, wind, 'b-', label='Wind Force')
        ax1.set_ylabel('Wind (m/s²)')
        ax1.legend()
        ax1.grid(True)
        
        ax2.plot(times, ground, 'g-', label='Ground Height')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Ground Height (m)')
        ax2.legend()
        ax2.grid(True)
        
        fig4.suptitle('Auxiliary States (Injected)')
    
    plt.show()


# Run simulation
asyncio.run(main())