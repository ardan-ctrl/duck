from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class ProviderSettings:
    asr_provider: str = "script_stub"
    hooks_provider: str = "rules_stub"
    render_provider: str = "preview_stub"

    openai_model: str = "gpt-4.1-mini"
    faster_whisper_model: str = "small"
    faster_whisper_device: str = "cpu"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b-instruct"

    remotion_entry: str = "remotion/index.ts"
    remotion_composition: str = "AutoCutMain"
    remotion_fps: int = 30
    remotion_width: int = 1080
    remotion_height: int = 1920

    @classmethod
    def from_env(cls) -> "ProviderSettings":
        return cls(
            asr_provider=os.getenv("AUTOCUT_ASR_PROVIDER", "script_stub"),
            hooks_provider=os.getenv("AUTOCUT_HOOKS_PROVIDER", "rules_stub"),
            render_provider=os.getenv("AUTOCUT_RENDER_PROVIDER", "preview_stub"),
            openai_model=os.getenv("AUTOCUT_OPENAI_MODEL", "gpt-4.1-mini"),
            faster_whisper_model=os.getenv("AUTOCUT_FASTER_WHISPER_MODEL", "small"),
            faster_whisper_device=os.getenv("AUTOCUT_FASTER_WHISPER_DEVICE", "cpu"),
            ollama_url=os.getenv("AUTOCUT_OLLAMA_URL", "http://127.0.0.1:11434"),
            ollama_model=os.getenv("AUTOCUT_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
            remotion_entry=os.getenv("AUTOCUT_REMOTION_ENTRY", "remotion/index.ts"),
            remotion_composition=os.getenv("AUTOCUT_REMOTION_COMPOSITION", "AutoCutMain"),
            remotion_fps=int(os.getenv("AUTOCUT_REMOTION_FPS", "30")),
            remotion_width=int(os.getenv("AUTOCUT_REMOTION_WIDTH", "1080")),
            remotion_height=int(os.getenv("AUTOCUT_REMOTION_HEIGHT", "1920")),
        )
