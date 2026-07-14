# AI-Native 工作流 · Two Ways a Design Fails

> **项目**：基于双轴分诊的人机协同决策界面部署前评估（v2.4）——用真实 reliance 日志校准的 LLM agent panel，在真人研究前对 AI 辅助决策界面做低成本部署前评估。核心依据见 [开题沟通稿_分歧度分诊_部署前评估_v2.4.md](开题沟通稿_分歧度分诊_部署前评估_v2.4.md)；工程可行性与分工见 [实验实施与AI分工计划.md](实验实施与AI分工计划.md)。
> **本文用途**：把这套 **Spec-Driven Development + Agent Execution + 独立审计 Gate** 的 AI 协作工作流，落到本项目的实际参数上。它是一篇**方法论论文**，因此在通用工程 gate 之上，额外加了一道**科研方法学审计 gate**（§4.5、§6）——「能跑」在这里**不等于**「正确」。
> **每个 issue** 都照 §12 的 checklist 跑一遍，质量可复现。

---

## 0. 项目参数（本项目已适配好的值）

本项目已把通用占位符替换为下表实际值，全文引用同名参数即可。

| 参数 | 含义 | 本项目取值 |
|---|---|---|
| `<REPO>` | 仓库名 | `two-ways-a-design-fail` |
| `<REPO_PATH>` | 主 checkout 的绝对路径 | `C:\Users\v-elzhang\Desktop\MyFolder\two ways a design fail` |
| `<OWNER>` | GitHub owner | `EloiseJulia` |
| `<DEFAULT_BRANCH>` | 主干分支 | `main` |
| `<WORKTREE_ROOT>` | worktree 存放目录 | `<REPO_PATH>/.worktrees` |
| `<AGENT_CLI>` | 使用的 agent CLI | `copilot`（Copilot Premium，多模型、token 不限额） |
| `<MODEL>` | 复杂任务默认模型 | 可用的最强长上下文模型（统计/校准模块用高 effort） |
| `<COMPUTE>` | 执行重任务的机器 | 本地 + 待定的批量推理端点 / GPU（见闸 2） |
| `<SPEC_DIR>` | spec 存放目录（= 冻结设计） | `SPEC.md`（根目录单一事实源，见 §2） |
| `<PLAN_DIR>` | plan 存放目录 | `docs/plans/` |
| `<RESEARCH_DIR>` | 调研报告目录 | `docs/research/` |
| `<REPORT_STORE>` | 重型交付物（图/大文件）存放处（git 外） | `~/reports/two-ways-a-design-fail/` |
| `<COMMIT_TRAILER>` | 每个 commit 的署名 trailer | `Co-authored-by: Copilot <copilot@github.com>` |
| `<BUILD_CMD>` | 环境/依赖验证命令 | `pip install -e .` / `uv sync` |
| `<RUN_CMD>` | 跑真实产物（一次纵切实验） | `python -m experiments.e1 --config configs/vslice_v0.yaml` |
| `<TEST_CMD>` | 全量测试命令 | `pytest` |

> 本项目是单人 + Copilot 多 agent/session 并行代工，没有服务器 tmux 常驻；把「长驻 agent」理解为「本地多个终端/session 里跑 agent」即可，方法论不变。

---

## 0.5 三道闸：AI 过不了、必须你先亲自清掉（先于一切代码）

代码量约 **80–90% 可交给 AI**，但有三道闸**与写多少代码无关**，决定项目能否启动。详见 [实验实施与AI分工计划.md](实验实施与AI分工计划.md) §1。

| 闸 | 内容 | 不过的后果 |
|---|---|---|
| **闸 1 · 数据** | 能否真正拿到 Bansal CHI'21 与 Lu & Yin CHI'21 的**原始 trial 级数据**（可下载的 CSV/日志，不是论文图表） | 拿不到 → E1 无法校准/验证，项目空转。**没结论前别让 AI 写数据管道**（它会对着想象的格式写白工，甚至编出不存在的下载链接）。 |
| **闸 2 · 批量推理通道** | 「Copilot 不限额」是否等于**可在 Python `for` 循环里调几万次的批量 API** | 只有交互聊天 → agent panel 的推理循环跑不起来。备选：Azure OpenAI / 各家 API key；开源权重档用本地/托管 vLLM（需 GPU，AI 开不出来）。 |
| **闸 3 · 你自己当 PI** | 科学正确性（无泄漏、无污染、统计不自欺）**无法外包** | 全托管 AI → 产出「能跑、数字漂亮、方法学却是错的」管道，对一篇方法论论文是致命的。 |

> **一句话：AI 能当整个工程团队，但当不了 PI。** 你的角色是「定架构 + 做集成 + 验正确性 + 解释结果」——恰是 AI 干不了的高价值 10%。

---

## 1. 一句话定位与五条铁律

