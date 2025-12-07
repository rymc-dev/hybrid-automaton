# hybrid-automaton

[![PyPI - Version](https://img.shields.io/pypi/v/hybrid-automaton.svg)](https://pypi.org/project/hybrid-automaton)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hybrid-automaton.svg)](https://pypi.org/project/hybrid-automaton)

-----

| Field         | Value        |
|---------------|--------------|
| Last Updated  | 2025-12-07   |
| Version       | 0.0.5        |

## Overview
Hybrid Automaton is a Python-based framework for simulating and running hybrid automata in both real-time and offline settings. It provides a lightweight, flexible foundation for defining custom automata, while remaining easily integrable into real-world technology stacks such as ROS2 or other systems. The design emphasizes simplicity, extensibility, and practical applicability for a wide range of use cases.

This project was created out of necessaity for a USV Hybrid Automaton project and is the first implementation of its kind therefore there may be issues and shortcomings therefore if you have ideas for 
how to improve this pkg please reach out and become a collaborator.

## Table of Contents

- [hybrid-automaton](#hybrid-automaton)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Collaborators](#collaborators)
  - [License](#license)

## Installation

```console
pip install hybrid-automaton
```

## Usage

Below is a sample of one of the demonstration hybrid automaton implementations being ran in simulation mode,
for custom hybrid-automaton definition and running please checkout our further documentation and 
please read the source code. 

```python
from hybrid_automatons import bouncing_ball
from hybrid_automaton import Automaton
from hybrid_automaton_runner import AutomatonRunner

ha: Automaton = bouncing_ball(gravity=-9.81, restitution=0.8)
ha_runner: AutomatonRunner = AutomatonRunner(hybrid_automaton=ha, sampling_rate=0.001)
await ha_runner.run(
    x0=np.array([5.0, 0.0]), collect_auxiliary=False, collect_control=False, real_time_mode=False, integrate=True, duration=10.0, dt=0.001
)
ha_runner.print_summary()
```

## Collaborators
This project was created by:
- **[Ryan McKee](https://github.com/rymc-dev)**

Please cite this package as described below if used in research:

```bibtex
@misc{hybrid_automaton_2025,
  author       = {Ryan McKee},
  title        = {hybrid-automaton v0.0.4},
  howpublished = {GitHub repository},
  year         = {2025},
  note         = {Accessed: Dec. 2, 2025},
  url          = {https://github.com/rymc-dev/hybrid-automaton}
}
```

## License

`hybrid-automaton` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
