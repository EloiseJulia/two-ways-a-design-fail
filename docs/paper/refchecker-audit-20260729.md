# RefChecker 全量引用审计（2026-07-29）

**论文**：*Two Ways a Design Fails*  
**输入**：`main.tex`、`references.bib`  
**指定工具**：`C:\Users\v-elzhang\Desktop\MyFolder\refchecker` v3.0.158  
**机器原始结果**：`refchecker-report-20260729.json`

## 1. 覆盖与方法

- 当前正文共有 **49 个 citation 命令**：44 个 `\cite`，其余为 `\citeauthor`。
- 正文引用 **36 个唯一 key**，BibTeX 也有 **36 条**；无缺失 key，无未引用条目。
- RefChecker 的 `.tex` 路径识别到 `\bibliography{references}` 后错误回退到 PDF/GROBID；本机无 Docker/提取 LLM，因此该路径未生成结果。随后按工具原生支持方式直接检查 `references.bib`，成功覆盖 **36/36**。
- RefChecker 汇总：**0 unverified，0 likely hallucinated，4 errors，23 warnings，25 information**。人工对照正式 DOI、ACL Anthology、PMLR、arXiv 当前版本和商业网页后，4 个 error 均为解析/名字归一化误报，23 个 warning 主要是把 arXiv/SSRN 首发年或 DOI 错当正式出版元数据。
- 当前 RefChecker 只有 `--openalex-db`（本地数据库）参数，没有 OpenAlex API-key 参数，也未读取 `OPENALEX_API_KEY`；因此用户提供的 key 未写入命令、环境或仓库。在线核验使用工具内置的多源链路。

## 2. 总体结论

1. **真实性**：36/36 均找到真实来源；未发现捏造或无法验证的文献。
2. **元数据**：当前 BibTeX 的关键身份字段总体正确。RefChecker 的“Poor”评级不应采纳；它混淆了预印本与正式出版记录，并对 LaTeX 重音姓名解析不完整。
3. **覆盖**：36 个正文 key 与 36 个 BibTeX 条目完全对应。
4. **内容支持**：仍有 **6 类需要修改或降格的实质问题**，其中最明确的是 `wang2025mixture` 被 4 次用于支持 routing/strongest-first，但该文研究多模型分层聚合，不研究 router。

## 3. 36 条元数据逐条裁决

符号：**通过** = 当前关键字段可接受；**通过（工具误报）** = RefChecker 报错/警告，但权威记录支持当前 BibTeX；**通过/注意** = 来源真实且记录可接受，正文使用或版本口径需注意。