**Spec-Driven Development + Agent Execution + 独立审计 Gate。**

质量不是靠「用了多少 agent」堆出来的，而是靠**验证机制**守出来的。五条铁律（每条都是踩坑换来的）：

| # | 铁律 | 教训 |
|---|---|---|
| 1 | **验证真实产物，不只看测试绿** | 关键配置被误删、整条命令失效，却通过了几十个测试——只有 build + 跑真产物才抓得到 |
| 2 | **独立敌对审计 > 自审** | 自审容易判「都是 pre-existing / PASS」；独立新 agent 常挖出真 bug（尤其隐蔽的**统计/方法学**错误） |
| 3 | **并行只对「独立切片」，依赖链必须串行** | 硬并行依赖链 = 冲突 + 跨切片一致性 bug 更隐蔽 |
| 4 | **共享基础设施/schema 改动标注交你，永不自 merge** | `INTERFACES.md` 里的 schema/签名是全局契约；agent 只测明白、标注醒目，merge 是人的判断 |
| 5 | **知道何时停手** | 一道彻底审计 0 新问题后继续审 = 边际收益趋零的焦虑循环；验到合理程度就交 |
| 6 | **能跑 ≠ 正确（本项目专属）** | 这是一篇**方法论**论文：泄漏/污染/beta-binomial 算错/阈值事后回填都会让「能跑的漂亮管道」静默作废；正确性由你负责（§6） |

外加一条贯穿铁律：**「标注边界 ≠ 修 bug」**——低风险且真超范围的可文档化为「已知边界」；但**会静默丢数据 / 破坏正确性**的（如泄漏、身份维度缺失、超弥散算成原始方差）**必须修**。

---

## 2. 三层文档体系 · 单一事实源（全部 git 追踪）

多个无记忆 session 各写各的、代码拼不拢（接口对不上、schema 各定各的）是本项目的头号风险。解法是在根目录维护**三份共享大脑**，每个新 session 第一件事是读它们：

| 层 | 位置 | 作用 | 谁拥有 |
|---|---|---|---|
| **执行规范** | `AGENTS.md`（或本文件） | 定义 HOW：worktree 隔离 / PR 流程 / 分支命名 / commit 规范 / auto-merge 策略 | 你（PI） |
| **冻结设计** | **`SPEC.md`** | 双轴定义、RQ/H、E1–E6、双阈协议——基本就是 v2.4 开题稿的技术版 | 你 或 Agent（讨论后写） |
| **接口契约** | **`INTERFACES.md`** | 所有模块的数据 schema 与函数签名（数据帧列名、`AgentResponse` 结构、指标函数输入输出）——**防代码拼不拢的关键** | 你 + Agent |
| **进度与坐标** | **`PROGRESS.md`** | 已完成/进行中/待办 + 已知坑 + **预注册阈值冻结时间戳**（防事后调参）。每个 session 结束前更新 | Agent（你审） |
| **执行脚本** | `<PLAN_DIR>` | 每个 slice 一个 plan：架构图 + 数据流 + 分步骤 checklist + 测试步骤 + push 点 | Agent（执行中生成） |
| **调研报告**（可选） | `<RESEARCH_DIR>` | 数据集可获取性核实 / 批量 API 选型 / license 审查 | Research Agent |

> **每个新 agent/session 的开场白**：「先读 `SPEC.md` / `INTERFACES.md` / `PROGRESS.md`，严格按 `INTERFACES.md` 的签名实现 X 模块，不要改动其它模块的接口，完成后更新 `PROGRESS.md`。」

**Spec 与 Plan 都可以由 Agent 写**，但必须**经你确认后 commit**。区别：
- **单 issue 交互模式**：讨论后 Agent 写 spec（spec 质量取决于讨论深度）。
- **多 issue 非交互模式**：Agent 自主写 spec，所以 **issue body 质量决定 spec 质量**。

---

## 3. 全生命周期总览

```
① 调研(可选) → ② Issue 准备 → ③ 拆分+依赖分析 → ④ 每 slice 执行
                                                        ↓
        ⑦ Manager 自动合并(audit PASS) ← ⑥ 整体 PR-Audit ← ⑤ 独立敌对审计(每 slice)
                    ↓
        仅三闸/方法学争议/判断题 → 升级给你(PI)
```

**不可跳过的 gate：**
- 每个 slice 完 → ④自检 + ⑤独立敌对审计（含 §4.5 方法学）
- 全部 slice 完 → ⑥整体 PR-Audit（build 真产物 + 全量测试 + diff 卫生 + 方法学）
- 合并前 → 独立 audit PASS（取代人工 review）；FAIL/争议才升级给你

---

## 4. 角色总表

