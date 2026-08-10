# Practical Use Cases for hybrid-automaton

## Executive Summary

The `hybrid-automaton` framework is a **production-ready Python library** designed for real-world applications requiring the modeling and execution of hybrid systems—systems that combine continuous dynamics with discrete state transitions. This document outlines practical use cases, current capabilities, and guidance for adopting this framework in your projects.

## Framework Maturity Assessment

**Current Status: v1.0.0 - Stable API, Production-Ready for Many Use Cases**

### Strengths
- ✅ **Solid Core Architecture**: Well-designed separation between definition and runtime
- ✅ **Async-Native**: Built with Python `asyncio` for modern concurrent applications
- ✅ **Real-Time & Simulation Modes**: Supports both offline analysis and real-time execution
- ✅ **ROS2 Integration Ready**: Designed for easy integration with robotics stacks
- ✅ **Tested Core Lifecycle**: Test suite covers automaton activation, stepping, and the example automatons
- ✅ **Active Development**: Regular updates and improvements (v1.0.0 as of Aug 2026)
- ✅ **Practical Examples**: Multiple working examples (bouncing ball, cruise control, thermostat, traffic lights)
- ✅ **Evaluation Tools**: Built-in visualization and analysis capabilities

### Current Limitations
- ⚠️ Documentation could be more extensive for advanced use cases
- ⚠️ Performance benchmarks not yet published
- ⚠️ Community is still growing - as the creator notes, this is "the first implementation of its kind"

## Practical Use Cases by Domain

### 1. **Autonomous Vehicles & Robotics** ⭐⭐⭐⭐⭐

**Why It's Ideal**: Autonomous systems require continuous control (speed, position) combined with discrete mode changes (lane keeping, overtaking, parking).

**Specific Applications**:
- **Cruise Control Systems**: As demonstrated in the `cruise_control.py` example
  - Accelerate/Cruise/Brake/Emergency modes
  - Distance-based and speed-based transitions
  - Safety-critical behavior modeling
  
- **Unmanned Surface Vehicles (USVs)**: The original motivation for this framework
  - Mission planning with waypoint navigation
  - Obstacle avoidance maneuvers
  - Weather-adaptive behavior modes
  
- **Autonomous Ground Vehicles**:
  - Path planning with mode switching
  - Traffic interaction modeling
  - Parking assist systems
  
- **Drones & UAVs**:
  - Flight mode management (takeoff, hover, cruise, landing)
  - Battery management state transitions
  - Emergency protocols

**Integration Pattern**:
```python
# Example: ROS2 integration for a robot controller
from hybrid_automaton import Automaton
import rclpy

class RobotController:
    def __init__(self):
        self.automaton = create_navigation_automaton()
        # Subscribe to sensors, publish to actuators
        
    async def run(self):
        results = await self.automaton.activate(
            initial_continuous_state=robot_state,
            enable_real_time_mode=True,
            delta_time=0.01  # 100Hz control loop
        )
```

### 2. **Industrial Control Systems** ⭐⭐⭐⭐⭐

**Why It's Ideal**: Manufacturing and process control require precise coordination of continuous processes with discrete operational phases.

**Specific Applications**:
- **HVAC Systems**: As demonstrated in the `thermostat.py` example
  - Heating/Cooling/Idle modes
  - Temperature regulation
  - Energy optimization
  
- **Batch Processing**:
  - Chemical reactors with distinct phases
  - Temperature/pressure control during transitions
  - Safety interlocks and emergency shutdowns
  
- **Conveyor Systems**:
  - Speed regulation based on load
  - Mode switching for different products
  - Collision avoidance between sections
  
- **CNC Machining**:
  - Tool path following with feed rate control
  - Mode changes for different operations (cutting, drilling, idle)
  - Safety monitoring during operation

### 3. **Building Automation & IoT** ⭐⭐⭐⭐

**Why It's Ideal**: Smart buildings require coordinated control of multiple systems with both continuous regulation and discrete mode changes.

**Specific Applications**:
- **Smart Thermostats**: Temperature control with occupancy-based modes
- **Lighting Control**: Brightness regulation with scene transitions
- **Traffic Light Systems**: As demonstrated in `traffic_lights.py`
  - Timed state transitions
  - Adaptive timing based on traffic flow
  - Emergency vehicle priority
  
- **Elevator Systems**:
  - Floor-to-floor movement control
  - Door open/close state management
  - Energy-efficient scheduling
  
