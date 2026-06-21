#!/usr/bin/env python3
"""Sensitive data detection and masking helpers."""

from __future__ import annotations

import re
from typing import Any

from dataset_io import value_to_string
from dataset_models import Dataset


CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}")

SENSITIVE_NAME_PATTERNS = {
    "cpf": "cpf",
    "cnpj": "cnpj",
    "email": "email",
    "e-mail": "email",
    "telefone": "phone",
    "phone": "phone",
    "celular": "phone",
    "nome": "person_name",
    "name": "person_name",
}


def detect_sensitive(dataset: Dataset) -> dict[str, Any]:
    columns: dict[str, list[str]] = {}
    examples: dict[str, list[str]] = {}
    for column in dataset.columns:
        kinds = set()
        lowered = normalize_name(column)
        for pattern, kind in SENSITIVE_NAME_PATTERNS.items():
            if pattern in lowered:
                kinds.add(kind)
        samples = [row.get(column, "") for row in dataset.rows[:100] if row.get(column, "")]
        if "cpf" in lowered or any(is_formatted_cpf(value) for value in samples):
            kinds.add("cpf")
        if any(CNPJ_RE.search(value) for value in samples):
            kinds.add("cnpj")
        if any(EMAIL_RE.search(value) for value in samples):
            kinds.add("email")
        if (
            lowered not in {"amount", "value", "valor"}
            and "id" not in lowered
            and "codigo" not in lowered
            and "code" not in lowered
            and any(PHONE_RE.fullmatch(value) for value in samples)
        ):
            kinds.add("phone")
        if kinds:
            columns[column] = sorted(kinds)
            examples[column] = [mask_value(column, value) for value in samples[:3]]
    return {
        "has_sensitive_data": bool(columns),
        "columns": columns,
        "masked_examples": examples,
    }


def normalize_name(value: str) -> str:
    return value.strip().casefold().replace("_", " ").replace("-", " ")


def is_formatted_cpf(value: str) -> bool:
    digits = re.sub(r"\D", "", value.strip())
    return bool(re.fullmatch(r"\d{3}\.?\d{3}\.?\d{3}-\d{2}", value.strip())) and is_valid_cpf(digits)


def is_valid_cpf(digits: str) -> bool:
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    numbers = [int(item) for item in digits]
    for size in (9, 10):
        total = sum(numbers[index] * (size + 1 - index) for index in range(size))
        check = (total * 10) % 11
        if check == 10:
            check = 0
        if check != numbers[size]:
            return False
    return True


def is_valid_cnpj(digits: str) -> bool:
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    numbers = [int(item) for item in digits]
    weights = ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    for index, weight_set in enumerate(weights):
        total = sum(number * weight for number, weight in zip(numbers, weight_set))
        check = 11 - (total % 11)
        if check >= 10:
            check = 0
        if check != numbers[12 + index]:
            return False
    return True


def mask_row(row: dict[str, str]) -> dict[str, str]:
    return {column: mask_value(column, value) for column, value in row.items()}


def mask_value(column: str, value: str) -> str:
    text = value_to_string(value)
    lowered = normalize_name(column)
    if not text:
        return text
    digits = re.sub(r"\D", "", text)
    if "telefone" in lowered or "phone" in lowered or "celular" in lowered:
        return f"***{digits[-4:]}" if digits else "***"
    if "nome" in lowered or "name" in lowered:
        return f"{text[:1]}***"
    if "cpf" in lowered or is_valid_cpf(digits):
        return f"***{digits[-2:]}" if digits else "***"
    if "cnpj" in lowered or is_valid_cnpj(digits):
        return f"***{digits[-4:]}" if digits else "***"
    if "email" in lowered or EMAIL_RE.fullmatch(text):
        local, _, domain = text.partition("@")
        return f"{local[:1]}***@{domain}" if domain else "***"
    return text