| 角色 | 何时用 | 位置 | 关键约束 |
|---|---|---|---|
| **你（PI + 首席验证官）** | 关键节点 | 本地 / 浏览器 | 启动 Manager；过三道闸（§0.5）；裁决判断题与方法学争议（§6）；**日常 PR 不手动审——交 AI**（audit 为合并闸） |
| **Manager Agent（本项目总调度）** | 全程 | 常驻交互 session | **只调度不干活**：依赖分析 + 派单 + 合并决策；只有它碰 `main`/`topic` 的 git 与 `gh pr merge`；永不碰主 checkout；**audit PASS 后自动合并**，仅三闸/判断题升级给你 |
| **Research Agent**（可选） | 数据/API/选型不明 | 独立 session，doc-only | 输出 research md，直接 commit `<DEFAULT_BRANCH>`；不写代码；**不能代你搞定 gated 数据**（会编不存在的链接） |
| **Sub-Agent（实现）** | 每个 slice | 独立 worktree + session | 只在自己 worktree；spec→plan→执行；严格按 `INTERFACES.md` 签名；自检 gate；**永不 merge** |
| **Audit Agent（独立敌对）** | 每 slice 完 + 整体 | **全新 session、无上下文** | 目标是挑毛病；不信任何既有结论；**包括方法学审计（§4.5）**；只报不修（PASS = 合并闸） |

**两种规模：**
- **单 slice（日常默认）**：不需要 Manager。你在 worktree 里起一个交互 session，讨论 → spec → plan → 执行 → review。
- **多 slice 并行（本项目默认）**：由 Manager Agent 编排多个 Sub-Agent（见下方「编排层」与 §4.7 模块分工）。

---

## 编排层 · Manager Agent 驱动（Copilot CLI · 本项目实际运行方式）

本项目**全流程由一个常驻 Manager Agent 交互 session 调度**；它**只做拆分 / 派单 / 调度 / 合并决策，绝不自己写代码、跑统计、做分析**——所有具体任务（调研、实现、审计、修复）都由它用 `copilot -p` **新开 session** 委派给 subagent。

**权限与合并策略（本项目已选全自动，覆盖通用模板的“人工合并”规则）：**
- Copilot CLI 全程 `--allow-all`（= `--allow-all-tools --allow-all-paths --allow-all-urls`；等价 `--yolo`）。
- **PR 由 AI 审、AI 合，人不手动 review**：**独立 audit subagent（含 §4.5 方法学审计）PASS = 合并闸**，取代人工 review。写代码的 subagent 不自审自合；由**另一个** audit session 判定、由 **Manager**（第三个 session）执行 `gh pr merge`。
- **只升级给你（PI）的三类**：① §0.5 三道闸（数据可获取性、批量 API 通道、需 PI 判断的科学正确性）；② audit 反复 FAIL 或分诊为方法学争议；③ 判断题（venue、范围收窄、是否投 E6）。**其余 Manager 自决**（含排期、并行/串行、slice 粒度、非争议性设计取舍）。

**Manager 启动（交互 session，可用 `ask_user` 向你提问）：**
```powershell
cd "<REPO_PATH>"
copilot --allow-all --name manager-twdf --model auto --effort high -i (Get-Content .\docs\manager-prompt.md -Raw)
```
> 完整 Manager prompt 见 [docs/manager-prompt.md](docs/manager-prompt.md)（可直接跑）。`--model auto` 可换成你可用的最强长上下文模型。

**Manager 派 subagent（每个任务新开非交互 session）：**
```powershell
# 实现型 slice（worktree + draft PR）
copilot -p (Get-Content .\.prompts\impl-S1.md -Raw) --allow-all --name impl-S1 --model <MODEL> --log-dir .\.copilot-logs --share

# 独立敌对 + 方法学审计（全新 session、无上下文、只报不修）
copilot -p (Get-Content .\.prompts\audit-S1.md -Raw) --allow-all --name audit-S1 --model <MODEL> --effort high

# 调研（doc-only：数据可获取性 / 批量 API 选型）
copilot -p (Get-Content .\.prompts\research-data.md -Raw) --allow-all --name research-data --model <MODEL>
```
> **为什么用文件传 prompt**：Windows PowerShell 内联多行 prompt 引号极易破碎；Manager 应把每个 subagent prompt 写进 `.prompts\<name>.md` 再 `Get-Content -Raw` 传入。
> subagent 是 `-p` 非交互，**不能反问**；它把 findings / 产物作为输出返回 Manager。Manager 汇总后自决或升级给你。独立 slice 可后台并发（`Start-Job` 或多开终端），依赖链串行。

