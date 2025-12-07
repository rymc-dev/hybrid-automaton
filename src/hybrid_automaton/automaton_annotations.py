import numpy as np
from typing import Callable
from .automaton_runtime_context import Context

class Annotation:
    def __init__(self, func: Callable, name=None, priority=0, description=""):
        self.func = func
        self.name = name or func.__name__
        self.priority = priority
        self.description = description

    def __call__(self, ctx: Context):
        if not isinstance(ctx, Context):
            raise TypeError(f"{self.name}: ctx must be a Context instance")
        return self.func(ctx)

# Decorators
def guard(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Guard '{f.__name__}' must return bool")
        return Annotation(f, name=name, priority=priority, description=description)
    return wrapper(func) if func else wrapper

def invariant(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not bool:
                raise TypeError(f"Invariant '{f.__name__}' must return bool")
        return Annotation(f, name=name, priority=priority, description=description)
    return wrapper(func) if func else wrapper

def reset(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        def inner(ctx: Context):
            result = f(ctx)
            if not isinstance(result, Context):
                raise TypeError(f"Reset '{f.__name__}' must return a Context instance")
            return result
        inner.__name__ = name or f.__name__
        inner.priority = priority
        inner.description = description
        return inner
    return wrapper(func) if func else wrapper

def continuous_dynamics(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not np.ndarray:
                raise TypeError(f"Continuous Dynamics '{f.__name__}' must return np.ndarray")
        
        def inner(ctx):
            # Validate context first
            from .automaton_runtime_context import Context
            if not isinstance(ctx, Context):
                raise TypeError(f"Continuous Dynamics '{f.__name__}': ctx must be a Context instance")

            result = f(ctx)
            if not isinstance(result, np.ndarray):
                raise TypeError(f"Continuous Dynamics '{f.__name__}' must return np.ndarray")
            return result

        inner.__name__ = name or f.__name__
        inner.priority = priority
        inner.description = description
        return inner

    return wrapper(func) if func else wrapper


def integration(func: Callable = None, *, name=None, priority=0, description=""):
    def wrapper(f):
        if hasattr(f, "__annotations__") and "return" in f.__annotations__:
            if f.__annotations__["return"] is not np.ndarray:
                raise TypeError(f"Integration '{f.__name__}' must return np.ndarray")
        def inner(ctx):
            result = f(ctx)
            if not isinstance(result, np.ndarray):
                raise TypeError(f"Integration '{f.__name__}' must return np.ndarray")
            return result
        inner.__name__ = name or f.__name__
        inner.priority = priority
        inner.description = description
        return inner
    return wrapper(func) if func else wrapper
