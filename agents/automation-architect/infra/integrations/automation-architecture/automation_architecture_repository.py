"""Repository for deterministic automation architecture decisions."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml


AUTOMATION_TYPES = {"python", "playwright", "selenium", "pyautogui", "lambda", "docker", "scheduler", "manual"}
FORBIDDEN_MARKER_PATTERN = re.compile(r"\b(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)\b\s*[:=]", re.IGNORECASE)

DELEGATES: dict[str, dict[str, Any]] = {
    "python": {
        "agent_id": "python-automation-builder",
        "capability_id": "plan-python-automation",
        "write_policy": "read_only",
        "available": True,
    },
    "selenium": {
        "agent_id": "selenium-automation-builder",
        "capability_id": "plan-selenium-automation",
        "write_policy": "read_only",
        "available": True,
    },
    "pyautogui": {
        "agent_id": "pyautogui-automation-builder",
        "capability_id": "plan-desktop-automation",
        "write_policy": "read_only",
        "available": True,
    },
    "lambda": {
        "agent_id": "aws-lambda-builder",
        "capability_id": "plan-lambda",
        "write_policy": "read_only",
        "available": True,
    },
    "docker": {
        "agent_id": "docker-container-builder",
        "capability_id": "analyze-containerization-target",
        "write_policy": "read_only",
        "available": True,
    },
    "scheduler": {
        "agent_id": "execution-loop-builder",
        "capability_id": "plan-execution-loop",
        "write_policy": "read_only",
        "available": True,
    },
    "playwright": {
        "agent_id": "playwright-automation-builder",
        "capability_id": "plan-playwright-automation",
        "write_policy": "read_only",
        "available": True,
    },
    "manual": {
        "agent_id": None,
        "capability_id": None,
        "write_policy": "read_only",
        "available": False,
        "blocked_reason": "needs-human-runbook-or-more-context",
    },
}

SIGNALS: dict[str, set[str]] = {
    "api": {"api", "rest", "graphql", "endpoint", "webhook", "http", "requests"},
    "file": {"arquivo", "arquivos", "csv", "json", "xlsx", "planilha", "relatorio", "pasta", "log"},
    "python": {"python", "script", "requests", "pandas", "csv", "arquivo", "arquivos", "local"},
    "web": {"web", "site", "browser", "navegador", "pagina", "formulario", "login"},
    "selenium": {"selenium", "webdriver", "grid", "selenium-grid", "legacy-browser"},
    "playwright": {"playwright"},
    "desktop": {"desktop", "janela", "clique", "clicar", "teclado", "mouse", "screenshot", "tela", "pyautogui"},
    "lambda": {"lambda", "serverless", "eventbridge", "s3", "cloudwatch", "aws", "evento", "event-driven"},
    "docker": {"docker", "dockerfile", "compose", "container", "containerizar", "imagem", "build"},
    "scheduler": {"agenda", "agendado", "agendar", "cron", "periodico", "diario", "retry", "loop", "repetir", "recorrente"},
    "external_write": {"postar", "enviar", "atualizar", "deletar", "apagar", "criar", "alterar", "write", "delete", "deploy"},
    "destructive": {"deletar", "apagar", "remover", "drop", "truncate", "destrutivo"},
}


class AutomationArchitectureError(RuntimeError):
    """Raised when the automation architect cannot read input."""


class AutomationArchitectureRepository:
    def classify_automation_request(self, *, request: str | None = None, spec_path: Path | None = None) -> dict[str, Any]:
        loaded = self.load_request(request=request, spec_path=spec_path)
        if loaded["status"] != "ok":
            return loaded

        text = loaded["text"]
        normalized = normalize(text)
        scores = self.score_types(normalized)
        automation_type, score = self.choose_type(scores, normalized)
        evidence = self.evidence(normalized)
        confidence = self.confidence_label(score, evidence, automation_type)
        delegate = DELEGATES[automation_type]
        risks = self.risks_for(automation_type, confidence, evidence, text, delegate)
        questions = self.questions_for(automation_type, confidence, evidence)
        requires_confirmation = confidence == "low" or bool({"external_write", "destructive"} & set(evidence)) or automation_type == "pyautogui"

        return {
            "kind": "automation-classification",
            "status": "needs-input" if confidence == "low" else "ok",
            "automation_type": automation_type,
            "confidence": confidence,
            "score": score,
            "reason": self.reason_for(automation_type, evidence, delegate),
            "evidence": evidence,
            "risks": risks,
            "questions": questions,
            "requires_confirmation": requires_confirmation,
            "recommended_agent": delegate.get("agent_id"),
            "recommended_capability": delegate.get("capability_id"),
            "available_delegate": bool(delegate.get("available")),
            "delegation": self.public_delegate(automation_type),
            "alternatives": self.alternatives_for(automation_type, evidence),
            "write_policy": "read_only",
        }

    def plan_automation_solution(self, *, request: str | None = None, spec_path: Path | None = None) -> dict[str, Any]:
        classification = self.classify_automation_request(request=request, spec_path=spec_path)
        if classification.get("kind") != "automation-classification":
            return classification
        if not classification.get("automation_type"):
            return classification

        return {
            "kind": "automation-solution-plan",
            "status": classification["status"],
            "classification": classification,
            "contract": {
                "inputs": self.contract_inputs(classification),
                "outputs": self.contract_outputs(classification),
                "side_effects": self.side_effects(classification),
                "execution_mode": self.execution_mode(classification),
            },
            "guardrails": self.guardrails_for(classification),
            "delegation": self.delegation_contract(classification),
            "next_steps": self.next_steps_for(classification),
            "write_policy": "read_only",
        }

    def delegate_automation_build(self, *, request: str | None = None, spec_path: Path | None = None) -> dict[str, Any]:
        plan = self.plan_automation_solution(request=request, spec_path=spec_path)
        if plan.get("kind") != "automation-solution-plan":
            return plan
        classification = plan["classification"]
        delegation = plan["delegation"]
        return {
            "kind": "automation-delegation",
            "status": "ok" if delegation.get("available") and classification.get("confidence") != "low" else "needs-input",
            "manual_only": True,
            "reason": "Delegacao automatica nao e executada nesta fase; o contrato abaixo deve ser usado pelo operador ou runtime futuro.",
            "classification": classification,
            "delegation": delegation,
            "required_confirmation": classification.get("requires_confirmation"),
            "questions": classification.get("questions", []),
            "write_policy": "delegated",
        }

    def review_automation_solution(
        self,
        *,
        request: str | None = None,
        spec_path: Path | None = None,
        solution: str | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_automation_solution(request=request, spec_path=spec_path)
        if plan.get("kind") != "automation-solution-plan":
            return plan

        solution_text = solution or ""
        normalized_solution = normalize(solution_text)
        findings = list(plan["classification"].get("risks", []))
        if FORBIDDEN_MARKER_PATTERN.search(solution_text):
            findings.append("solution appears to contain a hardcoded secret marker")
        if "pyautogui" in normalized_solution and "ultimo recurso" not in normalized_solution and "last resort" not in normalized_solution:
            findings.append("PyAutoGUI usage must justify why API, CLI, browser automation or native automation cannot be used")
        if ("selenium" in normalized_solution or "pyautogui" in normalized_solution) and "api" in plan["classification"].get("evidence", []):
            findings.append("visual/browser automation should not replace an available API without justification")
        if "execute" in normalized_solution and "--dry-run" not in normalized_solution and "dry-run" not in normalized_solution:
            findings.append("automation execution should expose dry-run before real side effects")

        valid = not findings or all("low confidence" in finding for finding in findings)
        return {
            "kind": "automation-review",
            "status": "ok" if valid else "failed",
            "valid": valid,
            "classification": plan["classification"],
            "findings": findings,
            "required_confirmation": plan["classification"].get("requires_confirmation"),
            "write_policy": "read_only",
        }

    def load_request(self, *, request: str | None, spec_path: Path | None) -> dict[str, Any]:
        parts: list[str] = []
        if request and request.strip():
            parts.append(request.strip())
        if spec_path:
            if not spec_path.exists():
                raise AutomationArchitectureError(f"spec not found: {spec_path}")
            parts.append(self.spec_text(spec_path))
        if not parts:
            return {
                "kind": "automation-classification",
                "status": "needs-input",
                "missing_fields": ["request"],
                "questions": ["Qual tarefa deve ser automatizada e em qual sistema/ambiente?"],
                "write_policy": "read_only",
            }
        return {"status": "ok", "text": "\n".join(parts)}

    def spec_text(self, path: Path) -> str:
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw) or {}
        if isinstance(data, dict):
            return " ".join(flatten_mapping(data))
        if isinstance(data, list):
            return " ".join(str(item) for item in data)
        return str(data)

    def score_types(self, normalized: str) -> dict[str, int]:
        evidence = set(self.evidence(normalized))
        scores = {automation_type: 0 for automation_type in AUTOMATION_TYPES}

        if evidence & {"api", "file"}:
            scores["python"] += 5
        if "python" in evidence:
            scores["python"] += 5
        if "web" in evidence:
            scores["playwright"] += 4
        if "playwright" in evidence:
            scores["playwright"] += 7
        if "selenium" in evidence:
            scores["selenium"] += 8
            scores["playwright"] -= 2
        if "desktop" in evidence:
            scores["pyautogui"] += 7
        if "lambda" in evidence:
            scores["lambda"] += 8
        if "docker" in evidence:
            scores["docker"] += 8
        if "scheduler" in evidence:
            scores["scheduler"] += 6
        if evidence == {"scheduler"}:
            scores["scheduler"] += 2
        if "api" in evidence and "web" in evidence:
            scores["python"] += 3
            scores["playwright"] -= 2
        if "docker" in evidence and "lambda" not in evidence:
            scores["python"] -= 2
        if not evidence:
            scores["manual"] = 1
        return scores

    def choose_type(self, scores: dict[str, int], normalized: str) -> tuple[str, int]:
        if "playwright" in normalized:
            return "playwright", max(scores["playwright"], 8)
        if "selenium" in normalized or "webdriver" in normalized:
            return "selenium", max(scores["selenium"], 8)
        if "pyautogui" in normalized:
            return "pyautogui", max(scores["pyautogui"], 8)
        best_type, best_score = max(scores.items(), key=lambda item: (item[1], item[0]))
        if best_score <= 0:
            return "manual", 1
        return best_type, best_score

    def evidence(self, normalized: str) -> list[str]:
        tokens = set(re.findall(r"[a-z0-9][a-z0-9._-]*", normalized))
        found: list[str] = []
        for kind, words in SIGNALS.items():
            if words & tokens or any(word in normalized for word in words if len(word) >= 6):
                found.append(kind)
        if "api" in found and has_negated_api(normalized):
            found.remove("api")
        return found

    def confidence_label(self, score: int, evidence: list[str], automation_type: str) -> str:
        if automation_type == "manual" or score < 4:
            return "low"
        if score >= 8:
            return "high"
        if score >= 5 and evidence:
            return "medium"
        return "low"

    def reason_for(self, automation_type: str, evidence: list[str], delegate: dict[str, Any]) -> str:
        if automation_type == "python":
            return "Pedido favorece automacao deterministica por API, arquivo, CLI ou script local."
        if automation_type == "playwright":
            return "Pedido favorece automacao web moderna sem API explicita; Playwright e o builder recomendado."
        if automation_type == "selenium":
            return "Pedido menciona Selenium/WebDriver ou requisito legado especifico."
        if automation_type == "pyautogui":
            return "Pedido parece depender de interface desktop/visual; usar apenas se nao houver alternativa melhor."
        if automation_type == "lambda":
            return "Pedido aponta para execucao cloud, serverless ou event-driven."
        if automation_type == "docker":
            return "Pedido aponta para empacotamento, imagem, compose ou reprodutibilidade de ambiente."
        if automation_type == "scheduler":
            return "Pedido aponta para agendamento, repeticao controlada, retry ou loop operacional."
        if not delegate.get("available"):
            return "Contexto insuficiente para escolher builder especializado com seguranca."
        return f"Classificacao baseada nos sinais: {', '.join(evidence) or '-'}."

    def risks_for(self, automation_type: str, confidence: str, evidence: list[str], text: str, delegate: dict[str, Any]) -> list[str]:
        risks: list[str] = []
        if confidence == "low":
            risks.append("low confidence: missing target, environment or side-effect details")
        if "external_write" in evidence:
            risks.append("external write requires explicit policy and confirmation")
        if "destructive" in evidence:
            risks.append("destructive operation must be blocked by default")
        if automation_type == "pyautogui":
            risks.append("desktop visual automation is fragile and must be a last resort")
        if automation_type == "playwright":
            risks.append("browser automation can expose sensitive UI data in screenshots and traces")
        if FORBIDDEN_MARKER_PATTERN.search(text):
            risks.append("request appears to contain a hardcoded secret marker")
        return risks

    def questions_for(self, automation_type: str, confidence: str, evidence: list[str]) -> list[str]:
        questions: list[str] = []
        if confidence == "low":
            questions.append("Qual sistema, arquivo, API, pagina ou aplicacao deve ser automatizado?")
            questions.append("A automacao deve apenas ler dados ou tambem escrever/alterar algo?")
        if automation_type == "pyautogui":
            questions.append("Existe API, CLI, arquivo, automacao nativa ou alternativa web antes de usar PyAutoGUI?")
        if automation_type == "playwright":
            questions.append("Existe API documentada que possa substituir a automacao do navegador?")
        if "scheduler" in evidence:
            questions.append("Qual frequencia, criterio de parada e budget maximo de execucao?")
        return questions

    def public_delegate(self, automation_type: str) -> dict[str, Any]:
        delegate = dict(DELEGATES[automation_type])
        return {
            "agent_id": delegate.get("agent_id"),
            "capability_id": delegate.get("capability_id"),
            "available": bool(delegate.get("available")),
            "write_policy": delegate.get("write_policy"),
            "blocked_reason": delegate.get("blocked_reason"),
            "related_problem": delegate.get("related_problem"),
        }

    def alternatives_for(self, automation_type: str, evidence: list[str]) -> list[dict[str, str]]:
        alternatives: list[dict[str, str]] = []
        if automation_type != "python":
            alternatives.append({"automation_type": "python", "reason": "Preferivel quando API, CLI ou arquivos forem suficientes."})
        if automation_type not in {"playwright", "selenium"} and "web" in evidence:
            alternatives.append({"automation_type": "playwright", "reason": "Opcao natural para web moderna sem API."})
        if automation_type != "docker":
            alternatives.append({"automation_type": "docker", "reason": "Util se o problema incluir empacotamento ou reprodutibilidade."})
        if automation_type != "scheduler" and "scheduler" in evidence:
            alternatives.append({"automation_type": "scheduler", "reason": "Util quando a execucao precisa repetir com criterio de parada."})
        return alternatives[:3]

    def delegation_contract(self, classification: dict[str, Any]) -> dict[str, Any]:
        delegate = classification["delegation"]
        return {
            "available": delegate.get("available"),
            "agent_id": delegate.get("agent_id"),
            "capability_id": delegate.get("capability_id"),
            "write_policy": delegate.get("write_policy"),
            "manual_command": self.manual_command(delegate),
            "expected_inputs": self.expected_inputs(classification),
            "blocked_reason": delegate.get("blocked_reason"),
            "related_problem": delegate.get("related_problem"),
        }

    def manual_command(self, delegate: dict[str, Any]) -> str | None:
        if not delegate.get("available"):
            return None
        return f"agent run {delegate['agent_id']} {delegate['capability_id']} --spec <automation-spec.yaml>"

    def expected_inputs(self, classification: dict[str, Any]) -> list[str]:
        automation_type = classification.get("automation_type")
        if automation_type in {"python", "selenium", "pyautogui"}:
            return ["automation_name", "purpose", "inputs", "outputs", "systems", "side_effects"]
        if automation_type == "playwright":
            return ["automation_name", "purpose", "target_url", "selectors", "steps", "assertions", "auth_strategy", "side_effects"]
        if automation_type == "lambda":
            return ["function_name", "runtime", "trigger", "inputs", "outputs", "iam_permissions"]
        if automation_type == "docker":
            return ["target_project", "runtime", "ports", "environment", "build_context"]
        if automation_type == "scheduler":
            return ["task_name", "frequency", "stop_criteria", "budget", "side_effects"]
        return ["request", "target_system", "side_effects"]

    def contract_inputs(self, classification: dict[str, Any]) -> list[str]:
        return self.expected_inputs(classification)

    def contract_outputs(self, classification: dict[str, Any]) -> list[str]:
        automation_type = classification.get("automation_type")
        if automation_type == "docker":
            return ["Dockerfile", "docker-compose.yml", "README.docker.md"]
        if automation_type == "lambda":
            return ["lambda project", "deployment plan", "security review"]
        if automation_type == "scheduler":
            return ["loop plan", "runner", "registration plan"]
        if automation_type in {"python", "selenium", "pyautogui"}:
            return ["script", "tests", "README", "capability wrapper plan"]
        if automation_type == "playwright":
            return ["playwright script", "screenshots/traces", "tests", "README", "capability wrapper plan"]
        return ["runbook", "open questions"]

    def side_effects(self, classification: dict[str, Any]) -> str:
        evidence = set(classification.get("evidence", []))
        if "destructive" in evidence:
            return "destructive-blocked"
        if "external_write" in evidence:
            return "external-write-confirm"
        return "read-or-local-write"

    def execution_mode(self, classification: dict[str, Any]) -> str:
        automation_type = classification.get("automation_type")
        if automation_type == "lambda":
            return "cloud-event-driven"
        if automation_type == "scheduler":
            return "controlled-loop-or-scheduled-task"
        if automation_type == "docker":
            return "local-build-plan"
        return "manual-or-local-runner"

    def guardrails_for(self, classification: dict[str, Any]) -> list[str]:
        guardrails = [
            "Nao hardcodar credenciais.",
            "Expor dry-run antes de execucao real.",
            "Preservar logs redigidos e saida previsivel.",
            "Bloquear escrita externa sem confirmacao explicita.",
        ]
        if classification.get("automation_type") == "pyautogui":
            guardrails.append("Exigir failsafe, screenshots e justificativa de ultimo recurso.")
        if classification.get("automation_type") in {"playwright", "selenium"}:
            guardrails.append("Preferir API documentada quando existir.")
        return guardrails

    def next_steps_for(self, classification: dict[str, Any]) -> list[str]:
        if classification.get("confidence") == "low":
            return ["Responder perguntas pendentes antes de gerar artefatos."]
        if not classification.get("available_delegate"):
            return ["Refinar contexto ou aguardar builder especializado antes de delegar."]
        return [
            "Criar spec do builder recomendado com entradas, saidas, sistemas e side effects.",
            "Executar capability de planejamento do builder recomendado.",
            "Revisar o artefato antes de qualquer execucao real.",
        ]


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def has_negated_api(normalized: str) -> bool:
    return bool(
        re.search(r"\bsem\s+(?:uma\s+|nenhuma\s+)?api\b", normalized)
        or re.search(r"\bnao\s+(?:ha|existe|possui|tem)\s+(?:uma\s+|nenhuma\s+)?api\b", normalized)
        or re.search(r"\bno\s+api\b", normalized)
    )


def flatten_mapping(value: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    for key, item in value.items():
        parts.append(str(key))
        if isinstance(item, dict):
            parts.extend(flatten_mapping(item))
        elif isinstance(item, list):
            parts.extend(str(entry) for entry in item)
        else:
            parts.append(str(item))
    return parts
