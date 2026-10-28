"""独立复核 CSV：用 SQLite DISTINCT/分组核对口径，不导入生成器。"""
import argparse
import csv
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path

def load(conn,path,name):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f);columns=reader.fieldnames
        conn.execute(f"CREATE TABLE {name} ({','.join(c+' TEXT' for c in columns)})")
        conn.executemany(f"INSERT INTO {name} VALUES ({','.join('?' for _ in columns)})",
                         [tuple(r[c] for c in columns) for r in reader])

def count(db,sql):
    return db.execute(sql).fetchone()[0]

def run(root):
    for chapter in ["第02章","第03章"]:
        folder=root/chapter
        hashes=json.loads((folder/"结果核对/输入SHA256.json").read_text(encoding="utf-8"))
        for name,expected in hashes.items():
            assert hashlib.sha256((folder/"输入资料"/name).read_bytes()).hexdigest()==expected,name
    c2=root/"第02章"; e=json.loads((c2/"结果核对/预期指标.json").read_text(encoding="utf-8"))
    db=sqlite3.connect(":memory:")
    load(db,c2/"输入资料/运维工单.csv","raw")
    db.executescript("""
      CREATE TABLE distinct_tickets AS SELECT DISTINCT * FROM raw;
      CREATE TABLE conflicts AS SELECT ticket_id FROM distinct_tickets GROUP BY ticket_id HAVING COUNT(*)>1;
      CREATE TABLE clean AS SELECT * FROM distinct_tickets WHERE ticket_id NOT IN (SELECT ticket_id FROM conflicts);
      CREATE TABLE overdue AS SELECT * FROM clean WHERE status IN ('待处理','处理中')
      AND (julianday('2026-10-12T12:00:00+08:00')-julianday(created_at))*24 >
        CASE priority WHEN 'P1' THEN 4 WHEN 'P2' THEN 12 WHEN 'P3' THEN 24 ELSE 48 END;
    """)
    for key,sql in {
      "raw_rows":"SELECT COUNT(*) FROM raw",
      "exact_duplicate_rows":"SELECT (SELECT COUNT(*) FROM raw)-(SELECT COUNT(*) FROM distinct_tickets)",
      "conflict_ticket_ids":"SELECT COUNT(*) FROM conflicts",
      "usable_tickets":"SELECT COUNT(*) FROM clean",
      "pending_tickets":"SELECT COUNT(*) FROM clean WHERE status IN ('待处理','处理中')",
      "overdue_tickets":"SELECT COUNT(*) FROM overdue",
      "high_priority_overdue":"SELECT COUNT(*) FROM overdue WHERE priority IN ('P1','P2')",
      "missing_owner":"SELECT COUNT(*) FROM clean WHERE owner=''",
      "overdue_missing_owner":"SELECT COUNT(*) FROM overdue WHERE owner=''"
    }.items(): assert count(db,sql)==e[key],key
    top=[r[0] for r in db.execute("SELECT ticket_id FROM overdue WHERE priority IN ('P1','P2') ORDER BY priority,created_at,ticket_id LIMIT 20")]
    assert top==e["top20_ids"]
    db.close()
    c3=root/"第03章";e=json.loads((c3/"结果核对/预期指标.json").read_text(encoding="utf-8"))
    db=sqlite3.connect(":memory:")
    for filename,name in [("订单导出","orders"),("支付流水","payments"),("发货记录","ships"),("商品主数据","products"),("库存快照","stocks")]:
        load(db,c3/f"输入资料/{filename}.csv",name)
    db.executescript("""
      CREATE TABLE distinct_orders AS SELECT DISTINCT * FROM orders;
      CREATE TABLE conflicts AS SELECT order_id FROM distinct_orders GROUP BY order_id HAVING COUNT(*)>1;
      CREATE TABLE clean AS SELECT * FROM distinct_orders WHERE order_id NOT IN (SELECT order_id FROM conflicts);
      CREATE TABLE valid AS SELECT * FROM clean WHERE CAST(quantity AS INTEGER)>0
       AND status IN ('已支付','已发货','待支付','已取消') AND sku IN (SELECT sku FROM products);
      CREATE TABLE distinct_payments AS SELECT DISTINCT * FROM payments;
      CREATE TABLE payment_groups AS SELECT order_id,COUNT(*) AS n,SUM(CAST(amount_cents AS INTEGER)) AS amount
       FROM distinct_payments WHERE result='成功' GROUP BY order_id;
      CREATE TABLE joined AS SELECT v.*,COALESCE(p.n,0) AS n,p.amount FROM valid v LEFT JOIN payment_groups p USING(order_id);
      CREATE TABLE overdue AS SELECT v.* FROM valid v WHERE status='已支付'
       AND (julianday('2026-10-12T12:00:00+08:00')-julianday(paid_at))*24>24;
    """)
    checks={
      "raw_order_rows":"SELECT COUNT(*) FROM orders",
      "exact_duplicate_order_rows":"SELECT (SELECT COUNT(*) FROM orders)-(SELECT COUNT(*) FROM distinct_orders)",
      "conflict_order_ids":"SELECT COUNT(*) FROM conflicts",
      "invalid_orders":"SELECT (SELECT COUNT(*) FROM clean)-(SELECT COUNT(*) FROM valid)",
      "usable_orders":"SELECT COUNT(*) FROM valid",
      "missing_channel":"SELECT COUNT(*) FROM valid WHERE channel=''",
      "paid_status_orders":"SELECT COUNT(*) FROM valid WHERE status IN ('已支付','已发货')",
      "paid_status_amount_cents":"SELECT SUM(CAST(order_amount_cents AS INTEGER)) FROM valid WHERE status IN ('已支付','已发货')",
      "payment_raw_rows":"SELECT COUNT(*) FROM payments",
      "payment_exact_duplicate_rows":"SELECT (SELECT COUNT(*) FROM payments)-(SELECT COUNT(*) FROM distinct_payments)",
      "unique_payment_rows":"SELECT COUNT(*) FROM distinct_payments",
      "orphan_payment_rows":"SELECT COUNT(*) FROM distinct_payments WHERE order_id NOT IN (SELECT order_id FROM orders)",
      "excluded_order_payment_rows":"SELECT COUNT(*) FROM distinct_payments WHERE order_id IN (SELECT order_id FROM orders) AND order_id NOT IN (SELECT order_id FROM valid)",
      "shipment_rows":"SELECT COUNT(*) FROM ships",
      "orphan_shipment_rows":"SELECT COUNT(*) FROM ships WHERE order_id NOT IN (SELECT order_id FROM orders)",
      "excluded_order_shipment_rows":"SELECT COUNT(*) FROM ships WHERE order_id IN (SELECT order_id FROM orders) AND order_id NOT IN (SELECT order_id FROM valid)",
      "overdue_unshipped":"SELECT COUNT(*) FROM overdue",
      "overdue_stock_insufficient":"SELECT COUNT(*) FROM overdue o JOIN stocks s ON o.store=s.store AND o.sku=s.sku WHERE CAST(s.available AS INTEGER)<CAST(o.quantity AS INTEGER)"
    }
    for key,sql in checks.items():assert count(db,sql)==e[key],key
    predicates={
      "缺少成功流水":"status IN ('已支付','已发货') AND n=0",
      "多笔成功流水":"status IN ('已支付','已发货') AND n>1",
      "支付金额不一致":"status IN ('已支付','已发货') AND n=1 AND amount!=CAST(order_amount_cents AS INTEGER)",
      "未支付状态存在成功流水":"status NOT IN ('已支付','已发货') AND n>0"}
    actual_issues={k:count(db,"SELECT COUNT(*) FROM joined WHERE "+condition) for k,condition in predicates.items()}
    assert actual_issues==e["payment_issues"]
    assert sum(actual_issues.values())==e["payment_issue_orders"]
    assert dict(db.execute("SELECT status,COUNT(*) FROM valid GROUP BY status"))==e["by_status"]
    for store,values in e["by_store"].items():
        rows=db.execute("SELECT status,order_amount_cents FROM valid WHERE store=?",(store,)).fetchall()
        paid=[r for r in rows if r[0] in ("已支付","已发货")]
        assert dict(orders=len(rows),paid_orders=len(paid),paid_amount_cents=sum(int(r[1]) for r in paid))==values
    for table,keys in [("products",["sku"]),("stocks",["store","sku"])]:
        assert count(db,f"SELECT COUNT(*) FROM {table}")==count(db,f"SELECT COUNT(*) FROM (SELECT DISTINCT {','.join(keys)} FROM {table})")
    # 发货只能发生在支付之后，且不超过数据基准时间；孤立发货只检验时间上界。
    as_of=datetime.fromisoformat("2026-10-12T12:00:00+08:00")
    for shipped,paid in db.execute("SELECT s.shipped_at,o.paid_at FROM ships s LEFT JOIN distinct_orders o USING(order_id)"):
        assert datetime.fromisoformat(shipped)<=as_of
        if paid:assert datetime.fromisoformat(shipped)>datetime.fromisoformat(paid)
    db.close()
    print("PASS: input hashes, ticket scope/SLA/Top20, order cleaning, joins, integer amounts, anomaly counts and timestamps")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True,help="包含第02章、第03章的目录")
    run(parser.parse_args().root)
