"""CLI: run corporate-events pipeline on a document batch."""

from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

from config.settings import get_settings
from output.exceptions_report import write_exceptions_report
from output.record_builder import build_document_output, write_document_json
from pipeline.orchestrator import run_pipeline


def _list_pdfs(input_dir: Path) -> list[Path]:
    pdfs = sorted(input_dir.glob("*.pdf"))
    return [p for p in pdfs if p.is_file()]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Process corporate-event PDFs and write JSON records + exceptions report."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Directory with PDF notices (default: DOCUMENTS_PATH / documents/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output/)",
    )
    return parser.parse_args(argv)


def run_batch(input_dir: Path, output_dir: Path) -> int:
    settings = get_settings()
    if not input_dir.is_dir():
        print(f"ERROR: input directory not found: {input_dir}", file=sys.stderr)
        return 1
    if not settings.openai_api_key:
        print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    pdfs = _list_pdfs(input_dir)
    if not pdfs:
        print(f"ERROR: no PDF files in {input_dir}", file=sys.stderr)
        return 1

    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)

    payloads: list[dict] = []
    failures = 0
    total = len(pdfs)

    print(f"Processing {total} document(s) from {input_dir} -> {output_dir}")
    for index, pdf_path in enumerate(pdfs, start=1):
        print(f"[{index}/{total}] {pdf_path.name} ...", flush=True)
        try:
            state = run_pipeline(pdf_path, settings)
            payload = build_document_output(state, settings)
            out_path = records_dir / f"{state.document_id}.json"
            write_document_json(payload, out_path)
            payloads.append(payload)
            route = state.route_decision or "?"
            overall = (
                f"{state.overall_confidence:.3f}"
                if state.overall_confidence is not None
                else "-"
            )
            tipo = (
                state.record.tipo_evento.value
                if state.record and state.record.tipo_evento
                else "-"
            )
            print(
                f"  -> ok | tipo={tipo} | route={route} | overall={overall} | "
                f"wrote {out_path}",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001 - batch continues
            failures += 1
            print(f"  -> FAIL: {exc}", file=sys.stderr, flush=True)
            traceback.print_exc()

    report_path = write_exceptions_report(
        payloads,
        output_dir / "exceptions_report.md",
    )
    print(f"Exceptions report: {report_path}")
    print(f"Done. success={len(payloads)} fail={failures}")
    return 0 if failures == 0 else 2


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = get_settings()
    input_dir = args.input if args.input is not None else settings.documents_path
    return run_batch(input_dir, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
