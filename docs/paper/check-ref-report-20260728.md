# 全量 citation 审计报告（2026-07-28）

**论文**：*Two Ways a Design Fails*  
**审计对象**：`main.tex`、`references.bib`  
**指定工具**：`C:\Users\v-elzhang\Desktop\MyFolder\check-cite`（check-ref workflow）  
**审计方式**：只读；未修改论文正文或参考文献库  

## 1. 审计口径与覆盖率

本报告按 check-ref 要求做两维核查，并将多 key 合引拆开判断：

1. **真实性与元数据**：先用工具脚本逐条查询 OpenAlex / Semantic Scholar，再用 DOI/Crossref、ACM、PMLR、ACL Anthology、arXiv 或商业网站原页独立复核。
2. **内容支持**：逐个检查 citation 邻近主张，区分“直接支持”“部分/间接支持”“不支持”。同一 `\cite{a,b}` 不因其中一篇支持就让整组通过。

覆盖统计：

| 项目 | 数量 | 结果 |
|---|---:|---|
| `references.bib` 条目 | 36 | 36 条均找到真实对应来源 |
| 唯一 cited keys | 36 | 与 bibliography 完全一致 |
| 原始 citation 命令 | 47 | 43 个 `\cite` + 4 个 `\citeauthor` |
| 实质引用点 | 43 | 4 组同句 `\citeauthor` + `\cite` 合并计数 |
| key 出现 / claim-source 对 | 70 | 全部逐对判断 |
| cited 但 bib 缺失 | 0 | 无 |
| bib 中未引用 | 0 | 无 |

工具检索说明：Semantic Scholar 在无 DOI 检索中多次返回 429；这些失败没有被当作通过，而是改由 OpenAlex 和上述权威原始页面复核。商业网页没有稳定 DOI/出版记录，按页面当前可见标题、日期和文案判断。

## 2. 总体结论

### 2.1 真实性与元数据

- **36/36 来源真实存在**，没有发现捏造文献。
- **32/36 的关键身份字段可接受**。
- **3 条有明确元数据错误**：`uxia_synthetic` 年份、`seshadri2026lost` venue、`robinson2026influence` 作者表。
- **1 条商业网页记录无法验证所填 2025 年和旧标题**：`syntheticusers`；URL 有效，但当前页已换标题且显示 ©2026。
- 另有多条不是错误、但 camera-ready 应升级为正式出版记录或补 DOI/pages。

### 2.2 内容支持

按 70 个 claim-source 对计：

| 判定 | 数量 | 含义 |
|---|---:|---|
| 直接支持 | 44 | 来源的研究对象、方法或结论直接覆盖主张 |
| 部分/间接支持 | 19 | 只支持主张的一部分，或主张是作者基于来源作出的合理延伸 |
| 不支持 | 7 | 主题相近但具体主张不在来源中，或来源研究对象/机制不同 |

最需要修正的内容问题：

1. `wang2025mixture` **不支持 strongest-first / quality-optimal routing**。它研究多模型分层聚合（Mixture-of-Agents）以提升输出能力，不是请求路由，更没有给出“按能力从强到弱选择后端”的顺序。该问题在引用点 8、36、37、42 重复出现。
2. `hamalainen2023evaluating` **不支持“caricature rather than simulate subpopulations”**，也不直接支持 collapse diversity / echo priors / distribution mis-estimation。该文评估 LLM 生成 synthetic HCI research data，并强调输出可显得可信及其方法风险；“caricature”的直接证据来自 `cheng2023compost`。该问题在引用点 4、14 重复出现。
3. `rastogi2022deciding` **不支持“offline estimation of team performance”**。该文建立认知偏差框架并包含两项用户实验和去锚策略，不是离线估计研究。
4. `bansal2021whole` 与 `gajos2022people` 都不直接证明“variance is usually a nuisance to be averaged away”；它们可作为均值导向 human-AI 研究的背景，但该措辞是本文的综合判断。
5. 商业平台确实宣传“minutes, not weeks”，但 `syntheticusers` 当前页明确自称“discovery co-pilot, not a replacement for real research”；把两家都概括成替代真人研究过强。
6. `park2024generative` 的“约 85% accuracy”应写清：当前版本报告 83%/82%/86%，是**相对于参与者两周 test-retest consistency 的比例**，不是普通的 85% raw accuracy。

