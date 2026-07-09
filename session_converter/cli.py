"""CLI interface for session converter."""

import sys
import time
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .models import ConversionStats
from .parsers import ClaudeParser, CodexParser
from .emitters import ClaudeEmitter, CodexEmitter
from .utils import read_jsonl, write_jsonl, detect_format, calculate_duration

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Convert AI assistant sessions between Claude Code and Codex CLI formats."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('-o', '--output', type=click.Path(path_type=Path), help='Output file path')
@click.option('--to', 'target_format', type=click.Choice(['claude', 'codex']), help='Target format (auto-detected if not specified)')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
@click.option('--validate', is_flag=True, help='Validate output after conversion')
@click.option('--stats', is_flag=True, help='Show conversion statistics')
@click.option('-v', '--verbose', is_flag=True, help='Verbose logging')
def convert(
    input_file: Path,
    output: Optional[Path],
    target_format: Optional[str],
    pretty: bool,
    validate: bool,
    stats: bool,
    verbose: bool
) -> None:
    """Convert session between formats (auto-detects source format).
    
    This is the recommended command for converting sessions. It automatically
    detects whether your input is Claude Code or Codex CLI format and converts
    to the other format, or to the format you specify with --to.
    """
    # Detect source format
    source_format = detect_format(input_file)
    
    if not source_format:
        console.print("[red]Error:[/red] Could not detect session format")
        console.print("Please specify formats explicitly using:")
        console.print("  session-convert claude-to-codex <file>")
        console.print("  session-convert codex-to-claude <file>")
        sys.exit(1)
    
    if verbose:
        console.print(f"[cyan]Detected format:[/cyan] {source_format.title()}")
    
    # Determine target format
    if not target_format:
        # Auto-select opposite format
        target_format = 'codex' if source_format == 'claude' else 'claude'
        if verbose:
            console.print(f"[cyan]Target format:[/cyan] {target_format.title()}")
    elif target_format == source_format:
        console.print(f"[yellow]Warning:[/yellow] Source and target formats are the same ({source_format})")
        console.print("No conversion needed. Use 'session-convert info' to view session details.")
        sys.exit(0)
    
    _convert_session(
        input_file=input_file,
        output=output,
        source_format=source_format,
        target_format=target_format,
        pretty=pretty,
        validate=validate,
        stats=stats,
        verbose=verbose
    )


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('-o', '--output', type=click.Path(path_type=Path), help='Output file path')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
@click.option('--preserve-unknown', is_flag=True, help='Keep unknown fields in output')
@click.option('--validate', is_flag=True, help='Validate output after conversion')
@click.option('--stats', is_flag=True, help='Show conversion statistics')
@click.option('-v', '--verbose', is_flag=True, help='Verbose logging')
def claude_to_codex(
    input_file: Path,
    output: Optional[Path],
    pretty: bool,
    preserve_unknown: bool,
    validate: bool,
    stats: bool,
    verbose: bool
) -> None:
    """Convert Claude Code session to Codex CLI format.
    
    Note: Consider using 'session-convert convert' for automatic format detection.
    """
    _convert_session(
        input_file=input_file,
        output=output,
        source_format='claude',
        target_format='codex',
        pretty=pretty,
        validate=validate,
        stats=stats,
        verbose=verbose
    )


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('-o', '--output', type=click.Path(path_type=Path), help='Output file path')
@click.option('--pretty', is_flag=True, help='Pretty-print JSON output')
@click.option('--preserve-unknown', is_flag=True, help='Keep unknown fields in output')
@click.option('--validate', is_flag=True, help='Validate output after conversion')
@click.option('--stats', is_flag=True, help='Show conversion statistics')
@click.option('-v', '--verbose', is_flag=True, help='Verbose logging')
def codex_to_claude(
    input_file: Path,
    output: Optional[Path],
    pretty: bool,
    preserve_unknown: bool,
    validate: bool,
    stats: bool,
    verbose: bool
) -> None:
    """Convert Codex CLI session to Claude Code format.
    
    Note: Consider using 'session-convert convert' for automatic format detection.
    """
    _convert_session(
        input_file=input_file,
        output=output,
        source_format='codex',
        target_format='claude',
        pretty=pretty,
        validate=validate,
        stats=stats,
        verbose=verbose
    )


