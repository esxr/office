#!/usr/bin/env python3
"""
Utility to help debug hanging async code by dumping task information.
This can be used to identify which tasks are hanging.
"""

import asyncio
import sys
import argparse
import traceback
import signal
from typing import List, Dict, Any
import time


def dump_tasks() -> None:
    """Dump information about pending tasks."""
    print("\n--- PENDING ASYNCIO TASKS ---")
    tasks = asyncio.all_tasks()

    if not tasks:
        print("No pending tasks.")
        return

    for i, task in enumerate(tasks):
        print(f"\nTask {i+1}/{len(tasks)}:")
        print(f"  Name: {task.get_name()}")
        print(f"  State: {task._state}")
        print(f"  Cancelled: {task.cancelled()}")
        print(f"  Done: {task.done()}")

        # Get the stack for this task
        stack = getattr(task, "_coro", None)
        if stack:
            stack_trace = "".join(traceback.format_stack(stack.cr_frame))
            print(f"  Stack Trace:\n{stack_trace}")
        else:
            print("  No stack trace available")

    print("\n--- END PENDING TASKS ---")


def setup_debugging(interval: int = 60) -> None:
    """Set up debugging helpers including signal handlers.

    Args:
        interval: Time interval in seconds for automated task dumps
    """
    # Register signal handlers for SIGUSR1 to dump tasks on demand
    try:
        signal.signal(signal.SIGUSR1, lambda sig, frame: dump_tasks())
        print(f"Send SIGUSR1 to process {sys.pid} to dump pending tasks")
    except AttributeError:
        # SIGUSR1 not available on Windows
        print("SIGUSR1 not available on this platform")

    # Also register SIGINT (Ctrl+C) to dump tasks before exiting
    signal.signal(signal.SIGINT, lambda sig, frame: (dump_tasks(), sys.exit(0)))

    # Start a background task to periodically dump tasks if interval > 0
    if interval > 0:

        async def periodic_dump():
            while True:
                await asyncio.sleep(interval)
                dump_tasks()

        loop = asyncio.get_event_loop()
        loop.create_task(periodic_dump(), name="periodic_task_dump")
        print(f"Will dump pending tasks every {interval} seconds")


async def monitor_task(coro, timeout: int = 30) -> Any:
    """Run a coroutine with monitoring to detect if it hangs.

    Args:
        coro: The coroutine to monitor
        timeout: Timeout in seconds before dumping task info

    Returns:
        The result of the coroutine
    """
    task = asyncio.create_task(coro)

    try:
        return await asyncio.wait_for(task, timeout=timeout)
    except asyncio.TimeoutError:
        print(f"\nTask timed out after {timeout} seconds. Current state:")
        dump_tasks()

        # Don't cancel the task, let it continue running
        print("\nContinuing to wait for the task...")
        return await task


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debug hanging async code")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Interval in seconds to automatically dump task info (0 to disable)",
    )
    args = parser.parse_args()

    setup_debugging(args.interval)

    print("Debug setup complete. Run your async code with this module imported.")
    print("Example usage in your code:")
    print("  from debug_async import setup_debugging, monitor_task, dump_tasks")
    print("  setup_debugging(interval=30)  # Dump tasks every 30 seconds")
    print(
        "  result = await monitor_task(your_coroutine(), timeout=60)  # Monitor with 60s timeout"
    )
