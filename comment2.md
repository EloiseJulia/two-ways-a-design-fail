面向 CCF-A / CHI Full Paper 的系统提升建议
总原则：先不开展真人实验（最后再做），也不要用计划中的真人实验补偿当前论证缺口。
当前阶段先把论文提升成一篇扎实的 synthetic-user measurement validity / backend robustness 研究；真人实验作为最后一个独立阶段，用于完成 external validity 和 human grounding。
________________________________________
一、首先重设论文的核心定位
1. 不要再把“合成用户风险筛查器”作为已经实现的主要贡献
当前论文尚未证明 synthetic panel 能正确识别对真人危险的界面，也没有确定或验证筛查阈值。现有 panel–human correspondence 不显著或信息不足，因此暂时不能把它包装成：
	validated pre-deployment screen；
	reliable danger detector；
	synthetic replacement for formative user studies；
	能判断某项设计是否可以 release 的工具。
论文目前真正有证据支撑的核心问题应改为：
在使用 LLM synthetic users 评估人机界面风险时，风险测量是否具有跨模型稳定性、构念效度和方法鲁棒性？
核心发现相应改写为：
相同刺激、persona 和分析协议，在不同 backend LLM 上会产生显著不同的风险估计；这种差异不仅体现在绝对错误建议采纳率，也体现在 framing effect 和 persona heterogeneity。因此，synthetic-panel measurement 不能被视为与 backend 无关。
论文当前已经观察到 aggregate adoption、coercive-framing effect 和 panel disagreement 的模型依赖性，而明确提示的 persona disposition 排序相对稳定。这个“什么稳定、什么不稳定”的区分，应成为全文的中心。 [two ways a...esign fail | PDF]
________________________________________
2. 从“提出一个筛查工具”转成“审计一种新兴研究方法”
建议把论文定义为以下三种类型的组合：
	Measurement audit
审计 synthetic user panel 测量界面风险时的 backend dependence。
	Robustness study
系统分解模型、prompt、persona、item 和生成随机性对结果的影响。
	Construct-validity study
检查所谓的 over-reliance、heterogeneity 和 coercion sensitivity 到底测到了什么。
这会让论文的主张和当前证据更加匹配，也更容易形成 CHI 所重视的方法论贡献。
________________________________________
二、重新组织 Research Questions
建议把现有研究问题重构为四组。
RQ1：Backend invariance
RQ1. To what extent are synthetic-panel estimates of interface-level reliance risk invariant across backend LLMs?
回答重点：
	绝对 wrong-advice adoption 是否稳定；
	matched framing effect 是否稳定；
	persona heterogeneity 是否稳定；
	模型排序是否跨数据集、prompt 和随机采样保持；
	结论是定量偏移，还是会导致定性决策翻转。
最后一点很重要。不要只说数值不同，要回答：
同一个设计是否会因为 backend 不同而从“高风险”变成“低风险”？
这才对应真正的方法学后果。
________________________________________
RQ2：Variance decomposition
RQ2. How much of the observed synthetic-user risk estimate is attributable to backend model, item, persona specification, prompt wording, and generation randomness?
这是把论文从“比较几个模型”提升到“测量学研究”的关键。
至少分解以下来源：
	backend model；
	dataset/task；
	item；
	persona；
	interface condition；
	prompt template/paraphrase；
	generation seed/sample；
	model × condition；
	model × persona；
	model × item；
	persona × condition。
如果分析表明 backend model 或 model × condition 的方差很大，就能更有力地支持“backend choice is a first-order methodological decision”。
________________________________________
RQ3：Construct and manipulation validity
RQ3. Which synthetic-panel signals reflect stable sensitivity to the intended manipulation, and which primarily reflect explicit persona instructions or model-specific response tendencies?
这里需要区分：
	aggregate wrong-advice adoption；
	framing-induced switching；
	persona ordering；
	conflict-conditioned heterogeneity；
	generic instruction-following；
	default acquiescence；
	susceptibility to authority；
	resistance to factually incorrect advice。
尤其要明确：
trusting-novice persona 排名最高，是有效的 vulnerability signal，还是显式 prompt compliance？
当前文章已经把这一结果降级为 manipulation check，这是正确方向；下一步要用消融实验确定其来源。 [two ways a...esign fail | PDF]
________________________________________
RQ4：Robust screening without human validation
在真人实验完成前，不要问“能否预测真人”，而应问：
RQ4. Can conservative multi-model aggregation reduce backend-induced decision instability compared with single-model synthetic panels?
可以研究：
	worst-case estimate；
	median ensemble；
	majority vote；
	uncertainty-aware abstention；
	leave-one-model-out ensemble；
	model-disagreement-triggered escalation；
	lower/upper risk bounds。
