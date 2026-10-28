"""已有 Python 程序：校验订单基础字段，不依赖 MCP、数据库或模型。"""
import json
import sys
from datetime import datetime
from pathlib import Path


def check_orders(records: list) -> dict:
    if not isinstance(records, list) or len(records) > 1000:
        raise ValueError("输入必须为最多 1000 条记录的数组")
    issues = []
    seen = set()
    for row, record in enumerate(records, 1):
        errors = []
        if not isinstance(record, dict):
            issues.append({"row": row, "errors": ["记录必须为对象"]})
            continue
        order_id = record.get("id")
        if not isinstance(order_id, str) or not order_id.strip():
            errors.append("id 必须为非空字符串")
        elif order_id in seen:
            errors.append("id 重复")
        else:
            seen.add(order_id)
        if record.get("status") not in ("paid", "shipped", "cancelled"):
            errors.append("status 必须为 paid/shipped/cancelled")
        quantity = record.get("quantity")
        if type(quantity) is not int or quantity <= 0:
            errors.append("quantity 必须为正整数")
        try:
            paid_at = datetime.fromisoformat(record["paid_at"])
            if paid_at.utcoffset() is None:
                raise ValueError("缺少时区")
        except (KeyError, TypeError, ValueError):
            errors.append("paid_at 必须为带时区的 ISO 时间")
        if errors:
            issues.append({"row": row, "errors": errors})
    return {"valid": not issues, "record_count": len(records),
            "error_count": sum(len(i["errors"]) for i in issues), "issues": issues}


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise ValueError("用法：python -m app.checker INPUT.json")
        records = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
        result = check_orders(records)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["valid"] else 1
    except (OSError, ValueError) as error:
        print(json.dumps({"execution_error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
