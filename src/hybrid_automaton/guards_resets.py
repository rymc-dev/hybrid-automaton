from typing import Protocol
from typing import Tuple, Any

class GuardFunction(Protocol):
    def __call__(self, x, aux_x, u, ctx, dt) -> bool: 
        ...

class ResetFunction(Protocol): 
    def __call__(self, x, aux_x, u, ctx, dt) -> Tuple[Any, Any]: 
        ...

class InvariantFunction(Protocol): 
    def __call__(self, x, aux_x, u, ctx, dt) -> bool: 
        ...

class IntegrationFunction(Protocol):
    def __call__(self, x, aux_x, xdot, dt):
        ...