这里评估的是：
聚合方法是否减少 synthetic measurement 内部的不稳定性。
暂时不要声称它提高了真人预测准确率。
________________________________________
三、重新定义论文贡献
建议将贡献严格限制为以下四项。
Contribution 1：跨模型测量不稳定性的系统证据
不是泛泛地说“模型结果不同”，而是证明：
	不同 backend 会显著改变风险估计；
	某些指标只是 level shift；
	某些指标的 framing effect 也会改变；
	某些情况下会导致风险判断翻转；
	更强模型并不必然产生更一致或更“人类化”的 synthetic users。
建议避免使用：
Frontier models suppress real danger.
改成：
Frontier and non-frontier models produce materially different synthetic risk estimates; without human grounding, these estimates cannot be ranked by validity.
在真人实验前，不能判断究竟是 frontier model 漏警，还是较弱模型产生假阳性。
________________________________________
Contribution 2：synthetic panel 的方差分解框架
将现有 “persona × model” 设计升级成一个方法框架：
Synthetic-panel results should be reported as distributions over models, prompts, personas and generations rather than as a single point estimate.
最好给出一套可复用的报告清单：
	backend sensitivity；
	prompt sensitivity；
	stochastic sensitivity；
	persona ablation；
	item robustness；
	decision instability；
	abstention region；
	uncertainty interval。
这比单独提出两个风险轴更可能形成真正的 CHI 方法贡献。
________________________________________
Contribution 3：区分稳定与不稳定的 synthetic signals
建议形成一个明确分类：
相对稳定的部分
例如：
	显式 prompt disposition 被模型执行；
	某些 persona 相对排序跨 backend 保持；
	coercive bundle 相对 neutral condition 可能在多数模型上增加 switching。
不稳定的部分
例如：
	绝对错误建议采纳率；
	framing effect magnitude；
	persona heterogeneity；
	基于单一阈值的风险分类；
	不同模型对高置信错误建议的基线抵抗能力。
当前论文已观察到 persona 排序稳定、aggregate signal 不稳定，可以在扩展实验后把这个区分提升为核心理论结果。 [two ways a...esign fail | PDF]
________________________________________
Contribution 4：保守的多模型评估协议
不要称其为“validated danger screen”，可称为：
	robustness protocol；
	synthetic-panel audit protocol；
	conservative pre-study evaluation procedure；
	backend-aware measurement protocol。
其输出不应是简单的 safe/unsafe，而应是：
	consistently low synthetic risk；
	consistently high synthetic risk；
	backend-sensitive；
	prompt-sensitive；
	high uncertainty；
	abstain / requires human evaluation。
这样即使暂时没有真人数据，协议依然可以凭借内部稳定性和透明度成立。
________________________________________
四、优先级最高的新增实验
以下实验均可在真人实验之前完成。
________________________________________
实验 1：多次采样与生成随机性分析
当前每个 prompt 只有一次 generation，无法判断模型差异是否大于模型内部随机性；论文也将此列为限制。 [two ways a...esign fail | PDF]
建议设计
每个完整条件至少重复生成：
	最低：5 次；
	建议：10 次；
	资源允许：20 次。
至少选择：
	两个代表性 OpenAI 模型；
	一个独立厂商模型；
	一个表现出高 adoption 的模型；
	一个表现出低 adoption 的模型。
必须回答
	同模型重复运行的 adoption variance 有多大？
	backend 间差异是否显著大于 backend 内差异？
	persona 排序在重复采样后是否稳定？
	framing effect 的方向是否稳定？
	risk classification 翻转率是多少？
	增加样本数后结论是否收敛？
建议报告
	intraclass correlation；
	rank stability；
	sign consistency；
	decision flip rate；
	model-within-generation variance；
	bootstrap confidence intervals；
	convergence curves。
这个实验非常关键，因为没有它，论文只能说“这一次运行中模型不同”。
________________________________________
实验 2：Prompt paraphrase robustness
当前结果可能依赖单一 prompt template，而非 conceptual manipulation。
建议设计
为每个关键 condition 构造 5–10 个语义等价版本：
	neutral advice；
	coercive advice；
	placebo；
	persona description；
	decision output format。