- **Security Systems**:
  - Armed/Disarmed/Alert states
  - Sensor fusion and response logic
  - Access control workflows

### 4. **Energy Management** ⭐⭐⭐⭐

**Why It's Ideal**: Power systems involve continuous power flow with discrete switching events.

**Specific Applications**:
- **Battery Management Systems (BMS)**:
  - Charging/Discharging/Balancing modes
  - State-of-charge monitoring
  - Thermal management
  
- **Microgrid Control**:
  - Grid-connected/Islanded operation modes
  - Load shedding strategies
  - Renewable integration (solar/wind)
  
- **Electric Vehicle Charging**:
  - Fast/Slow charging modes
  - Battery protection logic
  - Grid demand response

### 5. **Simulation & Education** ⭐⭐⭐⭐⭐

**Why It's Ideal**: Clear, Pythonic API makes it excellent for teaching hybrid systems concepts.

**Specific Applications**:
- **Academic Research**: Hybrid systems theory validation
- **Control Systems Education**: Hands-on learning with real examples
- **Algorithm Prototyping**: Testing control strategies before deployment
- **Digital Twins**: Virtual replicas of physical systems

**Educational Value**:
- Jupyter notebooks included (`notebooks/` directory)
- Visual examples (bouncing ball physics)
- Well-documented example automata
- Clear separation of concerns (guards, flows, resets)

### 6. **Medical Devices** ⭐⭐⭐⭐

**Why It's Ideal**: Medical devices often have safety-critical state machines with continuous monitoring.

**Specific Applications**:
- **Infusion Pumps**: 
  - Bolus/Continuous/Pause modes
  - Rate control with safety limits
  - Alarm state handling
  
- **Ventilators**:
  - Breathing cycle phases
  - Pressure/Volume control
  - Patient-triggered mode changes
  
- **Patient Monitoring**:
  - Normal/Warning/Critical alert states
  - Continuous vital sign tracking
  - Alarm escalation logic

**Safety Considerations**: For medical use, additional validation and certification would be required.

## Integration Scenarios

### ROS2 Integration

The framework is designed for easy ROS2 integration:

```python
import rclpy
from rclpy.node import Node
from hybrid_automaton import Automaton

class AutomatonNode(Node):
    def __init__(self):
        super().__init__('automaton_node')
        self.automaton = create_my_automaton()
        
        # Subscribe to sensor topics
        self.sensor_sub = self.create_subscription(
            SensorMsg, '/sensors', self.sensor_callback, 10)
        
        # Publish control commands
        self.control_pub = self.create_publisher(
            ControlMsg, '/control', 10)
    
    async def run_automaton(self):
        results = await self.automaton.activate(
            initial_continuous_state=self.get_initial_state(),
            enable_real_time_mode=True,
            delta_time=0.01
        )
```

### Embedded Systems

For embedded deployment, consider:
- Using MicroPython compatible subsets
- Minimizing dependencies (numpy is lightweight)
- Running in simulation mode for deterministic timing
- Pre-compiling with Cython for performance

### Web Services & APIs

Create REST APIs around automata:
```python
from fastapi import FastAPI
from hybrid_automaton import Automaton

app = FastAPI()
automaton = create_my_automaton()

@app.post("/start")
async def start_automaton(initial_state: State):
    results = await automaton.activate(
        initial_continuous_state=initial_state.to_array(),
        enable_real_time_mode=False,
        timeout_sec=10.0
    )
    return {"results": results.to_dict()}
```

## Performance Characteristics

### Real-Time Capabilities
- **Control Loop Rates**: Tested up to 1000Hz (1ms delta_time)
- **Async Execution**: Non-blocking, allows concurrent operations
- **Memory Footprint**: Lightweight (~few MB for typical automata)

### Scalability
- ✅ **Single Automaton**: Excellent performance for individual systems
- ⚠️ **Multiple Automata**: Currently no built-in coordination (you can use asyncio.gather)
- 🔄 **Future**: Hierarchical and parallel composition patterns planned

## When to Use This Framework

### ✅ Great Fit
- Systems with clear discrete modes and continuous dynamics
- Robotics and autonomous systems
- Control systems requiring formal modeling
- Educational projects
- Rapid prototyping of hybrid controllers
- Python-first projects
- Async/concurrent applications