def _convert_session(
    input_file: Path,
    output: Optional[Path],
    source_format: str,
    target_format: str,
    pretty: bool,
    validate: bool,
    stats: bool,
    verbose: bool
) -> None:
    """Internal conversion logic."""
    start_time = time.time()
    
    try:
        # Display progress
        if verbose:
            console.print(f"[cyan]Reading:[/cyan] {input_file}")
        
        # Parse input
        if source_format == 'claude':
            parser = ClaudeParser()
            session = parser.parse(input_file)
            warnings = parser.warnings
        else:
            parser = CodexParser()
            session = parser.parse(input_file)
            warnings = parser.warnings
        
        if verbose:
            console.print(f"[green]✓[/green] Parsed {source_format.title()} format")
            console.print(f"  Session ID: {session.id}")
            console.print(f"  Turns: {session.get_turn_count()}")
            console.print(f"  Tool calls: {session.get_tool_call_count()}")
        
        # Convert to target format
        if target_format == 'codex':
            emitter = CodexEmitter()
        else:
            emitter = ClaudeEmitter()
        
        events = emitter.emit(session)
        
        if verbose:
            console.print(f"[green]✓[/green] Converted to {target_format.title()} format")
            console.print(f"  Output events: {len(events)}")
        
        # Write output
        if output:
            write_jsonl(output, events, pretty=pretty)
            if verbose:
                console.print(f"[green]✓[/green] Wrote output to {output}")
        else:
            # Write to stdout
            import json
            for event in events:
                if pretty:
                    print(json.dumps(event, indent=2))
                else:
                    print(json.dumps(event))
        
        # Show statistics
        duration = time.time() - start_time
        
        if stats:
            conversion_stats = ConversionStats(
                input_file=str(input_file),
                output_file=str(output) if output else 'stdout',
                source_format=source_format,
                target_format=target_format,
                session_id=session.id,
                turn_count=session.get_turn_count(),
                tool_call_count=session.get_tool_call_count(),
                event_count=len(events),
                duration_seconds=duration,
                warnings=warnings,
            )
            _print_stats(conversion_stats)
        
        if warnings and verbose:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  - {warning}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
