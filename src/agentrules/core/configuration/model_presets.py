"""Helpers for mapping user configuration to model presets."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from agentrules.config import agents as agent_settings
from agentrules.config.agents import PresetDefinition
from agentrules.core.agents.base import ModelProvider

from . import get_config_manager
from .constants import PROVIDER_ENV_MAP

PHASE_TITLES: dict[str, str] = {
    "phase1": "Phase 1 – Initial Discovery",
    "phase2": "Phase 2 – Methodical Planning",
    "phase3": "Phase 3 – Deep Analysis",
    "phase4": "Phase 4 – Synthesis",
    "phase5": "Phase 5 – Consolidation",
    "final": "Final Analysis",
    "researcher": "Researcher Agent",
}

PHASE_SEQUENCE: list[str] = list(agent_settings.MODEL_PRESET_DEFAULTS.keys())


@dataclass(frozen=True)
class PresetInfo:
    key: str
    label: str
    description: str
    provider: ModelProvider

    @property
    def provider_slug(self) -> str:
        return self.provider.value

    @property
    def provider_display(self) -> str:
        return _provider_display_name(self.provider)


def _build_preset_infos(
    presets: Iterable[tuple[str, PresetDefinition]],
) -> dict[str, PresetInfo]:
    info_map: dict[str, PresetInfo] = {}
    for key, meta in presets:
        info_map[key] = PresetInfo(
            key=key,
            label=meta["label"],
            description=meta["description"],
            provider=meta["provider"],
        )
    return info_map


PRESET_INFOS: dict[str, PresetInfo] = _build_preset_infos(agent_settings.MODEL_PRESETS.items())

CONFIG_MANAGER = get_config_manager()


def get_phase_title(phase: str) -> str:
    return PHASE_TITLES.get(phase, phase.title())


def get_default_preset_key(phase: str) -> str | None:
    return agent_settings.MODEL_PRESET_DEFAULTS.get(phase)


def get_preset_info(key: str) -> PresetInfo | None:
    return PRESET_INFOS.get(key)


def get_available_presets_for_phase(
    phase: str,
    provider_keys: Mapping[str, str | None] | None = None,
) -> list[PresetInfo]:
    provider_keys = provider_keys or CONFIG_MANAGER.get_current_provider_keys()
    default_key = get_default_preset_key(phase)
    available: list[PresetInfo] = []

    for key, info in PRESET_INFOS.items():
        if key != default_key and not _provider_available(info.provider_slug, provider_keys):
            continue
        available.append(info)

    # Ensure default preset is present even if no keys are configured yet
    if default_key and not any(p.key == default_key for p in available):
        info = get_preset_info(default_key)
        if info:
            available.insert(0, info)

    return available


def get_active_presets(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    overrides = overrides or CONFIG_MANAGER.get_model_overrides()
    global_default = overrides.get("default")
    
    active: dict[str, str] = {}
    
    # Include the global default setting itself so the UI knows about it
    if global_default:
        active["default"] = global_default

    for phase in PHASE_SEQUENCE:
        override = overrides.get(phase)
        if override is not None:
            active[phase] = override
            continue
        
        # Fallback to global user default
        if global_default:
            active[phase] = global_default
            continue

        default_key = get_default_preset_key(phase)
        if default_key is not None:
            active[phase] = default_key
    return active


def apply_user_overrides(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    """
    Apply user-selected model presets to the global MODEL_CONFIG.
    Returns the applied preset mapping for further inspection.
    """
    overrides = overrides or CONFIG_MANAGER.get_model_overrides()
    global_default = overrides.get("default")
    
    applied: dict[str, str] = {}

    # reset to defaults first
    for phase, preset_key in agent_settings.MODEL_PRESET_DEFAULTS.items():
        # Determine effective key
        effective_key = overrides.get(phase)
        if effective_key is None:
            effective_key = global_default or preset_key
            
        preset_def = agent_settings.MODEL_PRESETS.get(effective_key)
        if preset_def:
            agent_settings.MODEL_CONFIG[phase] = preset_def["config"]
            applied[phase] = effective_key
        else:
            # Fallback if key is invalid (e.g. plugin removed)
            default_def = agent_settings.MODEL_PRESETS.get(preset_key)
            if default_def:
                agent_settings.MODEL_CONFIG[phase] = default_def["config"]
                applied[phase] = preset_key

    return applied


def _provider_available(provider_slug: str, provider_keys: Mapping[str, str | None]) -> bool:
    # first check persisted keys
    if provider_keys.get(provider_slug):
        return True

    env_var = PROVIDER_ENV_MAP.get(provider_slug)
    if env_var and os.getenv(env_var):
        return True

    return False


def _provider_display_name(provider: ModelProvider) -> str:
    mapping = {
        ModelProvider.OPENAI: "OpenAI",
        ModelProvider.ANTHROPIC: "Anthropic",
        ModelProvider.GEMINI: "Google Gemini",
        ModelProvider.DEEPSEEK: "DeepSeek",
        ModelProvider.XAI: "xAI Grok",
        ModelProvider.OPENROUTER: "OpenRouter",
        ModelProvider.ZAI: "Zhipu AI (GLM)",
    }
    return mapping.get(provider, provider.value.title())
