import os
import json


def save_profile(
    profile_name, cli_inputs, config, script, wordlist, output, base, console
):
    profiles_dir = os.path.join(base, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    pf = {
        "cli_inputs": cli_inputs,
        "config": config,
        "script": script,
        "wordlist": wordlist,
        "output": output,
    }
    with open(
        os.path.join(profiles_dir, f"{profile_name}.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(pf, f, indent=2)
    console.print(f"[bold green]Profile saved:[/bold green] {profile_name}")


def load_profile(profile_name, base, console):
    profiles_dir = os.path.join(base, "profiles")
    profile_path = os.path.join(profiles_dir, f"{profile_name}.json")
    if not os.path.exists(profile_path):
        console.print(f"[red]Profile {profile_name} not found![/red]")
        return None
    with open(profile_path, "r", encoding="utf-8") as f:
        pf = json.load(f)
    console.print(f"[bold cyan]Loaded profile:[/bold cyan] {profile_name}")
    return pf