改写时保持：
	advice label 不变；
	信息量不变；
	confidence 不变；
	不额外增加说服内容；
	句式、语气和信息顺序变化。
核心指标
	同一模型跨 paraphrase 的 adoption variance；
	framing effect 的方向一致率；
	模型排名稳定性；
	persona 排名稳定性；
	backend variance 与 wording variance 的相对大小；
	condition classification flip rate。
目标
证明文章报告的现象不是某一套 prompt wording 的偶然产物。
________________________________________
实验 3：Persona descriptor ablation
这是当前论文最明显的缺口之一。
至少设置四类 persona
A. Explicit-label persona
保留：
	trusting；
	skeptical；
	novice；
	expert。
作为现有基线。
B. Behavioral-description persona
删除标签，仅描述行为倾向，例如：
	通常是否核验自动化建议；
	对高置信系统建议如何反应；
	是否有相关任务经验；
	在不确定状态下是否寻求额外证据。
C. Background-only persona
只保留：
	经验年限；
	任务熟悉度；
	AI 使用频率；
	决策环境。
不直接描述信任或采纳倾向。
D. Label-shuffled / contradictory controls
例如：
	标签写 trusting，但行为描述强调会独立核验；
	标签写 expert，但不给出相关领域能力；
	随机交换 persona 名称；
	删除所有 persona 信息。
必须回答
	trusting-novice 排名是否依赖显式关键词？
	标签和行为描述冲突时，模型跟随哪一个？
	无 persona 条件下是否仍出现类似分群？
	persona effect 能否超过 prompt compliance baseline？
	不同 backend 对 persona cue 的敏感度是否不同？
解释规则
	如果删除显式标签后效应消失：将 persona 结果明确归类为 prompt compliance。
	如果行为描述版本仍稳定：可以主张一定程度的 construct sensitivity。
	在真人实验前，仍不能主张对真实人群具有 external validity。
________________________________________
实验 4：Coercive framing 因素消融
当前 dark condition 把 confidence、authority 和 accountability 捆绑在一起，因此只能观察 bundled effect，无法解释作用机制。 [two ways a...esign fail | PDF]
建议使用析因设计
至少拆成三个二元因素：
	High confidence：有 / 无；
	Authority cue：有 / 无；
	Accountability or pressure cue：有 / 无。
如果完整实施，就是 2×2×2设计。
如计算成本不足
至少增加以下单因素条件：
	confidence only；
	authority only；
	accountability only；
	confidence + authority；
	confidence + accountability；
	authority + accountability；
	full bundle；
	neutral baseline。
必须分析
	各因素主效应；
	两两交互；
	三阶交互；
	model × factor interaction；
	persona × factor interaction；
	conflict-conditioned switching。
重要价值
如果不同模型分别对“置信度”“权威”和“责任压力”敏感，论文就不再只是报告 backend difference，还能解释差异来自什么 behavioral mechanism。
________________________________________
实验 5：扩大任务结构，而不仅是增加同类数据集
目前 beer 和 Amazon book 都属于英文二分类情感判断，因此只能算同一任务家族内的复现。 [two ways a...esign fail | PDF]
建议至少加入三类不同任务
任务 A：事实判断
	可由明确 ground truth 自动评分；
	重点考察错误建议采纳。
任务 B：数值或概率推理
	需要独立推算；
	可以检测 AI 高置信度是否压制独立判断。
任务 C：证据权衡任务
	给定多条证据；
	AI 建议与部分证据冲突；
	检查模型是采纳结论还是核验依据。
可选任务 D：多分类决策
测试二分类结构之外的泛化。
选择原则
	有明确、可核验的 ground truth；
	不需要真实高风险部署；
	不涉及不可控的专业伦理风险；
	能构造 faithful、wrong、neutral 和 coercive advice；
	能定义独立判断与 advice-induced switching。
目标
从“两套 sentiment 数据”提升到“跨任务结构复制”。
________________________________________
实验 6：随机新 item，而不是继续使用按人类 variance 筛选的 item
当前 item 使用人类 reliance variance 进行过选择，这可能放大目标效应；论文也主动承认这一点。 [two ways a...esign fail | PDF]
建议增加两个 item set：
	Random fresh set：从原始任务总体随机抽取；
	Prospectively held-out set：制定规则后完全冻结的新刺激集。