**Manager 运行闭环（每个 issue）：**
1. 读工作流 + [开题稿 v2.4](开题沟通稿_分歧度分诊_部署前评估_v2.4.md) + [实验分工计划](实验实施与AI分工计划.md) + SPEC/INTERFACES/PROGRESS（缺则先建骨架）。
2. **先过 §0.5 三道闸** → 未清零就 `ask_user` 升级给你，别让 subagent 对着想象的数据格式写白工。
3. 依赖分析（§2.1 模块图 A–E）→ 定 slice 与并行/串行。
4. 先派 **纵切 v0**（§2.2）打通端到端骨架。
5. 每 slice：派 impl subagent → 派 audit subagent（独立敌对 + 方法学）→ PASS 则 Manager `gh pr merge`；FAIL 则派 fix subagent 重跑，直到 PASS 或分诊升级。
6. 全部 slice 完：派一次整体 PR-Audit（§阶段5 A–H 面）→ PASS 合并。
7. 每步更新 PROGRESS.md；**预注册阈值 τ_disp/τ_level 在看结果前冻结并记时间戳**。

---

---

## 阶段 0 · 调研（可选，技术路线不明时）

**何时需要**：选模型 / 定算法路线 / 审 license / 比 SOTA。

**启动模板：**
```bash
<AGENT_CLI> --name research-<topic> --model <MODEL> \
  -i 'Research SOTA for <topic> (issue #<N>). Compare: <候选 A/B/C>.
For each: accuracy/benchmark, LICENSE (permissive vs restrictive), input/output
format, runtime cost, integration fit with our <现有框架>.
Read AGENTS.md §<相关章节> first.
Output <RESEARCH_DIR>/<date>-<topic>.md with a comparison TABLE + a clear
recommendation + rationale + honest caveats.
Commit directly to <DEFAULT_BRANCH> (doc-only). Trailer: <COMMIT_TRAILER>'
```

**关键**：让它输出**对比表 + 推荐 + 诚实 caveat**（尤其 license：可商用 vs 仅研究用途）。

**能做 / 不能做**：能搜文献/仓库/官方文档、比公开 benchmark、审 license、读本仓库理解集成约束；**不能**跑重型 benchmark（那要执行 agent）、不能保证结论绝对准（你最终判断）。

---

## 阶段 1 · Issue 准备

| 情况 | 做法 |
|---|---|
| 已有合适 open issue | 确认 body 够详细 |
| body 太简单 | 先补 body（acceptance criteria + 相关文件/模块 + Non-goals + parent epic 链接） |
| 全新工作 | 创建 issue，写清 body |

**「body 够详细」=**：① 说清做什么（acceptance criteria）② 提到相关文件/模块/现有模式 ③ parent epic 链接 ④ Non-goals（告诉 agent 什么不要动）。

> 单 issue 交互模式下 body 可以不完整（讨论时补）；**Manager 非交互模式下 body 必须完整**（没有讨论机会）。

**（可选）登记看板 `<PROJECT_BOARD>`**：设 Status=In progress，填 Agent 字段（谁在干、worktree 路径、session 引用），方便你随时知道谁在做什么。

---

## 阶段 2 · 拆分 + 依赖分析（最容易出错的一步）

**先画依赖图，再决定并行还是串行。**

```
对每个候选 slice 问：它读/写哪些文件、哪些模块、哪些数据结构？
  ├─ 两个 slice 改同一批文件 / 后者依赖前者产物  → 串行（依赖链）
  └─ 完全独立（不同文件、无产物依赖）           → 并行（独立切片）
```

- **依赖链**（如：建结构 → 扩展 → 改上游接口）：**串行**。硬并行会冲突，且跨切片的一致性 bug 更隐蔽。
- **独立切片**（如多个互不相关的 bug fix）：**并行**，各自独立 worktree；重型任务受资源上限约束（如一张 GPU 一个 agent）。

**产物**：Manager 写 spec + per-slice plan，标明每个 slice 的**依赖关系 + 并行/串行编排**，commit 到 topic 分支。

### 2.1 本项目模块分解与 agent 分工（依赖已标注）

清晰的模块边界 = 干净的 session 分配。详见 [实验实施与AI分工计划.md](实验实施与AI分工计划.md) §4。

| Agent/Session | 模块 | 依赖 | 阻塞于 |
|---|---|---|---|
| **S0（你 + AI）** | 架构：仓库、`SPEC/INTERFACES/PROGRESS`、config、schema | — | 最先做 |
| **A · 数据与特征** | 加载 Bansal/Lu&Yin → 统一 schema；抽取原子认知-交互特征（§4.3 特征向量） | S0 | **闸 1（数据）** |
| **B · Panel 引擎** | 双系统架构、persona、反事实配对、摩擦代理、模型 provider 抽象、序列有状态模式 | S0 | **闸 2（API）** |
| **C · 指标与统计** | beta-binomial 超弥散、bootstrap、置换检验、双轴信号、PAS/ECS/ECE、四基线 | A 的 schema | — |
| **D · 校准与协议** | 特征空间/分区校准、双阈值学习、弃权逻辑、泛化梯度、逆转区 | B + C | — |
| **E · 实验与报告** | E1–E5 编排、结果表、图、预注册日志 | A+B+C+D | — |