def info(input_file: Path) -> None:
    """Display information about a session file."""
    try:
        # Detect format
        format_type = detect_format(input_file)
        
        if not format_type:
            console.print("[red]Error:[/red] Could not detect session format")
            sys.exit(1)
        
        # Parse session
        if format_type == 'claude':
            parser = ClaudeParser()
        else:
            parser = CodexParser()
        
        session = parser.parse(input_file)
        
        # Create info table
        table = Table(title=f"Session Information: {input_file.name}", show_header=False)
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("Format", format_type.title())
        table.add_row("Session ID", session.id)
        table.add_row("Turns", str(session.get_turn_count()))
        table.add_row("Tool Calls", str(session.get_tool_call_count()))
        table.add_row("Events", str(session.get_event_count()))
        
        if session.model:
            table.add_row("Model", session.model)
        table.add_row("CWD", session.cwd)
        if session.git_branch:
            table.add_row("Git Branch", session.git_branch)
        if session.git_commit:
            table.add_row("Git Commit", session.git_commit[:8])
        if session.version:
            table.add_row("CLI Version", session.version)
        
        console.print(table)
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--format', 'format_type', type=click.Choice(['claude', 'codex']), help='Session format')
def validate(input_file: Path, format_type: Optional[str]) -> None:
    """Validate a session file format."""
    try:
        # Detect format if not specified
        if not format_type:
            format_type = detect_format(input_file)
            if not format_type:
                console.print("[red]Error:[/red] Could not detect format. Please specify with --format")
                sys.exit(1)
        
        console.print(f"[cyan]Validating as {format_type.title()} format...[/cyan]")
        
        # Parse to validate
        if format_type == 'claude':
            parser = ClaudeParser()
        else:
            parser = CodexParser()
        
        session = parser.parse(input_file)
        
        console.print(f"[green]✓[/green] Valid {format_type.title()} session file")
        console.print(f"  Session ID: {session.id}")
        console.print(f"  Turns: {session.get_turn_count()}")
        
        if parser.warnings:
            console.print(f"\n[yellow]Warnings: {len(parser.warnings)}[/yellow]")
            for warning in parser.warnings[:5]:  # Show first 5
                console.print(f"  - {warning}")
            if len(parser.warnings) > 5:
                console.print(f"  ... and {len(parser.warnings) - 5} more")
    
    except Exception as e:
        console.print(f"[red]✗[/red] Invalid session file")
        console.print(f"  Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, path_type=Path))
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--from', 'source_format', type=click.Choice(['claude', 'codex']), required=True, help='Source format')
@click.option('--to', 'target_format', type=click.Choice(['claude', 'codex']), required=True, help='Target format')
@click.option('--pattern', default='*.jsonl', help='Glob pattern for input files')
@click.option('--recursive', is_flag=True, help='Search subdirectories')
@click.option('--continue-on-error', is_flag=True, help='Continue if a file fails')
@click.option('--stats', is_flag=True, help='Show statistics')
def batch(
    input_dir: Path,
    output_dir: Path,
    source_format: str,
    target_format: str,
    pattern: str,
    recursive: bool,
    continue_on_error: bool,
    stats: bool
) -> None:
    """Batch convert multiple session files."""
    try:
        # Find input files
        if recursive:
            files = list(input_dir.rglob(pattern))
        else:
            files = list(input_dir.glob(pattern))
        
        if not files:
            console.print(f"[yellow]No files matching '{pattern}' found in {input_dir}[/yellow]")
            return
        
        console.print(f"Found {len(files)} files to convert")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert files
        success_count = 0
        error_count = 0
        
        for file in files:
            try:
                relative_path = file.relative_to(input_dir)
                output_file = output_dir / relative_path
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                console.print(f"\n[cyan]Converting:[/cyan] {relative_path}")
                
                _convert_session(
                    input_file=file,
                    output=output_file,
                    source_format=source_format,
                    target_format=target_format,
                    pretty=False,
                    validate=False,
                    stats=False,
                    verbose=False
                )
                
                console.print(f"[green]✓[/green] {relative_path}")
                success_count += 1
            
            except Exception as e:
                console.print(f"[red]✗[/red] {relative_path}: {e}")
                error_count += 1
                
                if not continue_on_error:
                    raise
        
        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Success: {success_count}")
        console.print(f"  Errors: {error_count}")
    
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _print_stats(stats: ConversionStats) -> None:
    """Print conversion statistics."""
    panel_content = f"""
[cyan]Input:[/cyan] {stats.input_file} ({stats.source_format.title()})
[cyan]Output:[/cyan] {stats.output_file} ({stats.target_format.title()})

[bold]Session Information:[/bold]
  Session ID: {stats.session_id}
  Turns: {stats.turn_count}
  Tool Calls: {stats.tool_call_count}
  Events: {stats.event_count}

[bold]Conversion:[/bold]
  Duration: {stats.duration_seconds:.2f}s
  Warnings: {len(stats.warnings)}
  Errors: {len(stats.errors)}
"""
    
    console.print(Panel(panel_content.strip(), title="Conversion Statistics", border_style="green"))
    
    if stats.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in stats.warnings:
            console.print(f"  - {warning}")
    
    if stats.errors:
        console.print("\n[red]Errors:[/red]")
        for error in stats.errors:
            console.print(f"  - {error}")


if __name__ == '__main__':
    cli()
