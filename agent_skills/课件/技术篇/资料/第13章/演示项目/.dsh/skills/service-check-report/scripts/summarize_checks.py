"""离线电商服务巡检汇总，Python 标准库实现。"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

FIELDS = {"id", "service", "path", "status_code", "elapsed_ms"}


def summarize(data):
    if not isinstance(data, list) or not data:
        raise ValueError("输入必须是非空 JSON 数组")
    seen, items = set(), []
    for index, item in enumerate(data, 1):
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise ValueError(f"第 {index} 条字段缺失、多余或不是对象")
        for key in ("id", "service", "path"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise ValueError(f"第 {index} 条 {key} 必须是非空字符串")
        if item["id"] in seen:
            raise ValueError(f"重复记录ID：{item['id']}")
        seen.add(item["id"])
        code, duration = item["status_code"], item["elapsed_ms"]
        if type(code) is not int or not 100 <= code <= 599:
            raise ValueError(f"第 {index} 条状态码非法")
        if type(duration) is not int or duration < 0:
            raise ValueError(f"第 {index} 条耗时非法")
        category = ("失败" if not 200 <= code < 300 else
                    "慢响应" if duration >= 1000 else "正常")
        items.append({**item, "category": category})
    counts = Counter(x["category"] for x in items)
    return {"total": len(items), "normal": counts["正常"],
            "slow": counts["慢响应"], "failed": counts["失败"],
            "items": items}


def main():
    parser = argparse.ArgumentParser(description="汇总离线巡检结果")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    source = Path(args.input).resolve()
    output = Path(args.output_dir).resolve()
    try:
        if output.exists():
            raise ValueError("输出目录已存在，请使用新的目录")
        result = summarize(json.loads(source.read_text(encoding="utf-8-sig")))
        result["input_file"] = str(source)
        output.mkdir(parents=True, exist_ok=False)
        with (output / "巡检汇总.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        print(f"汇总已生成：{output}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"处理失败：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