**并行建议**：A 和 B 可同时起步（分别阻塞于各自外部资源——闸 1/闸 2）；C 只需 A 的 schema 就能开工（先用假数据写好、真数据到位再接）。

### 2.2 推进策略：先纵切一刀，再横向铺开（强烈建议）

**不要**让五个 agent 各把模块写"完整"再集成——那对单人协调多 session 是集成地狱。改为**先打通一条最薄的端到端纵切**：

> **纵切 v0**：Bansal 一个数据集 × 一个模型 × 十来个任务 × 一个 UI 对比 → 只算**轴一超弥散信号 E1** → 跑出一个"分歧度 vs 人类超弥散"的相关数字。

打通它，证明"数据→panel→指标→结果"整条链能拼起来。**然后再横向加**：加模型（跨家族三角）→ 加轴二（暗黑/系统性过度依赖）→ 加特征与校准 → 加 E3/E4/E5。集成风险第一天就暴露，每加一块都在一条能跑的链上增量。

---

## 阶段 3 · 每个 Slice 执行

### 3.1 脚手架
```bash
git -C <REPO_PATH> worktree add <WORKTREE_ROOT>/<name> -b feature/<N>-<name> <DEFAULT_BRANCH>
cd <WORKTREE_ROOT>/<name>
git commit --allow-empty -m "bootstrap #<N>

<COMMIT_TRAILER>"                    # 空分支开不了 PR，先引导提交
git push -u origin feature/<N>-<name>
# 开 draft PR（用你的 PR 工具），base=<DEFAULT_BRANCH>，body 写 "WIP. Refs #<N>."
```
> **早开 draft PR** 拿 CI + owner 可见性；**但不 mark ready、不 merge**。

### 3.2 执行流程（spec → plan → code）
1. 贴**开场 prompt**（§使用方法 A）→ agent 读代码 + 问 ≤5 个澄清问题
2. 你答问 → agent 写 **spec** → 你确认
3. agent 写 **plan** → 你确认
4. agent 执行：写代码 → 跑测试 → 自检 → push（累积在 draft PR）

**你在关口把关**：spec 看 Acceptance Criteria + Non-goals + 拆分；plan 看是否覆盖验收 + 有测试步骤 + 有 push 点。**判断题（选哪个方案、要不要扩范围）由你拍板，不让 agent 闷头猜。**

### 3.3 自检 gate（agent mark ready 之前必须自答）
- 目标产物真的能跑（不只是 import / 单测）？
- 幂等？重跑收敛？
- **身份维度完整**（主键/标识没漏维度 → 避免不同配置静默撞车）？
- 无依赖 / 空输入优雅降级？
- diff 只动该动的，无残留 debug / 无误删？

---

## 阶段 4 · 独立敌对审计（质量皇冠，每 slice 完做）

**必须是全新 session、无上下文、抱着「我一定要挑出毛病」的心态**——写代码的 agent 审自己有偏见。

审计 prompt（§使用方法 D）核心：
- 「你没写这份代码，把 PR 描述和一切既有结论当**不可信**，从源码重新验证」
- **先读代码找逻辑 bug**（身份维度缺失 / 静默丢行 / 坐标/数值缩放 / 注入 / 多步写原子性 / 旁路校验），再跑验证
- **验证真实产物**（build + run，不只单测）
- **独立归因测试失败**（clean `<DEFAULT_BRANCH>` 对比复现，禁止「猜 pre-existing」）
- 输出 **ranked findings**（BLOCKER/MAJOR/MINOR/UNVERIFIED）+ 明确 verdict；**只报不修**

**审计回来后分诊：**
- 我们代码 + 修法清楚 → 修
- 共享 infra / `INTERFACES.md` 契约 → **不擅改，文档 + follow-up issue，交你**
- 会静默丢数据 / 破坏正确性 → **必须修**（哪怕它自称「边界」）

### 4.5 方法学审计 gate（本项目专属 · 最重要的一道）

工程 bug 让代码"跑不了"，方法学 bug 让代码"跑得漂亮却是错的"——对一篇卖方法学的论文，后者致命。**每一条你都要亲自核对，或让第二个 AI 以对抗视角复核（"请找出这段统计代码里的方法学错误"）。** 详见 [实验实施与AI分工计划.md](实验实施与AI分工计划.md) §6。

