"""Utility functions for hybrid automaton runner."""
import asyncio
from typing import List


async def deactivate_after_timeout(timeout_sec: float, *tasks):
    """
    Cancel tasks after a timeout.
    
    Args:
        timeout_sec: Timeout duration in seconds
        *tasks: Variable number of asyncio tasks to cancel
    """
    await asyncio.sleep(timeout_sec)
    for task in tasks:
        task.cancel()
    # Wait for all tasks to finish cancelling
    await asyncio.gather(*tasks, return_exceptions=True)


async def run_with_timeout(coro, timeout_sec: float):
    """
    Run a coroutine with a timeout.
    
    Args:
        coro: Coroutine to run
        timeout_sec: Timeout duration in seconds
    
    Returns:
        Result of coroutine or None if timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_sec)
    except asyncio.TimeoutError:
        print(f"Operation timed out after {timeout_sec} seconds")
        return None