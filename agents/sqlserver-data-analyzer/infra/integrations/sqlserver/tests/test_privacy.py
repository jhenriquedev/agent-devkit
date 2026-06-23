#!/usr/bin/env python3
"""Privacy and masking tests for sqlserver-data-analyzer.

Covers G6: mask_if_sensitive must handle CPF, CNPJ, email, phone, name,
address, token, and password. Also covers CPF helpers (G11).
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

# Add runner_support to path
RUNNER_SUPPORT_DIR = Path(__file__).resolve().parents[4] / "capabilities" / "_shared"

# Also add sqlserver dir for repository helpers
SQLSERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SQLSERVER_DIR))

def load_runner_support():
    spec = importlib.util.spec_from_file_location(
        "sqlserver_data_analyzer_runner_support",
        RUNNER_SUPPORT_DIR / "runner_support.py",
    )
    if spec is None or spec.loader is None:
        raise ImportError("cannot load sqlserver data analyzer runner_support")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_runner_support = load_runner_support()
mask_address = _runner_support.mask_address
mask_cnpj = _runner_support.mask_cnpj
mask_cpf = _runner_support.mask_cpf
mask_email = _runner_support.mask_email
mask_if_sensitive = _runner_support.mask_if_sensitive
mask_name = _runner_support.mask_name
mask_phone = _runner_support.mask_phone
from sqlserver_repository import (  # noqa: E402
    analyze_cpf_values,
    is_valid_cpf,
)


class MaskCpfTest(unittest.TestCase):
    def test_mask_valid_cpf(self) -> None:
        result = mask_cpf("123.456.789-09")
        self.assertTrue(result.startswith("123."))
        self.assertNotIn("456", result)
        self.assertTrue(result.endswith("-09"))

    def test_mask_invalid_cpf_passthrough(self) -> None:
        result = mask_cpf("not-a-cpf")
        self.assertEqual(result, "not-a-cpf")

    def test_mask_cpf_plain_digits(self) -> None:
        result = mask_cpf("12345678909")
        self.assertTrue(result.startswith("123."))
        self.assertTrue(result.endswith("-09"))


class MaskCnpjTest(unittest.TestCase):
    def test_mask_valid_cnpj(self) -> None:
        result = mask_cnpj("12.345.678/0001-95")
        self.assertTrue(result.startswith("12."))
        self.assertTrue(result.endswith("-95"))
        self.assertNotIn("345", result)

    def test_mask_invalid_cnpj_passthrough(self) -> None:
        result = mask_cnpj("not-a-cnpj")
        self.assertEqual(result, "not-a-cnpj")

    def test_mask_cnpj_plain_digits(self) -> None:
        result = mask_cnpj("12345678000195")
        self.assertTrue(result.startswith("12."))
        self.assertTrue(result.endswith("-95"))


class MaskEmailTest(unittest.TestCase):
    def test_mask_email(self) -> None:
        result = mask_email("user@example.com")
        self.assertIn("***@", result)
        self.assertNotIn("user", result)
        self.assertTrue(result.endswith("example.com"))

    def test_mask_email_no_at_passthrough(self) -> None:
        result = mask_email("noemail")
        self.assertEqual(result, "noemail")


class MaskPhoneTest(unittest.TestCase):
    def test_mask_phone_number(self) -> None:
        result = mask_phone("(11) 99999-8877")
        self.assertTrue(result.endswith("77"))
        self.assertNotIn("9999", result)

    def test_mask_short_value_passthrough(self) -> None:
        result = mask_phone("123")
        self.assertEqual(result, "123")


class MaskNameTest(unittest.TestCase):
    def test_mask_full_name(self) -> None:
        result = mask_name("João Silva")
        self.assertNotIn("João", result)
        self.assertNotIn("Silva", result)
        self.assertIn("***", result)

    def test_mask_single_word(self) -> None:
        result = mask_name("Maria")
        self.assertIn("***", result)
        self.assertNotIn("Maria", result)

    def test_mask_empty_passthrough(self) -> None:
        result = mask_name("-")
        self.assertEqual(result, "-")


class MaskAddressTest(unittest.TestCase):
    def test_mask_address(self) -> None:
        result = mask_address("Rua das Flores, 123")
        self.assertTrue(result.startswith("Rua"))
        self.assertIn("***", result)
        self.assertNotIn("123", result)

    def test_mask_empty_passthrough(self) -> None:
        result = mask_address("-")
        self.assertEqual(result, "-")


class MaskIfSensitiveTest(unittest.TestCase):
    """Integration tests: mask_if_sensitive dispatches correctly for all PII types."""

    def test_cpf_column_masked(self) -> None:
        result = mask_if_sensitive("cpf_cliente", "123.456.789-09")
        self.assertNotIn("456", result)

    def test_cnpj_column_masked(self) -> None:
        result = mask_if_sensitive("cnpj_empresa", "12.345.678/0001-95")
        self.assertNotIn("345", result)

    def test_email_column_masked(self) -> None:
        result = mask_if_sensitive("email", "user@example.com")
        self.assertIn("***@", result)

    def test_telefone_column_masked(self) -> None:
        result = mask_if_sensitive("telefone", "(11) 99999-8877")
        self.assertNotIn("9999", result)

    def test_phone_column_masked(self) -> None:
        result = mask_if_sensitive("phone_number", "(11) 99999-8877")
        self.assertNotIn("9999", result)

    def test_celular_column_masked(self) -> None:
        result = mask_if_sensitive("celular", "(11) 99999-8877")
        self.assertNotIn("9999", result)

    def test_nome_column_masked(self) -> None:
        result = mask_if_sensitive("nome_cliente", "João Silva")
        self.assertNotIn("João", result)

    def test_address_column_masked(self) -> None:
        result = mask_if_sensitive("endereco", "Rua das Flores, 123")
        self.assertIn("***", result)

    def test_token_column_masked(self) -> None:
        result = mask_if_sensitive("api_key", "super-secret-token")
        self.assertEqual(result, "***")

    def test_password_column_masked(self) -> None:
        result = mask_if_sensitive("password", "my-pass")
        self.assertEqual(result, "***")

    def test_senha_column_masked(self) -> None:
        result = mask_if_sensitive("senha_hash", "bcrypt-hash")
        self.assertEqual(result, "***")

    def test_non_sensitive_column_passthrough(self) -> None:
        result = mask_if_sensitive("product_name", "Widget A")
        # product_name ends with "_name" — note: spec says name columns are masked
        # This should be masked per spec (mask_name)
        self.assertIn("***", result)

    def test_plain_column_passthrough(self) -> None:
        result = mask_if_sensitive("price", "99.90")
        self.assertEqual(result, "99.90")

    def test_status_column_passthrough(self) -> None:
        result = mask_if_sensitive("status", "active")
        self.assertEqual(result, "active")


class CpfValidationTest(unittest.TestCase):
    def test_valid_cpf(self) -> None:
        # CPF 529.982.247-25 is a known-valid test CPF
        self.assertTrue(is_valid_cpf("52998224725"))

    def test_invalid_cpf_repeated_digits(self) -> None:
        self.assertFalse(is_valid_cpf("11111111111"))

    def test_invalid_cpf_wrong_check_digit(self) -> None:
        self.assertFalse(is_valid_cpf("12345678901"))

    def test_invalid_cpf_wrong_length(self) -> None:
        self.assertFalse(is_valid_cpf("123"))


class AnalyzeCpfValuesTest(unittest.TestCase):
    def test_no_cpf_values_exposed(self) -> None:
        cpfs = ["52998224725", "52998224725", "00000000000", "invalid", ""]
        result = analyze_cpf_values(cpfs, schema="dbo", table="customers", column="cpf")
        # Must not contain any actual CPF strings
        result_str = str(result)
        self.assertNotIn("52998224725", result_str)
        self.assertIn("total_rows", result)
        self.assertEqual(result["total_rows"], 5)

    def test_blank_count(self) -> None:
        result = analyze_cpf_values(["", None, "52998224725"], schema="s", table="t", column="c")
        self.assertEqual(result["blank_count"], 2)

    def test_duplicated_count(self) -> None:
        result = analyze_cpf_values(["52998224725", "52998224725"], schema="s", table="t", column="c")
        self.assertEqual(result["duplicated_document_count"], 1)
        self.assertEqual(result["duplicated_row_count"], 2)

    def test_repeated_digits_count(self) -> None:
        result = analyze_cpf_values(["11111111111"], schema="s", table="t", column="c")
        self.assertEqual(result["repeated_digits_count"], 1)


if __name__ == "__main__":
    unittest.main()
