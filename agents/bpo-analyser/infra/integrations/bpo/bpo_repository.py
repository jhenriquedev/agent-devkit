#!/usr/bin/env python3
"""Direct BPO SOAP repository using only Python stdlib."""

from __future__ import annotations

import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class BpoRepositoryError(RuntimeError):
    """Raised when BPO config, transport, or parsing fails."""


@dataclass(frozen=True)
class BpoEligibilityPolicy:
    eligible_situations: tuple[str, ...] = ("INT", "INTEGRADA", "APR", "APROVADA")
    eligible_proposal_types: tuple[str, ...] = ("3",)
    require_positive_withdraw_limit: bool = True


DEFAULT_ELIGIBILITY_POLICY = BpoEligibilityPolicy()


@dataclass(frozen=True)
class BpoConfig:
    servico_api_url: str
    ws_proposta_url: str
    user: str
    password: str
    ws_esteira_url: str = ""
    ws_formalizacao_url: str = ""
    consignacao_url: str = ""
    timeout: int = 30
    default_document_type: str = "Nao_Definido"
    tls_verify: bool = True
    eligibility_policy: BpoEligibilityPolicy = DEFAULT_ELIGIBILITY_POLICY
    forbidden_url_patterns: tuple[str, ...] = ()
    partner_contract_fields: tuple[str, ...] = ()
    originator_contract_fields: tuple[str, ...] = ()

    @classmethod
    def from_env(cls) -> "BpoConfig":
        load_dotenv()
        missing = [
            name
            for name in (
                "BPO_SERVICO_API_URL",
                "BPO_WS_PROPOSTA_URL",
                "BPO_CARTAO_USER",
                "BPO_CARTAO_PASSWORD",
            )
            if not os.environ.get(name)
        ]
        if missing:
            raise BpoRepositoryError(f"Missing env vars: {', '.join(missing)}")
        return cls(
            servico_api_url=os.environ["BPO_SERVICO_API_URL"].strip(),
            ws_proposta_url=os.environ["BPO_WS_PROPOSTA_URL"].strip(),
            user=os.environ["BPO_CARTAO_USER"].strip(),
            password=os.environ["BPO_CARTAO_PASSWORD"],
            ws_esteira_url=os.environ.get("BPO_WS_ESTEIRA_URL", "").strip(),
            ws_formalizacao_url=os.environ.get("BPO_WS_FORMALIZACAO_URL", "").strip(),
            consignacao_url=os.environ.get("BPO_CONSIGNACAO_URL", "").strip(),
            timeout=int(os.environ.get("BPO_HTTP_TIMEOUT") or "30"),
            default_document_type=os.environ.get("BPO_DEFAULT_DOCUMENT_TYPE", "Nao_Definido"),
            tls_verify=parse_bool(os.environ.get("BPO_TLS_VERIFY"), default=True),
            eligibility_policy=BpoEligibilityPolicy(
                eligible_situations=parse_csv_env(
                    "BPO_ELIGIBLE_SITUATIONS",
                    DEFAULT_ELIGIBILITY_POLICY.eligible_situations,
                ),
                eligible_proposal_types=parse_csv_env(
                    "BPO_ELIGIBLE_PROPOSAL_TYPES",
                    DEFAULT_ELIGIBILITY_POLICY.eligible_proposal_types,
                ),
                require_positive_withdraw_limit=parse_bool(
                    os.environ.get("BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT"),
                    default=True,
                ),
            ),
            forbidden_url_patterns=parse_csv_env("BPO_FORBIDDEN_URL_PATTERNS", ()),
            partner_contract_fields=parse_csv_env("BPO_PARTNER_CONTRACT_FIELDS", ()),
            originator_contract_fields=parse_csv_env("BPO_ORIGINATOR_CONTRACT_FIELDS", ()),
        )