比较：
	selected items；
	random items；
	held-out items。
如果模型依赖性仅在被筛选 item 上出现，结果的普适性就有限。如果在 random/held-out item 上仍成立，可信度会明显提升。
________________________________________
实验 7：不同 prompt presentation order
synthetic agent 可能受信息顺序影响。
至少测试：
	persona → task → AI advice；
	task → independent answer → persona reminder → AI advice；
	task → AI advice → persona；
	confidence before prediction；
	prediction before confidence；
	authority cue before/after advice。
报告：
	order effect；
	order × model interaction；
	condition effect 是否跨顺序保持。
如果结果高度依赖 prompt serialization，就应把这一点作为 synthetic-interface evaluation 的重要发现，而不是隐藏为实现细节。
________________________________________
实验 8：解析、拒答和格式依从性审计
不同模型可能因为：
	输出格式遵循程度不同；
	拒绝参与欺骗性 framing；
	输出解释而非二元决策；
	parser failure；
	默认安全策略不同
而产生表面 adoption 差异。
建议单独报告每个模型的：
	valid response rate；
	parse failure rate；
	refusal rate；
	hedging rate；
	non-binary answer rate；
	correction/challenge rate；
	spontaneous fact-checking rate。
不要把 refusal 或 challenge 简单编码成“不采纳”。应设置明确 taxonomy，例如：
	adopt AI；
	retain original judgment；
	abstain；
	challenge premise；
	refuse decision；
	malformed/unparseable。
主分析可以二元化，但必须提供多类别敏感性分析。
________________________________________
实验 9：跨模型 risk-ranking 与 decision-flip 分析
当前重点偏向均值差异，CHI 级别的方法论文还需要说明这些差异会造成什么实际后果。
建议定义若干不依赖真人数据的候选规则，例如：
	top 25% synthetic risk；
	statistically elevated over neutral；
	effect exceeds预设最小效应；
	two-axis Pareto frontier；
	posterior probability above threshold。
然后计算：
	不同 backend 对同一设计的分类一致率；
	pairwise agreement；
	Fleiss’ kappa；
	rank correlation；
	top-k overlap；
	false-clear disagreement；
	false-alarm disagreement；
	backend replacement flip rate。
注意：这里的 false clear / false alarm 只能相对于synthetic consensus rule定义，不能相对于真人危险定义。
________________________________________
实验 10：多模型聚合及 abstention 方法
可以提出几种 backend-aware 协议。
Conservative maximum
任一模型发出高风险信号，则进入人工评估。
优点：高召回倾向。
缺点：可能被异常模型主导。
Median ensemble
使用所有模型风险估计的中位数。
优点：对极端模型稳健。
缺点：可能掩盖少数 backend 的真实异常。
Quantile interval
报告模型间的风险区间，不给单点判断。
Disagreement-triggered abstention
如果模型间差异超过阈值，则输出：
Synthetic evidence is backend-sensitive; no automated conclusion should be drawn.
Leave-one-model-out ensemble
检测聚合结论是否被单一模型主导。
评价指标
在没有真人实验时，只评价：
	重采样稳定性；
	prompt 稳定性；
	模型替换稳定性；
	held-out task 稳定性；
	decision flip rate；
	coverage–abstention tradeoff。
不要评价“human accuracy”。
________________________________________
五、重构 Axis 1：避免 over-dispersion 概念过度延伸
当前 Axis 1 容易受到质疑，因为 synthetic personas 并不是从真实人群中抽样得到的，persona variance 很大程度由研究者设计。
建议将其暂时改名为：
	persona-conditioned response heterogeneity；
	或 synthetic-panel disagreement。
不要直接把它等同于：
	population heterogeneity；
	user vulnerability distribution；
	between-human over-dispersion。
必须增加的分析
1. Persona-set sensitivity
使用多套 persona 构造方法：
	人工设计的极端 persona；
	连续属性组合；
	随机组合；
	无 persona；
	behavior-only persona；
	matched-neutral persona。
检验 Axis 1 是否取决于研究者选择了哪些 persona。
2. Persona count sensitivity
分别使用：
	4 personas；
	6 personas；
	10 personas；
	20 personas。
