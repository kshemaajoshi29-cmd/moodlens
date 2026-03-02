from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="moodlens",
    help="AI-powered photo mood enhancement — colour grading via Claude + Pillow",
    add_completion=False,
)
console = Console()


@app.command()
def enhance(
    image_path: Path = typer.Argument(..., help="Path to the input image file"),
    mood: str = typer.Option(..., "--mood", "-m", help="Preset name or free-text mood description"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file path (defaults to <name>_moodlens.<fmt>)"
    ),
    intensity: float = typer.Option(
        1.0, "--intensity", "-i", min=0.0, max=1.0,
        help="Effect intensity (0 = no change, 1 = full effect)",
    ),
) -> None:
    """Enhance a photo's mood via colour grading. Faces and composition are never changed."""
    from ..config import Settings
    from ..presets import PRESETS
    from ..services.image_enhancer import ImageEnhancer
    from ..services.mood_interpreter import MoodInterpreter

    if not image_path.exists():
        console.print(f"[red]Error:[/red] File not found: {image_path}")
        raise typer.Exit(1)

    settings = Settings()
    image_bytes = image_path.read_bytes()

    mood_key = mood.lower().strip()
    if mood_key in PRESETS:
        adjustments = PRESETS[mood_key]
        console.print(f"Using preset [bold cyan]{mood_key}[/bold cyan] — {adjustments.style_notes}")
    else:
        console.print(f"Interpreting mood with Claude: [italic]{mood}[/italic]")
        interpreter = MoodInterpreter(settings)
        adjustments = interpreter.interpret(mood)
        console.print(f"Style: {adjustments.style_notes}")

    console.print(f"Applying colour grade (intensity={intensity:.2f}) …")

    enhancer = ImageEnhancer()
    enhanced_bytes = enhancer.enhance(
        image_bytes=image_bytes,
        adjustments=adjustments,
        intensity=intensity,
        output_format=settings.output_format,
    )

    if output is None:
        output = image_path.parent / f"{image_path.stem}_moodlens.{settings.output_format}"

    output.write_bytes(enhanced_bytes)
    size_kb = len(enhanced_bytes) / 1024
    console.print(f"[green]✓ Saved:[/green] {output} ({size_kb:.1f} KB)")


@app.command(name="list-presets")
def list_presets() -> None:
    """List all available preset moods."""
    from ..presets import PRESETS

    table = Table(title="MoodLens Presets", show_lines=True)
    table.add_column("Name", style="bold cyan", no_wrap=True)
    table.add_column("Style", style="green")
    table.add_column("Temp", style="yellow", justify="center")
    table.add_column("Sat", style="yellow", justify="center")
    table.add_column("Contrast", style="yellow", justify="center")

    for name, adj in PRESETS.items():
        table.add_row(
            name,
            adj.style_notes,
            f"{adj.temperature:+.2f}",
            f"{adj.saturation:.2f}",
            f"{adj.contrast:.2f}",
        )

    console.print(table)
    console.print("\nUsage: [cyan]moodlens enhance photo.jpg --mood vintage[/cyan]")
