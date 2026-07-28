# 《Two Ways a Design Fails》论文详解（中文）

> 面向合作者/导师/自己备查的完整说明。对应交付物 `docs/paper/main.tex`（CHI 2026 提交格式，
> 单栏匿名审稿版）。数字与 claim 强度以论文当前版本为准，均经独立审计。
> 一句话定位：**这是一篇"测量-审计"论文——审计"用 LLM 合成用户 panel 预筛界面风险"这个方法本身
> 可不可靠，而不是又一篇"AI 会误导人"的实证。**

---

## 1. 标题与核心主张
- **标题**：*Two Ways a Design Fails: When Does a Synthetic LLM Panel See the Danger?*
- **副标题**：*A Backend-Sensitivity Audit of Synthetic-User Interface-Content Risk Measurement*
- **核心主张**：一个合成 panel 对同一个界面给出的"风险读数"，会随研究者**自由选择**的东西
  （backend 模型、persona 提示词、生成采样）而剧烈漂移——漂移大到足以**翻转**这个界面的
  "安全/危险"判定。因此单一 backend 给出的"设计风险 = 0.6"这类数字，可能更多是**测量工具的属性**，
  而不是设计本身的属性。

---

## 2. 背景与问题（Introduction）

### 2.1 出发点：均值精度 ≠ 安全
一个 AI 建议界面（例如展示 AI 判定 + 置信度 + 高亮"解释"的评论审核工具），在试点里"平均看着不错"
（准确率上升、用户满意）。但**均值掩盖了"谁"在何时被界面推向危险**：
- 谨慎的专家几乎不动；
- 一个**信任 AI 的新手**几乎每次都照单全收——如果界面把一个"自信但错误"的 AI 建议以胁迫方式呈现，
  这个人可能被推向错误决定，而**总体均值几乎不动**。

这就是**"均值精度"与"安全"之间的鸿沟**。论文由此提出"一个设计会以两种方式失败"：

- **Axis 1 —— 过度离散（over-dispersion）**：界面诱导出**用户之间高度异质**的依赖。对中位用户安全、
  对尾部用户危险。方差在这里不是要被平均掉的噪声，而是**要关心的安全量**。
- **Axis 2 —— 胁迫下的错误采纳**：在胁迫性 framing 下，用户**系统性地采纳一个错误的 AI**。这在零离散
  时也危险——所有人一起失败。

> ⚠️ 重要框架（论文明确写出）：**Axis 2 是承重轴（load-bearing），Axis 1 是次要的、探索性的信号**——
> 因为 Axis 1 的人类对应性在所有可测配置里都是 NULL，论文把它当作"候选信号，尚未人类验证"。

### 2.2 捷径与它的两个未被检验的假设
检测这两种失败通常要做昂贵、慢、需 IRB 的**真人研究**。团队迭代界面的速度远快于此，于是一个新兴做法是：
先用一个**合成 panel**（persona 条件化的 LLM 智能体扮演一群用户）来预筛界面。商业市场（syntheticusers、
uxia 等）已经在卖"几分钟评估设计"的 AI 参与者。

论文指出，遵循标准工程默认的做法会**plausibly 采用两个几乎从未针对"界面风险"检验过的假设**：
1. **最强的可用 backend = 最好的模拟器**（这也正是 quality-optimal router 会选的）；
2. **单一 backend 的点估计**（"这个设计的错误采纳率是 0.6"）是**设计的属性**而非产生它的模型的属性。

论文对两者做实证检验，**两者都被证伪**。

### 2.3 一个"更靠前"的问题：测量可靠性/不变性
关于合成用户的争论几乎全在问"它们像不像真人（match humans）"。论文主张一个**逻辑上更靠前、却很少被检验**
的问题：当 panel 说某界面有风险时，这个读数是被界面产生的，还是被那一堆自由选择（哪个 backend、
persona 怎么措辞、抽到哪次生成）产生的？在问"panel 能否预测真人"之前，应先问"**换个研究者、或同一研究者
换一天重建它，它是否还在测同一个东西**"。这是**测量可靠性与不变性**问题——外部效度的前提。

### 2.4 四个研究问题（RQ）
- **RQ1（backend 不变性）**：panel 的界面风险估计（错误采纳的绝对水平、胁迫 framing 效应、persona 异质性）
  在各 backend 间是否一致？换 backend 能否把界面从"高风险"翻到"低风险"？