class BpoRepository:
    """Repository for read-only proposal analysis in BPO SOAP services."""

    def __init__(self, config: BpoConfig | None = None) -> None:
        self.config = config or BpoConfig.from_env()

    def test_connection(self, *, network: bool = False) -> dict[str, Any]:
        endpoints = {
            "servico_api": self.config.servico_api_url,
            "ws_proposta": self.config.ws_proposta_url,
            "ws_esteira": self.config.ws_esteira_url,
            "ws_formalizacao": self.config.ws_formalizacao_url,
            "consignacao": self.config.consignacao_url,
        }
        result: dict[str, Any] = {
            "configured": True,
            "user_configured": bool(self.config.user),
            "password_configured": bool(self.config.password),
            "timeout": self.config.timeout,
            "default_document_type": self.config.default_document_type,
            "tls_verify": self.config.tls_verify,
            "eligibility_policy": {
                "eligible_situations": list(self.config.eligibility_policy.eligible_situations),
                "eligible_proposal_types": list(
                    self.config.eligibility_policy.eligible_proposal_types
                ),
                "require_positive_withdraw_limit": (
                    self.config.eligibility_policy.require_positive_withdraw_limit
                ),
            },
            "contract_field_mapping": {
                "partner": list(self.config.partner_contract_fields),
                "originator": list(self.config.originator_contract_fields),
            },
            "endpoints": {
                key: {"configured": bool(value), "url": redact_url(value)}
                for key, value in endpoints.items()
            },
        }
        if network:
            for key, value in endpoints.items():
                if value:
                    result["endpoints"][key]["network"] = self._check_wsdl(value)
        return result

    def consult_proposal(self, proposal_number: str | int) -> dict[str, Any]:
        proposal = str(proposal_number).strip()
        if not proposal:
            raise BpoRepositoryError("proposal_number is required")
        envelope = build_consult_proposal_envelope(self.config.user, self.config.password, proposal)
        xml = self._soap_post(
            self.config.servico_api_url,
            envelope,
            soap_action="consultarPropostaPorNumeroProposta",
        )
        return parse_proposal_response(xml)

    def list_proposals_by_cpf(self, cpf: str) -> dict[str, Any]:
        document = normalize_cpf(cpf)
        envelope = build_list_proposals_by_cpf_envelope(
            self.config.user,
            self.config.password,
            document,
        )
        xml = self._soap_post(
            self.config.servico_api_url,
            envelope,
            soap_action="listarPropostasPorCpf",
        )
        return parse_proposals_by_cpf_response(
            xml,
            document,
            eligibility_policy=self.config.eligibility_policy,
            partner_contract_fields=self.config.partner_contract_fields,
            originator_contract_fields=self.config.originator_contract_fields,
        )

    def analyze_cpf_proposals(self, cpf: str) -> dict[str, Any]:
        proposals = self.list_proposals_by_cpf(cpf)
        return build_cpf_proposals_analysis(proposals)

    def find_latest_proposal_by_cpf(self, cpf: str) -> dict[str, Any]:
        analysis = self.analyze_cpf_proposals(cpf)
        return {
            "cpf": analysis["cpf"],
            "masked_cpf": analysis["masked_cpf"],
            "selected": analysis["facts"].get("latest_integrated_or_approved"),
            "criteria": "politica de elegibilidade configurada com data_ultimo_vencimento mais recente",
            "source_count": analysis["facts"].get("total"),
            "eligible_count": analysis["facts"].get("eligible_count"),
        }

    def consult_attached_documents(
        self,
        proposal_number: str | int,
        *,
        document_type: str | None = None,
        include_content: bool = False,
    ) -> dict[str, Any]:
        proposal = str(proposal_number).strip()
        if not proposal:
            raise BpoRepositoryError("proposal_number is required")
        doc_type = document_type or self.config.default_document_type
        envelope = build_attached_documents_envelope(
            self.config.user,
            self.config.password,
            proposal,
            doc_type,
        )
        xml = self._soap_post(
            self.config.ws_proposta_url,
            envelope,
            soap_action="http://tempuri.org/ConsultaDocumentosAnexados",
        )
        return parse_attached_documents_response(
            xml,
            requested_proposal_number=proposal,
            requested_document_type=doc_type,
            include_content=include_content,
        )

    def analyze_proposal(
        self,
        proposal_number: str | int,
        *,
        document_type: str | None = None,
    ) -> dict[str, Any]:
        proposal = self.consult_proposal(proposal_number)
        documents = self.consult_attached_documents(
            proposal_number,
            document_type=document_type,
            include_content=False,
        )
        return build_proposal_analysis(proposal, documents)

    def _soap_post(self, url: str, envelope: str, *, soap_action: str) -> str:
        forbidden_pattern = first_matching_forbidden_pattern(url, self.config.forbidden_url_patterns)
        if forbidden_pattern:
            raise BpoRepositoryError(
                f"URL matches configured forbidden BPO target pattern: {forbidden_pattern}"
            )
        request = urllib.request.Request(
            url,
            data=envelope.encode("utf-8"),
            method="POST",
            headers={
                "Accept": "text/xml",
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": soap_action,
            },
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout,
                context=self._ssl_context(),
            ) as response:
                return response.read().decode("utf-8-sig", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8-sig", errors="replace")
            raise BpoRepositoryError(f"BPO HTTP {exc.code}: {compact(body)}") from exc
        except urllib.error.URLError as exc:
            raise BpoRepositoryError(f"BPO transport error: {exc.reason}") from exc

    def _check_wsdl(self, url: str) -> dict[str, Any]:
        wsdl_url = f"{url}{'&' if '?' in url else '?'}WSDL"
        try:
            request = urllib.request.Request(wsdl_url, method="GET")
            with urllib.request.urlopen(
                request,
                timeout=self.config.timeout,
                context=self._ssl_context(),
            ) as response:
                return {"ok": 200 <= response.status < 400, "status": response.status}
        except Exception as exc:  # pragma: no cover - network diagnostic only
            return {"ok": False, "error": str(exc)}

    def _ssl_context(self) -> ssl.SSLContext | None:
        if self.config.tls_verify:
            return None
        return ssl._create_unverified_context()  # noqa: SLF001 - explicit local BPO compatibility


def build_consult_proposal_envelope(user: str, password: str, proposal_number: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:api="http://apis.bpo.com.br">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<api:consultarPropostaPorNumeroProposta>"
        f"<api:usuarioAcesso>{xml_escape(user)}</api:usuarioAcesso>"
        f"<api:senhaAcesso>{xml_escape(password)}</api:senhaAcesso>"
        f"<api:numeroProposta>{xml_escape(proposal_number)}</api:numeroProposta>"
        "</api:consultarPropostaPorNumeroProposta>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def build_attached_documents_envelope(
    user: str,
    password: str,
    proposal_number: str,
    document_type: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:tem="http://tempuri.org/">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<tem:ConsultaDocumentosAnexados>"
        f"<tem:pLoginUsuario>{xml_escape(user)}</tem:pLoginUsuario>"
        f"<tem:pSenha>{xml_escape(password)}</tem:pSenha>"
        f"<tem:pNumeroProposta>{xml_escape(proposal_number)}</tem:pNumeroProposta>"
        f"<tem:pTipoDocumento>{xml_escape(document_type)}</tem:pTipoDocumento>"
        "</tem:ConsultaDocumentosAnexados>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def build_list_proposals_by_cpf_envelope(user: str, password: str, cpf: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:api="http://apis.bpo.com.br">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<api:listarPropostasPorCpf>"
        f"<api:usuarioAcesso>{xml_escape(user)}</api:usuarioAcesso>"
        f"<api:senhaAcesso>{xml_escape(password)}</api:senhaAcesso>"
        f"<api:cpf>{xml_escape(cpf)}</api:cpf>"
        "</api:listarPropostasPorCpf>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )


def parse_proposal_response(xml: str) -> dict[str, Any]:
    root = parse_xml(xml)
    return_node = first_descendant(root, "consultarPropostaPorNumeroPropostaReturn")
    if return_node is None:
        return_node = first_descendant(root, "ConsultarPropostaResult")
    if return_node is None:
        raise BpoRepositoryError("proposal return node not found in BPO response")

    processing = child_object(return_node, "statusProcessamento")
    observations = parse_observations(return_node)
    proposal = {
        "formalization_id": text_of(return_node, "IDFormalizacao"),
        "activity": text_of(return_node, "atividade"),
        "employer_code": int_or_none(text_of(return_node, "codigoEmpregador")),
        "product_code": int_or_none(text_of(return_node, "codigoProduto")),
        "promoter_code": int_or_none(text_of(return_node, "codigoPromotora")),
        "cpf": text_of(return_node, "cpf"),
        "birth_date": text_of(return_node, "dataNascimento"),
        "first_due_date": text_of(return_node, "dataPrimeiroVencimento"),
        "situation_date": text_of(return_node, "dataSituacao"),
        "last_due_date": text_of(return_node, "dataUltimoVencimento"),
        "registration": text_of(return_node, "matricula"),
        "rejection_reason": text_of(return_node, "motivoReprovacao"),
        "customer_name": text_of(return_node, "nomeCliente"),
        "employer_name": text_of(return_node, "nomeEmpregador"),
        "product_name": text_of(return_node, "nomeProduto"),
        "promoter_name": text_of(return_node, "nomePromotora"),
        "contract_number": text_of(return_node, "numeroContrato"),
        "proposal_number": text_of(return_node, "numeroProposta"),
        "installments": int_or_none(text_of(return_node, "quantidadeParcelas")),
        "situation": text_of(return_node, "situacao"),
        "processing_status": {
            "status": bool_text(processing.get("Status") or processing.get("status")),
            "error_message": processing.get("MensagemErro") or processing.get("mensagemErro"),
        },
        "proposal_type": text_of(return_node, "tipoProposta"),
        "amounts": {
            "gross": float_or_none(text_of(return_node, "valorBruto")),
            "iof": float_or_none(text_of(return_node, "valorIOF")),
            "released": float_or_none(text_of(return_node, "valorLiberado")),
            "purchase_limit": float_or_none(text_of(return_node, "valorLimiteCompra")),
            "withdraw_limit": float_or_none(text_of(return_node, "valorLimiteSaque")),
            "installment": float_or_none(text_of(return_node, "valorParcela")),
            "rmc": float_or_none(text_of(return_node, "valorRMC")),
            "withdraw": float_or_none(text_of(return_node, "valorSaque")),
            "requested": float_or_none(text_of(return_node, "valorSolicitado")),
        },
        "observations": observations,
    }
    return proposal


def parse_attached_documents_response(
    xml: str,
    *,
    requested_proposal_number: str,
    requested_document_type: str,
    include_content: bool = False,
) -> dict[str, Any]:
    root = parse_xml(xml)
    processing_node = first_descendant(root, "StatusProcessamento")
    processing = child_object(processing_node, None) if processing_node is not None else {}
    file_nodes = [
        node
        for node in root.iter()
        if first_child(node, "NomeArquivo") is not None
        or first_child(node, "FileName") is not None
        or first_child(node, "ArquivoBase64") is not None
    ]
    files = []
    for node in file_nodes:
        item = {
            "proposal_number": int_or_none(text_of(node, "NumeroProposta")) or requested_proposal_number,
            "file_name": text_of(node, "NomeArquivo"),
            "document_type": text_of(node, "TipoDocumento") or requested_document_type,
            "extension_file_type": text_of(node, "ExtensaoArquivo"),
            "size": int_or_none(text_of(node, "Tamanho")),
            "has_file": bool(text_of(node, "Arquivo")),
            "has_file_base64": bool(text_of(node, "ArquivoBase64")),
        }
        if include_content:
            item["file_base64"] = text_of(node, "ArquivoBase64")
        files.append(item)
    return {
        "proposal_number": requested_proposal_number,
        "requested_document_type": requested_document_type,
        "processing_status": {
            "status": bool_text(processing.get("Status") or processing.get("status")),
            "error_message": processing.get("MensagemErro") or processing.get("mensagemErro"),
        },
        "count": len(files),
        "files": files,
    }


def parse_proposals_by_cpf_response(
    xml: str,
    cpf: str,
    *,
    eligibility_policy: BpoEligibilityPolicy = DEFAULT_ELIGIBILITY_POLICY,
    partner_contract_fields: tuple[str, ...] = (),
    originator_contract_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    root = parse_xml(xml)
    proposal_nodes = [
        node
        for node in root.iter()
        if local_name(node.tag) == "listarPropostasPorCpfReturn"
        or local_name(node.tag) == "PropostaAPI"
    ]
    proposals = [
        parse_cpf_proposal_node(
            node,
            eligibility_policy=eligibility_policy,
            partner_contract_fields=partner_contract_fields,
            originator_contract_fields=originator_contract_fields,
        )
        for node in proposal_nodes
    ]
    return {
        "cpf": cpf,
        "masked_cpf": mask_cpf(cpf),
        "count": len(proposals),
        "proposals": proposals,
    }


def parse_cpf_proposal_node(
    node: ET.Element,
    *,
    eligibility_policy: BpoEligibilityPolicy = DEFAULT_ELIGIBILITY_POLICY,
    partner_contract_fields: tuple[str, ...] = (),
    originator_contract_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    customer = first_child(node, "cliente")
    situation = first_text(node, ["situacao"])
    proposal_type = first_text(node, ["tipoProposta"])
    withdraw_limit = float_or_none(first_text(node, ["limiteSaque"]))
    return {
        "proposal_number": int_or_none(first_text(node, ["nrProposta", "numeroProposta"])),
        "bank_proposal_number": first_text(node, ["nrPropostaBanco"]),
        "id": first_text(node, ["id"]),
        "contract_number_partner": first_text(node, list(partner_contract_fields)),
        "contract_number_originator": first_text(node, list(originator_contract_fields)),
        "situation": situation,
        "situation_kind": situation_kind(situation),
        "activity": first_text(node, ["atividade"]),
        "proposal_type": proposal_type,
        "product_type": first_text(node, ["tipoProduto"]),
        "employer": first_text(node, ["empregador"]),
        "agency": first_text(node, ["orgao"]),
        "promoter_name": first_text(node, ["nomePromotora"]),
        "matrix_name": first_text(node, ["nomeMatriz"]),
        "table": first_text(node, ["tabela"]),
        "first_due_date": first_text(node, ["dataPrimeiroVcto", "dataPrimeiroVencimento"]),
        "last_due_date": first_text(node, ["dataUltimoVcto", "dataUltimoVencimento"]),
        "movement_date": first_text(node, ["dataMovimentacao"]),
        "typing_date": first_text(node, ["dataDigitacao"]),
        "term": int_or_none(first_text(node, ["prazo"])),
        "purchase_limit": float_or_none(first_text(node, ["limiteCompra"])),
        "withdraw_limit": withdraw_limit,
        "total_limit": float_or_none(first_text(node, ["limiteTotal"])),
        "requested_amount": float_or_none(first_text(node, ["valorSolicitado"])),
        "released_amount": float_or_none(first_text(node, ["valorLiberado"])),
        "installment_amount": float_or_none(first_text(node, ["valorParcela"])),
        "customer": {
            "name": first_text(customer, ["nome"]) if customer is not None else "",
            "cpf": first_text(customer, ["cpf"]) if customer is not None else "",
            "registration": first_text(customer, ["matricula"]) if customer is not None else "",
            "product_name": first_text(customer, ["nomeProduto"]) if customer is not None else "",
        },
        "observations": parse_observations(node),
        "is_eligible": is_operationally_eligible(
            situation,
            proposal_type,
            withdraw_limit,
            policy=eligibility_policy,
        ),
    }


def build_proposal_analysis(proposal: dict[str, Any], documents: dict[str, Any]) -> dict[str, Any]:
    observations = proposal.get("observations") or []
    files = documents.get("files") or []
    attention_points = []
    processing = proposal.get("processing_status") or {}
    if processing.get("status") is False:
        attention_points.append("Status de processamento da proposta retornou falha.")
    if not proposal.get("situation"):
        attention_points.append("Situacao da proposta nao foi retornada.")
    if proposal.get("rejection_reason"):
        attention_points.append("Proposta possui motivo de reprovacao informado.")
    if not observations:
        attention_points.append("Nenhuma observacao retornada pela BPO.")
    if not files:
        attention_points.append("Nenhum documento anexado retornado pela BPO.")
    document_types = sorted({str(item.get("document_type")) for item in files if item.get("document_type")})
    return {
        "proposal": proposal,
        "documents": documents,
        "facts": {
            "proposal_number": proposal.get("proposal_number") or documents.get("proposal_number"),
            "situation": proposal.get("situation"),
            "activity": proposal.get("activity"),
            "processing_status": processing,
            "observation_count": len(observations),
            "document_count": len(files),
            "document_types": document_types,
        },
        "inferences": {
            "attention_points": attention_points,
            "has_blocking_signals": bool(attention_points),
        },
    }


def build_cpf_proposals_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    proposals = payload.get("proposals") or []
    eligible = [item for item in proposals if item.get("is_eligible")]
    under_analysis = [
        item for item in proposals if item.get("situation_kind") in {"cadastrada", "pendente", "andamento"}
    ]
    rejected = [item for item in proposals if item.get("situation_kind") == "reprovada"]
    latest = latest_integrated_or_approved(proposals)
    attention_points = []
    if not proposals:
        attention_points.append("Nenhuma proposta retornada pela BPO para o CPF.")
    if under_analysis:
        attention_points.append("Existe proposta em analise para o CPF.")
    if rejected:
        attention_points.append("Existe proposta reprovada para o CPF.")
    if eligible:
        attention_points.append("Existe proposta elegivel pela politica operacional configurada.")
    return {
        "cpf": payload.get("cpf"),
        "masked_cpf": payload.get("masked_cpf"),
        "proposals": proposals,
        "facts": {
            "total": len(proposals),
            "eligible_count": len(eligible),
            "under_analysis_count": len(under_analysis),
            "rejected_count": len(rejected),
            "latest_integrated_or_approved": latest,
        },
        "groups": {
            "eligible": eligible,
            "under_analysis": under_analysis,
            "rejected": rejected,
        },
        "inferences": {
            "attention_points": attention_points,
            "has_blocking_signals": bool(under_analysis or rejected),
        },
    }


def latest_integrated_or_approved(proposals: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        item
        for item in proposals
        if item.get("situation_kind") in {"integrada", "aprovada"}
        and item.get("last_due_date")
    ]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda item: (
            1 if item.get("situation_kind") == "integrada" else 0,
            parse_date_key(item.get("last_due_date")),
        ),
        reverse=True,
    )[0]


def parse_observations(return_node: ET.Element) -> list[dict[str, Any]]:
    candidates = [
        node
        for node in return_node.iter()
        if local_name(node.tag) in {"observacoes", "item"}
        and (first_child(node, "observacao") is not None or first_child(node, "data") is not None)
    ]
    observations = []
    for node in candidates:
        observation = {
            "date": text_of(node, "data"),
            "text": text_of(node, "observacao"),
        }
        if observation["date"] or observation["text"]:
            observations.append(observation)
    return dedupe_dicts(observations)


def first_text(root: ET.Element | None, names: list[str]) -> str:
    if root is None:
        return ""
    for name in names:
        value = text_of(root, name)
        if value:
            return value
    return ""


def parse_xml(xml: str) -> ET.Element:
    try:
        return ET.fromstring(xml.encode("utf-8"))
    except ET.ParseError as exc:
        raise BpoRepositoryError(f"invalid BPO XML response: {exc}") from exc


def first_descendant(root: ET.Element, name: str) -> ET.Element | None:
    for node in root.iter():
        if local_name(node.tag) == name:
            return node
    return None


def first_child(root: ET.Element, name: str) -> ET.Element | None:
    for node in list(root):
        if local_name(node.tag) == name:
            return node
    return None


def text_of(root: ET.Element, name: str) -> str:
    node = first_child(root, name)
    if node is None:
        node = first_descendant(root, name)
    if node is None or node.text is None:
        return ""
    return node.text.strip()


def child_object(root: ET.Element | None, name: str | None) -> dict[str, str]:
    node = root if name is None else (first_child(root, name) if root is not None else None)
    if node is None:
        return {}
    return {local_name(child.tag): (child.text or "").strip() for child in list(node)}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def bool_text(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "sim"}:
        return True
    if text in {"false", "0", "nao", "não"}:
        return False
    return None


def normalize_cpf(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 11:
        raise BpoRepositoryError("cpf must have 11 digits")
    return digits


def situation_kind(value: str | None) -> str:
    text = str(value or "").strip().upper()
    mapping = {
        "INT": "integrada",
        "INTEGRADA": "integrada",
        "APR": "aprovada",
        "APROVADA": "aprovada",
        "CAD": "cadastrada",
        "CADASTRADA": "cadastrada",
        "PEN": "pendente",
        "PENDENTE": "pendente",
        "AND": "andamento",
        "ANDAMENTO": "andamento",
        "REP": "reprovada",
        "REPROVADA": "reprovada",
    }
    return mapping.get(text, text.lower())


def is_operationally_eligible(
    situation: str | None,
    proposal_type: str | int | None,
    withdraw_limit: float | None,
    *,
    policy: BpoEligibilityPolicy = DEFAULT_ELIGIBILITY_POLICY,
) -> bool:
    normalized_situations = {
        situation_kind(item).upper() for item in policy.eligible_situations if str(item).strip()
    }
    current_situation = situation_kind(situation).upper()
    allowed_types = {str(item).strip() for item in policy.eligible_proposal_types if str(item).strip()}
    current_type = str(proposal_type or "").strip()
    if current_situation not in normalized_situations:
        return False
    if allowed_types and current_type not in allowed_types:
        return False
    if policy.require_positive_withdraw_limit and (withdraw_limit or 0) <= 0:
        return False
    return True


def parse_date_key(value: str | None) -> datetime:
    if not value:
        return datetime.min
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text[:10], fmt)
            except ValueError:
                continue
    return datetime.min


def parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "sim"}


def parse_csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return tuple(item.strip() for item in re.split(r"[,;\n]", value) if item.strip())


def first_matching_forbidden_pattern(url: str, patterns: tuple[str, ...]) -> str:
    normalized_url = url.lower()
    for pattern in patterns:
        normalized_pattern = pattern.strip().lower()
        if normalized_pattern and normalized_pattern in normalized_url:
            return pattern
    return ""


def int_or_none(value: str) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def float_or_none(value: str) -> float | None:
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def xml_escape(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def compact(value: str) -> str:
    return " ".join(str(value).split())[:1000]


def redact_url(value: str) -> str:
    if not value:
        return ""
    parsed = urllib.parse.urlsplit(value)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def mask_cpf(value: str | None) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 11:
        return ""
    return f"{digits[:3]}.***.***-{digits[-2:]}"


def dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = tuple(sorted(item.items()))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def load_dotenv() -> None:
    for candidate in _dotenv_candidates():
        if not candidate.exists():
            continue
        for raw_line in candidate.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return


def _dotenv_candidates() -> list[Path]:
    paths = []
    for start in (Path.cwd(), Path(__file__).resolve()):
        current = start if start.is_dir() else start.parent
        paths.extend(parent / ".env" for parent in [current, *current.parents])
    seen = set()
    unique = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique
