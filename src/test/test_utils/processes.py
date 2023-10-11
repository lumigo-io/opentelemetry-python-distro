import psutil


def kill_process(process_name: str) -> None:
    proc_name = "undefined"
    cmd_line = "undefined"
    try:
        # Kill all processes with the given name
        for proc in psutil.process_iter(
            attrs=["pid", "name", "cmdline"], ad_value=None
        ):
            proc_name = proc.name()
            if proc.status() == psutil.STATUS_ZOMBIE:
                continue
            # The python process is named "Python" on OS X and "uvicorn" on CircleCI
            if proc_name == process_name:
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
                    and process_name in command
                ):
                    print(
                        f"Killing process with name '{proc_name}' and command '{command}'..."
                    )
                    proc.kill()
    except psutil.ZombieProcess as zp:
        print(
            f"Failed to kill zombie process '{proc_name}' (looking for {process_name}) with command line '{cmd_line}': {str(zp)}"
        )
    except psutil.NoSuchProcess as nsp:
        print(
            f"Failed to kill process '{proc_name}' (looking for {process_name}) with command line '{cmd_line}': {str(nsp)}"
        )