检查 disagreement 是否随着 persona 数量或极端 persona 比例机械变化。
3. Balanced reweighting
避免 trusting/skeptical 等类别比例决定 aggregate heterogeneity。
4. Alternative metrics
除 beta-binomial ρ和 mean disagreement 外，至少比较：
	pairwise disagreement；
	entropy；
	variance of switching probability；
	Gini impurity；
	random-effects variance；
	persona-level ICC。
5. 指标有效性边界
论文应明确：
在没有真人映射之前，Axis 1 表示 synthetic persona responses 对设计条件的敏感分化，而不是人类总体中的风险分布。
________________________________________
六、重构 Axis 2：从 adoption rate 转向 advice-induced behavioral change
绝对 adoption rate 容易受到模型基线倾向影响。更有解释力的主要因变量应是：
在同一 item 上，加入特定 framing 后，相对于独立判断或 neutral condition 产生的决策变化。
建议设置主要指标
Primary outcome
Conflict-conditioned switch-to-wrong rate：
	初始判断正确；
	AI 建议错误；
	加入 advice 后切换到错误答案。
Secondary outcomes
	absolute wrong-advice adoption；
	correction-to-right rate；
	retain-correct rate；
	abstention rate；
	challenge rate；
	confidence change；
	explanation reliance。
为什么这样更好
它能区分：
	模型本来就答错；
	模型被 AI advice 诱导答错；
	模型独立答对但在 framing 下改变；
	模型拒绝或质疑错误前提。
当前论文已开始使用 conflict-conditioned switch rate，应把它提升为主要而非辅助分析。 [two ways a...esign fail | PDF]
________________________________________
七、统计分析升级方案
1. 不要只进行逐模型比例比较
使用分层模型统一分析：
"Adopt"\_g∼"condition"×"model"×"persona"*(1∣"item" )*(1∣"prompt version" )*(1∣"generation" )
具体可以使用：
	hierarchical logistic regression；
	generalized linear mixed models；
	Bayesian multilevel models。
需要根据设计判断哪些项为 fixed effect、哪些为 random effect。
________________________________________
2. 报告模型间异质性，而不仅是 p-value
建议报告：
	variance components；
	heterogeneity intervals；
	interaction effect sizes；
	posterior distributions；
	probability of sign reversal；
	probability of exceeding a practically meaningful threshold。
________________________________________
3. 预设最小实质效应
不能只用“统计显著”判断 framing 是否重要。
建议预注册：
	最小 odds ratio；
	最小 absolute switch-rate increase；
	最小 risk-classification change；
	最小跨模型 disagreement。
阈值必须依据应用逻辑或 pilot sensitivity analysis 确定，而非看完结果后选择。
________________________________________
4. 区分 inference target
必须明确每项结论想泛化到哪里：
	这些具体 items；
	当前 task family；
	这些固定 personas；
	persona-generating process；
	这些具体 models；
	当前可用 LLM backend；
	某个“能力层级”。
如果模型不是从一个清晰总体中随机抽取，就不要轻易将六个模型泛化成“所有 LLM”。
________________________________________
5. 做 specification curve / multiverse analysis
分析结论是否依赖：
	conflict conditioning；
	persona weighting；
	refusal coding；
	missing-value treatment；
	different heterogeneity metrics；
	item clustering method；
	frequentist vs. Bayesian model；
	selected vs. fresh items。
把所有合理分析规格列出，展示结论是否稳健。
________________________________________
八、论文标题建议
当前标题有叙事性，但 “Two Ways a Design Fails” 容易让读者期待论文证明了真实设计对人的危险。
建议改成更符合证据的标题。
稳健型
When Synthetic Users Disagree: Backend Dependence in LLM-Based Interface Risk Evaluation
方法学型
The Panel Is the Model: Auditing Backend Sensitivity in Synthetic-User Evaluations
强调测量效度
Do Synthetic Users Measure the Same Risk? A Multi-Model Audit of LLM-Based Interface Evaluation
保留原题精神
When Does a Synthetic LLM Panel See the Danger? Auditing Backend Dependence in Interface-Risk Measurement
推荐第三或第四个。它们更准确，也不会过早声称检测到了真实危险。
________________________________________
九、摘要重写要求
摘要应采用以下结构。
1. Motivation
synthetic users 被用于低成本界面评估，但其结论可能依赖 backend model。
2. Gap
已有工作主要关心 synthetic users 是否匹配真人，较少先检验同一测量协议是否跨模型、prompt 和生成采样稳定。
3. Method
说明：
	多 backend；
	多任务；
	多 persona construction；
	prompt paraphrase；
	repeated generations；
	factorial framing manipulations；
	hierarchical variance decomposition。