- [ ] **训练/测试泄漏**：LOIO（E3）留出的整类干预，其任何信息（含校准阈值、特征归一化参数）**绝不能**在训练侧见过。AI 极易把归一化 fit 在全量数据上——这就是泄漏。
- [ ] **污染隔离**：是否真跑在扰动版数据上；模型训练截止日期 vs 数据发布日期是否如实报告。
- [ ] **beta-binomial 超弥散**：是否真从二项抽样噪声里**分离**出 between-user 超弥散，还是错算成原始方差？（错了整个 H1a 塌。）
- [ ] **均值预测器基线**：必须是"只输出 p(1−p)"的基线，且分歧度**确实显著优于它**——不能偷偷放水。
- [ ] **null model / 适当依赖锚点**：理性贝叶斯 null model 是否正确，"过度依赖"是否相对它定义。
- [ ] **难度控制**：E1 主估计量是否真的是 within-task 差分（难度配对内抵消），还是被写成 pooled 相关（会被难度混淆）。
- [ ] **双轴不串味**：轴一（离散）与轴二（水平）是否分别计算、分别设阈；暗黑条件下轴二是否确实触发（闭合盲区的验收点）。
- [ ] **researcher DoF / 预注册**：阈值 τ_disp、τ_level 是否**在看结果前**锁定并写进 `PROGRESS.md`？事后调参回填 = 科研不端。
- [ ] **多重比较**：扫多个干预时 Benjamini–Hochberg 校正是否真的做了。
- [ ] **AI 幻觉数字**：任何"结果摘要"以**代码重跑的原始输出**为准，不信 AI 在对话里复述的数字。

---

## 阶段 5 · 整体 PR-Audit（全部 slice 完，合并前一次总检）

| 面 | 查什么 |
|---|---|
| **A 真实产物** | `<BUILD_CMD>` + `<RUN_CMD>` 跑通；其它产物消费者没被连累 |
| **B 幂等/共存** | 重跑 0 新副作用；多配置共存不撞；超限报错不静默丢；`--force`/重置干净 |
| **C 结构/接口** | 统一视图/接口单值不 fan-out；约束真强制；下游消费者不被破坏 |
| **D 正确性** | 数值/坐标 round-trip；无依赖优雅 skip；空输入不崩 |
| **E 全量回归** | 跑**整个**测试套（不只子集）；每个失败 clean-main 独立归因 |
| **F diff 卫生** | 逐行看配置/依赖文件，防「误删」；无 throwaway/debug 残留；worktree 干净 |
| **G review 闭环** | 所有 review thread 回复 + 真修（不只回复）；lint |
| **H 方法学（本项目）** | §4.5 清单：无泄漏/污染、超弥散分离正确、基线未放水、难度受控、双轴不串味、预注册未事后回填 |

**产出**：PASS/FAIL 表 + ranked findings。确认的 bug 修，判断题标注交你。

---

## 阶段 6 · 交付（本项目：audit PASS → Manager 自动合并）

- **合并闸 = 独立 audit（含 §4.5 方法学）PASS**：Manager 直接 `gh pr merge --squash --delete-branch`，人不手动 review。
- Manager 合并后在 PROGRESS.md 记一笔（PR / diff 摘要 / audit verdict），供你事后抽查。
- **升级给你而不自合的情形**：audit 反复 FAIL、方法学争议、或触及 §0.5 三道闸 / 判断题。
- **（可选）图文报告**：结果 + 可视化 + 指标 + **诚实的精度验证**。
  - 别 overclaim：无 ground truth 时说清「是合理性/一致性/稳定性验证，不是误差 vs 真值」；要真误差就用**带 GT 的标定数据集**，并写明域差距。
  - 重型产物（图/大文件）放 `<REPORT_STORE>`（git 外），只把摘要发 PR。

---

## 7. 贯穿原则 · Gate · 陷阱速查

| 类别 | 要点 |
|---|---|
| **只读主 checkout** | agent 永不改 `<REPO_PATH>` 主 checkout；只 `git worktree add` / 只读 inspect（`git log/status/diff`） |
| **禁止在主 checkout 上 test-checkout** | 临时 checkout 某 commit 也不行（会留 detached HEAD）；要看某 commit 用临时 worktree |
| **PR-first；合并=audit PASS**（本项目） | 早开 draft 拿 CI/可见性；**独立 audit（含方法学）PASS 后由 Manager 自动 `gh pr merge`**，人不手动审 |
| **commit trailer** | 每个 commit 带 `<COMMIT_TRAILER>` |
| **空分支陷阱** | 0-commit 开不了 PR → 先 `git commit --allow-empty` 引导提交 |
| **删 worktree 陷阱** | 先 `cd <REPO_PATH>` 再 `git worktree remove`，否则后续 shell 找不到 cwd 报 ENOENT |
| **身份维度陷阱** | 主键/identity 要包含「所有影响输出的维度」（strategy/size/config），否则静默撞车 |
| **验证真实产物** | 测试绿 ≠ 产物能用；build + 跑真产物 |
| **别猜 pre-existing** | 任何「预先存在的失败」结论必须 clean-main 复现坐实 |
| **何时停** | 一道彻底审计 0 新问题 → 交付；别无限自证 |
| **squash 进 topic 的隐患** | slice squash-merge 进 topic 会压平历史，topic→main 可能报 dirty；优先 `--merge` 或 squash 后立即 `git merge --no-ff origin/<DEFAULT_BRANCH>` 补桥 |