- **RQ2（方差分解）**：合成风险估计有多少来自 backend、多少来自研究者选的 item 与 persona、多少来自生成随机性？
- **RQ3（构念 vs 顺从）**：哪些 panel 信号反映对目标操纵的稳定敏感性，哪些主要反映显式 persona 指令？
- **RQ4（backend 感知的报告）**：保守的多模型聚合 + 分歧触发的弃权，能否降低 backend 引入的测量不稳定？

---

## 3. 四个贡献（Contributions）
1. **一个系统的 backend 敏感性审计**，围绕一个命名指标 **风险分类翻转率（risk-classification flip rate）**：
   在多少比例的 backend 配对上，同一界面被判到决策阈值的不同侧。先前的 prompt/模型敏感性工作说明"输出在
   **量级**上漂移"；本文把它升级为"漂移**越过决策阈值、翻转 pass/fail 判定**"——这才是它对部署门槛有意义之处。
2. **capability–vulnerability 错配 + 漏洞覆盖（vulnerability-coverage）选择原则**：最强的 backend 恰恰最不能
   重现最高严重度的失败，所以为"漏洞覆盖"组 panel 是 **capability routing 的反面**——一条反直觉、可执行的
   "谁该来驱动合成用户研究"的原则。
3. **一套可复用的审计与报告协议**：backend/persona/item/generation 的方差分解、行为分类学、跨 backend 决策翻转
   分析、分歧触发弃权——**把结果报成"跨模型/提示/生成的分布"，而不是一个点估计**。
4. **两轴 over-dispersion/coercion 构念**（Axis 2 承重、Axis 1 探索），conflict-conditioned、在一个预注册的
   审计门控流水线上。流水线的过程完整性（三个自捕的静默损坏 bug）作为**方法透明性报告，而非单列为贡献**。

> 论文明确**不主张** panel 能预测个体真人、识别真实脆弱人群、或构成已验证的部署筛查器；panel↔human 对应性
> 在所有（欠功效的）可测配置里都是 NULL。人类预测效度留给后续独立研究（E6）。

---

## 4. 相关工作（Related Work）
- **模拟用户及其可靠性批评**：LLM 作为调查/用户研究/形成性评估的替身被提出（silicon sampling）；平行文献记录
  其作为代理的失败（压缩意见多样性、错误校准分布、非人类反应偏差、caricature 而非模拟子群）。**最接近、且并行**
  的工作是 Seshadri et al.《Lost in Simulation》（ICLR 2026）：在 agentic 评估里，LLM 模拟用户是不可靠代理
  （agent 成功率随 user-LLM 变动达 9 个百分点、系统性错校准、人口学差异）。**本文与之的区别**：
  (i) 他们量的是任务表现的**量级**漂移，本文量的是**越过决策阈值、翻转风险判定**；
  (ii) 他们的结局是 agent 任务成功，本文是**界面内容安全**分诊；
  (iii) 他们以人类对应性为 ground truth，本文**明确 disclaim 它**、转而审计内部测量稳定性。
  并行地，Robinson et al.《Under the Influence》佐证"任务能力、说服力、警惕性可分离"（强解题者未必能识破被误导），
  在 LLM-agent 层呼应本文的 capability–vulnerability 反转。
- **依赖与过度依赖**：大量工作研究人在给定置信/解释时如何恰当依赖 AI，常发现解释反而**抬高**过度依赖；近期工作
  在真人上基准化依赖干预（含 LSAT）。本文反转其一：把依赖**异质性**当作 Axis-1 安全 DV；并补充其二：不问"干预是否
  帮到人"，而问"**合成 panel 能否检测到它有帮助**、且该判定如何依赖 backend"。
- **暗黑模式/胁迫界面**：已被充分编目；本文 Axis-2 给出一个胁迫模式（自信错误 AI）的计算信号。
- **人机团队的离线评估**：最接近的是团队表现的离线估计；本文填补的是"**界面依赖安全的预研究筛查**"以及"这种筛查
  的信号何时可信"的刻画。
- **测量不变性/可靠性/效度**：借心理测量学之镜——**backend 是测量仪器的一部分**，故跨 backend 比风险是不变性问题，
  跨生成稳定性是可靠性问题。稳定不蕴含有效，但严重的 backend 不变性会瓦解任何建立在单一 backend 上的效度主张。
- **LLM 评估中的研究者自由度**：模型/提示/解码/解析/persona 措辞/样本量都是可移动结果的分析选择（"分叉花园"）。
  本文把这些自由度**当作研究对象**，采用规格曲线式多元宇宙报告，而不是单一规格。

