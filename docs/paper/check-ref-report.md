# check-ref 审计报告

**论文**：Two Ways a Design Fails — CHI submission draft  
**文件**：`main.tex` + `references.bib`  
**审计日期**：2026-07-20  
**审计工具**：check-ref (helloxAI/check-cite)  
**检索来源**：OpenAlex、Semantic Scholar、CrossRef、PMLR、ACL Anthology  
**本报告全程只读**，未对 `main.tex` 或 `references.bib` 做任何修改。

---

## 总体摘要

| 维度 | 总条/处 | 通过 | 有疑问 |
|---|---|---|---|
| 维度一：参考文献真实性 | 17 条 | 17 | 0（另有 2 条 camera-ready 建议） |
| 维度二：引用点内容匹配 | 13 处（含多 key 拆分共约 24 个引用点对） | 22 | 2 |

---

## 维度一：真实性核查结果

### 通过表（17/17）

| # | bib key | 核查 DOI / 路径 | 字段差异备注 |
|---|---|---|---|
| 1 | `bansal2021whole` | 10.1145/3411764.3445717 | 全部关键字段（标题/作者/年份/期刊）精确匹配。OpenAlex 及 S2 均确认为 CHI '21。 |
| 2 | `bucinca2021trust` | 10.1145/3449287 | OpenAlex/S2 标题略有截断（省略副标题），但 DOI 精确匹配，PACMHCI Vol.5 CSCW1 2021 ✓。 |
| 3 | `vasconcelos2023explanations` | 10.1145/3579605 | S2 显示年份为 2022（arXiv preprint），.bib 填 2023 为 PACMHCI 正式出版年，正确。PACMHCI Vol.7 CSCW1 ✓。 |
| 4 | `zhang2020confidence` | 10.1145/3351095.3372852 | 全部字段匹配；conference = FAT* '20（现 FAccT）✓。S2 作者名略缩写，不影响一致性。 |
| 5 | `lai2019human` | 10.1145/3287560.3287590 | OpenAlex 截断副标题，S2 完整返回 "A Case Study on Deception Detection"，与 .bib 完全一致。年份 2019（FAT* '19）✓。 |
| 6 | `schemmer2023appropriate` | 10.1145/3581641.3584066 | 全部字段匹配；venue = IUI '23 ✓。 |
| 7 | `gajos2022people` | 10.1145/3490099.3511138 | 全部字段匹配；venue = IUI '22 ✓。 |
| 8 | `santurkar2023whose` | PMLR v202/santurkar23a | 无 DOI in .bib，经 PMLR 官方页面确认标题/作者/年份/conference 全部一致（ICML '23, pp. 29971–30004）✓。 |
| 9 | `argyle2023out` | 10.1017/pan.2023.2 | S2 年份 2022（arXiv），.bib 填 2023 为 Political Analysis 正式发表年，DOI 精确匹配 ✓。Vol. 31, No. 3 ✓。 |
| 10 | `park2022social` | 10.1145/3526113.3545616 | 全部字段匹配；venue = UIST '22 ✓。第一作者 "Joon-Sung Park"（OpenAlex 加连字符）vs. .bib "Joon Sung Park"——同一人，差异可忽略。 |
| 11 | `aher2023using` | PMLR v202/aher23a | 无 DOI in .bib，经 PMLR 官方页面确认标题/作者/年份/conference 全部一致（ICML '23, pp. 337–371）✓。 |
| 12 | `hamalainen2023evaluating` | 10.1145/3544548.3580688 | 副标题大小写 "a Case Study" vs. "A Case Study" 差异不影响一致性。作者 Hämäläinen 拉丁化拼写与 .bib LaTeX 转义一致 ✓。CHI '23 ✓。 |
| 13 | `cheng2023compost` | 10.18653/v1/2023.emnlp-main.669（OpenAlex 返回） | .bib 无 DOI；经 OpenAlex 确认 EMNLP '23 正式发表，标题/作者/年份完全一致。**camera-ready 建议补充 DOI**（见下方说明）。 |
| 14 | `luguri2021shining` | 10.1093/jla/laaa006 | **OpenAlex 误报年份为 2020；CrossRef 权威记录确认 `issued.date-parts = [2021]`、`published-print = 2021-03-23`。.bib 年份 2021 正确。** Journal of Legal Analysis Vol.13 No.1 pp.43–109 ✓。 |
| 15 | `mildner2023dark` | 10.1145/3544548.3580695 | .bib 有 `% VERIFY` 注释；DOI 核实通过，标题/作者/年份/CHI '23 完全匹配，注释可删除。 |
| 16 | `rastogi2022deciding` | 10.1145/3512930 | 全部字段匹配；PACMHCI Vol.6 CSCW1 2022 ✓。标题大小写差异（"AI-Assisted" vs. "AI-assisted"）不影响一致性。 |
| 17 | `cao2025specializing` | 10.18653/v1/2025.naacl-long.162（ACL Anthology） | .bib 仅有 `note = {arXiv:2502.07068}`；经 ACL Anthology 确认 NAACL 2025 正式发表，标题/作者/年份完全一致，pp. 3141–3154。**camera-ready 建议替换为正式 DOI**（见下方说明）。 |