## 3. 维度一：36 条参考文献真实性与元数据

符号：**通过** = 关键身份字段一致；**修正** = 有明确错误；**核实/更新** = 来源真实，但记录不完整、版本已演进或网页字段无法稳定确认。

| # | bib key | 判定 | 独立复核与说明 |
|---:|---|---|---|
| 1 | `syntheticusers` | 核实/更新 | 官网真实且可访问；当前 H1 为 “Synthetic users, organic insights.”，©2026。当前页无可验证的 2025 发布日期，且明确称“discovery co-pilot, not a replacement for real research”。建议用访问日期型网页引用，不硬填无法证实的 2025。 |
| 2 | `uxia_synthetic` | **修正** | 网页正式标题为 “7 Top Synthetic User Testing Platforms to Watch in 2026”，`.bib` 使用了不完整的缩写标题；页面显示 “Jan 21, 2026”，页面元数据又显示 2026-07-25。标题应完整记录，年份无论采用哪一页面日期都应为 2026，并保留访问日期。 |
| 3 | `bansal2021whole` | 通过 | DOI `10.1145/3411764.3445717`；CHI 2021，作者、标题、年份一致，pp. 1–16。 |
| 4 | `bucinca2021trust` | 通过 | DOI `10.1145/3449287`；PACMHCI 5(CSCW1), 2021, pp. 1–21。 |
| 5 | `vasconcelos2023explanations` | 通过 | DOI `10.1145/3579605`；PACMHCI 7(CSCW1), 2023, pp. 1–38。 |
| 6 | `zhang2020confidence` | 通过 | DOI `10.1145/3351095.3372852`；FAT* 2020, pp. 295–305。 |
| 7 | `lai2019human` | 通过 | DOI `10.1145/3287560.3287590`；FAT* 2019, pp. 29–38；副标题一致。 |
| 8 | `schemmer2023appropriate` | 通过 | DOI `10.1145/3581641.3584066`；IUI 2023, pp. 410–422。 |
| 9 | `gajos2022people` | 通过 | DOI `10.1145/3490099.3511138`；IUI 2022, pp. 794–806。 |
| 10 | `santurkar2023whose` | 通过/补全 | PMLR 202, ICML 2023, pp. 29971–30004；标题、六位作者、年份一致。建议补 `volume/pages/publisher/url`。 |
| 11 | `argyle2023out` | 通过/补全 | DOI `10.1017/pan.2023.2`；Political Analysis 31(3), 2023, pp. 337–351。`.bib` 缺 pages。 |
| 12 | `park2022social` | 通过 | DOI `10.1145/3526113.3545616`；UIST 2022, pp. 1–18。 |
| 13 | `aher2023using` | 通过/补全 | PMLR 202, ICML 2023, pp. 337–371；标题、作者、年份一致。建议补 `volume/pages/publisher/url`。 |
| 14 | `hu2024quantifying` | 通过 | DOI `10.18653/v1/2024.acl-long.554`；ACL 2024, pp. 10289–10307。 |
| 15 | `park2024generative` | 通过/版本更新 | arXiv `2411.10109` 的 2024 v1 题名确为 *Generative Agent Simulations of 1,000 People*。当前 2026 v3 已改题为 *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*，样本为 1,052。旧版本引用不虚假，但应锁定 v1 或更新题名/版本。 |
| 16 | `bo2024rely` | 通过/正式版更新 | arXiv `2412.15584` 真实；当前记录给出正式 journal reference：CHI 2025。建议改为 CHI 2025 正式出版记录。 |
| 17 | `hamalainen2023evaluating` | 通过 | DOI `10.1145/3544548.3580688`；CHI 2023, pp. 1–19。标题仅有大小写差异。 |
| 18 | `cheng2023compost` | 通过/补全 | DOI `10.18653/v1/2023.emnlp-main.669`；EMNLP 2023, pp. 10853–10875。建议补 DOI/pages。 |
| 19 | `luguri2021shining` | 通过 | DOI `10.1093/jla/laaa006`；Journal of Legal Analysis 13(1), 2021, pp. 43–109。部分索引将早期上线误作 2020；正式卷期年份 2021 正确。 |
| 20 | `mildner2023dark` | 通过 | DOI `10.1145/3544548.3580695`；CHI 2023, pp. 1–15。`% VERIFY` 注释已无必要。 |
| 21 | `rastogi2022deciding` | 通过 | DOI `10.1145/3512930`；PACMHCI 6(CSCW1), 2022, pp. 1–22。 |
| 22 | `cao2025specializing` | 通过/补全 | 正式发表于 NAACL 2025；DOI `10.18653/v1/2025.naacl-long.162`，pp. 3141–3154。建议用正式记录替代仅 arXiv note。 |
| 23 | `dominguez2024questioning` | 通过 | arXiv `2306.07951`，v4 注明 NeurIPS 2024；标题、三位作者、年份和 venue 一致。 |
| 24 | `bisbee2024synthetic` | 通过/补全 | DOI `10.1017/pan.2024.5`；Political Analysis 32(4), 2024, pp. 401–416。建议补 DOI。 |
| 25 | `tjuatja2024llms` | 通过/补全 | DOI `10.1162/tacl_a_00685`；TACL 12, 2024, pp. 1011–1026。`.bib` 缺 pages。 |
| 26 | `sclar2024quantifying` | 通过 | arXiv `2310.11324`，camera-ready 注明 ICLR 2024；标题、作者一致。 |
| 27 | `mizrahi2024state` | 通过/补全 | DOI `10.1162/tacl_a_00681`；TACL 12, 2024, pp. 933–949。`.bib` 缺 pages。 |
| 28 | `haase2026within` | 通过 | arXiv `2601.21339`，2026-01-29 v1；标题、七位作者一致。 |
| 29 | `zheng2023judging` | 通过 | arXiv `2306.05685`；NeurIPS 2023 Datasets and Benchmarks；标题、作者与年份一致。 |
| 30 | `mitchell2019model` | 通过/补全 | DOI `10.1145/3287560.3287596`；FAT* 2019, pp. 220–229。`.bib` 缺 pages/publisher。 |
| 31 | `simmons2011false` | 通过 | DOI `10.1177/0956797611417632`；Psychological Science 22(11), pp. 1359–1366。 |
| 32 | `simonsohn2020specification` | 通过 | DOI `10.1038/s41562-020-0912-z`；Nature Human Behaviour 4, pp. 1208–1214。 |
| 33 | `ong2025routellm` | 通过 | arXiv `2406.18665`，v4；ICLR 2025；标题、八位作者一致。 |
| 34 | `wang2025mixture` | 通过 | arXiv `2406.04692`；ICLR 2025；标题与五位作者一致。注意真实性通过不等于支持本文的 routing 主张。 |
| 35 | `seshadri2026lost` | **修正** | arXiv `2601.17087` 真实，但 `.bib` 的 `note={ICLR 2026}` 错误。正式记录为 **ACL 2026 long paper**，DOI `10.18653/v1/2026.acl-long.2192`，pp. 47423–47439。 |
| 36 | `robinson2026influence` | **修正** | arXiv `2602.21262` 真实；当前 v3 作者为 Sasha Robinson、Katherine M. Collins、Ilia Sucholutsky、Kelsey R. Allen。`.bib` 多列了 **Kerem Oktar**，且因此作者顺序不符。 |

