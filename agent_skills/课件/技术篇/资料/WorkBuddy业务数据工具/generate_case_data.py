"""生成固定种子的虚构电商案例。仅标准库；目标目录必须不存在。"""
import argparse
import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

AS_OF = datetime(2026, 10, 12, 12, tzinfo=timezone(timedelta(hours=8)))
SLA = {"P1": 4, "P2": 12, "P3": 24, "P4": 48}
STORES = ["华东店", "华南店", "华北店"]

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def group_clean(rows, key):
    unique = {}
    for row in rows:
        unique.setdefault(tuple(row.items()), row)
    groups = defaultdict(list)
    for row in unique.values():
        groups[row[key]].append(row)
    conflicts = {k: v for k, v in groups.items() if len(v) > 1}
    clean = [v[0] for k, v in groups.items() if k not in conflicts]
    return clean, len(rows)-len(unique), conflicts

def make_tickets(rng):
    rows=[]
    systems=["订单中心","支付网关","库存服务","履约接口","商品中心"]
    notes=["支付状态更新滞后","导出字段缺失","库存查询超时","履约同步需核查","商品接口响应慢"]
    for i in range(1,3201):
        level=rng.choices(list(SLA),[8,22,45,25])[0]
        status=rng.choices(["待处理","处理中","已解决","已关闭"],[15,25,40,20])[0]
        if 21 <= i <= 100:
            status="待处理"
        opened=AS_OF-timedelta(hours=rng.randint(1,168), minutes=rng.randint(0,59))
        system=rng.randrange(5)
        rows.append(dict(ticket_id=f"INC{i:05d}",store=rng.choice(STORES),system=systems[system],
            priority=level,status=status,created_at=opened.isoformat(),
            updated_at=(opened+timedelta(minutes=30)).isoformat(),
            owner="" if 21<=i<=100 else rng.choice(["林工","周工","陈工","吴工","赵工"]),
            order_id=f"ORD{rng.randint(1,8000):06d}",summary=notes[system]))
    rows += [dict(rows[i]) for i in range(100,140)]
    rows += [{**rows[i],"owner":"待核验人员"} for i in range(20)]
    rng.shuffle(rows)
    return rows

