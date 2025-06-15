import os
import zipfile
from datetime import datetime


def backup_configs_and_scripts(config_dir, scripts_dir, backups_dir, base, console):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"autodork_backup_{timestamp}.zip"
    backup_path = os.path.join(backups_dir, backup_name)
    with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in [config_dir, scripts_dir]:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    fpath = os.path.join(root, file)
                    arcname = os.path.relpath(fpath, base)
                    zf.write(fpath, arcname)
    console.print(f"[bold green]Backup created:[/bold green] {backup_path}")


def list_backups(backups_dir, console):
    backups = [f for f in os.listdir(backups_dir) if f.endswith(".zip")]
    if not backups:
        console.print("[yellow]No backups found.[/yellow]")
        return []
    for i, b in enumerate(backups, 1):
        console.print(f"{i}. {b}")
    return backups


def restore_backup(backup_filename, backups_dir, base, console, inquirer):
    backup_path = os.path.join(backups_dir, backup_filename)
    if not os.path.exists(backup_path):
        console.print(f"[red]Backup {backup_filename} not found![/red]")
        return
    confirm = inquirer.confirm(
        message=f"Restore backup {backup_filename}? This will overwrite config/ and scripts/! Continue?"
    ).execute()
    if not confirm:
        console.print("[yellow]Restore cancelled.[/yellow]")
        return
    with zipfile.ZipFile(backup_path, "r") as zf:
        zf.extractall(base)
    console.print(f"[bold green]Backup {backup_filename} restored.[/bold green]")