### 不通过表

（无）

---

### Camera-ready 建议（次要字段，不影响通过/不通过判定）

**`cheng2023compost`**：缺少正式 DOI。建议在 .bib 中补充：
```bibtex
doi = {10.18653/v1/2023.emnlp-main.669}
```

**`cao2025specializing`**：目前仅有 `note = {arXiv:2502.07068}`，论文已正式发表于 NAACL 2025。建议更新为：
```bibtex
doi       = {10.18653/v1/2025.naacl-long.162},
pages     = {3141--3154},
address   = {Albuquerque, New Mexico},
```
（同时可删除 `note`，或保留作 arXiv 附注。）

---

## 维度二：引用点内容匹配核查

### 匹配通过表（22/24 个引用点对）

| 位置 | 引用 key | 引用处论断 | 摘要支持情况 |
|---|---|---|---|
| Intro § Axis 1 | `bansal2021whole` | "方差通常是被平均掉的噪音" | ✓ 论文聚焦平均准确率，不以方差为安全指标，符合描述。 |
| Intro § Axis 1 | `gajos2022people` | 同上 | ✓ 论文研究均值层面的学习收益，不关注方差。 |
| Intro § Axis 2 | `bucinca2021trust` | "coercive wrong-AI adoption dangerous even at zero dispersion" | ✓ 论文研究普遍的过度依赖问题，支持 uniform failure 场景。 |
| Intro § Axis 2 | `luguri2021shining` | "everyone can fail together（coercive designs）" | ✓ 论文实验证明强制性黑暗模式使几乎所有用户做出被操纵的选择（最高 4× 订阅率），支持 uniform failure。 |
| Intro & Related Work | `park2022social` | LLMs as synthetic HCI participants | ✓ 论文核心贡献即 LLM 驱动的 social simulacra。 |
| Intro & Related Work | `argyle2023out` | 同上 | ✓ 论文提出 "silicon samples" 方法模拟人类样本。 |
| Intro & Related Work | `aher2023using` | 同上 | ✓ 论文设计 Turing Experiment 用 LLM 复制人类实验。 |
| Intro & Related Work | `santurkar2023whose` | "compress opinion diversity, over-represent majority views" | ✓ 摘要明确提到与美国人口群体的"substantial misalignment"，及 LM 左偏倾向。 |
| Intro & Related Work | `cao2025specializing` | "mis-calibrate distributions" | ✓ 论文研究的是如何 specialize LLM 以修正默认分布估计的偏差，前提就是默认 LLM 存在分布错配。 |
| Intro & Related Work | `cheng2023compost` | "caricature rather than simulate subpopulations" | ✓ 论文标题/核心概念即 caricature，摘要直接支持。 |
| Related Work | `zhang2020confidence` | "appropriate reliance on AI given confidence/explanations" | ✓ 论文研究 confidence score 和 explanation 对 trust calibration 的影响。 |
| Related Work | `lai2019human` | 同上（reliance on AI） | ✓ 论文研究人类借助 ML 预测做决策，含 deception detection case study。 |
| Related Work | `schemmer2023appropriate` | 同上 | ✓ 论文标题即 "Appropriate Reliance on AI Advice"。 |
| Related Work | `bansal2021whole`（第2处） | "explanations increase over-reliance" | ✓ 摘要明确："explanations increased the chance that humans will accept the AI's recommendation, regardless of its correctness"——直接支持。 |
| Related Work | `luguri2021shining`（第2处） | "deceptive and coercive designs well catalogued" | ✓ 论文系统实验并目录化多种 dark pattern 策略。 |
| Related Work | `mildner2023dark` | 同上 | ✓ 论文对 SNS 中 dark pattern 做主题分析并发现 5 种新模式。 |
| Related Work | `rastogi2022deciding` | "offline estimation of team performance, studying bias and complementarity" | ✓ 摘要讨论 cognitive biases 在 human-AI 协作中的作用，并设计最优 time-allocation strategy。 |
| Method | `bansal2021whole`（第3处） | "条件定义（confidence-only; single/double highlighted-token; adaptive）" | ✓ 论文定义这些 explanation 条件并在三个数据集上实验，是文中方法的直接来源。 |