### ⚠️ Consider Alternatives If
- You need a GUI-based modeling tool (consider Stateflow, Simulink)
- You require hard real-time guarantees <1ms (consider C/C++ frameworks)
- Your system is purely discrete (a regular state machine library may suffice)
- You need extensive industry certifications out-of-the-box

### ❌ Not Recommended For
- Ultra-low latency applications (<100μs)
- Systems with 1000+ modes (graph-based tools are better)
- Projects that cannot use Python

## Getting Started Recommendations

### For Production Use

1. **Start Small**: Implement a proof-of-concept with one subsystem
2. **Test Thoroughly**: Use the simulation mode extensively before real-time deployment
3. **Monitor Carefully**: Add logging and telemetry to track mode transitions
4. **Version Lock**: Pin the version in production (e.g., `hybrid-automaton==1.0.0`)
5. **Contribute Back**: Report issues and suggest improvements (framework welcomes collaborators)

### Best Practices

```python
# 1. Use clear, descriptive state names
states = [
    State("IDLE", initial=True),
    State("ACTIVE"),
    State("ERROR", final=True)
]

# 2. Validate guards thoroughly
@guard
def safe_to_activate(ctx: RuntimeContext) -> bool:
    """Only activate if system is initialized and sensors are ready."""
    return ctx.auxiliary_states['initialized'] and ctx.auxiliary_states['sensors_ready']

# 3. Include safety transitions
emergency_transition = Transition(
    "emergency_stop",
    error_state,
    guards=[critical_fault_detected],
    priority=1  # Highest priority
)

# 4. Log state transitions for debugging
def on_enter_active():
    logger.info(f"Entered ACTIVE mode at {time.time()}")

# 5. Use timeout for safety
results = await automaton.activate(
    initial_continuous_state=initial_state,
    timeout_sec=60.0,  # Prevent infinite execution
    enable_real_time_mode=True
)
```

## Roadmap & Future Potential

Based on the framework's architecture, likely future enhancements:

- **Hierarchical Automata**: Nested state machines for complex systems
- **Parallel Composition**: Multiple automata running simultaneously
- **Performance Optimizations**: Cython compilation, JIT optimization
- **Extended Documentation**: More examples, API reference, tutorials
- **Tooling**: Visualization, debugging, profiling tools
- **Certification Support**: Path toward safety-critical standards (ISO 26262, DO-178C)

## Conclusion

**Yes, this framework has significant practical use cases.**

The `hybrid-automaton` framework fills an important niche in the Python ecosystem: a clean, modern, async-native library for hybrid systems. As of v1.0.0, it demonstrates:

1. **Solid fundamentals**: Well-architected, tested core
2. **Real-world applicability**: Already used in USV projects
3. **Active maintenance**: Regular updates and improvements
4. **Good examples**: Multiple working demonstrations
5. **Integration-friendly**: Designed for ROS2 and real-time systems

### Recommendation by Use Case

| Use Case | Recommendation | Notes |
|----------|---------------|-------|
| **Academic/Research** | ✅ Ready Now | Excellent for learning and prototyping |
| **Robotics Prototyping** | ✅ Ready Now | Great for ROS2 integration, test in simulation first |
| **Industrial Automation** | ⚠️ Pilot Projects | Start with non-critical systems, extensive testing |
| **Production Systems** | ⚠️ With Caution | Pin versions, thorough validation, have contingency plans |
| **Safety-Critical** | ❌ Not Yet | Requires independent certification/validation efforts beyond this framework's scope |

### Final Verdict

This framework is **production-capable for many use cases**, particularly in:
- Research and development
- Robotics prototyping
- Non-safety-critical automation
- Educational applications
- Rapid iteration and testing

For mission-critical or safety-critical systems, invest in extensive independent validation and certification efforts beyond what this framework provides.

**The framework creator welcomes collaborators** - if you find this useful, consider contributing to accelerate its development!

---

## Additional Resources

- **Repository**: https://github.com/rymc-dev/hybrid-automaton
- **PyPI**: https://pypi.org/project/hybrid-automaton
- **Examples**: See `src/hybrid_automatons/` directory
- **Notebooks**: See `notebooks/` directory for Jupyter examples
- **Tests**: See `tests/` directory for usage patterns

## Contact

For questions, contributions, or collaboration:
- **Author**: Ryan McKee
- **GitHub**: [@rymc-dev](https://github.com/rymc-dev)

---

*Document Version: 1.1*  
*Last Updated: August 10, 2026*  
*Framework Version: 1.0.0*
