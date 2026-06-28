#!/usr/bin/env python3
"""Tests for BPO repository helpers."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


BPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BPO_DIR))

from bpo_repository import (  # noqa: E402
    BpoConfig,
    BpoEligibilityPolicy,
    build_attached_documents_envelope,
    build_cpf_proposals_analysis,
    build_consult_proposal_envelope,
    build_list_proposals_by_cpf_envelope,
    build_proposal_analysis,
    first_matching_forbidden_pattern,
    is_operationally_eligible,
    parse_attached_documents_response,
    parse_proposal_response,
    parse_proposals_by_cpf_response,
    situation_kind,
)


PROPOSAL_XML = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns2:consultarPropostaPorNumeroPropostaResponse xmlns:ns2="http://apis.bpo.com.br">
      <consultarPropostaPorNumeroPropostaReturn>
        <IDFormalizacao>789</IDFormalizacao>
        <atividade>Analise de documentos</atividade>
        <codigoEmpregador>10</codigoEmpregador>
        <codigoProduto>20</codigoProduto>
        <codigoPromotora>30</codigoPromotora>
        <cpf>12345678901</cpf>
        <dataSituacao>2026-06-20T10:00:00</dataSituacao>
        <motivoReprovacao></motivoReprovacao>
        <nomeCliente>Ana Silva</nomeCliente>
        <nomeEmpregador>Orgao XPTO</nomeEmpregador>
        <nomeProduto>Cartao Beneficio</nomeProduto>
        <nomePromotora>Promotora A</nomePromotora>
        <numeroContrato>ABC123</numeroContrato>
        <numeroProposta>123456</numeroProposta>
        <observacoes>
          <item>
            <data>2026-06-20T11:00:00</data>
            <observacao>Documento pendente</observacao>
          </item>
        </observacoes>
        <quantidadeParcelas>12</quantidadeParcelas>
        <situacao>Pendente</situacao>
        <statusProcessamento>
          <Status>true</Status>
          <MensagemErro></MensagemErro>
        </statusProcessamento>
        <tipoProposta>Saque</tipoProposta>
        <valorLiberado>1000.50</valorLiberado>
        <valorSolicitado>1200.00</valorSolicitado>
      </consultarPropostaPorNumeroPropostaReturn>
    </ns2:consultarPropostaPorNumeroPropostaResponse>
  </soap:Body>
</soap:Envelope>
"""


DOCUMENTS_XML = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ConsultaDocumentosAnexadosResponse xmlns="http://tempuri.org/">
      <ConsultaDocumentosAnexadosResult>
        <StatusProcessamento>
          <Status>true</Status>
          <MensagemErro></MensagemErro>
        </StatusProcessamento>
        <Arquivos>
          <WsPropostaDocumentos>
            <NumeroProposta>123456</NumeroProposta>
            <NomeArquivo>ccb.pdf</NomeArquivo>
            <TipoDocumento>CCB_Negociavel</TipoDocumento>
            <ExtensaoArquivo>PDF</ExtensaoArquivo>
            <Tamanho>2048</Tamanho>
            <ArquivoBase64>YWJj</ArquivoBase64>
          </WsPropostaDocumentos>
        </Arquivos>
      </ConsultaDocumentosAnexadosResult>
    </ConsultaDocumentosAnexadosResponse>
  </soap:Body>
</soap:Envelope>
"""


PROPOSALS_BY_CPF_XML = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <listarPropostasPorCpfResponse xmlns="http://apis.bpo.com.br">
      <listarPropostasPorCpfReturn>
        <atividade>Integrada</atividade>
        <cliente>
          <cpf>12345678901</cpf>
          <nome>Ana Silva</nome>
          <matricula>9988</matricula>
        </cliente>
        <nrProposta>123456</nrProposta>
        <situacao>INT</situacao>
        <tipoProposta>3</tipoProposta>
        <dataUltimoVcto>2026-12-10T00:00:00</dataUltimoVcto>
        <limiteSaque>500.00</limiteSaque>
        <valorLiberado>1000.00</valorLiberado>
        <orgao>Orgao XPTO</orgao>
      </listarPropostasPorCpfReturn>
      <listarPropostasPorCpfReturn>
        <atividade>Pendente documental</atividade>
        <cliente>
          <cpf>12345678901</cpf>
          <nome>Ana Silva</nome>
        </cliente>
        <nrProposta>123457</nrProposta>
        <situacao>PEN</situacao>
        <tipoProposta>3</tipoProposta>
        <dataUltimoVcto>2027-01-10T00:00:00</dataUltimoVcto>
        <limiteSaque>0</limiteSaque>
        <valorLiberado>0</valorLiberado>
      </listarPropostasPorCpfReturn>
    </listarPropostasPorCpfResponse>
  </soap:Body>
</soap:Envelope>
"""


