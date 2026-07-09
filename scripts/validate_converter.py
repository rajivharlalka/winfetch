#!/usr/bin/env python3
"""Comprehensive validation script for session converter."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class ValidationResult:
    """Result of a validation test."""
    
    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details


class SessionConverterValidator:
    """Validate the session converter tool."""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.project_root = Path(__file__).parent.parent
    
    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        return result.returncode, result.stdout, result.stderr
    
    def test_cli_help(self) -> ValidationResult:
        """Test that CLI help works."""
        exit_code, stdout, stderr = self.run_command(["session-convert", "--help"])
        
        if exit_code == 0 and "Convert AI assistant sessions" in stdout:
            return ValidationResult(
                "CLI Help",
                True,
                "Help command works correctly"
            )
        else:
            return ValidationResult(
                "CLI Help",
                False,
                f"Help command failed with exit code {exit_code}",
                stderr
            )
    
    def test_example_files_exist(self) -> ValidationResult:
        """Test that example files exist."""
        claude_example = self.project_root / "examples" / "claude_session.jsonl"
        codex_example = self.project_root / "examples" / "codex_session.jsonl"
        
        if claude_example.exists() and codex_example.exists():
            return ValidationResult(
                "Example Files",
                True,
                "Both example files exist"
            )
        else:
            missing = []
            if not claude_example.exists():
                missing.append("claude_session.jsonl")
            if not codex_example.exists():
                missing.append("codex_session.jsonl")
            
            return ValidationResult(
                "Example Files",
                False,
                f"Missing example files: {', '.join(missing)}"
            )
    
    def test_info_command(self) -> ValidationResult:
        """Test the info command on examples."""
        claude_example = self.project_root / "examples" / "claude_session.jsonl"
        
        exit_code, stdout, stderr = self.run_command([
            "session-convert", "info", str(claude_example)
        ])
        
        if exit_code == 0 and "Session ID" in stdout:
            return ValidationResult(
                "Info Command",
                True,
                "Info command works on example files"
            )
        else:
            return ValidationResult(
                "Info Command",
                False,
                f"Info command failed with exit code {exit_code}",
                stderr
            )
    
    def test_validate_command(self) -> ValidationResult:
        """Test the validate command."""
        claude_example = self.project_root / "examples" / "claude_session.jsonl"
        
        exit_code, stdout, stderr = self.run_command([
            "session-convert", "validate", str(claude_example), "--format", "claude"
        ])
        
        if exit_code == 0 and "Valid" in stdout:
            return ValidationResult(
                "Validate Command",
                True,
                "Validation works on example files"
            )
        else:
            return ValidationResult(
                "Validate Command",
                False,
                f"Validate command failed with exit code {exit_code}",
                stderr
            )
    
    def test_claude_to_codex(self) -> ValidationResult:
        """Test Claude to Codex conversion."""
        claude_example = self.project_root / "examples" / "claude_session.jsonl"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_file = Path(f.name)
        
        try:
            exit_code, stdout, stderr = self.run_command([
                "session-convert", "claude-to-codex",
                str(claude_example), "-o", str(output_file)
            ])
            
            if exit_code != 0:
                return ValidationResult(
                    "Claude → Codex",
                    False,
                    f"Conversion failed with exit code {exit_code}",
                    stderr
                )
            
            # Verify output file exists and is valid
            if not output_file.exists():
                return ValidationResult(
                    "Claude → Codex",
                    False,
                    "Output file was not created"
                )
            
            # Check first line is session_meta
            with open(output_file) as f:
                first_line = f.readline()
                data = json.loads(first_line)
                
                if data.get('type') != 'session_meta':
                    return ValidationResult(
                        "Claude → Codex",
                        False,
                        f"First event should be session_meta, got {data.get('type')}"
                    )
            
            return ValidationResult(
                "Claude → Codex",
                True,
                "Conversion successful, output format correct"
            )
        
        finally:
            if output_file.exists():
                output_file.unlink()
    
    def test_codex_to_claude(self) -> ValidationResult:
        """Test Codex to Claude conversion."""
        codex_example = self.project_root / "examples" / "codex_session.jsonl"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            output_file = Path(f.name)
        
        try:
            exit_code, stdout, stderr = self.run_command([
                "session-convert", "codex-to-claude",
                str(codex_example), "-o", str(output_file)
            ])
            
            if exit_code != 0:
                return ValidationResult(
                    "Codex → Claude",
                    False,
                    f"Conversion failed with exit code {exit_code}",
                    stderr
                )
            
            # Verify output file exists and is valid
            if not output_file.exists():
                return ValidationResult(
                    "Codex → Claude",
                    False,
                    "Output file was not created"
                )
            
            # Check events have proper structure
            with open(output_file) as f:
                first_line = f.readline()
                data = json.loads(first_line)
                
                if 'uuid' not in data or 'sessionId' not in data:
                    return ValidationResult(
                        "Codex → Claude",
                        False,
                        "Output missing required Claude fields (uuid, sessionId)"
                    )
            
            return ValidationResult(
                "Codex → Claude",
                True,
                "Conversion successful, output format correct"
            )
        
        finally:
            if output_file.exists():
                output_file.unlink()
    
    def test_roundtrip_claude(self) -> ValidationResult:
        """Test round-trip: Claude → Codex → Claude."""
        claude_example = self.project_root / "examples" / "claude_session.jsonl"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f2:
            codex_temp = Path(f1.name)
            claude_temp = Path(f2.name)
        
        try:
            # Claude → Codex
            exit_code1, _, stderr1 = self.run_command([
                "session-convert", "claude-to-codex",
                str(claude_example), "-o", str(codex_temp)
            ])
            
            if exit_code1 != 0:
                return ValidationResult(
                    "Round-trip (Claude)",
                    False,
                    "First conversion (Claude→Codex) failed",
                    stderr1
                )
            
            # Codex → Claude
            exit_code2, _, stderr2 = self.run_command([
                "session-convert", "codex-to-claude",
                str(codex_temp), "-o", str(claude_temp)
            ])
            
            if exit_code2 != 0:
                return ValidationResult(
                    "Round-trip (Claude)",
                    False,
                    "Second conversion (Codex→Claude) failed",
                    stderr2
                )
            
            # Compare session info
            with open(claude_example) as f:
                original = [json.loads(line) for line in f if line.strip()]
            
            with open(claude_temp) as f:
                roundtrip = [json.loads(line) for line in f if line.strip()]
            
            # Check that session IDs match
            orig_session_id = original[0].get('sessionId')
            rt_session_id = roundtrip[0].get('sessionId')
            
            if orig_session_id != rt_session_id:
                return ValidationResult(
                    "Round-trip (Claude)",
                    False,
                    f"Session ID mismatch: {orig_session_id} != {rt_session_id}"
                )
            
            return ValidationResult(
                "Round-trip (Claude)",
                True,
                f"Round-trip successful, session ID preserved: {orig_session_id}"
            )
        
        finally:
            if codex_temp.exists():
                codex_temp.unlink()
            if claude_temp.exists():
                claude_temp.unlink()
    
    def test_roundtrip_codex(self) -> ValidationResult:
        """Test round-trip: Codex → Claude → Codex."""
        codex_example = self.project_root / "examples" / "codex_session.jsonl"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f2:
            claude_temp = Path(f1.name)
            codex_temp = Path(f2.name)
        
        try:
            # Codex → Claude
            exit_code1, _, stderr1 = self.run_command([
                "session-convert", "codex-to-claude",
                str(codex_example), "-o", str(claude_temp)
            ])
            
            if exit_code1 != 0:
                return ValidationResult(
                    "Round-trip (Codex)",
                    False,
                    "First conversion (Codex→Claude) failed",
                    stderr1
                )
            
            # Claude → Codex
            exit_code2, _, stderr2 = self.run_command([
                "session-convert", "claude-to-codex",
                str(claude_temp), "-o", str(codex_temp)
            ])
            
            if exit_code2 != 0:
                return ValidationResult(
                    "Round-trip (Codex)",
                    False,
                    "Second conversion (Claude→Codex) failed",
                    stderr2
                )
            
            # Compare session info
            with open(codex_example) as f:
                for line in f:
                    data = json.loads(line)
                    if data.get('type') == 'session_meta':
                        orig_session_id = data.get('payload', {}).get('id')
                        break
            
            with open(codex_temp) as f:
                for line in f:
                    data = json.loads(line)
                    if data.get('type') == 'session_meta':
                        rt_session_id = data.get('payload', {}).get('id')
                        break
            
            if orig_session_id != rt_session_id:
                return ValidationResult(
                    "Round-trip (Codex)",
                    False,
                    f"Session ID mismatch: {orig_session_id} != {rt_session_id}"
                )
            
            return ValidationResult(
                "Round-trip (Codex)",
                True,
                f"Round-trip successful, session ID preserved: {orig_session_id}"
            )
        
        finally:
            if claude_temp.exists():
                claude_temp.unlink()
            if codex_temp.exists():
                codex_temp.unlink()
    
    def run_all_tests(self) -> None:
        """Run all validation tests."""
        tests = [
            ("CLI Functionality", self.test_cli_help),
            ("Example Files", self.test_example_files_exist),
            ("Info Command", self.test_info_command),
            ("Validate Command", self.test_validate_command),
            ("Claude → Codex", self.test_claude_to_codex),
            ("Codex → Claude", self.test_codex_to_claude),
            ("Round-trip (Claude)", self.test_roundtrip_claude),
            ("Round-trip (Codex)", self.test_roundtrip_codex),
        ]
        
        console.print("\n[bold cyan]Running Session Converter Validation Tests[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running tests...", total=len(tests))
            
            for test_name, test_func in tests:
                progress.update(task, description=f"Testing: {test_name}")
                result = test_func()
                self.results.append(result)
                progress.advance(task)
        
        self.print_results()
    
    def print_results(self) -> None:
        """Print test results in a nice format."""
        # Summary table
        table = Table(title="Validation Results", show_header=True, header_style="bold magenta")
        table.add_column("Test", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Message", style="white")
        
        passed_count = 0
        failed_count = 0
        
        for result in self.results:
            if result.passed:
                status = "[green]✓ PASS[/green]"
                passed_count += 1
            else:
                status = "[red]✗ FAIL[/red]"
                failed_count += 1
            
            table.add_row(result.name, status, result.message)
        
        console.print("\n")
        console.print(table)
        
        # Summary panel
        total = passed_count + failed_count
        pass_rate = (passed_count / total * 100) if total > 0 else 0
        
        summary = f"""
[bold]Total Tests:[/bold] {total}
[green]Passed:[/green] {passed_count}
[red]Failed:[/red] {failed_count}
[cyan]Pass Rate:[/cyan] {pass_rate:.1f}%
"""
        
        panel_style = "green" if failed_count == 0 else "red"
        console.print(Panel(summary.strip(), title="Summary", border_style=panel_style))
        
        # Print details for failed tests
        if failed_count > 0:
            console.print("\n[bold red]Failed Test Details:[/bold red]\n")
            for result in self.results:
                if not result.passed and result.details:
                    console.print(f"[yellow]{result.name}:[/yellow]")
                    console.print(f"  {result.details}\n")
        
        # Exit with appropriate code
        sys.exit(0 if failed_count == 0 else 1)


def main():
    """Main entry point."""
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent.parent
    
    # Add the bin to PATH
    import os
    bin_path = os.path.expanduser("~/.local/bin")
    if bin_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{bin_path}:{os.environ.get('PATH', '')}"
    
    validator = SessionConverterValidator()
    validator.run_all_tests()


if __name__ == "__main__":
    main()
