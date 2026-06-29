"""Embedded mini-brain runtime backed by a bundled GGUF model."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cli.aikit.identity import identity_system_prompt
from cli.aikit.runtime_paths import ROOT


EMBEDDED_BACKEND_ID = "embedded-mini-brain"
EMBEDDED_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
EMBEDDED_MODEL_NAME = "qwen2.5-0.5b-instruct"
EMBEDDED_MODEL_PATH = ROOT / "models" / EMBEDDED_MODEL_NAME
EMBEDDED_MANIFEST_PATH = EMBEDDED_MODEL_PATH / "manifest.json"
EMBEDDED_MODEL_FILE = EMBEDDED_MODEL_PATH / "qwen2.5-0.5b-instruct-q2_k.gguf"
EMBEDDED_MODEL_SHA256 = "9ee36184e616dfc76df4f5dd66f908dbde6979524ae36e6cefb67f532f798cb8"
EMBEDDED_RUNTIME = "llama-cpp-python"
EMBEDDED_MAX_RESPONSE_CHARS = 2000
DEFAULT_MAX_TOKENS = 220
DEFAULT_CONTEXT_TOKENS = 2048

_LLAMA_CACHE: Any | None = None


def embedded_mini_brain_status() -> dict[str, Any]:
    manifest_exists = EMBEDDED_MANIFEST_PATH.exists()
    model_exists = EMBEDDED_MODEL_FILE.exists()
    dependency = llama_cpp_dependency_status()
    available = model_exists and dependency["status"] == "ok"
    return {
        "kind": "embedded-mini-brain",
        "id": EMBEDDED_BACKEND_ID,
        "status": "ok" if available else "missing",
        "available": available,
        "configured": model_exists,
        "provider": EMBEDDED_BACKEND_ID,
        "runtime": EMBEDDED_RUNTIME,
        "model": EMBEDDED_MODEL_ID,
        "hf_model": EMBEDDED_MODEL_ID,
        "model_name": EMBEDDED_MODEL_NAME,
        "model_path": str(EMBEDDED_MODEL_PATH),
        "model_file": str(EMBEDDED_MODEL_FILE),
        "model_file_present": model_exists,
        "sha256": EMBEDDED_MODEL_SHA256,
        "manifest_path": str(EMBEDDED_MANIFEST_PATH),
        "manifest_present": manifest_exists,
        "dependency": dependency,
        "auth": "none",
        "stored_secret": False,
        "message": (
            "Embedded Qwen2.5 mini-brain is available for real local inference."
            if available
            else "Embedded mini-brain model or llama_cpp runtime is missing."
        ),
    }


def invoke_embedded_mini_brain(prompt: str, *, public_name: str = "Agent DevKit") -> str:
    status = embedded_mini_brain_status()
    if not status["available"]:
        raise EmbeddedMiniBrainError(status["message"])
    llama = load_llama()
    payload = llama.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": embedded_system_prompt(public_name),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=int(os.environ.get("AGENT_DEVKIT_EMBEDDED_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))),
        temperature=float(os.environ.get("AGENT_DEVKIT_EMBEDDED_TEMPERATURE", "0.2")),
        top_p=float(os.environ.get("AGENT_DEVKIT_EMBEDDED_TOP_P", "0.9")),
        repeat_penalty=float(os.environ.get("AGENT_DEVKIT_EMBEDDED_REPEAT_PENALTY", "1.08")),
    )
    try:
        content = str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise EmbeddedMiniBrainError("Embedded mini-brain returned an unexpected response shape.") from exc
    if not content:
        raise EmbeddedMiniBrainError("Embedded mini-brain returned an empty response.")
    return content[:EMBEDDED_MAX_RESPONSE_CHARS]


def embedded_backend_doctor() -> dict[str, Any]:
    status = embedded_mini_brain_status()
    return {
        "id": EMBEDDED_BACKEND_ID,
        "display_name": "Embedded mini-brain",
        "kind": "embedded-local",
        "status": status["status"],
        "configured": status["configured"],
        "model": EMBEDDED_MODEL_ID,
        "model_file": status["model_file"],
        "runtime": EMBEDDED_RUNTIME,
        "auth_status": "none",
        "message": status["message"],
    }


def embedded_backend_config() -> dict[str, Any]:
    return {
        "kind": "embedded-local",
        "auth": "none",
        "model": EMBEDDED_MODEL_ID,
        "runtime": EMBEDDED_RUNTIME,
    }


def embedded_system_prompt(public_name: str) -> str:
    return "\n".join(
        [
            identity_system_prompt(name=public_name),
            "Voce e o mini cerebro local embarcado do Agent DevKit.",
            "Responda em portugues claro quando o usuario escrever em portugues.",
            "Voce pode conversar, orientar onboarding/setup, explicar capacidades e preparar tarefas simples.",
            "Nao finja ser Claude, Codex, OpenAI ou Ollama.",
            "Nao aprove escrita externa, operacoes destrutivas, decisoes finais de seguranca ou revisoes finais.",
            "Quando a tarefa exigir alto julgamento, diga que pode acionar Claude, Codex, Ollama ou APIs se configurados.",
        ]
    )


def load_llama() -> Any:
    global _LLAMA_CACHE
    if _LLAMA_CACHE is not None:
        return _LLAMA_CACHE
    try:
        from llama_cpp import Llama  # type: ignore
    except ImportError as exc:
        raise EmbeddedMiniBrainError("llama-cpp-python is required for embedded mini-brain inference.") from exc
    if not EMBEDDED_MODEL_FILE.exists():
        raise EmbeddedMiniBrainError(f"Embedded model file not found: {EMBEDDED_MODEL_FILE}")
    _LLAMA_CACHE = Llama(
        model_path=str(EMBEDDED_MODEL_FILE),
        n_ctx=int(os.environ.get("AGENT_DEVKIT_EMBEDDED_N_CTX", str(DEFAULT_CONTEXT_TOKENS))),
        n_threads=int(os.environ.get("AGENT_DEVKIT_EMBEDDED_THREADS", str(max(1, min(4, os.cpu_count() or 1))))),
        verbose=os.environ.get("AGENT_DEVKIT_EMBEDDED_VERBOSE") == "1",
    )
    return _LLAMA_CACHE


def llama_cpp_dependency_status() -> dict[str, Any]:
    try:
        import llama_cpp  # type: ignore
    except ImportError:
        return {
            "status": "missing",
            "module": "llama_cpp",
            "package": "llama-cpp-python",
        }
    return {
        "status": "ok",
        "module": "llama_cpp",
        "package": "llama-cpp-python",
        "version": getattr(llama_cpp, "__version__", None),
    }


class EmbeddedMiniBrainError(RuntimeError):
    """Raised when embedded local inference cannot run."""
