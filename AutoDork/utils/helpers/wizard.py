import os


def new_script_wizard(scripts_dir, inquirer, console):
    console.print("[bold cyan]Dork Script Creation Wizard[/bold cyan]")
    name = inquirer.text(message="Script display name:").execute()
    filename = inquirer.text(message="Script filename (e.g., my_dork.py):").execute()
    description = inquirer.text(message="Short description:").execute()
    num_inputs = int(inquirer.text(message="How many input fields?").execute())
    inputs = []
    for i in range(num_inputs):
        key = inquirer.text(message=f"Input #{i+1} name (var, no spaces):").execute()
        prompt = inquirer.text(message=f"Prompt for '{key}':").execute()
        inputs.append({"name": key, "prompt": prompt})
    dork_tmpl = inquirer.text(
        message="Google dork query template (use {input_names} for vars, comma-separate for multiple dorks):"
    ).execute()
    dork_templates = [d.strip() for d in dork_tmpl.split(",") if d.strip()]

    script_lines = [
        "def get_metadata():",
        f"    return {{",
        f"        'name': '{name}',",
        f"        'description': '{description}',",
        f"        'inputs': {inputs}",
        f"    }}",
        "",
        "def generate_dorks(inputs):",
        "    dorks = []",
    ]
    for d in dork_templates:
        script_lines.append(f"    dorks.append(f'''{d}'''.format(**inputs))")
    script_lines.append("    return dorks")
    script_content = "\n".join(script_lines)
    script_path = os.path.join(scripts_dir, filename)
    if os.path.exists(script_path):
        overwrite = inquirer.confirm(
            message=f"{filename} already exists. Overwrite?"
        ).execute()
        if not overwrite:
            console.print("[yellow]Cancelled.[/yellow]")
            return
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    console.print(f"[bold green]New dork script created: {script_path}[/bold green]")