---

## 5. 构念定义（The Two-Axis Construct）
- **Axis 1（用户间依赖过度离散）**：对每个 item，各 persona 产生依赖决定；估计超出单一同质用户会产生的二项方差
  的**超额方差**（beta-binomial 过度离散参数 ρ）。**conflict-conditioned**：只在 persona 的独立 System-1 判断
  与展示的 AI 不一致的 trial 上计算，隔离真正的依赖。为避免估计器在极端率下的边界行为，报告一个有界的替代量
  **mean panel disagreement**（六个 persona 的 conflict-conditioned 依赖率之间的方差），它与 ρ 单调同向。
- **Axis 2（胁迫下的错误采纳）**：在胁迫"dark" framing 下，界面以高置信 + 权威/问责话术展示一个**保证错误**的
  AI 判定（ground truth 的取反）。Axis-2 是各 persona 采纳它的比率。为把 **framing** 与普通"跟随错误建议"分开，
  用 matched item 上的中性/placebo/dark 对照。
- **从两轴到决策，并审计它**：筛查最终要把两轴变成动作（"若任一轴超阈 τ 则送人研究"）。论文**故意不提出/验证**
  这样一条规则，而是取其最简版本（对 Axis-2 采纳设阈）作为**审计对象**，问"它产生的决策是否跨 backend 稳定"。
  阈值一律不冻结——其校准与验证依赖真人研究。

---

## 6. 方法：合成 panel（Method）
- **Panel = personas × backends**：每个智能体是一个 persona（领域技能、AI 素养、风险敏感、谨慎的向量）叉乘一个
  基座 LLM（"backend"）。persona 覆盖 新手/专家 × 信任/怀疑 + 两个中庸，共 **6 个**。关键：persona 提示词跨 backend
  **完全一致**、解码温度**按 persona 固定（非按 backend）**——所以变 backend 时温度与措辞恒定，**backend 效应不与
  逐模型的提示/温度混淆**。
- **建议前/后决策（双系统）**：每个智能体先在**无 AI** 下给判断（冻结的 System-1 锚点），再在**有 AI 建议 + framing**
  下给决定（System-2）。依赖是相对 System-1 锚点定义的——这使 conflict-conditioning 成为可能，避免"人人同意所以人人
  顺从"的坍缩。
- **界面的文本化编码**：智能体收到每个界面条件的**文本序列化**（不是截图、不是视觉模型）。AI 预测、置信、（解释条件下）
  高亮 token 都渲染为文本，遵循 Bansal 的条件定义。**研究的是 prompt 层的界面 framing**；像素级布局/显著性/排版不建模，
  多模态渲染是 future work。（论文范围明确限定在**界面内容/framing 层**。）
- **刺激与数据集**：item 取自 Bansal 情感基准，从任何阈值拟合中留出，选在人类依赖异质性的位点（**item 选择用了人类
  依赖方差，但人类结果绝不泄露进智能体提示或作预测器——item 选择 ≠ 标签泄露**）。跑**两个评论情感数据集**：**beer** 与
  **Amazon 书评（amzbook）**。两者都是英文二分类情感，故视作"一个任务族内跨两数据集的复制"，非广义跨域；另有一个
  预注册的 **LSAT** 臂测不同任务结构。
- **Backends**：一个同厂系列（gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.5，同配置）+ 独立厂商（claude-sonnet-4.5,
  gemini-2.5-pro），共 **6 个**。同厂系列按发布排序仅用于呈现，不主张是已验证的能力刻度；"frontier"指写作时最新最强
  的通用模型（gpt-5.5）。后续扩展到 **11 个**（加 gpt-3.5-turbo, gpt-4, gpt-5.4, claude-opus-4.6, gemini-3.1-pro；
  claude-haiku-4.5 因 0 可解析决策被排除，作为仪器失败如实披露）。
- **严谨脊柱与过程完整性**：每个臂开跑前冻结（UTC 时间戳、提交记录）backend 集/persona 集/选题种子/条件/主 DV/每个
  效应的预测方向；偏差与事后分析标注为 exploratory。对应性分析盲编码，每次合并都经**独立审计 + 从原始数据重新推导**。
  这条脊柱捕到三个会各自产生"貌似合理却错误"的静默损坏 bug：Axis-2 **符号反转**（对 ground_truth 而非展示的 1−truth
  计分）、beta-binomial **边界伪影**、以及解析器在解析失败时**伪造** (decision=0, conf=0.5) 哨兵。它还捕到本文自己
  草稿里的一个统计错误——一个因 item 簇太少而产生伪交互的 GEE 检验。

