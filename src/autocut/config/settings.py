from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ProviderSettings:
    asr_provider: str = "script_stub"
    hooks_provider: str = "rules_stub"
    render_provider: str = "preview_stub"
    openai_model: str = "gpt-4.1-mini"

    @classmethod
    def from_env(cls) -> "ProviderSettings":
        return cls(
            asr_provider=os.getenv("AUTOCUT_ASR_PROVIDER", "script_stub"),
            hooks_provider=os.getenv("AUTOCUT_HOOKS_PROVIDER", "rules_stub"),
            render_provider=os.getenv("AUTOCUT_RENDER_PROVIDER", "preview_stub"),
            openai_model=os.getenv("AUTOCUT_OPENAI_MODEL", "gpt-4.1-mini"),
        )
