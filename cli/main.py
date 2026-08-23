import json
import os
import sys

import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="SwarmSRE Control Plane CLI")
incidents_app = typer.Typer(help="Manage and view incidents")
app.add_typer(incidents_app, name="incidents")

console = Console()

def get_api_url() -> str:
    return os.environ.get("SWARMSRE_API_URL", "http://localhost:8000")

@incidents_app.command("list")
def list_incidents():
    """List all incidents."""
    api_url = get_api_url()
    try:
        response = httpx.get(f"{api_url}/api/incidents")
        response.raise_for_status()
        incidents = response.json()
    except httpx.RequestError as e:
        console.print(f"[bold red]Error connecting to API:[/bold red] {e}")
        raise typer.Exit(1)
        
    table = Table(title="SwarmSRE Incidents")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Status", style="bold magenta")
    table.add_column("Created At", style="dim")
    
    for inc in incidents:
        table.add_row(
            inc["id"][:8],
            inc["title"],
            inc["status"],
            inc["created_at"]
        )
        
    console.print(table)

@incidents_app.command("get")
def get_incident(
    incident_id: str, 
    trace: bool = typer.Option(False, "--trace", "-t", help="Show full agent reasoning trace"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output in JSON format (useful with --trace)")
):
    """Get details for a specific incident."""
    api_url = get_api_url()
    try:
        response = httpx.get(f"{api_url}/api/incidents/{incident_id}")
        if response.status_code == 404:
            console.print(f"[bold red]Incident {incident_id} not found.[/bold red]")
            raise typer.Exit(1)
        response.raise_for_status()
        incident = response.json()
    except httpx.RequestError as e:
        console.print(f"[bold red]Error connecting to API:[/bold red] {e}")
        raise typer.Exit(1)

    if json_out:
        if trace:
            console.print_json(data=incident.get("agent_trace", []))
        else:
            console.print_json(data=incident)
        return

    # Compact summary by default
    console.print(Panel(
        f"[bold]Title:[/bold] {incident['title']}\n"
        f"[bold]Status:[/bold] {incident['status']}\n"
        f"[bold]Description:[/bold]\n{incident['description']}",
        title=f"Incident: {incident['id']}",
        border_style="blue"
    ))
    
    if incident.get("rca_summary"):
        console.print(Panel(incident["rca_summary"], title="RCA Summary", border_style="green"))

    # Progressive Disclosure for CLI
    if trace:
        trace_data = incident.get("agent_trace", [])
        if not trace_data:
            console.print("[yellow]No trace data available for this incident.[/yellow]")
            return
            
        console.print("\n[bold cyan]Agent Reasoning Trace:[/bold cyan]")
        for step in trace_data:
            agent = step["agent"]
            summary = step["summary"]
            details = step["details"]
            
            console.print(f"\n[bold]{agent}[/bold] ── {summary}")
            if details != summary:
                console.print(f"[dim]{details}[/dim]")
    else:
        if incident.get("agent_trace"):
            console.print(f"\n[dim]Tip: Use --trace to view the full {len(incident['agent_trace'])}-step agent reasoning chain.[/dim]")

@incidents_app.command("approve")
def approve_incident(incident_id: str):
    """Approve a PROPOSED patch."""
    api_url = get_api_url()
    try:
        response = httpx.post(f"{api_url}/api/incidents/{incident_id}/approve")
        if response.status_code == 404:
            console.print(f"[bold red]Incident {incident_id} not found.[/bold red]")
            raise typer.Exit(1)
        if response.status_code == 400:
            console.print(f"[bold red]Error:[/bold red] {response.json().get('detail')}")
            raise typer.Exit(1)
        response.raise_for_status()
        console.print(f"[bold green]Successfully approved patch for incident {incident_id}[/bold green]")
    except httpx.RequestError as e:
        console.print(f"[bold red]Error connecting to API:[/bold red] {e}")
        raise typer.Exit(1)

@incidents_app.command("reject")
def reject_incident(incident_id: str):
    """Reject a PROPOSED patch."""
    api_url = get_api_url()
    try:
        response = httpx.post(f"{api_url}/api/incidents/{incident_id}/reject")
        if response.status_code == 404:
            console.print(f"[bold red]Incident {incident_id} not found.[/bold red]")
            raise typer.Exit(1)
        if response.status_code == 400:
            console.print(f"[bold red]Error:[/bold red] {response.json().get('detail')}")
            raise typer.Exit(1)
        response.raise_for_status()
        console.print(f"[bold green]Successfully rejected patch for incident {incident_id}[/bold green]")
    except httpx.RequestError as e:
        console.print(f"[bold red]Error connecting to API:[/bold red] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