4. Main findings
按“稳定 vs. 不稳定”组织，而不是按 Axis 1 / Axis 2 罗列。
5. Contribution
强调：
	backend-sensitive measurement；
	variance decomposition；
	robust reporting protocol；
	aggregation/abstention procedure。
6. Boundary
明确写：
We evaluate internal and cross-backend robustness; human predictive validity is reserved for a separate validation study.
不要在摘要中以 planned human study 作为贡献。
________________________________________
十、Introduction 的重写逻辑
建议按以下顺序。
第一段：实际问题
LLM synthetic users 正被用于快速评估产品、界面和决策支持系统。
第二段：根本风险
synthetic-panel 输出可能同时由以下因素决定：
	被评估的界面；
	backend model；
	persona prompt；
	prompt wording；
	generation randomness。
如果无法分离这些来源，所谓“设计风险”可能只是测量工具的属性。
第三段：现有研究缺口
现有争论主要聚焦 synthetic–human correspondence，但在讨论 external validity 前，应先建立：
	repeatability；
	backend invariance；
	construct validity；
	decision stability。
第四段：本文问题
不是问 synthetic users 是否替代人，而是问：
当研究者更换模型、prompt 或随机生成时，是否仍会对同一设计作出相同判断？
第五段：方法概览
介绍多模型、多 prompt、多 generation、多任务和 persona ablation。
第六段：结果概览
精确区分：
	absolute levels 不稳定；
	condition effects 在何种范围稳定；
	persona prompt propagation 在何种条件下稳定；
	哪些设计导致 risk-decision flip；
	聚合/abstention 是否改善稳定性。
第七段：贡献
只列证据支持的贡献，不列未来真人实验。
________________________________________
十一、Related Work 需要补出的理论脉络
不要只覆盖 synthetic users、AI reliance 和 dark patterns。至少增加以下板块。
1. Measurement invariance
借用测量学思想讨论：
	同一构念在不同测量工具下是否具有相同含义；
	backend model 是否相当于测量 instrument；
	measurement non-invariance 如何影响比较。
2. Reliability vs. validity
必须清楚区分：
	repeatability；
	internal consistency；
	backend stability；
	construct validity；
	criterion validity；
	external validity。
核心观点可以是：
稳定并不等于有效，但跨 backend 严重不稳定会削弱任何有效性主张。
3. Researcher degrees of freedom in LLM evaluation
讨论：
	model choice；
	prompt choice；
	decoding setting；
	output parser；
	persona wording；
	sampling count。
将其定义为 synthetic-user research 中的 hidden analytic flexibility。
4. Algorithmic auditing and robustness
把工作连接到：
	sensitivity analysis；
	stress testing；
	model cards/evaluation reporting；
	multi-model benchmarking；
	uncertainty-aware decision systems。
5. Persona prompting and role-conditioning
更系统地区分：
	persona adherence；
	behavioral simulation；
	stereotype amplification；
	demographic essentialism；
	prompt-induced caricature。
________________________________________
十二、Discussion 应形成的主要观点
1. Backend 不是实现细节，而是测量工具的一部分
不能写：
We ran the same study with different models.
应提升为：
Changing the backend changes the measurement instrument.
这是整篇论文最值得保留的理论句子。
________________________________________
2. 更强模型不等于更好的 synthetic participant
但也不能直接说更强模型更差。
正确表达应是：
	capability 与 human fidelity 不是同一概念；
	resistance to wrong advice 可能提高任务正确率；
	但这未必对应目标用户；
	更高能力也可能减少可观察 persona differentiation；
	在没有真人基准时，不能根据能力或正确率选择 synthetic participant。
________________________________________
3. 稳定的 persona 排序不代表发现了真实人群
即使跨 backend 稳定，也可能意味着：
	所有模型都遵循相同显式指令；
	所有模型共享相似的 persona stereotype；
	persona 设计本身规定了结果。
