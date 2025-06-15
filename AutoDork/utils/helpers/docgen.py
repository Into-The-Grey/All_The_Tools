import os


def generate_docs(dork_scripts, base, console):
    docs_dir = os.path.join(base, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    md_path = os.path.join(docs_dir, "DorkScripts.md")
    lines = [
        "# AutoDork Script Documentation\n",
        "_Automatically generated list of available dork modules/scripts, their descriptions, and inputs._\n",
    ]
    for script in dork_scripts:
        lines.append(f"## {script['name']}")
        lines.append(f"**Filename:** `{script['filename']}`  ")
        lines.append(f"**Description:** {script['description']}\n")
        if script["inputs"]:
            lines.append("**Inputs:**")
            for inp in script["inputs"]:
                lines.append(f"- `{inp['name']}`: {inp.get('prompt','')}")
        else:
            lines.append("*No required inputs.*")
        try:
            if script["inputs"]:
                example_input = {
                    inp["name"]: f"example_{inp['name']}" for inp in script["inputs"]
                }
                dorks = script["module"].generate_dorks(example_input)
                lines.append("**Example Dorks:**")
                if dorks and isinstance(dorks, list):
                    lines += [f"    - `{d}`" for d in dorks[:5]]
                else:
                    lines.append("    - (No example dorks generated)")
        except Exception as e:
            lines.append(f"_Could not generate dork examples: {e}_")
        lines.append("\n---\n")
    with open(md_path, "w", encoding="utf-8") as mdfile:
        mdfile.write("\n".join(lines))
    console.print(f"[bold green]Generated documentation: {md_path}[/bold green]")
