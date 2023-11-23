import random
import string
import sys
import threading
import time
from typing import List, Union

import psutil

DEFAULT_APP_WAIT_TIME_SEC = 8

processes = {}


def _print_log(line: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {line}"
    sys.stderr.write(line)
    sys.stderr.flush()


def _find_in_stream(stream, text: str, process_handle: str) -> None:
    while (
        not processes[process_handle]["text_found"].is_set()
        and not processes[process_handle]["timed_out"].is_set()
    ):
        try:
            line = stream.readline().decode("utf-8")
            if text in line:
                processes[process_handle]["text_found"].set()
            _print_log(line)
        except Exception:
            pass


def _random_string(length: int) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def _process_timeout(process_handle, timeout=DEFAULT_APP_WAIT_TIME_SEC) -> bool:
    _print_log(
        f"Waiting up to {timeout} seconds to abort search on process {process_handle}..."
    )
    timeout_remaining = timeout
    while (
        timeout_remaining > 0 and not processes[process_handle]["text_found"].is_set()
    ):
        time.sleep(1)
        timeout_remaining -= 1
    if not processes[process_handle]["text_found"].is_set():
        processes[process_handle]["timed_out"].set()


def wait_for_process_output(
    process, text: str, timeout=DEFAULT_APP_WAIT_TIME_SEC
) -> None:
    """This function checks if the given text is in the process output within the given time limit."""
    start_time = time.time()

    process_handle = _random_string(10)
    processes[process_handle] = {
        "text_found": threading.Event(),
        "timed_out": threading.Event(),
    }

    # start a new thread to stop searching after the timeout
    threading.Thread(target=_process_timeout, args=(process_handle, timeout)).start()
    # search for the text in the stdout and stderr streams
    threading.Thread(
        target=_find_in_stream, args=(process.stdout, text, process_handle)
    ).start()
    threading.Thread(
        target=_find_in_stream, args=(process.stderr, text, process_handle)
    ).start()

    while True:
        if processes[process_handle]["text_found"].is_set():
            return
        if processes[process_handle]["timed_out"].is_set():
            raise Exception(
                f"Failed to find '{text}' in process output after {time.time() - start_time} seconds."
            )


def is_process_match(command: str, process_names: List[str]) -> bool:
    if len(process_names) == 1:
        command_parts = command.split(" ")
        if command_parts[0] == process_names[0]:
            return True
    if len(process_names) > 1 and all(
        [process_name in command for process_name in process_names]
    ):
        return True
    return False


def kill_process(process_names: Union[str, List[str]]) -> None:
    if isinstance(process_names, str):
        process_names = [process_names]
    proc_name = "undefined"
    cmd_line = "undefined"
    # Kill all processes with the given name
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"], ad_value=None):
        try:
            proc_name = proc.name()
            if proc.status() == psutil.STATUS_ZOMBIE:
                continue
            # The python process is named "Python" on OS X and "uvicorn" on CircleCI
            if is_process_match(proc_name, process_names):
                print(f"Killing process with name {proc_name}...")
                proc.kill()
            elif proc_name.lower().startswith("python"):
                # drop the first argument, which is the python executable
                python_command_parts = proc.cmdline()[1:]
                # the initial command part is the last part of the path
                python_command_parts[0] = python_command_parts[0].split("/")[-1]
                # combine the remaining arguments
                command = " ".join(python_command_parts)
                print(
                    f"Evaluating process with name '{proc_name}' and command '{command}'..."
                )
                if (
                    len(cmd_line) > 1
                    and "nox" not in command
                    and is_process_match(command, process_names)
                ):
                    print(
                        f"Killing process with name '{proc_name}' and command '{command}'..."
                    )
                    proc.kill()
        except psutil.ZombieProcess as zp:
            print(
                f"Failed to kill zombie process {print_process_identifier(proc_name, cmd_line, process_names)}: {str(zp)}"
            )
        except psutil.NoSuchProcess as nsp:
            print(
                f"Failed to kill process {print_process_identifier(proc_name, cmd_line, process_names)}: {str(nsp)}"
            )


def print_process_identifier(proc_name: str, cmd_line: str, process_names: List[str]):
    return f"process '{proc_name}' (looking for {','.join(process_names)}) with command line '{cmd_line}'"


def wait_for_app_start(timeout=DEFAULT_APP_WAIT_TIME_SEC):
    print(
        "WARNING: wait_for_app_start() is deprecated, use wait_for_process_output() instead.",
        file=sys.stderr,
        flush=True,
    )
    time.sleep(timeout)
