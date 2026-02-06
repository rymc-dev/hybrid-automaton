# hybrid-automaton

[![PyPI - Version](https://img.shields.io/pypi/v/hybrid-automaton.svg)](https://pypi.org/project/hybrid-automaton)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hybrid-automaton.svg)](https://pypi.org/project/hybrid-automaton)

-----

| Field         | Value        |
|---------------|--------------|
| Last Updated  | 2026-02-06   |
| Version       | 0.0.6        |

## Overview
Hybrid Automaton is a Python-based framework for simulating and running hybrid automata in both real-time and offline settings. It provides a lightweight, flexible foundation for defining & evaluating custom automata, while remaining easily integrable into real-world technology stacks such as ROS2 or other systems. The design emphasizes simplicity, extensibility, and practical applicability for a wide range of use cases.

This project was created out of necessity for a USV Hybrid Automaton project and is the first implementation of its kind. While still in active development, **it is production-capable for many real-world applications** including robotics, industrial control, building automation, and more. See [Practical Use Cases](#practical-use-cases) below for detailed information.

**Framework Status**: Beta (v0.0.6) - Ready for production use in non-safety-critical applications with proper testing.

If you have ideas for improvement or want to contribute, please reach out and become a collaborator!

## Table of Contents

- [hybrid-automaton](#hybrid-automaton)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Practical Use Cases](#practical-use-cases)
  - [Collaborators](#collaborators)
  - [License](#license)

## Installation

```console
pip install hybrid-automaton
```

## Usage

Below is a sample of how one of the demonstration hybrid automaton (`bouncing ball`) definitions are ran in simulation mode. The definition of the Automaton
using the framework can be found here: [bouncing ball automaton definition](./src/hybrid_automatons/bouncing_ball.py)

```python
from hybrid_automatons import bouncing_ball
from hybrid_automaton import Automaton
from hybrid_automaton import AutomatonResult

ha: Automaton = bouncing_ball(gravity=-9.81, restitution=0.8)
results: AutomatonResult = await ha.activate(
    initial_continuous_state=np.array([5.0, 0.0]), 
    enable_real_time_mode=False,
    continuous_state_sampler_enabled=True,
    continuous_state_sampler_rate=100,
    enable_self_integration=True,
    delta_time=0.001,
    timeout_sec=30.0,
    output_dir = os.path.join(os.getcwd(), 'logs', 'bouncing_ball_run') 
)
print (results)
```

## Practical Use Cases

**Is this framework ready for real-world use?** Yes! While still in active development (v0.0.6), hybrid-automaton is production-capable for many applications.

### Key Applications

This framework excels in domains requiring both continuous dynamics and discrete state management:

- **🚗 Autonomous Vehicles & Robotics**: Cruise control, USV navigation, drone flight controllers
- **🏭 Industrial Control**: HVAC systems, batch processing, conveyor control
- **🏢 Building Automation**: Smart thermostats, traffic lights, elevator systems  
- **⚡ Energy Management**: Battery management, microgrid control, EV charging
- **🎓 Education & Research**: Hybrid systems theory, control algorithm prototyping
- **🏥 Medical Devices**: Infusion pumps, ventilators (with proper validation)

### Framework Strengths

- ✅ **ROS2 Integration Ready** - Designed for robotics stacks
- ✅ **Real-Time & Simulation Modes** - Test offline, deploy online
- ✅ **Async-Native** - Built with Python asyncio for modern concurrent systems
- ✅ **Well-Tested** - Comprehensive test suite included
- ✅ **Rich Examples** - Bouncing ball, cruise control, thermostat, traffic lights

### Maturity Assessment

| Use Case | Status | Recommendation |
|----------|--------|----------------|
| Academic/Research | ✅ Ready | Excellent for prototyping and learning |
| Robotics Prototyping | ✅ Ready | Great for ROS2 projects, test thoroughly |
| Industrial Automation | ⚠️ Pilot Projects | Start with non-critical systems |
| Production Systems | ⚠️ With Caution | Pin versions, extensive validation |

**📚 For detailed use cases, integration patterns, and best practices, see [PRACTICAL_USES.md](./PRACTICAL_USES.md)**

## Collaborators

This project was created by:
- **[Ryan McKee](https://github.com/rymc-dev)**

### Contributing

We welcome contributions! This is an active project and the first open-source framework of its kind for hybrid automata in Python. Whether you're interested in:

- 🐛 Reporting bugs or suggesting features
- 📝 Improving documentation or examples  
- 🔧 Contributing code improvements
- 🧪 Adding test coverage
- 🎓 Using it in research or teaching

Please open an issue or pull request on [GitHub](https://github.com/rymc-dev/hybrid-automaton).

### Citation

Please cite this package as described below if used in research:

```bibtex
@misc{hybrid_automaton_2025,
  author       = {Ryan McKee},
  title        = {hybrid-automaton v0.0.6},
  howpublished = {GitHub repository},
  year         = {2026},
  note         = {Accessed: Feb. 04, 2026},
  url          = {https://github.com/rymc-dev/hybrid-automaton}
}
```

## License

`hybrid-automaton` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
