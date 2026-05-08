#!/usr/bin/env python3
"""
やよいの青色申告オンライン／弥生会計オンライン「スマート取引取込」用 CSV ジェネレータ。

弥生は Shift-JIS / CR+LF / 9 桁以内の金額 / 80 文字以内の摘要 を要求する。
このスクリプトは制約を検証したうえで、要件を満たした CSV を stdout に出力する。

入力 (stdin, JSON):
    [
      {
        "date": "2024/06/15",       # 必須。西暦 4 桁または和暦 (R/令和/令) で記述
        "income": 0,                # 入金額 (整数, 0-999999999)
        "outcome": 3280,            # 出金額 (整数, 0-999999999)
        "description": "さくら電器 ワイヤレスマウス",  # 任意 (80 文字超は切り捨て)
        "reduced_tax": false,       # 任意。true なら軽減税率欄に "※"
        "department": "",           # 任意 (24 文字以内)
        "invoice_class": ""         # 任意
      },
      ...
    ]

オプション:
    --header       1 行目にヘッダーを出力する
    --output PATH  ファイルに書き出す (省略時は stdout)
    --max-bytes N  出力サイズが N バイトを超えたらエラー (default: 200000)

使い方:
    python3 build_csv.py < transactions.json > out.csv
    python3 build_csv.py --header --output out.csv < transactions.json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from typing import Any

HEADER = ["日付", "入金", "出金", "摘要", "軽減税率", "部門", "請求書区分"]
MAX_AMOUNT = 999_999_999  # 9 桁
MAX_DESCRIPTION = 80
MAX_DEPARTMENT = 24
DEFAULT_MAX_BYTES = 200_000  # 200 KB 未満


def _validate_amount(value: Any, field: str, idx: int) -> int:
    if value in (None, ""):
        return 0
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"row {idx}: {field} must be an integer, got {value!r}")
    if value < 0:
        raise ValueError(f"row {idx}: {field} must be non-negative, got {value}")
    if value > MAX_AMOUNT:
        raise ValueError(
            f"row {idx}: {field}={value} exceeds 9-digit limit ({MAX_AMOUNT})"
        )
    return value


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]


def _row_from_transaction(tx: dict[str, Any], idx: int) -> list[str]:
    if "date" not in tx or not tx["date"]:
        raise ValueError(f"row {idx}: 'date' is required")
    date = str(tx["date"]).strip()

    income = _validate_amount(tx.get("income", 0), "income", idx)
    outcome = _validate_amount(tx.get("outcome", 0), "outcome", idx)
    if income == 0 and outcome == 0:
        raise ValueError(
            f"row {idx}: both income and outcome are 0; remove the row instead"
        )
    if income > 0 and outcome > 0:
        raise ValueError(
            f"row {idx}: income and outcome are both non-zero; pick one"
        )

    description = _truncate(str(tx.get("description", "")), MAX_DESCRIPTION)
    reduced_tax = "※" if tx.get("reduced_tax") else ""

    department = str(tx.get("department", ""))
    if len(department) > MAX_DEPARTMENT:
        raise ValueError(
            f"row {idx}: department exceeds {MAX_DEPARTMENT} chars: {department!r}"
        )

    invoice_class = str(tx.get("invoice_class", ""))

    return [
        date,
        str(income) if income > 0 else "",
        str(outcome) if outcome > 0 else "",
        description,
        reduced_tax,
        department,
        invoice_class,
    ]


def build_csv(transactions: list[dict[str, Any]], include_header: bool) -> bytes:
    """取引リストから Shift-JIS / CRLF の CSV バイト列を返す。"""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)

    if include_header:
        writer.writerow(HEADER)

    for idx, tx in enumerate(transactions, start=1):
        writer.writerow(_row_from_transaction(tx, idx))

    text = buf.getvalue()
    try:
        return text.encode("cp932")
    except UnicodeEncodeError as exc:
        # cp932 で表現できない文字を特定して報告
        bad = text[exc.start : exc.end]
        raise ValueError(
            f"Shift-JIS で表現できない文字が含まれています: {bad!r} "
            f"(摘要などから該当文字を除去してください)"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--header", action="store_true", help="ヘッダー行を出力する")
    parser.add_argument("--output", "-o", help="出力ファイルパス (省略時は stdout)")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"出力サイズの上限バイト数 (default: {DEFAULT_MAX_BYTES})",
    )
    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        print("error: stdin is empty (expected JSON array of transactions)", file=sys.stderr)
        return 1

    try:
        transactions = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(transactions, list):
        print("error: top-level JSON must be an array", file=sys.stderr)
        return 1

    try:
        data = build_csv(transactions, include_header=args.header)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if len(data) >= args.max_bytes:
        print(
            f"error: output is {len(data)} bytes (>= {args.max_bytes}); "
            "弥生は 200KB 未満を要求するので期間で分割してください",
            file=sys.stderr,
        )
        return 1

    if args.output:
        with open(args.output, "wb") as f:
            f.write(data)
    else:
        sys.stdout.buffer.write(data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
