import time
from typing import List, Union

import psutil


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


def print_process_identifier(proc_name: str, cmd_line: str, process_names: List[str]):
    return f"process '{proc_name}' (looking for {','.join(process_names)}) with command line '{cmd_line}'"


def wait_for_app_start():
    # TODO Make this deterministic
    time.sleep(8)
