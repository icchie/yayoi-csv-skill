#!/usr/bin/env python3
"""build_csv の self-test.

CI から呼ぶ想定。失敗があれば exit code 1 を返す。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_csv import build_csv  # noqa: E402

MAX_BYTES = 200_000


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_examples_round_trip() -> None:
    """examples/transactions.json から examples/sample-*.csv が再生成できることを確認。"""
    transactions = json.loads((ROOT / "examples" / "transactions.json").read_text("utf-8"))

    with_header = build_csv(transactions, include_header=True)
    expected_with = (ROOT / "examples" / "sample-with-header.csv").read_bytes()
    _assert(
        with_header == expected_with,
        "sample-with-header.csv does not match build_csv output",
    )

    no_header = build_csv(transactions, include_header=False)
    expected_no = (ROOT / "examples" / "sample-no-header.csv").read_bytes()
    _assert(
        no_header == expected_no,
        "sample-no-header.csv does not match build_csv output",
    )


def test_output_is_shift_jis_crlf() -> None:
    transactions = json.loads((ROOT / "examples" / "transactions.json").read_text("utf-8"))
    data = build_csv(transactions, include_header=True)

    _assert(b"\r\n" in data, "output must contain CRLF")
    _assert(not data.replace(b"\r\n", b"").count(b"\n"), "output must not contain bare LF")
    data.decode("cp932")  # raises if not valid Shift-JIS
    _assert(len(data) < MAX_BYTES, f"output {len(data)} bytes >= {MAX_BYTES}")


def test_amount_9_digit_guard() -> None:
    try:
        build_csv(
            [{"date": "2024/01/01", "income": 1_234_567_890, "outcome": 0}],
            include_header=False,
        )
    except ValueError:
        return
    raise AssertionError("9-digit guard did not trigger")


def test_zero_zero_guard() -> None:
    try:
        build_csv(
            [{"date": "2024/01/01", "income": 0, "outcome": 0}],
            include_header=False,
        )
    except ValueError:
        return
    raise AssertionError("zero-zero guard did not trigger")


def test_both_nonzero_guard() -> None:
    try:
        build_csv(
            [{"date": "2024/01/01", "income": 100, "outcome": 100}],
            include_header=False,
        )
    except ValueError:
        return
    raise AssertionError("both-nonzero guard did not trigger")


def test_non_cp932_guard() -> None:
    try:
        build_csv(
            [{"date": "2024/01/01", "income": 0, "outcome": 100, "description": "🦉"}],
            include_header=False,
        )
    except ValueError:
        return
    raise AssertionError("non-cp932 guard did not trigger")


def test_description_truncation() -> None:
    long = "あ" * 100
    out = build_csv(
        [{"date": "2024/01/01", "income": 0, "outcome": 100, "description": long}],
        include_header=False,
    )
    text = out.decode("cp932")
    # 摘要セルが 80 文字に切り詰められていること
    cells = text.rstrip("\r\n").split(",")
    _assert(cells[3] == "あ" * 80, f"description not truncated to 80 chars: got {len(cells[3])}")


def test_reduced_tax_mark() -> None:
    out = build_csv(
        [
            {
                "date": "2024/01/01",
                "income": 0,
                "outcome": 100,
                "description": "お茶",
                "reduced_tax": True,
            }
        ],
        include_header=False,
    ).decode("cp932")
    _assert("※" in out, "reduced_tax mark missing")


def test_department_length_guard() -> None:
    try:
        build_csv(
            [
                {
                    "date": "2024/01/01",
                    "income": 0,
                    "outcome": 100,
                    "department": "あ" * 25,
                }
            ],
            include_header=False,
        )
    except ValueError:
        return
    raise AssertionError("department length guard did not trigger")


def test_missing_date_guard() -> None:
    try:
        build_csv([{"income": 0, "outcome": 100}], include_header=False)
    except ValueError:
        return
    raise AssertionError("missing-date guard did not trigger")


def main() -> int:
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {test.__name__}: {exc}", file=sys.stderr)
        else:
            print(f"PASS {test.__name__}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
