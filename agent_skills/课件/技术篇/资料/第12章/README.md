# 第十二章配套资料：仓库补货建议技能

本案例从新的库存需求开始，全部输入、资料、模板和脚本均在本目录，
不需要前面章节的程序、订单样例或已安装技能。

[章节讲义](../../12-制作带资料、模板与脚本的Skills.md)

- [业务需求](输入资料/业务需求.md)
- [库存快照](输入资料/库存快照.json)
- [非法装箱量](输入资料/非法装箱量.json)
- [技能入口](stock-replenishment/SKILL.md)
- [参考规则](stock-replenishment/references/补货规则.md)
- [报告模板](stock-replenishment/assets/补货建议模板.md)
- [计算脚本](stock-replenishment/scripts/replenish.py)
- [结果核对](结果核对.md)

在本目录运行：

~~~powershell
py stock-replenishment/scripts/replenish.py --input "输入资料/库存快照.json" --output-dir "输出-正常"
py stock-replenishment/scripts/replenish.py --input "输入资料/非法装箱量.json" --output-dir "输出-异常"
~~~

Python 3 标准库即可运行。使用本机实际可用的 py、python 或 python3 命令。
全部相对参数按终端当前目录解释。输出目录必须尚不存在。
脚本生成计算 JSON，Agent 读取计算结果并按模板生成 Markdown 报告。