---

## 8. 分支命名约定

| 类型 | 格式 | 示例 |
|---|---|---|
| 新功能 | `feature/<short-name>` | `feature/123-add-cache` |
| Bug fix | `fix/<short-name>` | `fix/456-null-deref` |
| 重构 | `refactor/<short-name>` | `refactor/config-loader` |
| 实验 | `experiment/<short-name>` | `experiment/new-algo` |
| 多 slice 伞状 | `topic/<name>` | `topic/123-search-rework` |
| sub-agent slice | `slice/<topic>-S<N>` | `slice/123-S1-index` |

**Topic 模式**（多 sub-agent 并行）：
```
topic/xxx（伞状，Manager 维护）
  ├── slice/xxx-S1（Sub-Agent 1，audit PASS 后 Manager 合进 topic）
  ├── slice/xxx-S2（Sub-Agent 2，audit PASS 后 Manager 合进 topic）
  └── topic → main（整体 audit PASS 后 Manager 自动合并）
```

**auto-merge 策略（本项目全自动）**：slice → topic 与 topic → 主干**均由 Manager 在独立 audit（含 §4.5 方法学审计）PASS 后自动合并**，人不手动 approve。**唯一例外——升级给你**：audit 反复 FAIL、方法学争议、或 §0.5 三道闸未清零。

---

## 9. Agent 运维（监控 + 故障处理）

**监控**：
- 长驻 session 直接看（`tmux attach-session -t <TMUX_SESSION>`）
- 若 CLI 支持远程可见性，用浏览器监控 session（SSH 断开不影响）
- 看 PR 状态（draft = 工作中；non-draft = 自检通过等 review）
- 看看板 Status

**卡住 / 需要回应**：Agent 会在 blocking question 前 stop（不瞎猜）。用 `tmux send-keys` 或远程 session 页面回应。

**崩溃恢复**：找到 session ID → 用 CLI 的 resume 能力从断点继续，已 push 的 commits 不重做。

**完成后清理**（避免 worktree 堆积）：
```bash
cd <REPO_PATH>                                          # 先离开 worktree！
git worktree remove --force <WORKTREE_ROOT>/<name>
git branch -D feature/<N>-<name>                        # PR 已 merge 时
# 关掉对应长驻 pane
```

---

## 10. 明确不存在的东西（避免误解）

| 不存在 | 说明 |
|---|---|
| Goal → Spec 全自动 | issue 仍需人判断业务价值后创建 |
| 独立「Planner Agent」角色 | Manager 兼任规划职能 |
| 持久化向量记忆 / 知识图谱 | 仅有文件式 handoff 记忆（SPEC/INTERFACES/PROGRESS + `docs/<date>-handoff.md`，git 追踪，session 间接力）|
| 写代码的 subagent 自审自合（本项目） | 禁止自审自合；由**独立 audit subagent** PASS + **Manager**（另一 session）执行合并，人不手动审 |

---

## 11. 使用方法 · Prompt 模板全集

### A. Sub-Agent 开场 prompt（单 slice 执行）
```
You are working on issue #<N> (slice <k>), branch feature/<N>-<name>, draft PR
#<PR>. Full flow: read context, ask ≤5 questions, write a SHORT spec, wait for
my confirm, write a plan, wait for my confirm, THEN execute.

Read ALL before asking:
- issue #<N> (+ parent epic)
- AGENTS.md §<相关章节>
- <相关现有代码文件 + 1-2 个同类已完成实现作模板>

Scope/guardrails: <要做什么 + 明确 NOT touch>.
Constraints: 在 worktree <WORKTREE_ROOT>/<name>；确认 pwd 后再改；DO NOT touch
main checkout；commit trailer <COMMIT_TRAILER>；push 到 draft PR，测试绿前不 mark
ready；NEVER merge。判断题上报我，不要猜。
```

### B. Manager spawn（本项目总调度 · 完整 prompt 见 [docs/manager-prompt.md](docs/manager-prompt.md)）
```powershell
cd "<REPO_PATH>"
copilot --allow-all --name manager-twdf --model auto --effort high -i (Get-Content .\docs\manager-prompt.md -Raw)
```
Manager 只调度不干活：读上下文 → 过 §0.5 三道闸 → 依赖分析（§2.1）→ 先纵切 v0（§2.2）→
每 slice 派 impl+audit subagent → **audit PASS 后自己 `gh pr merge`** → 更新 PROGRESS.md。
仅三道闸 / 方法学争议 / 判断题升级给你，其余自决。subagent 用 `copilot -p (Get-Content
.\.prompts\<name>.md -Raw) --allow-all --name <name>` 新开非交互 session 委派。

