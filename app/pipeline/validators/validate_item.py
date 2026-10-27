"""Validator gabungan: menjalankan semua validator atas satu Item.

Urutan dan aturan berhentinya sama persis dengan orchestrator
Fase 2B: schema, ast, lint, sandbox, lalu fill_blank, dan
berhenti di kegagalan pertama. Dipakai endpoint edit, supaya
butir hasil edit diperiksa dengan aturan yang sama seperti
kandidat hasil generate.
"""

from app.pipeline.validators.ast_check import validate_ast
from app.pipeline.validators.fill_blank_check import validate_fill_blank
from app.pipeline.validators.lint_check import validate_lint
from app.pipeline.validators.sandbox_check import validate_sandbox
from app.pipeline.validators.schema_check import validate_schema
from app.schemas import Item, ValidationReport


def validate_item(item: Item) -> ValidationReport:
    """Memeriksa satu Item dengan semua validator, berurutan."""
    _, hasil_schema = validate_schema(item.model_dump(mode="json"))
    hasil = [hasil_schema]
    if not hasil_schema.passed:
        return ValidationReport(results=hasil)
    for periksa in (
        validate_ast,
        validate_lint,
        validate_sandbox,
        validate_fill_blank,
    ):
        hasil.append(periksa(item))
        if not hasil[-1].passed:
            break
    return ValidationReport(results=hasil)
