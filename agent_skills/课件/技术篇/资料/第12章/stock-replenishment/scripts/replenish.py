"""按固定库存规则测算补货；只使用 Python 标准库。"""
import argparse
import json
import sys
from pathlib import Path

TEXT_FIELDS = ("warehouse", "sku", "product")
NUMBER_FIELDS = ("sales_7d", "available", "inbound",
                 "lead_days", "safety_days", "pack_size")
FIELDS = set(TEXT_FIELDS + NUMBER_FIELDS)


def validate(data):
    if not isinstance(data, list) or not data:
        raise ValueError("输入必须是非空 JSON 数组")
    rows, seen = [], set()
    for index, raw in enumerate(data, 1):
        if not isinstance(raw, dict) or set(raw) != FIELDS:
            raise ValueError(f"第 {index} 条字段缺失、多余或不是对象")
        row = dict(raw)
        for key in TEXT_FIELDS:
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError(f"第 {index} 条 {key} 必须是非空字符串")
            row[key] = row[key].strip()
        for key in NUMBER_FIELDS:
            minimum = 1 if key in ("lead_days", "pack_size") else 0
            if type(row[key]) is not int or row[key] < minimum:
                raise ValueError(f"第 {index} 条 {key} 必须是大于等于 {minimum} 的整数")
        identity = (row["warehouse"], row["sku"])
        if identity in seen:
            raise ValueError(f"第 {index} 条仓库与 SKU 组合重复：{identity}")
        seen.add(identity)
        rows.append(row)
    return rows


def calculate(rows):
    items = []
    for row in rows:
        target = (row["sales_7d"] * (row["lead_days"] + row["safety_days"]) + 6) // 7
        position = row["available"] + row["inbound"]
        gap = max(target - position, 0)
        quantity = ((gap + row["pack_size"] - 1) // row["pack_size"]) * row["pack_size"]
        status = ("零销量待人工判断" if row["sales_7d"] == 0
                  else "建议补货" if quantity > 0 else "暂不补货")
        items.append({**row, "target_stock": target,
                      "stock_position": position, "gap": gap,
                      "suggested_quantity": quantity, "status": status})
    return {
        "rule_version": "1.0",
        "summary": {
            "warehouse_count": len({r["warehouse"] for r in rows}),
            "item_count": len(items),
            "replenish_count": sum(x["suggested_quantity"] > 0 for x in items),
            "total_quantity": sum(x["suggested_quantity"] for x in items),
            "zero_sales_count": sum(x["sales_7d"] == 0 for x in items),
        },
        "items": items,
    }


def main():
    parser = argparse.ArgumentParser(description="生成仓库补货计算结果")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    source = Path(args.input).resolve()
    output = Path(args.output_dir).resolve()
    try:
        if output.exists():
            raise ValueError("输出目录已存在，请使用新目录")
        data = json.loads(source.read_text(encoding="utf-8-sig"))
        result = calculate(validate(data))
        result["input_file"] = str(source)
        # 校验完成才创建输出目录；不允许覆盖已有目录。
        output.mkdir(parents=True, exist_ok=False)
        target = output / "补货计算.json"
        with target.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(f"计算完成：{target}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"处理失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