| # | key | 人工裁决 | RefChecker 与独立复核 |
|---:|---|---|---|
| 1 | `syntheticusers` | 通过/注意 | 当前 H1、2026 和访问说明一致；官网同时明确是 discovery co-pilot，not a replacement for real research。 |
| 2 | `uxia_synthetic` | 通过/注意 | 标题与 2026 一致；页面正文为 Jan. 21，元数据为 Jul. 25。支持“minutes, not weeks”，结尾又称 human research 的 complement。 |
| 3 | `bansal2021whole` | 通过（工具误报） | DOI/CHI 2021/pp. 1--16 正确；工具报 2020 是 arXiv 首发年。 |
| 4 | `bucinca2021trust` | 通过 | PACMHCI 5(CSCW1), 2021, DOI 正确；补 arXiv URL 仅为可选建议。 |
| 5 | `vasconcelos2023explanations` | 通过（工具误报） | PACMHCI 2023 正确；工具报 2022 是预印本年。 |
| 6 | `zhang2020confidence` | 通过 | FAccT 2020, pp. 295--305, DOI 正确。 |
| 7 | `lai2019human` | 通过（工具误报） | FAT* 2019 正确；工具报 2018 是预印本年。 |
| 8 | `schemmer2023appropriate` | 通过 | IUI 2023, pp. 410--422, DOI 正确。 |
| 9 | `gajos2022people` | 通过 | IUI 2022, pp. 794--806, DOI 正确。 |
| 10 | `santurkar2023whose` | 通过 | ICML/PMLR 202, pp. 29971--30004 与官方页一致。 |
| 11 | `argyle2023out` | 通过（工具误报） | Political Analysis 31(3), 2023 正确；2022 是预印本年。 |
| 12 | `park2022social` | 通过 | UIST 2022, pp. 1--18, DOI 正确。 |
| 13 | `aher2023using` | 通过（工具误报） | ICML/PMLR 2023 正确；`Rosa I. Arriaga` 对 `RosaI. Arriaga` 是数据库空格错误。 |
| 14 | `hu2024quantifying` | 通过（工具误报） | ACL 2024 正式 DOI 正确；工具错误偏好 arXiv DOI。 |
| 15 | `park2024generative` | 通过/注意 | 当前 v3 标题、11 位作者和版本一致；2024 是首次提交年，note 已说明 2026 修订。正文数值口径需改。 |
| 16 | `bo2024rely` | 通过（工具误报） | CHI 2025 正式 DOI/pp. 1--23 正确；2024 是预印本年。key 名不影响引用。 |
| 17 | `hamalainen2023evaluating` | 通过（工具误报） | BibTeX 实际列有 Perttu Hämäläinen、Mikke Tavast、Anton Kunnari；工具因 LaTeX 重音丢掉首位作者。 |
| 18 | `cheng2023compost` | 通过（工具误报） | EMNLP 2023 正式 DOI/pp. 10853--10875 正确；工具错误偏好 arXiv DOI。 |
| 19 | `luguri2021shining` | 通过（工具误报） | Journal of Legal Analysis 13(1), 2021 与正式 DOI 正确；2019/SSRN DOI 是工作论文记录。 |
| 20 | `mildner2023dark` | 通过 | CHI 2023, pp. 1--15, DOI 正确。 |
| 21 | `rastogi2022deciding` | 通过（工具误报） | PACMHCI 6(CSCW1), 2022 正确；2020 是预印本年。正文对论文定位不准确。 |
| 22 | `cao2025specializing` | 通过（工具误报） | ACL Anthology 确认 6 位作者、pp. 3141--3154、DOI；“Nations of the Americas”是 2025 官方卷名。 |
| 23 | `dominguez2024questioning` | 通过（工具误报） | arXiv 当前页确认 3 位作者且 comments 为 NeurIPS 2024；工具的两作者结果是重音解析错误。 |
| 24 | `bisbee2024synthetic` | 通过 | Political Analysis 32(4), pp. 401--416, DOI 正确。 |
| 25 | `tjuatja2024llms` | 通过/轻微姓名差异 | TACL 12 (2024), pp. 1011--1026 正确；`Tongshuang Wu` 与数据库 `Sherry Tongshuang Wu` 为同一作者。camera-ready 可采用出版页全名。 |
| 26 | `sclar2024quantifying` | 通过（工具误报） | ICLR 2024 正确；2023 是 arXiv 首发年。 |
| 27 | `mizrahi2024state` | 通过（工具误报） | TACL 12 (2024), pp. 933--949 与 DOI 正确；工具报 2023 是索引/预印本年。 |
| 28 | `haase2026within` | 通过 | arXiv 当前页确认 7 位作者；RefChecker 控制台漏掉 Jana Gonnermann-Müller，但未形成 error。 |
| 29 | `zheng2023judging` | 通过（工具误报） | NeurIPS 2023 Datasets and Benchmarks Track 可接受；工具只是将 venue 归一为 NeurIPS。 |
| 30 | `mitchell2019model` | 通过（工具误报） | FAT* 2019, pp. 220--229, DOI 正确；2018 是 arXiv 首发年。 |
| 31 | `simmons2011false` | 通过（工具误报） | 正式期刊名是 *Psychological Science*；工具返回的 *Psychology Science* 错误。 |
| 32 | `simonsohn2020specification` | 通过 | Nature Human Behaviour 4, pp. 1208--1214, DOI 正确。 |
| 33 | `ong2025routellm` | 通过（工具误报） | ICLR 2025 正式记录可接受；2024 是 arXiv 首发年。内容支持动态成本--质量 routing，但不是固定 strongest-first 算法。 |
| 34 | `wang2025mixture` | 通过（工具误报） | ICLR 2025 正式记录可接受；2024 是 arXiv 首发年。内容是 layered Mixture-of-Agents aggregation，不是 routing。 |
| 35 | `seshadri2026lost` | 通过（工具误报） | ACL 2026 正式 DOI/pp. 47423--47439 应优先；工具仍匹配 arXiv DOI 并误报 venue。 |
| 36 | `robinson2026influence` | 通过 | arXiv v3 当前页确认 4 位作者、标题与 2026；摘要直接支持 task skill/persuasion/vigilance 可分离。 |

## 4. 正文 claim--source 审计：需要处理的项

### P0：明确不支持或引用对象错误

