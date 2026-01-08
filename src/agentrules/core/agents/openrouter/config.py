"""Model defaults and configuration helpers for the OpenRouter architect."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agentrules.core.agents.base import ReasoningMode

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
API_BASE_ENV_VAR = "OPENROUTER_API_BASE"


@dataclass(frozen=True)
class ModelDefaults:
    """Provider-specific defaults applied when initialising an architect."""

    default_reasoning: ReasoningMode
    max_output_tokens: int | None = None
    tools_allowed: bool = True


_FALLBACK_DEFAULTS = ModelDefaults(
    default_reasoning=ReasoningMode.DISABLED,
    tools_allowed=True,
)


def resolve_model_defaults(model_name: str) -> ModelDefaults:
    """Return the default configuration bundle for the supplied OpenRouter model."""
    # OpenRouter has too many models to map individually.
    # We rely on fallback defaults for now.
    return _FALLBACK_DEFAULTS


def resolve_base_url(explicit_base_url: str | None) -> str:
    """
    Resolve the API base URL for OpenRouter requests.

    Preference order:
    1. Explicit base URL passed to the architect constructor.
    2. Environment variable ``OPENROUTER_API_BASE``.
    3. Provider default ``https://openrouter.ai/api/v1``.
    """
    if explicit_base_url:
        return explicit_base_url
    env_base = os.environ.get(API_BASE_ENV_VAR)
    if env_base:
        return env_base
    return DEFAULT_BASE_URL
