# Baton · 离职交接

[![test](https://github.com/wushiyi105-jpg/baton/workflows/test/badge.svg)](https://github.com/wushiyi105-jpg/baton/actions)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

![示例](assets/demo.gif)

交接清单按五类摊开：账号、文档、客户、代码、流程。权限没回收，签字直接被拒。

## 为什么不是一份 Word 交接单

交接最容易漏的是权限：文档给了、客户给了，后台子账号还挂着你的名字，三个月后出事还是找你。
Baton 把「账号类条目必须标已回收」当成签字闸门——不满足就抛错，而不是在备注里写「待处理」。
另外每条必须有接收人，归不到五类的条目直接报出来。

## 它做什么

1. **五类条目**：账号 / 文档 / 客户 / 代码 / 流程，超出这五类提示归类。
2. **接收人**：空接收人逐条报。
3. **权限闸门**：账号类条目没标回收，`sign` 直接拒绝。
4. **逾期**：交接日过了还有没做完的条目，列前三条。
5. **模板**：按角色一键补齐条目。

## 怎么用

```bash
pip install -e ".[dev]"
python -m baton seed
python -m baton status --iid 1 --day 2026-11-27
python -m baton sign --iid 1 --day 2026-11-27   # 有权限没回收时会被拒
python -m baton serve        # http://127.0.0.1:8009
```

真实种子：运营专员模板 6 条、1 个交接（小周，交接日 2026-11-28）、9 条条目（6 条已做完）。
以 2026-11-29 跑 `status --iid 1`：6/9（67%），社群管理员权限没写接收人、工位钥匙被归到「杂项」、
后台账号的权限没回收、交接日已过 1 天还有 3 条没做完，合计扣 23 分，结论是不能签字。
`sign --iid 1 --day 2026-11-29` 会以退出码 2 拒绝。

## 规则与扣分

| rule_id | 含义 | 扣分 |
| --- | --- | --- |
| `item.category` | 不在五类里 | 3 |
| `item.no_owner` | 没写接收人 | 4 |
| `access.open` | 账号类条目权限未回收（阻塞签字） | 10 |
| `handover.overdue` | 交接日已过且仍有未完成条目 | 6 |

## 边界

- 不接公司 AD，权限回收要自己去后台点；
- 不判断条目是否该交接，只判断有没有漏；
- 不生成离职证明。

## 作者

shiyi · GitHub [@wushiyi105-jpg](https://github.com/wushiyi105-jpg) · wushiyi105@gmail.com
