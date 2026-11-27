# 更新记录

## Unreleased

- 模板扩到 6 个岗位 36 条，新增 10 条高频遗漏与权限清单
- 新增 `handover` 可勾选 Markdown 与 `apply` 回填；账号类勾选即回收权限，签字后锁定
- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 五类条目与接收人校验
- 权限回收阻塞签字
- 逾期条目
- 角色模板补齐
