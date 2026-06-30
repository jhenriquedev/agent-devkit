"""Embedded mini-brain runtime backed by an on-demand GGUF model."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from cli.aikit.app_home import app_path, ensure_app_home
from cli.aikit.identity import identity_system_prompt
from cli.aikit.runtime_paths import ROOT


EMBEDDED_BACKEND_ID = "embedded-mini-brain"
EMBEDDED_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
EMBEDDED_MODEL_NAME = "qwen2.5-0.5b-instruct"
EMBEDDED_MODEL_SOURCE = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q2_k.gguf"
EMBEDDED_MODEL_SIZE_BYTES = 415182688
EMBEDDED_MODEL_PATH = app_path("models", EMBEDDED_MODEL_NAME)
EMBEDDED_MANIFEST_PATH = ROOT / "models" / EMBEDDED_MODEL_NAME / "manifest.json"
EMBEDDED_MODEL_FILE = EMBEDDED_MODEL_PATH / "qwen2.5-0.5b-instruct-q2_k.gguf"
EMBEDDED_MODEL_SHA256 = "9ee36184e616dfc76df4f5dd66f908dbde6979524ae36e6cefb67f532f798cb8"
EMBEDDED_RUNTIME = "llama-cpp-python"
EMBEDDED_RUNTIME_REQUIREMENT = "llama-cpp-python>=0.3.9"
EMBEDDED_MAX_RESPONSE_CHARS = 2000
DEFAULT_MAX_TOKENS = 220
DEFAULT_CONTEXT_TOKENS = 2048
SMOKE_RESPONSE_ENV = "AGENT_DEVKIT_EMBEDDED_SMOKE_RESPONSE"
SOURCE_ENV = "AGENT_DEVKIT_EMBEDDED_MODEL_SOURCE"
SKIP_DEP_INSTALL_ENV = "AGENT_DEVKIT_EMBEDDED_SKIP_DEP_INSTALL"

_LLAMA_CACHE: Any | None = None


def embedded_mini_brain_status() -> dict[str, Any]:
    manifest_exists = EMBEDDED_MANIFEST_PATH.exists()
    model_exists = EMBEDDED_MODEL_FILE.exists()
    model_sha256 = sha256_file(EMBEDDED_MODEL_FILE) if model_exists else None
    smoke_mode = bool(os.environ.get(SMOKE_RESPONSE_ENV))
    model_file_valid = smoke_mode or (model_sha256 == EMBEDDED_MODEL_SHA256 if model_exists else False)
    dependency = llama_cpp_dependency_status()
    available = model_file_valid and dependency["status"] == "ok"
    if available:
        status = "ok"
    elif not model_exists:
        status = "not-installed"
    elif not model_file_valid:
        status = "invalid-model"
    elif dependency["status"] != "ok":
        status = "dependency-missing"
    else:
        status = "missing"
    return {
        "kind": "embedded-mini-brain",
        "id": EMBEDDED_BACKEND_ID,
        "status": status,
        "available": available,
        "configured": model_file_valid,
        "provider": EMBEDDED_BACKEND_ID,
        "runtime": EMBEDDED_RUNTIME,
        "runtime_requirement": EMBEDDED_RUNTIME_REQUIREMENT,
        "model": EMBEDDED_MODEL_ID,
        "hf_model": EMBEDDED_MODEL_ID,
        "model_name": EMBEDDED_MODEL_NAME,
        "model_path": str(EMBEDDED_MODEL_PATH),
        "model_file": str(EMBEDDED_MODEL_FILE),
        "model_file_present": model_exists,
        "model_file_valid": model_file_valid,
        "model_file_sha256": model_sha256,
        "smoke_mode": smoke_mode,
        "model_size_bytes": EMBEDDED_MODEL_SIZE_BYTES,
        "download_url": model_source(),
        "sha256": EMBEDDED_MODEL_SHA256,
        "manifest_path": str(EMBEDDED_MANIFEST_PATH),
        "manifest_present": manifest_exists,
        "dependency": dependency,
        "auth": "none",
        "stored_secret": False,
        "install_command": "agent setup mini-brain --yes",
        "message": (
            "Embedded Qwen2.5 mini-brain is available for real local inference."
            if available
            else "Embedded mini-brain model is not installed or llama_cpp runtime is missing."
        ),
    }


def invoke_embedded_mini_brain(prompt: str, *, public_name: str = "Agent DevKit") -> str:
    status = embedded_mini_brain_status()
    if not status["available"]:
        raise EmbeddedMiniBrainError(status["message"])
    smoke_response = os.environ.get(SMOKE_RESPONSE_ENV)
    if smoke_response:
        return f"{public_name}: {smoke_response}"[:EMBEDDED_MAX_RESPONSE_CHARS]
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
        "model_file": str(EMBEDDED_MODEL_FILE),
    }


def setup_embedded_mini_brain(*, dry_run: bool = False, yes: bool = False) -> dict[str, Any]:
    before = embedded_mini_brain_status()
    plan = embedded_install_plan()
    if dry_run or not yes:
        needs_confirmation = not dry_run and not yes
        return {
            "kind": "embedded-mini-brain-install",
            "status": "planned" if dry_run else "needs-confirmation",
            "ok": bool(dry_run),
            "exit_code": 2 if needs_confirmation else 0,
            "dry_run": dry_run,
            "yes": yes,
            "before": before,
            "after": before,
            "plan": plan,
            "message": "Use --yes to download the embedded mini-brain model and install its local runtime.",
        }

    ensure_app_home()
    EMBEDDED_MODEL_PATH.mkdir(parents=True, exist_ok=True)
    download_result = ensure_model_file()
    dependency_result = ensure_llama_cpp_dependency()
    after = embedded_mini_brain_status()
    ok = after.get("available") is True
    return {
        "kind": "embedded-mini-brain-install",
        "status": "ok" if ok else "failed",
        "ok": ok,
        "exit_code": 0 if ok else 1,
        "dry_run": False,
        "yes": True,
        "before": before,
        "after": after,
        "plan": plan,
        "download": download_result,
        "dependency_install": dependency_result,
    }


def embedded_install_plan() -> dict[str, Any]:
    return {
        "provider": EMBEDDED_BACKEND_ID,
        "model": EMBEDDED_MODEL_ID,
        "model_name": EMBEDDED_MODEL_NAME,
        "download_url": model_source(),
        "size_bytes": EMBEDDED_MODEL_SIZE_BYTES,
        "sha256": EMBEDDED_MODEL_SHA256,
        "destination": str(EMBEDDED_MODEL_FILE),
        "runtime_requirement": EMBEDDED_RUNTIME_REQUIREMENT,
        "writes": [
            str(EMBEDDED_MODEL_FILE),
            str(app_path("python")),
        ],
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
    if sha256_file(EMBEDDED_MODEL_FILE) != EMBEDDED_MODEL_SHA256:
        raise EmbeddedMiniBrainError(f"Embedded model file failed SHA-256 validation: {EMBEDDED_MODEL_FILE}")
    _LLAMA_CACHE = Llama(
        model_path=str(EMBEDDED_MODEL_FILE),
        n_ctx=int(os.environ.get("AGENT_DEVKIT_EMBEDDED_N_CTX", str(DEFAULT_CONTEXT_TOKENS))),
        n_threads=int(os.environ.get("AGENT_DEVKIT_EMBEDDED_THREADS", str(max(1, min(4, os.cpu_count() or 1))))),
        verbose=os.environ.get("AGENT_DEVKIT_EMBEDDED_VERBOSE") == "1",
    )
    return _LLAMA_CACHE


def llama_cpp_dependency_status() -> dict[str, Any]:
    if os.environ.get(SMOKE_RESPONSE_ENV):
        return {
            "status": "ok",
            "module": "llama_cpp",
            "package": "llama-cpp-python",
            "mode": "smoke",
        }
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


def ensure_model_file() -> dict[str, Any]:
    if os.environ.get(SMOKE_RESPONSE_ENV):
        return {
            "status": "skipped",
            "ok": True,
            "model_file": str(EMBEDDED_MODEL_FILE),
            "reason": "smoke-mode",
        }
    if EMBEDDED_MODEL_FILE.exists() and sha256_file(EMBEDDED_MODEL_FILE) == EMBEDDED_MODEL_SHA256:
        return {
            "status": "already-installed",
            "ok": True,
            "model_file": str(EMBEDDED_MODEL_FILE),
            "sha256": EMBEDDED_MODEL_SHA256,
        }
    partial = EMBEDDED_MODEL_FILE.with_suffix(EMBEDDED_MODEL_FILE.suffix + ".part")
    source = model_source()
    try:
        if Path(source).expanduser().exists():
            shutil.copyfile(Path(source).expanduser(), partial)
        else:
            with urllib.request.urlopen(source, timeout=120) as response, partial.open("wb") as target:
                shutil.copyfileobj(response, target)
    except (OSError, urllib.error.URLError) as exc:
        return {
            "status": "failed",
            "ok": False,
            "model_file": str(EMBEDDED_MODEL_FILE),
            "source": source,
            "message": str(exc),
        }
    actual_sha = sha256_file(partial)
    if actual_sha != EMBEDDED_MODEL_SHA256:
        return {
            "status": "failed",
            "ok": False,
            "model_file": str(EMBEDDED_MODEL_FILE),
            "source": source,
            "sha256": actual_sha,
            "expected_sha256": EMBEDDED_MODEL_SHA256,
            "message": "Downloaded embedded model failed SHA-256 validation.",
        }
    partial.replace(EMBEDDED_MODEL_FILE)
    return {
        "status": "downloaded",
        "ok": True,
        "model_file": str(EMBEDDED_MODEL_FILE),
        "source": source,
        "sha256": EMBEDDED_MODEL_SHA256,
    }


def ensure_llama_cpp_dependency() -> dict[str, Any]:
    current = llama_cpp_dependency_status()
    if current.get("status") == "ok":
        return {"status": "already-installed", "ok": True, "dependency": current}
    if os.environ.get(SKIP_DEP_INSTALL_ENV) == "1":
        return {"status": "skipped", "ok": True, "dependency": current, "reason": "disabled-by-env"}
    command = [sys.executable, "-m", "pip", "install", EMBEDDED_RUNTIME_REQUIREMENT]
    process = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
    return {
        "status": "installed" if process.returncode == 0 else "failed",
        "ok": process.returncode == 0,
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-4000:],
        "stderr": process.stderr[-4000:],
    }


def model_source() -> str:
    return os.environ.get(SOURCE_ENV) or EMBEDDED_MODEL_SOURCE


def sha256_file(path: Path) -> str:
    hash_obj = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


class EmbeddedMiniBrainError(RuntimeError):
    """Raised when embedded local inference cannot run."""
