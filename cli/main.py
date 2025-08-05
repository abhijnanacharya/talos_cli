import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from orchestrator.dag_executor import run_dag_from_yaml
from typer.core import TyperGroup
from typer import Context

console = Console()
RUN_HISTORY_FILE = Path(".dag_executor/run_history.log")


class TalosGroup(TyperGroup):
    def get_help(self, ctx: Context) -> str:
        ascii_art = Text("""
  _________  ________  ___       ________  ________      
|\___   ___\\   __  \|\  \     |\   __  \|\   ____\     
\|___ \  \_\ \  \|\  \ \  \    \ \  \|\  \ \  \___|_    
     \ \  \ \ \   __  \ \  \    \ \  \\\  \ \_____  \   
      \ \  \ \ \  \ \  \ \  \____\ \  \\\  \|____|\  \  
       \ \__\ \ \__\ \__\ \_______\ \_______\____\_\  \ 
        \|__|  \|__|\|__|\|_______|\|_______|\_________\\
                                            \|_________|
        """, style="bold cyan")

        tagline = Panel.fit(
            "[bold magenta]TALOS[/bold magenta] - YAML-first DAG Orchestrator\n"
            "🔧 Build multi-agent LLM workflows\n"
            "🚀 Created by Abhijnan Acharya\n"
            "📬 Reach me at: abhijnanachary11\[at]gmail.com\n"
            "[dim]Tip: Use --help with a command to learn more[/dim]",
            title="📦 Talos CLI",
            border_style="magenta"
        )

        console.print(ascii_art, soft_wrap=True)
        console.print(tagline)
        return super().get_help(ctx)

app = typer.Typer(cls=TalosGroup, add_completion=True)


@app.command()
def run(f: Path = typer.Option(..., "-f", "--file", help="Path to DAG YAML file")):
    """Run a DAG YAML file."""
    if not f.exists():
        typer.echo(f"❌ File not found: {f}")
        raise typer.Exit(1)

    typer.echo(f"🚀 Running DAG from: {f}")
    run_dag_from_yaml(str(f))

    RUN_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RUN_HISTORY_FILE.open("a") as log:
        log.write(f"{f}\n")


@app.command()
def list():
    """List all previously run DAG YAML files."""
    if not RUN_HISTORY_FILE.exists():
        typer.echo("📭 No DAGs run yet.")
        return

    typer.echo("📜 Previously run DAGs:")
    with RUN_HISTORY_FILE.open() as log:
        for i, line in enumerate(log.readlines(), 1):
            typer.echo(f"{i}. {line.strip()}")


@app.command()
def version():
    """Show the current version of Talos."""
    console.print("[bold green]Talos v0.1.0[/]")


def run_cli():
    app()