---

## 7. 实验与结果（Experiments & Results）

> 报告纪律：逐 backend（不跨不可比的 backend 汇总）、给效应量、置信区间、Benjamini–Hochberg（BH）校正。

### 7.1 真人过度离散确实存在（锚点）
在 Bansal 人类数据上用同款 beta-binomial 估计器：conflict-conditioned 过度离散为正且排除 0（ρ≈0.067）。
用 **split-half reliability**（在这种"每格单观测"结构上唯一 well-identified 的主方法）：无-AI 依赖表现为**稳定特质**
（stable-user share≈0.74），有 AI 时降到**任务主导**的 0.32–0.41。（一个可选的方差分量 GLMM 未收敛、不使用；一个
AI 条件 expert-adaptive 的 split-half reliability 为负、被排除在该区间外——如实披露。）**该锚点不用于验证合成 panel**
（那条链在所有配置里都是 NULL），且不推广到第二个人类数据集（Lu & Yin）。

### 7.2 错误采纳强烈依赖 backend
同一个"保证错误"界面，跨 6 个 backend 的聚合错误采纳（beer / amzbook）：
gpt-4o-mini 0.50/0.48，gpt-4.1 0.60/**0.66**，gpt-4o 0.43/0.48，gpt-5.5 **0.30/0.15**。
采纳峰在 gpt-4.1 是真的（vs gpt-4o Fisher p=0.014/0.006），但**模型特异**：最小模型在 chance；BH 后 gpt-4.1 的高采纳
在 amzbook 存活（p=0.003）、在 beer 仅名义显著。三个 frontier 模型均未显著高于 0.5。Axis-1 平行（gpt-5.5 在两数据集
最同质）。**读法**：gpt-5.5 的跨数据集低采纳 + axis-1 坍缩是最一致的模式；采纳量级其余为模型特异。

### 7.3 是胁迫，还是普通跟随错误建议？（matched framing 对照）
在中性条件下 AI 建议**自然错误**的 item 子集（每格 8 个）上，同一错误标签在 中性/placebo/dark 三种 framing 下呈现，
差异只归因于 framing。**胁迫效应存在**：dark 相对 matched 中性把错误采纳的 odds ratio 抬到 **beer 1.90（95%CI 1.42–2.53）**、
amzbook 一个**小得多的 1.17（95%CI 1.04–1.31, p=0.010）**；非胁迫 placebo 保持在基线或以下。
- **少簇稳健复分析**（因只有 8 个 item 簇）：beer 效应稳健——item 随机截距 2.02、item 固定效应 1.92、item cluster bootstrap 1.93，**全部排除 1**；
  **amzbook 方法依赖**——随机截距 OR 1.22、CI 0.93–1.61**跨 1**，故 amzbook 读作 **directional only（仅方向性）**。
- **形式检验不支持 backend 依赖的 framing 效应**：dark×model 交互在两数据集均不显著。故只主张：(i) 一个真实的**捆绑**胁迫
  效应存在（置信/权威/问责共变，未拆分），量级跨 backend 不可区分；(ii) 强烈 backend 依赖的是**绝对采纳水平**，不是 framing 斜率。

### 7.4 跨 backend 决策不稳定：同一界面被翻转（核心结果）
把同一 dark 界面当一个设计，问 6 个 backend 是否一致——**不一致**。聚合错误采纳在 6 个 backend 间 beer 0.30–0.60、
amzbook 0.15–0.66。变成筛查决策（"采纳≥τ 就 flag"）后，flag 不只在单一阈值不稳，而是在整个合理操作区间不稳：τ 扫过
0.35–0.65（beer）/0.30–0.65（amzbook），总有些 backend flag、有些不 flag，**没有一个阈值能让 6 个 backend 一致**。
τ=0.5 时 beer 被 3/6 flag、amzbook 被 1/6。**pairwise backend flip rate** 在 beer 峰值 **0.60**（= 6 backend 3–3 划分的
机械上限）、amzbook 0.33。一个行为审计排除了一个良性解释——低采纳 backend 并非**拒答**（显式挑战/拒绝语很罕见，
OpenAI 系 0%、claude/gemini 2–4%），低采纳靠的是基于证据的重新核实。

### 7.5 方差从哪来（RQ2）
逐 trial 的交叉随机效应模型（adopt ∼ 1 + (1|backend) + (1|persona) + (1|item)）把方差**更多**分给研究者选的 item 与 persona，
而非 backend（近似方差份额：item≈0.28、persona≈0.23、backend≈0.07、残差≈0.42）。这不是与 7.4 矛盾，而是其锐化：**单 trial 层
backend 是温和噪声，但在实践者读到的聚合估计层，backend 仍把数字移动到足以翻转决策**。含义对每个来源相同——item 选择、
persona 措辞、backend 都是分析者选择——故合成 panel 结果应报成**分布**。**生成随机性最小**：预注册多代运行（3 backend × 两条件
× 6 persona × 20 item × 5 seed = 3600 trial）中，生成对 dark 采纳方差贡献≈0（固定效应 η²=0.001，vs item 0.22 / persona 0.15 /
backend 0.07）；每 backend 的聚合估计在 5 seed 间至多移动 SD=0.03——相对翻转决策的 backend 间 0.31 差距微不足道。

### 7.6 一个 backend 稳定的操纵检查：panel 忠实传播被提示的信任倾向（RQ3）
聚合采纳**率**模型特异，但"哪个 persona 采纳最多"的**排序**稳定：一个**显式的信任-新手 persona（p5）在全部 12 个
backend×dataset 格里都是最高采纳者**。用考虑伪重复结构的交叉随机效应 logistic：OR≈**26**（因 p5 采纳近天花板，OR
**量级不应当作精确效应量**；主证据是 model-free 的"12/12 格严格居首"）。论文谨慎地把它当作**操纵检查而非头条发现**：
p5 是被**提示定义**为信任+新手的，"它最采纳 AI"很大程度是**指令的后果**；其价值是一个**可靠性属性**——panel 忠实稳定地把
被提示的倾向转成行为。且跨厂商排序一致性主要由这一个 persona 撑着（去掉 p5，beer 的平均 Spearman 从 0.87 掉到 0.77、
amzbook 从 0.50 塌到 0.09）。一个**背景-only descriptor ablation**（去掉显式 deference 指令）结果是**混合且 backend 依赖**的，
如实报告。两个替代诱导（第一人称 backstory、few-shot 示范）不移除 deference **内容**，被当作该倾向的不同编码、而非 deference-free
控制；反循环论证只靠中性背景-only 臂。

### 7.7 capability–vulnerability 错配：强 backend 低估了脆弱用户（贡献 2）
用每个 backend 的无辅助任务能力（System-1 准确率）作为能力代理：**最强的 backend（gpt-5.5, 0.93）恰恰最不能重现最高严重度
失败**——在信任-新手 persona（p5）上，5 个 backend 的 dark 采纳≈1.0，gpt-5.5 只有 **0.50**。隔离 AI 影响（AI-induced flip =
P(adopt | System-1 correct)）后同序：frontier 最少把正确答案翻成错误 AI（0.16），中档最多（0.46）。
- **n=11 扩展（汇合两数据集）**：能力与三个脆弱度度量负相关（Spearman：聚合采纳 −0.82、AI-induced flip −0.67、p5 采纳 −0.65；
  BH p≤0.03）。**分级**：聚合采纳负相关**稳健**（每数据集单独显著、每个 leave-one-out jackknife 显著）；flip 与 p5 负相关
  **仅 suggestive**（由 amzbook 撑、单 backend 脆弱）。**定性读法与相关性无关**：frontier backend 几乎对脆弱 persona 视而不见。
- **覆盖（load-bearing、假设最轻）**：把"persona 的 dark 采纳达阈 0.5"记为被覆盖，则**单个 frontier backend**（router 会选的）
  beer 只覆盖 1/6、amzbook 0/6；一对弱 backend（gpt-4.1, gpt-4o-mini）覆盖 4 和 5（匹配全 6-backend panel）。覆盖对 panel size
  单调，所以要点不是"模型越多越好"，而是"**默认最优选择恰是此用途下最差的**"。为漏洞覆盖选 panel 是 capability routing 的
  **反面**。形式化为**次模集合覆盖**，greedy 带 (1−1/e) 保证：clean flip 度量下 greedy 两个 backend 覆盖全部高危格，capability-first
  的首选（frontier）只覆盖一个格、到 k=6 才全覆盖。RAIR/RSR（恰当依赖词汇）也显示 frontier 是"最恰当依赖的用户"——这正使它
  成为"危险即过度依赖"的界面**最没用的探针**。

### 7.8 错配是否跨任务结构存活？（LSAT，部分泛化）
beer/amzbook 都是英文二分类情感，模式可能是任务**结构**的伪影。作为预注册稳健性臂，在 20 道 LSAT 逻辑推理题（4 选 1、更难、
不同建议格式）上重放同样 6 backend/6 persona/dark 协议（720 dark trial 全满足 â≠g；System-2 解析率=1.00）。**冻结的复制规则**
三取二存活：
- persona 脆弱度**排序几乎完全保留**（信任-新手仍居首，dark 采纳 LSAT 0.54 / binary 0.90；秩相关 ρ=0.90, p=.015）；
- capability×vulnerability **符号保留**（frontier 仍最低采纳/最低 flip、压平 p5 峰；ρ(cap,flip)=−0.83 在每个子样本落在 [−1,−0.7]，
  但名义 p=.04 脆弱，故读作稳健**符号**而非显著系数）；
- 覆盖反转**存活**（单最强 backend 覆盖 0/6，全 panel 1/6）。
- **不复制**的是本文自己的非不变性**量级**：聚合 dark 采纳只跨 0.04–0.27（range 0.225，略低于冻结的 0.25），因更难的 4 选 1 压缩了
  跨 backend 差距。故报作**部分泛化**——错配与 persona 排序跨任务结构，但聚合差距的大小是任务依赖的。

### 7.9 审计一个保护性设计：方向可迁、量级不可（保护性干预臂）
最常见的用法不是认证一个绝对风险数，而是**比较**设计（"加个 safeguard 有没有用？"）。在保证错误 AI 上加两种保护 framing：
**cognitive forcing**（先自证再依赖）与 **verification/uncertainty 显示**（AI 可能自信地错，核对文本）。
- **效应真实、且最帮到最该帮的人**：跨 backend 汇合，保护 framing 相对中性 plain 基线显著降低错误 AI 采纳（plain 0.37 → forcing 0.30 /
  verify 0.29；条件主效应 LRT χ²=11.9, df=2, p=0.003）；信任-新手 persona 从 0.78（plain）降到 0.53/0.46（p5 主效应 χ²=34.2, p<1e-6）。
- **方向 backend 稳健、量级不然**：6 个 backend 每个都呈非增阶梯（保护收益≥0），但量级从≈0.12（gpt-4o-mini）到≈0.01（gemini，
  几乎无效）。backend×condition 交互不显著（欠功效），读作"**无可检测的 backend 依赖**"，非等价证据。
- **一个被证伪的预测，如实报告**：预注册预期保护收益 backend 依赖、抗拒的 frontier 有地板（近零收益）。**并非如此**——frontier
  gpt-5.5 是中游收益（0.09），近零的反而是**最弱**的 gemini；收益与能力、基线过度依赖都不相关。诚实读法：**一个界面内改进的
  方向**能挺过翻转绝对水平的 backend 切换，但其**大小**（乃至在某个 backend 上的存在与否）不能。
- **实践指引**：合成 panel 对**相对问题**（"这个 safeguard 减少过度依赖吗"）比对**绝对问题**（"这界面危险吗"）更可靠——但因为
  保护条件是**直接指令**智能体去深思/核验，panel 检测到的是"一个**被直接指令的操纵的方向**"，而非已验证的比较筛查能力；且即便相对
  读数也非 backend-free（只在 gemini 上跑会得出"safeguard 无效"）。

### 7.10 panel↔human 对应性未验证（诚实 NULL）
在所有可测配置里，panel 的逐条件 Axis-1 信号都**不显著**跟踪人类锚点（n=5 条件的 Spearman，BH 下对 6 个模型全 null）。amzbook 上
对应性**退化**（人类锚点逐条件过度离散近常数，检验无信息量而非真 null）。故**不作任何预测效度主张**；只有一个有功效的真人研究
（E6）能补上。

---

## 8. 讨论（Discussion）
- **backend 是测量仪器的一部分**：本研究的自然读法不是"用不同模型跑同实验得了不同数"，而是"**换 backend 就换了仪器**"——合成
  panel 的界面风险读数由被测设计与分析者恰好选的 backend/prompt/generation 共同产生。当这些选择翻转风险分类时，单-backend 的"设计
  风险"数还不是设计的属性。这把"我该用哪个 LLM 驱动合成研究"从实现细节升为一级方法论选择。
- **更强不等于更有效**：把最强模型当最好模拟器很诱人，但 frontier 最少跟随胁迫错误 AI——这可能让它是更好的**解题者**，却没说明
  它是否跟踪目标用户；更高能力甚至压缩了筛查所依赖的 persona 区分度。缺人类判据时，能力与正确性都不是选合成参与者的理由；本文
  刻意不主张 frontier"错过真实危险"或弱模型"更像人"——那都需要尚未做的真人研究。
- **分歧是信息，不只是噪声**：因读数对仪器敏感，跨 backend 分歧不是要被平均掉的测量误差，而是可用信号——它标出"单-backend 判定
  不该被信任"的界面，把报告协议从"谨慎的劝告"变成**可执行的弃权规则**。
- **三种失败要区分**：(i) 界面级合成信号（智能体表现出采纳/分歧）、(ii) 测量失败（信号随 backend/prompt 翻转）、(iii) 面向人的设计
  失败（真实用户受害）。本文确立 (i)、刻画 (ii)；(iii) 留给真人研究。
- **对商业合成用户工具的含义**（针对市场"遵循标准工程默认会 plausibly 采用"的两个假设）：
  **① 重新想"frontier-first"** ——最强模型这个直觉几乎是风险审计的最差选择；应为漏洞覆盖组 panel（可能要故意纳入更弱/更多样的 backend）。
  load-bearing 主张是假设最轻的覆盖结果（单 frontier 几乎覆盖不到风险），而非能力相关性"定律"。
  **② 退掉单一点估计** ——一个 backend 的数不是 backend 不变的（移动到足以翻转筛查决策）；像天气预报一样报成**跨 backend/prompt/generation
  的分布**，配**分歧触发弃权**（这里 range 超 0.2 时——示例性、未校准——工具应拒绝认证、改路由到真人测试）。
  **③ 相对优于绝对** ——这类工具对它们通常被问的比较问题更可靠（每个 backend 都重现了保护设计收益的**方向**，虽非量级），故即便比较
  判定也应跨 backend 报告。三者都不替代真人研究；它让一个诚实的合成筛查成为**知道何时该交给真人**的分诊步骤。

---

## 9. 局限（Limitations）
- **合成 persona 不是人**（核心威胁）：不主张个体真人、真实人群分布、或哪个 backend 最像人；persona 排序是提示属性、非心理特质。
- **测量非 backend 不变**：这是发现而非仅告诫；不主张可部署的 backend 无关检测器。
- **对应性未验证且欠功效**（n=5 条件、amzbook 退化）：不作预测效度主张。
- **两数据集都是二分类情感**：非广义跨域；LSAT 臂部分弥补（错配与 persona 排序迁移、聚合差距大小不迁移）。
- **胁迫是捆绑操纵**：dark 同时变置信/权威/问责，不做因子拆分。
- **生成与提示格式敏感性**：主结果每 prompt 一次生成；生成随机性直接估计并发现对聚合估计可忽略；提示改写/呈现顺序敏感性是 future work。
- **规格审计部分**：分解 backend/persona/item 方差并扫阈值，但完整规格曲线/多元宇宙分析是 future work。
- **item 选择用了人类依赖方差**（已披露）：留出不等于移除对人类判据的选择；fresh-item 人类检查待真人研究。
- **capability–vulnerability 错配基于合成证据 + 粗能力代理 + 部分机械成分**（能正确回答就无法再采纳错误 AI）；只有聚合采纳负相关
  jackknife 稳健，flip/p5 更细的相关由 amzbook 撑、单点脆弱；故以假设最轻的覆盖结果领先、相关性作支撑。
- **prompt 层非像素层**：研究 prompt framing 而非视觉界面效应；多模态渲染是 future work。

---

## 10. 计划中的真人验证（E6）——**这才是提升中稿率的决定性一步**

> **目的（关键框架）**：E6 **不是**证明"AI 会误导人"（那是已知的前人工作，会被"we already know"拒）。E6 是要**验证合成 panel
> 本身**——补上 panel↔human 的 NULL。H1（胁迫对真人有效）只是**操纵有效性的前提检查**；真正 payload 是 H2（**谁**易感）与
> H3（**哪个 backend** 最像人，即 capability–vulnerability 反转的真人检验）。

- **假设（预注册、无论结果都报）**：
  - **H1（主，操纵有效性）**：dark 界面上真人对错误 AI 的 conflict-conditioned 采纳高于 faithful/placebo。若失败 = 构念外部无效（可发表边界）。
  - **H2（次，"谁"）**：高"trusting-novice 指数"（高 AI-deference × 低领域技能）的被试在 dark 上采纳更高——persona 定位的真人检验。
  - **H3（探索-确证，"哪个 backend"）**：按各 backend panel 对真人模式的匹配度排序，预测**中档 gpt-4.1 比抗拒的 frontier gpt-5.5 更贴合真人**
    ——即最强的 panel 模型是最不像人的筛查器。
- **设计**：被试内、三界面（Faithful / Placebo / Dark）、平衡顺序；一域（beer）；~15 道留出的 conflict-eligible item/界面（泄露防火墙）。
  **dark 保持 cue-only 且与合成臂匹配**（不加逐题理由——一个探针显示加理由反而**降低**合成采纳，因 LLM 会核对并拆穿可检验的错误理由；
  故理由会既无益又破坏 H3 匹配）。用**更难/更含糊的题**解决"太明显没人改"，不动操纵。
- **样本与功效（Monte Carlo）**：**H1** 在 N≥40 功效≈1.00（怎么都稳）。**H2 是约束项**：中等调节（gap 0.25）功效 0.71（N40）→ **0.90（N60 平衡）
  / 0.82（N60 学术偏斜）**；小调节（gap 0.15）在任何可行 N 都测不出。→ **目标 N≈60、一次采齐、purposive 招募**（有意招"信任 AI 的新手"，
  否则高 index 组凑不够）。
- **诚信承诺**：预注册 + "所有结局都可发表"（消灭作弊动机）；不 optional stopping、不事后剔除、不 p-hacking、除公开自变量外不诱导被试；
  从原始数据重新推导。
- **每种结局的意义**（都诚实、都可发表）：H1+H2 成立 = panel 的信号与"谁易感"被真人验证（强结果）；H1 成立 H2 null = 收缩到聚合 Axis-2；
  H3 显示 gpt-4.1>gpt-5.5 = silicon-sampling 的头条警示；H3 反转 = 反转不迁移至真人（重要边界）；任何 null = 对合成 panel 预测效度的可发表界。
- **工程现状**：已构建一个 pilot-ready 的本地网页任务原型（多语言 en/zh/ja/de、真实留出难题、Latin-square 轮转、cue-only dark、
  记录逐 trial S1/最终/置信/RT + trusting-novice 问卷 + debrief）。招募走导师人脉（一次性样本）→ 先用熟人 pilot 除险再花正式样本。

---

## 11. 关键数字速查表

| 主题 | 结果 | 分级 |
|---|---|---|
| 错误采纳跨 backend 范围 | 0.15–0.66（beer 0.30–0.60 / amzbook 0.15–0.66） | 稳健 |
| 风险分类翻转率 | beer **0.60**（=3–3 机械上限）/ amzbook 0.33 | 稳健（描述性） |
| 胁迫 OR（beer） | **1.90**（复分析 2.02/1.92/1.93 均排除 1） | 稳健 |
| 胁迫 OR（amzbook） | 1.17（混合模型 CI 跨 1）→ **directional only** | 脆弱 |
| persona p5 居首 | 全 12 格严格居首（OR≈26 但近天花板，量级不精确） | 稳健（model-free） |
| 方差份额 | item≈0.28 / persona≈0.23 / backend≈0.07 / 生成 η²=0.001 | 稳健 |
| capability×vulnerability（n=11 汇合） | 聚合采纳 −0.82（BH、jackknife 稳健）；flip −0.67、p5 −0.65 | 聚合稳健 / flip·p5 suggestive |
| 覆盖 | 单 frontier 覆盖 1/6(beer)·0/6(amzbook)；弱对 4–5/6；greedy k=1–2 | 稳健（假设轻） |
| LSAT 泛化 | persona 排序 ρ=0.90 迁移、cap-vuln 符号迁移、覆盖反转迁移；聚合差距不迁移 | 部分泛化 |
| 保护性干预 | 方向 backend 稳健（全≥0）、量级不然（gemini≈0）；预注册 H2/H3 被证伪 | 方向稳健 |
| panel↔human 对应性 | 全配置 NULL（amzbook 退化） | NULL（E6 才能补） |

---

## 12. 一句话总结
**这不是"AI 会误导人"的又一次演示，而是对"用 LLM 合成用户预筛界面风险"这一方法的诚实审计：它的风险读数随 backend 剧烈漂移、
足以翻转判定；最强的模型恰恰最看不见最脆弱的用户；把结果报成分布并在分歧时弃权才诚实；而 panel 到底能不能预测真人，留给
预注册的 E6 真人研究来回答。**
