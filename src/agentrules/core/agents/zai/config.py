"""Model defaults and configuration helpers for the ZAI architect."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agentrules.core.agents.base import ReasoningMode

DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
API_BASE_ENV_VAR = "ZAI_API_BASE"


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
    """Return the default configuration bundle for the supplied ZAI model."""
    return _FALLBACK_DEFAULTS


def resolve_base_url(explicit_base_url: str | None) -> str:
    """
    Resolve the API base URL for ZAI requests.

    Preference order:
    1. Explicit base URL passed to the architect constructor.
    2. Environment variable ``ZAI_API_BASE``.
    3. Provider default ``https://open.bigmodel.cn/api/paas/v4``.
    """
    if explicit_base_url:
        return explicit_base_url
    env_base = os.environ.get(API_BASE_ENV_VAR)
    if env_base:
        return env_base
    return DEFAULT_BASE_URL
