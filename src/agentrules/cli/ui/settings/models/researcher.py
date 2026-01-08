"""Researcher agent model configuration."""

from __future__ import annotations

import questionary

from agentrules.cli.context import CliContext
from agentrules.cli.services import configuration
from agentrules.cli.ui.styles import CLI_STYLE, navigation_choice
from agentrules.core.configuration import model_presets

from .utils import current_labels, fuzzy_select_model


def configure_researcher_phase(
    context: CliContext,
    presets: list[model_presets.PresetInfo],
    current_key: str | None,
    default_key: str | None,
    current_mode: str,
    tavily_available: bool,
    offline_mode: bool,
) -> bool:
    """Handle interactive configuration for the researcher agent."""

    console = context.console

    if not tavily_available and not offline_mode:
        console.print(
            "[yellow]Add a Tavily API key under Settings → Provider API keys to enable the researcher agent.[/]"
        )
        return False

    mode_choices = [
        questionary.Choice(
            title="On" + (" [current]" if current_mode == "on" else ""),
            value="on",
        ),
        questionary.Choice(
            title="Off" + (" [current]" if current_mode == "off" else ""),
            value="off",
        ),
        navigation_choice("Cancel", value="__CANCEL__"),
    ]

    mode_selection = questionary.select(
        "Researcher agent mode:",
        choices=mode_choices,
        default=current_mode,
        qmark="🔍",
        style=CLI_STYLE,
    ).ask()

    if mode_selection in (None, "__CANCEL__"):
        console.print("[yellow]Researcher configuration cancelled.[/]")
        return False

    desired_mode = mode_selection
    mode_changed = desired_mode != current_mode

    if desired_mode == "off":
        if mode_changed:
            configuration.save_researcher_mode("off")
            _render_mode_message(console.print, "off")
            return True
        console.print("[dim]Researcher agent already disabled.[/]")
        return False

    selection = fuzzy_select_model(
        presets,
        current_key,
        default_key,
        include_reset=True,
    )

    if selection is None:
        console.print("[yellow]Researcher configuration cancelled.[/]")
        return False

    if selection == "__RESET__":
        # If user explicitly picks "Reset", we clear the override.
        # But we also need to handle the case where they just wanted to toggle mode and kept the default.
        # Actually, fuzzy_select_model handles selection.
        # If selection is Reset, we reset.
        configuration.save_phase_model("researcher", None)
        console.print("[green]Researcher preset reset to default.[/]")
    else:
        # Check if they picked "Keep current" equivalent?
        # fuzzy_select_model doesn't have "Keep current". It has the list.
        # If they pick the one marked [current], it's effectively keeping it.
        # We just save it.
        configuration.save_phase_model("researcher", selection)
        preset_info = model_presets.get_preset_info(selection)
        if preset_info:
            console.print(
                f"[green]Researcher agent will use {preset_info.label} [{preset_info.provider_display}].[/]"
            )
        else:
            console.print("[green]Researcher preset updated.[/]")

    if mode_changed:
        configuration.save_researcher_mode(desired_mode)
        _render_mode_message(console.print, desired_mode)

    return True


def _render_mode_message(printer, mode: str) -> None:
    """Emit feedback after researcher mode changes."""

    if mode == "on":
        printer("[green]Researcher agent enabled.[/]")
    else:
        printer("[yellow]Researcher agent disabled for Phase 1.[/]")