### C. Spec / Plan 确认 prompt
```
Spec confirmed — proceed to the plan.        # 或列出要改的 Acceptance/Non-goals
Plan confirmed. Execute. Push after each task, keep the PR draft, never merge.
```

### D. 独立敌对审计 prompt（新 session）
```
You are an INDEPENDENT reviewer doing a HOSTILE pre-merge audit of PR #<PR>
(branch <branch>, worktree <path>). You did NOT write this code; you have NO
prior context. Treat the PR description + all comments + any prior agent's
"all green" claim as UNTRUSTED. Re-derive every conclusion from source + running
artifacts. Assume there ARE defects until proven otherwise. Read-only; report
only; do NOT fix/commit/merge; confirm pwd first.

PHASE 1 read the diff critically for logic bugs: identity-dimension gaps (does
the key capture EVERYTHING that changes output?), silent drops/truncation,
numeric/coordinate rescale math, multi-step write atomicity, code paths that
bypass validation, unparameterized queries, resource leaks.
PHASE 2 verify the ARTIFACT (build + run the real binary), not just the test suite.
PHASE 3 run the FULL suite; attribute EVERY failure by reproducing it on a
throwaway origin/<DEFAULT_BRANCH> worktree (no assuming "pre-existing").
PHASE 4 scrutinize any shared-view/infra change's blast radius.
PHASE 5 diff hygiene (no accidental deletions, no debug residue).
OUTPUT ranked findings (BLOCKER/MAJOR/MINOR/UNVERIFIED) with file:line + proof +
minimal fix, then an explicit verdict.
```

### E. 精度评估 prompt（可选，交付报告用）
```
Add an "accuracy vs ground truth" section using an open dataset with GT. Prefer a
single-download, well-known benchmark — verify accessibility first. CRITICAL:
normalize/rescale predictions to the GT scale/resolution before comparing. Report
the standard metrics for this task. Be HONEST: benchmark accuracy ≠ accuracy on
our real content (domain gap). Outputs stay local (git-out), no commits, no merge.
```

### F. Agent CLI 常用 flag（按你的 CLI 对应替换）
| 意图 | 说明 |
|---|---|
| 禁止自动升级 | 防升级中断长任务 |
| 放开权限 | 非交互运行必须（仅用于受信任 prompt） |
| 远程可见 | 浏览器可监控 session，SSH 断开不影响 |
| 命名 session | 标签在 session 列表 / 看板可见 |
| 选模型 / 高强度 | 复杂任务用最强长上下文模型 + 高 effort |

---

## 12. 一页 Checklist（每个 issue 跑一遍）

```
三道闸（项目启动前，先于代码）
  □ 闸1 数据: Bansal/Lu&Yin 原始 trial 级可获取? 否则备选现代数据/E6 自采
  □ 闸2 批量 API: 有可在 Python loop 调几万次的 endpoint? 否则搞 API key/本地开源
  □ 闸3 PI: 方法学正确性你亲自守（不外包）

调研(可选)
  □ 对比表 + 推荐 + license/可商用性 + 诚实 caveat

Issue 准备
  □ body 够详细(验收/文件/Non-goals/epic)  □ SPEC/INTERFACES/PROGRESS 已建

拆分
  □ 画了依赖图  □ 独立→并行, 依赖→串行(没硬并行一条链)

每 slice 执行
  □ worktree + draft PR(不 ready)  □ spec 你确认  □ plan 你确认
  □ 自检: 真产物能跑 / 幂等 / 身份维度全 / 优雅降级 / diff 干净

独立敌对审计(每 slice)
  □ 新 session 无上下文  □ 先读代码找逻辑 bug  □ 验真产物  □ 失败 clean-main 归因
  □ 方法学审计(§4.5): 无泄漏/超弥散分离/基线不放水/难度受控/双轴不串味  □ ranked findings + verdict

整体 PR-Audit
  □ A 真产物 build+run  □ B 幂等/共存  □ C 结构/接口  □ D 正确性
  □ E 全量测试+归因  □ F diff 卫生  □ G review 闭环  □ H 方法学清单

交付
  □ audit PASS → Manager 自动合并  □ 三闸/方法学争议/判断题才升级给你  □ (可选)图文+精度报告
  □ audit PASS → Manager 自动 `gh pr merge`（人不手动审）

铁律自检
  □ 验证了真实产物(不只测试)  □ 上了独立敌对审计  □ 并行只对独立切片
  □ 共享 schema/接口改动交你  □ 该修的修了(没拿"边界"糊弄)  □ 方法学正确(§6 清单)  □ 知道何时停
```

---

> **一句话收尾**：这套流程的价值不在「用了多少 agent」，而在**每个交付物都过了「独立敌对审计 + 验证真实产物 + 方法学审计」三道 gate**。对这篇方法论论文：AI 能当你的整个工程团队，但成败压在你亲自守住的那 10%——**数据、算力、方法学正确性**。