只有 label ablation、behavior-only persona 和最终真人验证后，才能更强地解释该结果。
________________________________________
4. Synthetic evaluation 需要“分歧即信息”
模型间分歧不应只是噪声，也可以成为输出：
High cross-backend disagreement indicates that the synthetic evidence is instrument-sensitive and should not support an automated conclusion.
这可以自然导向 abstention protocol。
________________________________________
5. 把“失败”从界面失败改为测量失败
建议区分三种失败：
	Interface-level synthetic signal：在 synthetic agents 中观察到 adoption 或 disagreement；
	Measurement failure：更换 backend/prompt 后结论翻转；
	Human-facing design failure：真实用户受到损害。
当前论文主要能证明第 1、2 类；第 3 类留给真人实验。
________________________________________
十三、Limitations 不能只列清单，要与主张边界一一对应
建议明确以下边界：
	不预测个体真人；
	不推断真实人口分布；
	不确定哪个 backend 更接近人；
	不把 synthetic disagreement 等同于 human heterogeneity；
	不把 prompt obedience 等同于心理特质；
	不把 bundled framing effect 等同于单独的 authority effect；
	不把同任务家族复现称为跨领域泛化；
	不把内部稳健性等同于外部有效性；
	不把模型拒答或安全策略简单解释为抵抗操纵；
	不把当前模型集合泛化为所有 LLM。
同时，每项 limitation 后面说明论文中采取了什么缓解措施，而不是全部推给未来工作。
________________________________________
十四、真人实验暂时留空时的处理方式
正文中怎么处理
可以保留一个短节：
Human validation as a separate phase
只写三件事：
	当前研究目标是 internal robustness 和 construct sensitivity；
	human predictive validity 不属于本文已完成证据；
	真人实验将在 protocol 和分析方法冻结后独立开展。
不要把未实施的真人实验写成完整贡献，也不要在结果部分反复引用未来研究来支持当前结论。
________________________________________
建议加入明确占位符
可以留一个内部编辑标记，但投稿稿件中应删除：
[HUMAN VALIDATION PHASE — TO BE CONDUCTED AFTER THE SYNTHETIC
ROBUSTNESS PROTOCOL, EXCLUSION RULES, AND ANALYSIS PLAN ARE FROZEN.]
``
真人实验开始前必须冻结：
	研究假设；
	主要因变量；
	item set；
	exclusion criteria；
	synthetic model selection；
	“哪个模型最接近人”的评价规则；
	subgroup analysis；
	stopping rule；
	multiple-comparison plan。
防止看到真人结果后再选择最有利的 synthetic configuration。
________________________________________
十五、工程与可复现性要求
为了达到 CHI 级别，建议提供完整 supplement 或匿名仓库，至少包括：
	完整 prompt templates；
	所有 paraphrases；
	persona definitions；
	model names and dated versions；
	API dates；
	decoding parameters；
	system prompts；
	retry policy；
	parser implementation；
	raw model outputs；
	refusal and parse-failure labels；
	frozen item IDs；
	preregistration；
	analysis scripts；
	environment lockfile；
	cost and token accounting；
	audit log；
	known deviations；
	model deprecation/replacement policy。
尤其要记录准确的模型版本和调用时间，因为 backend 可能静默更新。
________________________________________
十六、建议的执行优先级
P0：必须完成，否则难达到 A 档
	重设定位：measurement audit，而不是 validated screening；
	多次 generation；
	prompt paraphrase robustness；
	persona descriptor ablation；
	coercive bundle factorial ablation；
	fresh/random item set；
	至少加入两种不同任务结构；
	hierarchical variance decomposition；
	refusal/parser taxonomy；
	将 conflict-conditioned switching 设为主要 outcome。
P1：强烈建议完成
	多模型 aggregation；
	disagreement-triggered abstention；
	persona-set sensitivity；
	specification curve；
	presentation-order robustness；
	risk-decision flip analysis；
	leave-one-model-out result；
	preregister新增实验。
P2：可在篇幅或算力足够时完成
	更大模型覆盖；
	多语言任务；
	多模态界面呈现；
	自动 persona generation 与人工 persona 对比；
	更细粒度的解释文本编码；
	模型内部 confidence calibration。
________________________________________
十七、可直接交给 AI 的修改指令
请将这篇论文按 CHI Full Paper / CCF-A 水准进行系统重构。

核心限制：
1. 暂时不开展真人实验。
2. 不得使用计划中的真人实验补偿当前论证缺口。
3. 不得声称 synthetic panel 已经能够预测真人、识别真实脆弱人群，
或作为经过验证的部署前风险筛查器。
4. 当前阶段的核心定位应改为：
对 LLM synthetic-user interface evaluation 进行 backend sensitivity、
measurement invariance、construct validity 和 robustness audit。
5. 所有结论必须区分：
a. synthetic-agent behavior；
b. measurement robustness；
c. human-facing design risk。
在真人验证前，只允许对前两者作实证主张。