---

### 有疑问表（2/24 个引用点对）

| 位置 | 引用 key | 引用处论断 | 疑点类型 | 说明 |
|---|---|---|---|---|
| Related Work § Reliance | `vasconcelos2023explanations` | "often finding explanations **increase** over-reliance rather than calibrate it" | **摘要不支持——方向相反** | 该论文的核心贡献是证明"在某些条件下解释 **可以降低** 过度依赖"（"demonstrating empirically that there are scenarios where AI explanations **reduce** overreliance"）。论文的前提虽然承认前人工作发现解释无效果（null effect），但本文 claim 方向为"可以 reduce"，而非"会 increase"。被引处论断与该论文的主要结论方向相反，存在张冠李戴风险。**建议**：若要引用"解释会增加过度依赖"，bansal2021whole 单独引用即足够；vasconcelos2023explanations 更适合在"最近有研究显示解释在特定条件下可减少过度依赖"处引用。 |
| Intro / Related Work | `hamalainen2023evaluating` | "caricature rather than simulate subpopulations" | **话题层面假阳性** | 该论文实验结论是"GPT-3 可以生成可信的 HCI 体验叙述"（正向结论），主要担忧是 **可信度过高** 导致的滥用风险，而非 caricature/歪曲。"caricature" 一词出自 cheng2023compost，不是 hamalainen2023evaluating 的发现。两篇同列引用，在话题（LLM 可靠性）上相关，但 hämäläinen 的具体结论方向更接近"可能过于可信（hyper-believable）"而非"夸张失真"。**建议**：该处引用归类为"话题相关但具体论断不符"；如果想用 hämäläinen，更准确的引用点是"LLM 生成的 HCI 数据存在可靠性顾虑"或 Introduction 中广义的 LLM 可靠性批评，而不是 "caricature" 这个具体说法。 |

---

## 结论与建议

**维度一（真实性）**：17 条参考文献全部通过。无条目存在标题/作者/年份张冠李戴问题。次要建议：
- 删除 `mildner2023dark` 条目上的 `% VERIFY` 注释（已核实通过）。
- Camera-ready 前为 `cheng2023compost` 和 `cao2025specializing` 补充正式 DOI。
- 注意：`luguri2021shining` 的年份 2021 正确，OpenAlex 数据库存在错误（标为2020），无需修改 .bib。

**维度二（内容匹配）**：2 处有疑问，均不是"引用不存在的文献"或"张冠李戴"，而是引用逻辑层面的问题：
1. `vasconcelos2023explanations` 被放在"解释会增加过度依赖"的支撑引用中，与该文主要结论方向相反——**建议调整引用位置或补充说明**。
2. `hamalainen2023evaluating` 被用于支撑 "caricature" 论断，实际上该文的主要发现是 LLM 回答"可信"（偏正向），而非"夸张失真"——**建议分开引用或调整措辞**。

**本报告未对 `main.tex`、`references.bib` 或任何其他文件做任何修改。**
