import os
import shlex


def save_schedule_script(name, sys_argv, base, console):
    script_dir = os.path.join(base, "schedules")
    os.makedirs(script_dir, exist_ok=True)
    script_path = os.path.join(script_dir, f"{name}.sh")
    cmd = " ".join(
        [shlex.quote(arg) for arg in ["python3", sys_argv[0]] + sys_argv[1:]]
    )
    with open(script_path, "w") as f:
        f.write(f"#!/bin/bash\ncd {base}\n{cmd}\n")
    os.chmod(script_path, 0o755)
    console.print(f"[bold green]Saved schedule script: {script_path}[/bold green]")
