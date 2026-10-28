# 第十三章配套资料：DeepSeek Harness

[章节讲义](../../13-DeepSeek-Harness介绍与上手.md)

将“演示项目”整个目录复制到独立位置，在 Harness 中将该目录选为工作区。
必须包含隐藏目录 .dsh，其中存放本章技能。
不需要以前章节的订单脚本，不需要运行企业项目服务。

- [任务说明](演示项目/任务说明.md)
- [巡检快照](演示项目/输入资料/巡检快照.json)
- [技能入口](演示项目/.dsh/skills/service-check-report/SKILL.md)
- [核对结果](结果核对.md)
- [提示词](演示提示词.md)
- [官方资料](官方资料.md)

在演示项目目录可以单独运行脚本：

~~~powershell
py .dsh/skills/service-check-report/scripts/summarize_checks.py --input "输入资料/巡检快照.json" --output-dir "脚本输出-01"
~~~

计算脚本只生成 巡检汇总.json，Agent 再按照模板生成 巡检日报.md。
