from typing import Callable
import numpy as np

class Condition: 
    def __init__(
        self, 
        func: Callable, 
        name: str = None,
        priority: int = 0,
        description: str = ""
    ): 
        self.func = func
        self.name = name or func.__name__
        self.priority = priority
        self.description = description
        
    def __call__(self, ctx):
        self._validate_context(ctx)
        return self.func(ctx)
    
    
    def _validate_context(self, ctx): 
        if not hasattr(ctx, 'x'):
            raise TypeError(f"{self.name}: Context must have 'x'")
        if not hasattr(ctx, 'aux'): 
            raise TypeError(f"{self.name}: Context must have aux")
        if not hasattr(ctx, "cfg"):
            raise TypeError(f"{self.name}: Context must have 'cfg'")

def guard(func: Callable = None, *, name: str = None, priority: int = 0, description: str = ""):
    def wrapper(f):
        # Check the return type annotation if present
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Guard function '{f.__name__}' must have return type 'bool'")
        return Condition(f, name=name, priority=priority, description=description)
    if func is not None:
        return wrapper(func)
    return wrapper

def reset(func: Callable = None, *, name: str = None, priority: int = 0, description: str = ""):
    def wrapper(f):
        # Check the return type annotation if present
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Guard function '{f.__name__}' must have return type 'bool'")
        return Condition(f, name=name, priority=priority, description=description)
    if func is not None:
        return wrapper(func)
    return wrapper

def invariant(func: Callable = None, *, name: str = None, priority: int = 0, description: str = ""):
    def wrapper(f):
        # Check the return type annotation if present
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Guard function '{f.__name__}' must have return type 'bool'")
        return Condition(f, name=name, priority=priority, description=description)
    if func is not None:
        return wrapper(func)
    return wrapper

def continuous_dynamics(func: Callable = None, *, name: str = None, priority: int = 0, description: str = ""):
    def wrapper(f):
        # Check the return type annotation if present
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Guard function '{f.__name__}' must have return type 'bool'")
        return Condition(f, name=name, priority=priority, description=description)
    if func is not None:
        return wrapper(func)
    return wrapper