class BpoRepositoryTest(unittest.TestCase):
    def test_config_reads_required_env(self) -> None:
        env = {
            "BPO_SERVICO_API_URL": "https://example.com/ServicoAPI",
            "BPO_WS_PROPOSTA_URL": "https://example.com/WsProposta.asmx",
            "BPO_CARTAO_USER": "agent",
            "BPO_CARTAO_PASSWORD": "secret",
        }
        with patch("bpo_repository.load_dotenv", lambda: None), patch.dict(
            os.environ, env, clear=True
        ):
            config = BpoConfig.from_env()

        self.assertEqual(config.servico_api_url, "https://example.com/ServicoAPI")
        self.assertEqual(config.ws_proposta_url, "https://example.com/WsProposta.asmx")
        self.assertEqual(config.user, "agent")
        self.assertEqual(config.default_document_type, "Nao_Definido")
        self.assertEqual(config.eligibility_policy.eligible_proposal_types, ("3",))
        self.assertEqual(config.forbidden_url_patterns, ())

    def test_config_reads_optional_policy_env(self) -> None:
        env = {
            "BPO_SERVICO_API_URL": "https://example.com/ServicoAPI",
            "BPO_WS_PROPOSTA_URL": "https://example.com/WsProposta.asmx",
            "BPO_CARTAO_USER": "agent",
            "BPO_CARTAO_PASSWORD": "secret",
            "BPO_ELIGIBLE_SITUATIONS": "INT;APR;CUSTOM",
            "BPO_ELIGIBLE_PROPOSAL_TYPES": "3,7",
            "BPO_REQUIRE_POSITIVE_WITHDRAW_LIMIT": "false",
            "BPO_FORBIDDEN_URL_PATTERNS": "/internal-api,/legacy-app",
            "BPO_PARTNER_CONTRACT_FIELDS": "numeroContratoParceiro",
            "BPO_ORIGINATOR_CONTRACT_FIELDS": "numeroContratoOriginador",
        }
        with patch("bpo_repository.load_dotenv", lambda: None), patch.dict(
            os.environ, env, clear=True
        ):
            config = BpoConfig.from_env()

        self.assertEqual(config.eligibility_policy.eligible_situations, ("INT", "APR", "CUSTOM"))
        self.assertEqual(config.eligibility_policy.eligible_proposal_types, ("3", "7"))
        self.assertFalse(config.eligibility_policy.require_positive_withdraw_limit)
        self.assertEqual(config.forbidden_url_patterns, ("/internal-api", "/legacy-app"))
        self.assertEqual(config.partner_contract_fields, ("numeroContratoParceiro",))
        self.assertEqual(config.originator_contract_fields, ("numeroContratoOriginador",))

    def test_builds_consult_proposal_envelope(self) -> None:
        envelope = build_consult_proposal_envelope("user&", "p<ss", "123")

        self.assertIn("consultarPropostaPorNumeroProposta", envelope)
        self.assertIn("user&amp;", envelope)
        self.assertIn("p&lt;ss", envelope)
        self.assertIn("<api:numeroProposta>123</api:numeroProposta>", envelope)

    def test_builds_attached_documents_envelope(self) -> None:
        envelope = build_attached_documents_envelope("user", "secret", "123", "CCB_Negociavel")

        self.assertIn("ConsultaDocumentosAnexados", envelope)
        self.assertIn("<tem:pNumeroProposta>123</tem:pNumeroProposta>", envelope)
        self.assertIn("<tem:pTipoDocumento>CCB_Negociavel</tem:pTipoDocumento>", envelope)

    def test_builds_list_proposals_by_cpf_envelope(self) -> None:
        envelope = build_list_proposals_by_cpf_envelope("user", "secret", "12345678901")

        self.assertIn("listarPropostasPorCpf", envelope)
        self.assertIn("<api:cpf>12345678901</api:cpf>", envelope)

    def test_parse_proposal_response(self) -> None:
        proposal = parse_proposal_response(PROPOSAL_XML)

        self.assertEqual(proposal["proposal_number"], "123456")
        self.assertEqual(proposal["situation"], "Pendente")
        self.assertEqual(proposal["activity"], "Analise de documentos")
        self.assertEqual(proposal["processing_status"]["status"], True)
        self.assertEqual(proposal["amounts"]["released"], 1000.50)
        self.assertEqual(proposal["observations"][0]["text"], "Documento pendente")

    def test_parse_attached_documents_omits_content_by_default(self) -> None:
        payload = parse_attached_documents_response(
            DOCUMENTS_XML,
            requested_proposal_number="123456",
            requested_document_type="Nao_Definido",
        )

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["files"][0]["file_name"], "ccb.pdf")
        self.assertEqual(payload["files"][0]["document_type"], "CCB_Negociavel")
        self.assertNotIn("file_base64", payload["files"][0])
        self.assertEqual(payload["processing_status"]["status"], True)

    def test_parse_attached_documents_can_include_content(self) -> None:
        payload = parse_attached_documents_response(
            DOCUMENTS_XML,
            requested_proposal_number="123456",
            requested_document_type="Nao_Definido",
            include_content=True,
        )

        self.assertEqual(payload["files"][0]["file_base64"], "YWJj")

    def test_build_proposal_analysis_flags_missing_documents(self) -> None:
        proposal = parse_proposal_response(PROPOSAL_XML)
        analysis = build_proposal_analysis(
            proposal,
            {"proposal_number": "123456", "files": [], "count": 0},
        )

        self.assertEqual(analysis["facts"]["proposal_number"], "123456")
        self.assertTrue(analysis["inferences"]["has_blocking_signals"])
        self.assertIn(
            "Nenhum documento anexado retornado pela BPO.",
            analysis["inferences"]["attention_points"],
        )

    def test_parse_proposals_by_cpf_response(self) -> None:
        payload = parse_proposals_by_cpf_response(PROPOSALS_BY_CPF_XML, "12345678901")

        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["masked_cpf"], "123.***.***-01")
        self.assertEqual(payload["proposals"][0]["proposal_number"], 123456)
        self.assertEqual(payload["proposals"][0]["situation_kind"], "integrada")
        self.assertEqual(payload["proposals"][0]["is_eligible"], True)
        self.assertEqual(payload["proposals"][1]["situation_kind"], "pendente")

    def test_build_cpf_proposals_analysis(self) -> None:
        payload = parse_proposals_by_cpf_response(PROPOSALS_BY_CPF_XML, "12345678901")
        analysis = build_cpf_proposals_analysis(payload)

        self.assertEqual(analysis["facts"]["total"], 2)
        self.assertEqual(analysis["facts"]["eligible_count"], 1)
        self.assertEqual(analysis["facts"]["under_analysis_count"], 1)
        self.assertEqual(
            analysis["facts"]["latest_integrated_or_approved"]["proposal_number"],
            123456,
        )

    def test_situation_kind_maps_known_bpo_codes(self) -> None:
        self.assertEqual(situation_kind("INT"), "integrada")
        self.assertEqual(situation_kind("INTEGRADA"), "integrada")
        self.assertEqual(situation_kind("APR"), "aprovada")
        self.assertEqual(situation_kind("APROVADA"), "aprovada")
        self.assertEqual(situation_kind("CAD"), "cadastrada")
        self.assertEqual(situation_kind("PEN"), "pendente")
        self.assertEqual(situation_kind("AND"), "andamento")
        self.assertEqual(situation_kind("REP"), "reprovada")
        self.assertEqual(situation_kind("DESCONHECIDA"), "desconhecida")

    def test_operational_eligibility_uses_configured_policy(self) -> None:
        self.assertTrue(is_operationally_eligible("INT", "3", 1.0))
        self.assertTrue(is_operationally_eligible("APR", 3, 1.0))
        self.assertFalse(is_operationally_eligible("PEN", "3", 1.0))
        self.assertFalse(is_operationally_eligible("INT", "2", 1.0))
        self.assertFalse(is_operationally_eligible("INT", "3", 0.0))
        self.assertFalse(is_operationally_eligible("DESCONHECIDA", "3", 1.0))

        policy = BpoEligibilityPolicy(
            eligible_situations=("PEN",),
            eligible_proposal_types=("2",),
            require_positive_withdraw_limit=False,
        )
        self.assertTrue(is_operationally_eligible("PEN", "2", 0.0, policy=policy))

    def test_forbidden_url_patterns_are_user_configured(self) -> None:
        self.assertEqual(
            first_matching_forbidden_pattern(
                "https://example.com/internal-api/proposals",
                ("/internal-api",),
            ),
            "/internal-api",
        )
        self.assertEqual(first_matching_forbidden_pattern("https://example.com/bpo", ()), "")

    def test_latest_integrated_or_approved_prioritizes_integrated_over_newer_approved(self) -> None:
        payload = {
            "cpf": "12345678901",
            "masked_cpf": "123.***.***-01",
            "count": 2,
            "proposals": [
                {
                    "proposal_number": 123456,
                    "situation": "INT",
                    "situation_kind": "integrada",
                    "proposal_type": "3",
                    "is_eligible": True,
                    "last_due_date": "2026-01-10T00:00:00",
                    "withdraw_limit": 500.0,
                },
                {
                    "proposal_number": 123457,
                    "situation": "APR",
                    "situation_kind": "aprovada",
                    "proposal_type": "3",
                    "is_eligible": True,
                    "last_due_date": "2026-12-10T00:00:00",
                    "withdraw_limit": 500.0,
                },
            ],
        }

        analysis = build_cpf_proposals_analysis(payload)

        self.assertEqual(
            analysis["facts"]["latest_integrated_or_approved"]["proposal_number"],
            123456,
        )


if __name__ == "__main__":
    unittest.main()