## 4. 维度二：43 个实质引用点 / 70 个 claim-source 对

符号：**✓** 直接支持；**△** 部分、间接或合理延伸；**✗** 不支持该具体主张。

| ID | `main.tex` 行 | 邻近主张 | 按 key 拆分的判断 |
|---:|---:|---|---|
| 1 | 121 | 既有工作通常把用户间方差当作应平均掉的 nuisance | `bansal2021whole` △：研究平均团队表现/依赖，但未主张方差是 nuisance；`gajos2022people` △：研究 AI assistance 与 incidental learning，亦未直接讨论用户方差。 |
| 2 | 125 | coercive framing 下用户会系统采用错误 AI，甚至人人一起失败 | `bucinca2021trust` △：直接支持 over-reliance 与 cognitive forcing，但不研究 coercive framing；`vasconcelos2023explanations` △：支持成本/收益影响 over-reliance，但不是 coercive wrong-AI design；`luguri2021shining` △：直接证明 dark patterns 可强力操纵选择，但不涉及 AI advice。三篇合在一起构成跨文献推论，不是任何一篇的直接结论。 |
| 3 | 136 | synthetic users 已用于 HCI/社会研究 | `park2022social` ✓；`argyle2023out` ✓；`aher2023using` ✓。分别覆盖 social prototype、survey silicon samples、复制人类实验。 |
| 4 | 138 | LLM 模拟人会压缩多样性、回显基座先验、误估分布 | `santurkar2023whose` △：支持群体意见错配、倾向和 steering 后仍错配，但“collapse diversity”较强；`cao2025specializing` ✓：默认方法及最佳方法仍难准确模拟分布；`bisbee2024synthetic` ✓：更低响应变异、回归差异和提示/时间不稳定；`dominguez2024questioning` ✓：选项顺序/标签偏差和近均匀响应；`cheng2023compost` ✓：直接证明部分群体/话题易 caricature；`hamalainen2023evaluating` ✗：研究 synthetic HCI data 的可生成性与可信风险，不给出这些 collapse/prior/distribution 结论。 |
| 5 | 143 | 商业平台宣传几分钟完成设计评估，压缩或替代数周真人研究 | `syntheticusers` △：直接支持“minutes, not weeks”和无需招募，但当前页同时明确“not a replacement for real research”；`uxia_synthetic` ✓：直接写明 minutes 而非 days/weeks，并称 replace slow, expensive human testing；同页结尾又建议作为 human-centric research 的 complement，正文最好保留限定。 |
| 6 | 147 | quality-optimal router 会自然选择最强后端 | `ong2025routellm` ✓：明确在 stronger/ weaker LLM 间按成本和 response quality 动态路由；“无成本约束时偏向 stronger”是其目标的直接推论。 |
| 7 | 170 | synthetic panel 的 reliability/invariance 逻辑上先于 external validity | `santurkar2023whose` △：提供群体错配证据，但不提出该逻辑优先关系；`cheng2023compost` △：展示 model/persona/topic 对 caricature 的影响，但也不直接论证 psychometric ordering。主张主要是本文的方法论论证。 |
| 8 | 233 | vulnerability coverage selection 是 capability routing 的反面 | `ong2025routellm` ✓：提供 quality/capability routing 对照；`wang2025mixture` ✗：MoA 是多模型聚合，不是路由或 strongest-first selection。 |
| 9 | 255 | LLM 被提出用于 surveys、user studies、formative evaluation | `park2022social` ✓；`argyle2023out` ✓；`aher2023using` ✓。 |
| 10 | 257 | 模拟用户压缩意见多样性并过度代表多数观点 | `santurkar2023whose` △：直接支持 demographic misalignment、左倾倾向和部分群体代表不足；摘要不直接证明普遍“压缩多样性/过度代表多数”。 |
| 11 | 257 | 模拟用户误校准分布 | `cao2025specializing` ✓：直接以真实/预测 response distribution divergence 为任务且最佳模型仍困难；`dominguez2024questioning` ✓：直接展示顺序偏差和随机化后趋近均匀分布。 |
| 12 | 258 | LLM 呈现非人类 response biases | `tjuatja2024llms` ✓：九模型通常不能反映 human-like response biases，且会对人类不敏感的扰动敏感。 |
| 13 | 259 | LLM 不能可靠替代 human survey samples | `bisbee2024synthetic` ✓：标题与结论均直接支持，含低变异、回归不一致和不可复现。 |
| 14 | 260 | LLM caricature 而非模拟 subpopulations | `cheng2023compost` ✓：直接定义并测量 individuation/exaggeration caricature；`hamalainen2023evaluating` ✗：没有这一发现。 |
| 15 | 261 | agentic evaluation 中 simulated users 随后端变化九个百分点，且有误校准和人口差距 | `seshadri2026lost` ✓：摘要逐项直接支持。 |
| 16 | 267 | task skill、persuasion、对误导的 vigilance 可分离 | `robinson2026influence` ✓：摘要明确称三者 dissociable，并显示强任务表现不保证识别误导。 |
| 17 | 273 | interview-grounded agents 以约 85% accuracy 重现个人调查回答 | `park2024generative` △：数值来源真实，但应表述为 interview/survey/combined agents 达到参与者自身 test-retest consistency 的 83%/82%/86%，不是普通 raw accuracy；样本当前为 1,052。 |
| 18 | 276 | persona 解释 annotation variance，较大 instruction-tuned models 在 persona matters 时模拟更好 | `hu2024quantifying` ✓：与论文研究问题和结论直接一致。 |
| 19 | 285 | 大量工作研究 confidence/explanations 下的 appropriate reliance | `bansal2021whole` ✓；`bucinca2021trust` ✓；`zhang2020confidence` ✓；`lai2019human` ✓；`schemmer2023appropriate` ✓。五篇共同且各自相关。 |
| 20 | 287 | explanations 有时增加 over-reliance | `bansal2021whole` ✓：直接发现解释增加接受 AI 建议的概率，不论 AI 对错。 |
| 21 | 290 | disclaimers/uncertainty highlighting 降低 over-reliance，却通常不改善 appropriate reliance | `bo2024rely` ✓：随机实验的核心结论直接支持；该文现已有 CHI 2025 正式版。 |
| 22 | 291 | 精心设计的 explanations 可降低 over-reliance | `vasconcelos2023explanations` ✓：标题、框架和五项研究直接支持。 |
| 23 | 299 | deceptive/coercive designs 已被系统整理 | `luguri2021shining` ✓：实验比较多类 dark patterns；`mildner2023dark` ✓：对 social-network dark patterns 作主题分析。 |
| 24 | 304 | Rastogi 是“offline estimation of team performance for decision support” | `rastogi2022deciding` ✗：该文建立认知偏差/准确率框架，并用两项用户实验验证去锚和时间分配策略；权威摘要不支持“offline estimation”这一定位。 |
| 25 | 311 | measurement invariance 问的是工具在群体/情境间是否含义相同 | `santurkar2023whose` △：展示不同群体被代表程度不同；`tjuatja2024llms` △：展示 wording/context response effects；二者提供类比案例，但不是 measurement invariance 定义来源。 |
| 26 | 319 | 严重 backend non-invariance 会破坏单 backend validity claim | `dominguez2024questioning` ✓：43 模型、排序/标签偏差及随机化后的近均匀响应直接显示单配置调查推断不稳。 |
| 27 | 324 | LLM evaluation 自由度类似 undisclosed analytic flexibility | `simmons2011false` ✓：直接建立分析/收集/报告自由度如何抬高 false positives；LLM 类比由本文提出。 |
| 28 | 325 | 小 prompt-format 改动会大幅改变结果 | `sclar2024quantifying` ✓：最大 76 accuracy points，且跨模型格式表现相关弱。 |
| 29 | 326 | single-prompt scores 会误表模型能力 | `mizrahi2024state` ✓：650 万实例、20 模型、39 任务显示绝对与相对表现都随 instruction template 大幅变化。 |
| 30 | 328 | 已有工作把 creative-task 变异拆为 model/prompt/sampling | `haase2026within` ✓：12 模型 × 10 prompts × 100 samples，直接报告三类方差比例。 |
| 31 | 329 | 采用 specification-curve-style multiverse reporting | `simonsohn2020specification` ✓：方法来源直接对应。 |
| 32 | 336 | sensitivity analysis、abstention 立场延续 model/evaluation-card tradition | `mitchell2019model` △：直接支持结构化模型用途/限制/性能报告；不直接提出本文的跨后端 sensitivity 或 abstention 规则。 |
| 33 | 337 | multi-model benchmarking 与 reliability-aware judging | `zheng2023judging` ✓：比较多模型，并系统研究 judge 的 position/verbosity/self-enhancement biases、human agreement 和缓解方法。 |
| 34 | 400 | 文本界面条件沿用 Bansal 的 confidence-only 与 highlighted-token definitions | `bansal2021whole` ✓：直接方法来源。 |
| 35 | 453 | 使用 Bansal human data 估计 between-user reliance over-dispersion | `bansal2021whole` ✓：正确标注原始 human dataset；具体 over-dispersion 数值是本文重分析结果。 |
| 36 | 745 | 单个 frontier backend 是 quality-optimal router 会选的模型 | `ong2025routellm` △：支持 strong/weak quality routing，但实际 router 在成本约束下并非永远选 strongest；`wang2025mixture` ✗：不是 routing。 |
| 37 | 781 | capability-first 顺序就是 quality-optimal router 偏好的 strongest-first 顺序 | `ong2025routellm` △：其目标是 cost-quality 动态选择，而非固定 strongest-first 排序；`wang2025mixture` ✗：无路由顺序。该 strongest-first 定义应明确为本文构造的 baseline，而非两文既有算法。 |
| 38 | 791 | RAIR/RSR 属于 established appropriate-reliance vocabulary | `schemmer2023appropriate` ✓：论文直接概念化 appropriate reliance，并使用相应 reliance/self-reliance 区分。 |
| 39 | 812 | LSAT logical-reasoning arm 复用 Bansal task/protocol context | `bansal2021whole` ✓：Bansal 的实验任务/界面条件包含该类任务；本文的新 robustness 结果不归因给来源。 |
| 40 | 853 | cognitive forcing 要求先独立思考再看/采用 AI | `bucinca2021trust` ✓：三种 forcing interventions 的直接理论与设计来源。 |
| 41 | 961 | 商业平台会采用文中所说的“standard engineering defaults” | `syntheticusers` △；`uxia_synthetic` △：页面支持速度、规模、persona、自动分析等平台实践，但没有说明默认只用最强 backend 或单 backend point estimate。该句是合理的行业假设，不能写成平台已证实事实。 |
| 42 | 963 | strongest model 是 quality-optimal router 的选择，且与 risk audit 相反 | `ong2025routellm` △：可作为 quality/cost routing 对照，但 strongest-only 是无成本约束下的推论；`wang2025mixture` ✗：MoA 聚合不支持 strongest-first routing。risk inversion 本身由本文实验提供，不应归因给两篇来源。 |
| 43 | 1011 | 完整 specification-curve/multiverse analysis 留作未来工作 | `simonsohn2020specification` ✓：正确引用所指方法。 |

