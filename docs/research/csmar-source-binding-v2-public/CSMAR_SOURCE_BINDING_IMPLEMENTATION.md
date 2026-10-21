Public derivative of historical report. Original SHA256: e5fdf36f493172c24ae3e8865ccd7d20ef4c9616ae15fae20d792aff5acd389c. Local references are redacted; historical conclusions are retained. This is not the original file or current execution evidence.

# CSMAR原件来源绑定实施说明

2026-10-21。NO LIVE MONEY。正式研究状态：FORMAL_ADMISSION_BLOCKED。

实现位于 `qbot/research/data/csmar/`。`profiles.py` 固定8种原生表、DES字典字节版本、字段单位和主键；`native.py` 负责受限ZIP/XLSX流式读取；`binding.py` 提供局部规范投影、逐行来源链、外部原件引用、重放及候选发布；模块CLI提供build/replay/verify。没有增加依赖，没有建立第二套金融认证或Provider。

外部原件引用是现有 `SourceArtifact` 持有的小型JSON，其source_id为 `CSMAR_ZIP_REFERENCE_V1`。引用只允许ZIP文件名；解析根由操作员参数或 `FACTORLAB_CSMAR_ROOT` 指定，临时根由 `FACTORLAB_CSMAR_SCRATCH` 指定。引用不能自己选择信任根。它绑定ZIP SHA/长度、XLSX成员SHA、完整工作表清单/预期行数、字段字典版本、证券/日期范围、代码及运行时版本。原件完整路径记录在私有重放收据。供应商版本保持UNKNOWN，供应商采集时间为null；SourceArtifact.acquired_at只是本地引用收据生成时间。文件名批次、版权成员及授权限制另列在私有来源登记中，本地sha256快照不是供应商历史版本。

每次重放在同一只读文件句柄上，解析前后各流式重算整个ZIP SHA，并检查打开前后路径及文件标识。只将一个选定XLSX成员写入独占临时文件，校验成员SHA和ZIP CRC后流式解析XML；不复制整个ZIP，不全库解压，不读取旧审计Parquet作为来源证明。原生单元格数值词法字符串保持不变，规范价格用合同规定的Decimal转换再投影为现有float64类型；逐值精确重放比较使用固定Python/pandas/PyArrow版本。

来源sidecar与规范行保持同序，保存ZIP SHA、XLSX成员/成员SHA、sheet、原生行号、原代码、原日期、全部原始字段值摘要和转换规则版本。native.parquet保留全部选中原生字段，没有覆盖供应商字段。任意规范记录可通过同序lineage定位到原件，并重读原生记录检验摘要。跨工作表或分卷重复主键拒绝，不静默去重。

资格引擎仅增加CSMAR RAW解析分支和实现哈希依赖。`_unbound_real_roles()`未修改。`admission.py`、SourceArtifact合同、18列Schema、LocalParquetProvider、金融门禁、研究窗口、因子、模型及历史证据未修改。新分支只在原件重放结果与全部声称RAW行/列精确相等时移除RAW技术阻断。UNITS等11个金融角色继续未绑定。

`write_candidate()`发布隔离候选材料，不假冒v2包。真实试点也通过原有 `publish_qualification()`生成不完整的现有格式资格包，包内仅复制小型引用和小表；原ZIP保留外部，只要原件缺失、内容变化或解析代码/运行时变化，重放就拒绝。LocalParquetProvider原v2入口仍要求RAW/ADJUSTMENT/STATUS/PIT均通过及完整来源资格，因此不完整真实包不能导入正式研究。

诊断桥 `publish_diagnostic()`复用原Provider。它先重放RAW及000905候选；股票调用方必须另行提供完整18列和显式调整观察。只验证其raw_*、量额与原件相等，不凭原价或因子填造adj_*、adj_factor或turnover。输出保留schema-v1诊断身份，正式入口因缺v2拒绝。指数按现有none调整合同复制指数原价到raw/adj，因子1仅适用于指数；指数缺少换手率保留NaN。真实原价/因子三表本身不足以构造完整股票18列；无需改Schema，也不授予后复权资格。

可运行命令（在独立worktree根，使用仓库既有Python 3.9.25研究环境）：

```powershell
python -B -m qbot.research.data.csmar build request.json --source-root 'LOCAL_REFERENCE_ca10a10e7584 Raw' --scratch 'LOCAL_REFERENCE_be2c86549bbb' --output 'LOCAL_REFERENCE_1cba67c500cd'
python -B -m qbot.research.data.csmar verify 'LOCAL_REFERENCE_ded3c68b117c' --source-root 'LOCAL_REFERENCE_ca10a10e7584 Raw' --scratch 'LOCAL_REFERENCE_be2c86549bbb'
python -B -m examples.research.csmar_source_binding_pilot --audit 'LOCAL_REFERENCE_9ce2844d522b' --source-root 'LOCAL_REFERENCE_ca10a10e7584 Raw' --output 'LOCAL_REFERENCE_589393aed3d3'
```

受限临时空间：单XLSX 192 MiB；内层解压总声明4 GiB、成员数4096、压缩比上限1000；小XML/共享字符串16 MiB；选中记录最多100000且估算留存字节64 MiB，超限要求分区；选定工作表最多Excel原生行数。临时文件退出时自动删除，至少保留1 GiB额外空闲空间。试点输出总量上限2 GiB，所有真实行留在本任务私有目录；清理只针对本任务目录并须先保留收据，不清理旧审计缓存。

边界：外部哈希引用不是防篡改硬件或永久存储；它能发现与固定快照不一致及读取期间变化，不证明供应商从未修订、历史知识时间或授权有效性。范围只覆盖指定成员/全部所选sheet及选定证券日期，不声明全库分卷完整或五年资格。批量部署仍需运营级不可变存储、受治理版本、批次调度和独立金融补证。

原始JUnit错误回溯和统一diff的上下文空行包含行尾空格，字节原样保留。此目录的局部Git属性仅对这两份证据关闭行尾空格格式检查；源码、测试断言、金融门禁及历史控制保持原样。
