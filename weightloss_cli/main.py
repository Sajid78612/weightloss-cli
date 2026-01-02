import typer
import json
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()
console = Console()

DATA_FILE = Path.home() / "weightloss_data.json"

def load_data():
    """Load the JSON data or return a skeleton structure if missing."""
    if not DATA_FILE.exists():
        return {"goal": None, "entries": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"goal": None, "entries": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.command()
def set_goal(weight: float):
    """Set or update your target goal weight."""
    data = load_data()
    data["goal"] = weight
    save_data(data)
    console.print(f"[green]Goal set to {weight} lbs![/green]")

@app.command()
def add(weight: float):
    """
    Log today's weight and see your stats.
    """
    data = load_data()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Handle Goal Setup if missing
    if data["goal"] is None:
        console.print("[yellow]No goal weight found.[/yellow]")
        goal = typer.prompt("What is your goal weight?", type=float)
        data["goal"] = goal

    # 2. Add the new entry
    # Check if entry for today exists, update it if so
    entry_exists = False
    for entry in data["entries"]:
        if entry["date"] == today_str:
            entry["weight"] = weight
            entry_exists = True
            break
    
    if not entry_exists:
        data["entries"].append({"date": today_str, "weight": weight})

    save_data(data)

    # 3. Calculate Stats
    entries = data["entries"]
    current_weight = weight
    start_weight = entries[0]["weight"]
    goal_weight = data["goal"]
    
    total_lost = start_weight - current_weight
    remaining = current_weight - goal_weight

    # Date math
    start_date = datetime.strptime(entries[0]["date"], "%Y-%m-%d")
    current_date = datetime.strptime(today_str, "%Y-%m-%d")
    days_elapsed = (current_date - start_date).days

    # Construct the Report
    report_lines = [
        f"[bold]Current Weight:[/bold] {current_weight} lbs",
        f"[bold]Goal Weight:[/bold]    {goal_weight} lbs",
        f"[bold]Total Lost:[/bold]     [green]{total_lost:.1f} lbs[/green]",
    ]

    # Rate Calculation (avoid division by zero on day 1)
    if days_elapsed > 0 and total_lost > 0:
        weeks_elapsed = days_elapsed / 7
        avg_per_week = total_lost / weeks_elapsed
        
        report_lines.append(f"[bold]Average Loss:[/bold]   {avg_per_week:.2f} lbs/week")

        if avg_per_week > 0 and remaining > 0:
            weeks_to_go = remaining / avg_per_week
            days_to_go = int(weeks_to_go * 7)
            report_lines.append(f"\n[cyan]At this pace, you will reach your goal in [bold]{days_to_go} days[/bold]![/cyan]")
    elif days_elapsed == 0:
        report_lines.append("\n[italic]Day 1! Keep going to see predictions.[/italic]")
    else:
        report_lines.append("\n[yellow]No weight lost yet (or weight gained). Keep pushing![/yellow]")

    console.print(Panel("\n".join(report_lines), title="Weight Loss Report", expand=False))

@app.command()
def history():
    """View all past entries."""
    data = load_data()
    table = Table(title="Weight History")
    table.add_column("Date", style="cyan")
    table.add_column("Weight", style="magenta")

    for entry in data["entries"]:
        table.add_row(entry["date"], str(entry["weight"]))
    
    console.print(table)

if __name__ == "__main__":
    app()