## 5. 建议的修正优先级

### P0：提交前必须修正

1. 将 `seshadri2026lost` 从 `ICLR 2026` 改为 ACL 2026 正式记录（DOI `10.18653/v1/2026.acl-long.2192`）。
2. 删除 `robinson2026influence` 作者表中不存在于当前 arXiv v3 的 `Kerem Oktar`，并按原页恢复作者顺序。
3. 将 `uxia_synthetic` 改为网页完整标题，并将年份改为 2026。
4. 删除四处用 `wang2025mixture` 支撑 routing/strongest-first 的引用，或把文字改为“capability-oriented multi-model systems”并明确 MoA 是聚合而非路由。
5. 从 “caricature” 具体论断中移除 `hamalainen2023evaluating`；保留 `cheng2023compost` 即有直接证据。
6. 改写 `rastogi2022deciding` 的 “offline estimation” 定位。

### P1：论证精度修正

1. 将 “≈85% accuracy” 改为“达到参与者自身 test-retest consistency 的 83%–86%”，并决定锁定 2024 v1 还是引用当前 2026 v3。
2. 将商业平台表述限定为“加速、前置筛查或在部分流程中 stand in”；注明 Synthetic Users 当前自称 complement/co-pilot。
3. 把 “variance, usually a nuisance” 明确标成本文对既有均值导向研究的概括，而不是 Bansal/Gajos 的直接结论。
4. 将 capability-first 明确写成本文构造的 strongest-first baseline；RouteLLM 本身是按请求动态权衡成本/质量，不是固定顺序。

### P2：camera-ready 元数据补全

补齐 `cheng2023compost`、`cao2025specializing`、`bisbee2024synthetic` 的 DOI；补齐 `santurkar2023whose`、`aher2023using`、`argyle2023out`、`tjuatja2024llms`、`mizrahi2024state`、`mitchell2019model` 的 pages/volume/publisher 等正式字段；将 `bo2024rely` 升级为 CHI 2025 正式记录；删除 `mildner2023dark` 上已完成核实的 `% VERIFY` 注释。

## 6. 最终审计声明

本轮检查覆盖了 bibliography 中全部 36 条记录、正文全部 47 个 citation 命令，并在合并 4 组重复的 narrative author-year 写法后，对全部 43 个实质引用点、70 个 claim-source 对逐项作出判断。未发现漏引 key、未引用条目或虚构来源；发现 3 条明确元数据错误、1 条商业网页日期/标题不可稳定验证、7 个不支持的 claim-source 对，以及 19 个需要降格为“部分/间接支持”的 claim-source 对。

本报告未修改 `main.tex`、`references.bib` 或旧版 `check-ref-report.md`。