"""由人工在独立终端执行，审批令牌通过隐藏输入读取。"""
import argparse
import getpass
import json
import httpx


def main():
    parser = argparse.ArgumentParser(description="查看订单清单并提交人工审批")
    parser.add_argument("workflow_id")
    parser.add_argument("--decision", choices=["approve", "reject"], required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    token = getpass.getpass("审批令牌（不会显示）：")
    with httpx.Client(base_url=args.url, headers={"Authorization": f"Bearer {token}"}, timeout=10, trust_env=False) as client:
        response = client.get(f"/workflows/{args.workflow_id}")
        response.raise_for_status()
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        answer = input(f"确认对上述清单提交 {args.decision}？输入工作流编号确认：")
        if answer.strip() != args.workflow_id:
            print("未确认，未提交审批")
            return
        response = client.post(f"/workflows/{args.workflow_id}/decision", json={"decision": args.decision})
        response.raise_for_status()
        print("审批已记录。由 Agent 调用恢复工具后推进流程。")


if __name__ == "__main__":
    main()