1. **`wang2025mixture` 不支持 routing / strongest-first。** 该文提出 layered MoA，让每层模型读取上一层所有输出并聚合能力。正文在约第 208、714、750、926 行共 4 次把它与 RouteLLM 并列，用于“quality-optimal router”“strongest-first order”“inverse of capability routing”。应从这 4 处移除；`ong2025routellm` 足以提供 capability/cost-quality routing 对照，同时正文须明确 strongest-first 是本文构造的 capability-first baseline。
2. **`rastogi2022deciding` 不应称为 “offline estimation of team performance”。** 该文研究 AI-assisted decision-making 中的认知偏差、互补性与干预，并包含用户实验，不是离线团队表现估计。应改写段落标题/首句。
3. **`hamalainen2023evaluating` 不直接支持 caricature。** 它支持 synthetic HCI data 的可生成性、表面可信与方法风险；“caricature rather than simulate subpopulations”的直接来源是 `cheng2023compost`。在两个具体 caricature/collapse 引用组中移除或把主张拆开。

### P1：数值或措辞需要限定

4. **`park2024generative` 的 `≈85% accuracy` 口径不准确。** 当前 v3 报告 interview-only / survey-only / combined agents 达到参与者本人两周 test-retest consistency 的 **83% / 82% / 86%**。这不是普通 raw accuracy。建议正文写成“达到参与者自身 test-retest consistency 的 82%--86%”。
5. **商业平台不能统一表述为替代真人研究。** 两页都支持分钟级速度；Uxia 局部文案说 replace slow human testing，但总结又称 complements。Synthetic Users 当前页更明确写 `not a replacement for real research`。正文现有 “compress (or stand in for)” 已比旧稿谨慎，但后文“standard engineering defaults”仍应标为本文对行业实践的合理假设，而非两平台已证实的默认配置。
6. **RouteLLM 不等于固定 strongest-first。** `ong2025routellm` 支持按请求在强/弱模型间做成本--质量动态路由；无成本约束时偏向强模型是合理推论，但“router 的顺序/第一选择”不是论文原算法定义。正文应持续使用 `capability-first baseline constructed here` 一类限定。

### P2：可保留但应视为综合推论

- `bucinca2021trust`、`vasconcelos2023explanations`、`luguri2021shining` 合起来为“coercive framing 下采用错误 AI”提供跨文献动机，但没有任何单篇直接实验当前组合的 expert-authority + accountability + confidently-wrong-AI 条件。
- `santurkar2023whose`、`cheng2023compost` 能说明群体代表错配与 caricature，但“measurement reliability/invariance logically prior to external validity”是本文的方法论论证，不是两篇来源的原结论。
- `santurkar2023whose`、`tjuatja2024llms` 是 measurement-invariance 的类比证据，不是该心理测量概念的定义性来源。camera-ready 最好补一条 psychometrics 定义文献。
- `mitchell2019model` 支持结构化报告模型用途、限制和性能，但不直接提出本文的 cross-backend sensitivity/abstention 规则。

## 5. RefChecker 结果如何解读

- **不应修改的年份警告**：`bansal2021whole`、`vasconcelos2023explanations`、`lai2019human`、`argyle2023out`、`aher2023using`、`bo2024rely`、`luguri2021shining`、`rastogi2022deciding`、`dominguez2024questioning`、`tjuatja2024llms`、`sclar2024quantifying`、`mizrahi2024state`、`mitchell2019model`、`ong2025routellm`、`wang2025mixture`。它们大多是预印本年与正式出版年之差。
- **不应替换的 DOI**：ACL/EMNLP/CHI/期刊正式 DOI 应优先于 arXiv 或 SSRN DOI；包括 `hu2024quantifying`、`cheng2023compost`、`luguri2021shining`、`seshadri2026lost`。
- **不应采纳的作者 error**：`aher2023using` 是空格归一化；`hamalainen2023evaluating`、`dominguez2024questioning` 是 LaTeX 重音解析丢作者；`tjuatja2024llms` 是作者全名变体。
- **仅为信息提示**：补 arXiv URL 不是修正正式出版记录的必要条件。

## 6. 最终结论

当前文献库的真实性和关键元数据已经较干净：**36/36 真实，36/36 被正文引用，0 缺失，0 闲置，0 未验证，0 疑似捏造**。本轮没有发现必须据 RefChecker 修改的 BibTeX 身份字段。提交前真正应优先处理的是正文的 3 个明确支持错误（MoA/routing、Rastogi/offline estimation、Hämäläinen/caricature）和 3 个限定问题（Park 的 82%--86% test-retest 口径、商业平台替代措辞、RouteLLM 与 fixed strongest-first 的区别）。