def make_trade(rng):
    products=[dict(sku=f"SKU{i:03d}",product_name=f"{['蓝牙耳机','机械键盘','显示器支架','充电器'][i%4]}-{i:03d}",
                   category=["数码音频","电脑外设","办公配件","充电配件"][i%4],
                   unit_price_cents=rng.randint(1900,89900)) for i in range(1,81)]
    stocks=[dict(store=s,sku=p["sku"],available=rng.choice([0,0,1,2,5,10,30,80]),
                 snapshot_at=AS_OF.isoformat()) for s in STORES for p in products]
    orders=[]; payments=[]; shipments=[]
    for i in range(1,8001):
        product=rng.choice(products);qty=rng.randint(1,5)
        created=AS_OF-timedelta(hours=rng.randint(2,240),minutes=rng.randint(0,59))
        paid=created+timedelta(hours=1)
        status=rng.choices(["已支付","已发货","待支付","已取消"],[32,48,12,8])[0]
        if 171<=i<=194 or 321<=i<=355 or 366<=i<=375 or 600<=i<=659:
            status="已支付"
        if 356<=i<=365: status="待支付"
        order_id=f"ORD{i:06d}"
        row=dict(order_id=order_id,store=rng.choice(STORES),sku=product["sku"],quantity=qty,
            order_amount_cents=int(product["unit_price_cents"])*qty,status=status,
            channel="" if 71<=i<=170 else rng.choice(["商城App","商城Web","小程序"]),
            created_at=created.isoformat(),paid_at=paid.isoformat() if status in ("已支付","已发货") else "")
        orders.append(row)
        if (status in ("已支付","已发货") and not 321<=i<=355) or 356<=i<=365:
            payment=dict(payment_id=f"PAY{i:06d}",order_id=order_id,result="成功",
                         amount_cents=row["order_amount_cents"]+(100 if 171<=i<=194 else 0),paid_at=paid.isoformat())
            payments.append(payment)
            if 600<=i<=659:payments.append(dict(payment))
            if 366<=i<=375:payments.append({**payment,"payment_id":f"PAYX{i:06d}"})
        if status=="已发货":
            # 必须不晚于基准时刻；不把未来发货记录混入快照。
            elapsed=int((AS_OF-paid).total_seconds()//60)
            shipped=paid+timedelta(minutes=rng.randint(1,max(1,elapsed)))
            shipments.append(dict(shipment_id=f"SHP{i:06d}",order_id=order_id,
                                  shipped_at=shipped.isoformat(),warehouse=rng.choice(["上海仓","广州仓","北京仓"])))
        if 31<=i<=50:row["quantity"]=0
        if 51<=i<=60:row["status"]="未知状态"
        if 61<=i<=70:row["sku"]="SKU-NOT-FOUND"
    orders += [dict(orders[i]) for i in range(199,319)]
    orders += [{**orders[i],"order_amount_cents":orders[i]["order_amount_cents"]+500} for i in range(30)]
    for i in range(15):
        payments.append(dict(payment_id=f"PAY-ORPHAN-{i:02d}",order_id=f"MISSING-P-{i:02d}",result="成功",
                             amount_cents=10000,paid_at=AS_OF.isoformat()))
    for i in range(20):
        shipments.append(dict(shipment_id=f"SHP-ORPHAN-{i:02d}",order_id=f"MISSING-S-{i:02d}",
                              shipped_at=AS_OF.isoformat(),warehouse="上海仓"))
    for collection in [orders,payments,shipments]:rng.shuffle(collection)
    return orders,payments,shipments,products,stocks

def assess_tickets(folder):
    raw=read_csv(folder/"输入资料/运维工单.csv")
    clean,duplicates,conflicts=group_clean(raw,"ticket_id")
    pending=[r for r in clean if r["status"] in ("待处理","处理中")]
    overdue=[r for r in pending if (AS_OF-datetime.fromisoformat(r["created_at"])).total_seconds()>SLA[r["priority"]]*3600]
    high=[r for r in overdue if r["priority"] in ("P1","P2")]
    high.sort(key=lambda r:(r["priority"],r["created_at"],r["ticket_id"]))
    summary=dict(raw_rows=len(raw),exact_duplicate_rows=duplicates,unique_ticket_ids=len({r["ticket_id"] for r in raw}),
        conflict_ticket_ids=len(conflicts),conflict_version_rows=sum(map(len,conflicts.values())),
        usable_tickets=len(clean),pending_tickets=len(pending),overdue_tickets=len(overdue),
        high_priority_overdue=len(high),missing_owner=sum(not r["owner"] for r in clean),
        overdue_missing_owner=sum(not r["owner"] for r in overdue),
        by_status=dict(sorted(Counter(r["status"] for r in clean).items())),
        top20_ids=[r["ticket_id"] for r in high[:20]])
    checks=folder/"结果核对"
    write_json(checks/"预期指标.json",summary)
    write_csv(checks/"高优先级超时清单.csv",high)
    write_json(checks/"冲突工单.json",conflicts)
    return summary

def assess_trade(folder):
    inp=folder/"输入资料"
    raw=read_csv(inp/"订单导出.csv")
    clean,duplicates,conflicts=group_clean(raw,"order_id")
    products={r["sku"]:r for r in read_csv(inp/"商品主数据.csv")}
    stocks={(r["store"],r["sku"]):int(r["available"]) for r in read_csv(inp/"库存快照.csv")}
    invalid=[];valid=[]
    for r in clean:
        errors=[]
        if int(r["quantity"])<=0:errors.append("数量非法")
        if r["status"] not in ["已支付","已发货","待支付","已取消"]:errors.append("状态非法")
        if r["sku"] not in products:errors.append("SKU未匹配")
        if errors:invalid.append(dict(order_id=r["order_id"],reason="、".join(errors)))
        else:valid.append(r)
    pay_raw=read_csv(inp/"支付流水.csv"); pays,pay_dup,pay_conflicts=group_clean(pay_raw,"payment_id")
    ship_raw=read_csv(inp/"发货记录.csv");ships,ship_dup,ship_conflicts=group_clean(ship_raw,"shipment_id")
    assert not pay_conflicts and not ship_conflicts
    order_ids={r["order_id"] for r in raw}
    excluded= set(conflicts)|{r["order_id"] for r in invalid}
    pay_map=defaultdict(list)
    for r in pays:
        if r["result"]=="成功":pay_map[r["order_id"]].append(r)
    issues=[];overdue=[];paid_orders=[]
    for r in valid:
        values=pay_map[r["order_id"]]; active=r["status"] in ("已支付","已发货")
        reason=None
        if active:
            paid_orders.append(r)
            if not values:reason="缺少成功流水"
            elif len(values)>1:reason="多笔成功流水"
            elif int(values[0]["amount_cents"])!=int(r["order_amount_cents"]):reason="支付金额不一致"
        elif values:reason="未支付状态存在成功流水"
        if reason:issues.append(dict(order_id=r["order_id"],reason=reason,store=r["store"]))
        if r["status"]=="已支付" and (AS_OF-datetime.fromisoformat(r["paid_at"])).total_seconds()>24*3600:
            overdue.append(dict(order_id=r["order_id"],store=r["store"],sku=r["sku"],
                available=stocks[(r["store"],r["sku"])],quantity=int(r["quantity"]),
                stock_insufficient=stocks[(r["store"],r["sku"])]<int(r["quantity"])))
    summary=dict(raw_order_rows=len(raw),exact_duplicate_order_rows=duplicates,
        unique_order_ids=len(order_ids),conflict_order_ids=len(conflicts),
        conflict_version_rows=sum(map(len,conflicts.values())),invalid_orders=len(invalid),
        usable_orders=len(valid),missing_channel=sum(not r["channel"] for r in valid),
        by_status=dict(sorted(Counter(r["status"] for r in valid).items())),
        paid_status_orders=len(paid_orders),paid_status_amount_cents=sum(int(r["order_amount_cents"]) for r in paid_orders),
        payment_raw_rows=len(pay_raw),payment_exact_duplicate_rows=pay_dup,unique_payment_rows=len(pays),
        orphan_payment_rows=sum(r["order_id"] not in order_ids for r in pays),
        excluded_order_payment_rows=sum(r["order_id"] in excluded for r in pays),
        payment_issue_orders=len(issues),payment_issues=dict(sorted(Counter(r["reason"] for r in issues).items())),
        shipment_rows=len(ship_raw),orphan_shipment_rows=sum(r["order_id"] not in order_ids for r in ships),
        excluded_order_shipment_rows=sum(r["order_id"] in excluded for r in ships),
        products=len(products),stock_rows=len(stocks),overdue_unshipped=len(overdue),
        overdue_stock_insufficient=sum(r["stock_insufficient"] for r in overdue),
        by_store={s:dict(orders=sum(r["store"]==s for r in valid),
            paid_orders=sum(r["store"]==s for r in paid_orders),
            paid_amount_cents=sum(int(r["order_amount_cents"]) for r in paid_orders if r["store"]==s)) for s in STORES})
    checks=folder/"结果核对"
    write_json(checks/"预期指标.json",summary)
    write_json(checks/"冲突订单.json",conflicts)
    write_csv(checks/"非法订单清单.csv",invalid)
    write_csv(checks/"支付异常清单.csv",issues)
    write_csv(checks/"超时未发货清单.csv",overdue)
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True,help="新目录；已存在时拒绝覆盖")
    parser.add_argument("--seed",type=int,default=20261012)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    rng=random.Random(args.seed)
    c2=args.output/"第02章";c3=args.output/"第03章"
    write_csv(c2/"输入资料/运维工单.csv",make_tickets(rng))
    data=make_trade(rng)
    for name,rows in zip(["订单导出","支付流水","发货记录","商品主数据","库存快照"],data):
        write_csv(c3/f"输入资料/{name}.csv",rows)
    stats={"seed":args.seed,"as_of":AS_OF.isoformat(),"第02章":assess_tickets(c2),"第03章":assess_trade(c3)}
    write_json(args.output/"生成清单.json",stats)
    for folder in [c2,c3]:
        manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((folder/"输入资料").glob("*.csv"))}
        write_json(folder/"结果核对/输入SHA256.json",manifest)
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
