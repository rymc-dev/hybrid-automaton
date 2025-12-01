from typing import Protocol, Dict
from typing import Tuple, Any
from .automaton import Automaton
import numpy as np



class GuardFunction(Protocol):
    def __call__(self, x: np.array, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], u: Dict[str, Automaton.Runtime.ControlInput], 
                 cfg: Dict, clk: Automaton.Runtime.Clock) -> bool: 
        """ 
        Args: 
            - x: np.array
                continous state represntation for the agent to be integrated against
            - aux_x: Dict[str, Automaton.Runtime.AuxiliaryState]
                auxiliarySatte which is continous states updated externally of the automaton
                or in resets
            u: Dict[str, Automaton.Runtime.ControlInput]
                control inputs
            cfg: Dict
                static configuration for the automaton
            clk: Dict[str, Automaton.Runtime.Clock]
                this is a reference to the automatons currently active clock
        
        Output: 
            bool: 
                represents if the guard holds or not
        """
        ...

class ResetFunction(Protocol): 
    def __call__(self, x: np.array, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], u: Dict[str, Automaton.Runtime.ControlInput], 
                 cfg: Dict, clk: Automaton.Runtime.Clock) -> Tuple[np.array, Dict[str, Automaton.Runtime.AuxiliaryState], Dict[str, Automaton.Runtime.ControlInput]]: 
        """ 
        Args: 
            - x: np.array
                continous state represntation for the agent to be integrated against
            - aux_x: Dict[str, Automaton.Runtime.AuxiliaryState]
                auxiliarySatte which is continous states updated externally of the automaton
                or in resets
            u: Dict[str, Automaton.Runtime.ControlInput]
                control inputs
            cfg: Dict
                static configuration for the automaton
            clk: Dict[str, Automaton.Runtime.Clock]
                this is a reference to the automatons currently active clock
        
        Output: 
            x: np.array
                reset can effect the agent state
            aux_x: Dict[str, Automaton.Runtime.AuxiliaryState]
                new auxilary state after reset has occured
            u: Dict[str, Automaton.Runtime.ControlInput]
                new control inputs after reset was completed.
        """
        ...

class InvariantFunction(Protocol): 
    def __call__(self, x: np.array, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], u: Dict[str, Automaton.Runtime.ControlInput], 
                 cfg: Dict, clk: Automaton.Runtime.Clock) ->  bool: 
        """ 
        Args: 
            - x: np.array
                continous state represntation for the agent to be integrated against
            - aux_x: Dict[str, Automaton.Runtime.AuxiliaryState]
                auxiliarySatte which is continous states updated externally of the automaton
                or in resets
            u: Dict[str, Automaton.Runtime.ControlInput]
                control inputs
            cfg: Dict
                static configuration for the automaton
            clk: Dict[str, Automaton.Runtime.Clock]
                this is a reference to the automatons currently active clock
        
        Output: 
            bool
                represents if the invariant holds or not
        """
        ...

class ContinousDynamicsFunction(Protocol): 
    def __call__(self, x: np.array, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], u: Dict[str, Automaton.Runtime.ControlInput], 
                 cfg: Dict, clk: Automaton.Runtime.Clock) ->  np.array: 
        """ 
        Args: 
            - x: np.array
                continous state represntation for the agent to be integrated against
            - aux_x: Dict[str, Automaton.Runtime.AuxiliaryState]
                auxiliarySatte which is continous states updated externally of the automaton
                or in resets
            u: Dict[str, Automaton.Runtime.ControlInput]
                control inputs
            cfg: Dict
                static configuration for the automaton
            clk: Dict[str, Automaton.Runtime.Clock]
                this is a reference to the automatons currently active clock
        
        Output: 
            bool
                the continous dynamics of the x continous agent state
        """
        ...

class IntegrationFunction(Protocol):
    def __call__(self, x: np.array, aux_x: Dict[str, Automaton.Runtime.AuxiliaryState], u: Dict[str, Automaton.Runtime.ControlInput], 
                 cfg: Dict, clk: Automaton.Runtime.Clock) -> np.array: 
        """ 
        Args: 
            - x: np.array
                continous state represntation for the agent to be integrated against
            - aux_x: Dict[str, Automaton.Runtime.AuxiliaryState]
                auxiliarySatte which is continous states updated externally of the automaton
                or in resets
            u: Dict[str, Automaton.Runtime.ControlInput]
                control inputs
            cfg: Dict
                static configuration for the automaton
            clk: Dict[str, Automaton.Runtime.Clock]
                this is a reference to the automatons currently active clock
        
        Output: 
            np.array
                represnets an update in state of the continous 
                state of the automaton after an integration is made.
        """
        ...