请依次完成以下任务：

A. 重写论文定位
- 将主问题从“synthetic panel 能否检测危险界面”改为
“synthetic-panel risk measurement 是否跨 backend、prompt、
persona construction 和 generation sampling 保持稳定”。
- 将 screening protocol 降格为 backend-aware audit protocol。
- 将 threshold-based release decision 改为 uncertainty-aware reporting
和 abstention。

B. 重写 Research Questions
- RQ1：backend invariance；
- RQ2：model/item/persona/prompt/generation variance decomposition；
- RQ3：construct sensitivity 与 prompt compliance 的区分；
- RQ4：multi-model aggregation 和 disagreement-triggered abstention
是否减少内部决策不稳定性。

C. 增加实验
- 每个关键 prompt 重复生成至少 10 次；
- 为关键 condition 设计至少 5 个语义等价 paraphrases；
- 设计 explicit-label、behavior-only、background-only、
no-persona 和 contradictory persona ablations；
- 将 confidence、authority、accountability cues 拆成 factorial design；
- 增加 fresh random items 和 prospectively held-out items；
- 增加至少两种不同于 binary sentiment 的任务结构；
- 记录 refusal、challenge、abstention、malformed output 和 parse failure；
- 测试 prompt information order；
- 评估跨模型 risk rank、agreement 和 decision flip rate；
- 比较 conservative maximum、median ensemble、quantile interval、
leave-one-model-out ensemble 和 disagreement-triggered abstention。

D. 重构指标
- 将 conflict-conditioned switch-to-wrong rate 设置为主要 Axis-2 outcome；
- 将 absolute wrong-advice adoption 降为次要 outcome；
- 将 Axis 1 改称 persona-conditioned response heterogeneity 或
synthetic-panel disagreement；
- 不得将 Axis 1 直接解释为真实人群 over-dispersion；
- 对 Axis 1 增加 persona-set、persona-count、weighting 和 metric sensitivity。

E. 升级统计分析
- 使用 hierarchical logistic/multilevel models；
- 分解 backend、item、persona、prompt、generation 和 interaction variance；
- 报告 effect size、uncertainty interval、sign-reversal probability、
rank stability 和 decision flip rate；
- 预设 practical significance thresholds；
- 进行 specification curve / multiverse analysis；
- 明确每项结论的 inference target。

F. 重写论文结构
- Introduction：从 synthetic-user measurement problem 切入；
- Related Work：增加 measurement invariance、reliability vs validity、
LLM evaluation degrees of freedom、persona prompting、robustness audit；
- Results：按 stable signals、unstable signals、variance sources、
decision consequences、aggregation/abstention 组织；
- Discussion：强调 backend 是测量工具的一部分，而非实现细节；
- Limitations：明确不能预测真人、不能推断人口分布、
不能判断哪个 backend 最接近人；
- Human Validation：只保留为独立后续阶段，不得作为当前贡献。

G. 控制叙事
- 删除或弱化“frontier model suppresses real danger”；
- 改为“不同 backend 产生不兼容的 synthetic risk estimates，
目前无法在缺少 human ground truth 时判断哪个更有效”；
- 将 trusting-novice 结果视为 manipulation check，
除非 descriptor ablation 后仍保持；
- 不把两个 sentiment datasets 称为 broad cross-domain replication；
- 不把 bundled coercion effect 解释成单一心理机制。

H. 输出要求
请产出：
1. 新标题候选；
2. 新摘要；
3. 新 Introduction 大纲；
4. 新 RQ 和 hypotheses；
5. 完整新增实验矩阵；
6. 变量与统计模型定义；
7. 主结果应如何组织；
8. Contribution statements；
9. Discussion arguments；
10. Limitations；
11. 真人实验前必须冻结的 preregistration 项目；
12. 原稿逐节修改清单；
13. 需要删除、降级或改写的过强主张列表。

修改目标：
使论文即便暂时没有真人实验，也能够作为一篇完整、严谨、
有明确方法学贡献的 synthetic-user measurement audit 成立；
完成真人实验后，再进一步建立 criterion validity 和 human grounding。

