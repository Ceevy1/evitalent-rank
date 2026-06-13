# EviTalent-Rank

EviTalent-Rank 是一个面向《人才简历综合优选》赛题的 V1 工程：基于证据约束与大语言模型语义增强，对电商、品牌、人力资源、生产、销售、研发六个领域的人才竞争力进行确定性评分、排序和解释。

## 项目目标

- 从 DOCX/PDF/TXT 简历中抽取结构化经历、项目、能力标签和成果事件。
- 对候选人计算 BCS、ECI、Penalty 和 RankScore。
- 输出同领域排序、核心优势、风险提示、证据卡片和审计结果。
- 默认支持 Mock 演示模式，不依赖任何在线大模型 API。

## 方法创新点

1. 大语言模型只做结构化抽取、领域识别、能力标签识别、成果事件提取、证据定位和质量标记。
2. 最终排名由 Python 规则引擎按 YAML 配置确定性计算，不让大模型直接决定排名。
3. 每项评分事实绑定 `evidence_id` 和原文 `quote`，支持可解释和可追溯。
4. 缺失信息默认中性分 50，并降低 ECI，而不是直接按 0 分处理。
5. 将“情商”替换为跨部门协同、团队搭建、人才培养、冲突处理、组织推动等可观察证据。
6. 内置公平性、稳定性和时间线审计。

## 隐私保护原则

- 姓名、性别、出生日期、年龄、婚姻、家庭情况、籍贯、当前薪资、期望薪资会被识别并隔离。
- 主排名只基于脱敏后的结构化经历、能力和成果，不使用敏感字段。
- 敏感字段可用于公平性反事实审计，但不进入主评分。
- 原始简历放入 `data/raw/`，该目录已被 `.gitignore` 排除。
- 前端默认只展示脱敏文本、候选人编号、评分和证据，不展示真实敏感字段。

## 工程目录

```text
evitalent_rank/
├── config/                 # 领域权重、能力本体、归一化与应用配置
├── schemas/                # JSON Schema Draft 2020-12
├── prompts/                # LLM 抽取提示词
├── src/evitalent/          # 核心 Python 包
│   ├── parser/             # DOCX/PDF/TXT 解析
│   ├── privacy/            # PII 检测与脱敏
│   ├── extraction/         # Mock/LLM 抽取与 Schema 校验
│   ├── features/           # 特征工程
│   ├── scoring/            # BCS、ECI、Penalty、RankScore
│   ├── audit/              # 公平性、稳定性、时间线审计
│   ├── reporting/          # HTML 报告
│   └── api/                # FastAPI
├── app/streamlit_app.py    # Streamlit 页面
├── scripts/                # Demo 与批处理脚本
├── tests/                  # pytest 测试
└── data/fixtures/          # 脱敏 Mock 数据
```

## 安装方法

建议使用 Python 3.11。

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

安装：

```bash
pip install -e .
```

## Mock 演示

Mock 数据位于 `data/fixtures/`，不包含真实姓名、出生日期、婚姻和薪资。

```bash
python scripts/run_demo.py
```

输出会写入：

- `data/outputs/rankings/`
- `data/outputs/html_reports/`

## LLM 模式配置

系统默认使用 `mock`，这样没有任何模型、没有 API key 时也能完整演示。真实简历进入模型前必须先经过 Stage 2 的解析与脱敏，LLM 输入只允许来自 `data/redacted/`，原始 `data/raw/` 内容不会发送给模型。

支持三种抽取模式：

- `mock`：默认模式，读取脱敏 fixture，不需要模型；
- `local_ollama`：推荐的本地模型模式，使用 OpenAI-compatible `/v1/chat/completions`；
- `compatible_api`：远程兼容 API，默认关闭，只有用户主动配置并选择后才调用。

复制 `.env.example` 为 `.env` 后配置。Mock 默认配置：

```bash
DEFAULT_EXTRACTION_MODE=mock
LLM_PROVIDER=mock
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TEMPERATURE=0
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=1
```

本地 Ollama 示例：

```bash
LLM_PROVIDER=local_ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
LLM_TEMPERATURE=0
```

安装并启动 Ollama 后，拉取模型并保持服务运行：

```bash
ollama pull qwen2.5:7b
ollama serve
```

远程 OpenAI-compatible API 示例：

```bash
LLM_PROVIDER=compatible_api
LLM_BASE_URL=https://your-compatible-endpoint/v1
LLM_API_KEY=your_api_key
LLM_MODEL=your_model
```

检查连接：

```bash
python scripts/check_llm_connection.py
```

所有 LLM 输出都会先通过 `schemas/candidate_extraction.schema.json`、Pydantic 模型、evidence link 和敏感字段复核。失败时 API 返回明确错误，失败结果不会写入正式 `data/extracted/`，也不能进入评分。

安全边界：

- 原始简历正文不得发送给模型；
- 不在日志中打印完整简历文本或模型输入全文；
- evidence quote 中若出现手机号、邮箱、证件号或薪资原文，会拒绝进入评分；
- LLM 不得输出最终排名，RankScore 始终由 Python 评分引擎计算。

## 混合成果抽取管线

根据本地 Ollama 冒烟测试，真实抽取已改为混合架构：

```text
脱敏文本
→ Python AchievementCandidateDetector 定位所有含业务数字的成果候选片段
→ Python 复合句拆分为单一指标候选
→ LLM 仅解释单条候选的 raw_metric_name、metric_value、unit、evidence_quote
→ Python EventTypeMapper / DirectionMapper 确定性标准化
→ GroundingValidator 校验证据 quote 与数字对齐
→ 通过校验的成果进入 CandidateExtraction
→ 现有评分引擎计算 BCS、ECI、Penalty、RankScore
```

LLM 不再负责标准 `event_type`、标准 `direction`、评分、排名或录用建议。映射失败的成果会标记为 `needs_review`，默认不进入核心成果评分。

运行混合抽取演示：

```bash
python scripts/run_candidate_detection_demo.py
python scripts/run_single_event_extraction_demo.py
python scripts/run_hybrid_extraction_demo.py
python scripts/evaluate_demo_extraction_accuracy.py
```

本地 Ollama 推荐配置：

```bash
LLM_PROVIDER=local_ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=evitalent-extractor:7b
LLM_TEMPERATURE=0
```

## Mock 结构化抽取

Stage 3 提供稳定的 Mock 模式，用于在不调用任何外部或本地大语言模型的情况下验证结构化输入层。

Fixture 数据位于：

```text
data/fixtures/extracted/
```

这些 JSON 全部为虚构、脱敏后的结构化候选人数据，用途是：

- 验证 `candidate_extraction.schema.json` 的 JSON Schema Draft 2020-12 约束；
- 验证 Pydantic v2 数据模型能够读取结构化结果；
- 验证每个评分事实能追溯到 `evidence_id` 和 `quote`；
- 为后续 Stage 4 评分引擎提供稳定输入。

MockExtractor 校验流程：

1. 根据 `document_id`、fixture 文件名或 `candidate_id` 加载 JSON；
2. 运行 JSON Schema 校验；
3. 运行 Pydantic 校验；
4. 运行 evidence link 完整性检查；
5. 返回 `CandidateExtraction` 对象。

运行 Mock 抽取演示：

```bash
python scripts/run_mock_extraction_demo.py
```

演示脚本只输出安全摘要，包括候选人编号、推荐领域、工作经历数量、成果事件数量、证据数量和校验状态，不打印任何敏感信息字段。

运行真实抽取链路演示：

```bash
python scripts/run_llm_extraction_demo.py
```

如果未配置 Ollama 或兼容 API，该脚本会安全回退到 mock，不会因为缺少模型而失败。

## 六领域评分引擎

Stage 4 实现确定性评分，不调用任何大语言模型。权重来自 `config/domain_weights.yaml`，加载时会校验每个领域十项一级指标权重之和必须为 `1.0`。

核心指标：

- `BCS`：基础竞争力分，按目标领域权重聚合十项一级指标。
- `ECI`：证据可信度指数，衡量量化证据、可追溯性、完整性、一致性和可核验性。
- `Penalty`：处罚项，处理普通日期矛盾、明显全职重叠、成果无法对应证据等问题，上限 8 分。
- `RankScore`：最终排序分。

公式：

```text
BCS = sum(domain_weight[axis] * axis_score[axis])

ECI =
0.30 * quantified_evidence_score
+ 0.25 * traceability_score
+ 0.20 * completeness_score
+ 0.15 * consistency_score
+ 0.10 * verifiability_score

RankScore = BCS * (0.85 + 0.15 * ECI / 100) - Penalty
```

十项一级指标：

```text
education, match, experience, stability, progression,
platform, management, competency, achievement, collaboration
```

缺失字段不会直接判零分。缺失下属人数、成果数字或部分日期时，相关轴使用中性基线或保守计算，同时通过 ECI 和风险提示体现“证据不足，建议进一步核验”。

运行评分演示：

```bash
python scripts/run_scoring_demo.py --domain hr
python scripts/run_scoring_demo.py --domain production
python scripts/export_demo_ranking_json.py
```

排序结果保存到：

```text
data/outputs/rankings/
```

## 公平性、稳定性与时间线审计

Stage 7 在不改变评分权重和主排名公式的前提下，对排序结果进行审计解释。

为什么需要公平性审计：

- 主排名始终基于脱敏后的结构化数据；
- 姓名、性别、年龄、出生日期、婚姻、家庭情况、籍贯、薪资不得进入主评分；
- 敏感字段只用于验证隔离是否有效，不用于重新评分；
- 确定性评分反事实测试中，只改变 `gender`、`birth_year`、`marital_status`、`salary_current`、`salary_expected`，教育、工作、项目、成果和证据保持不变；
- 如果 RankScore 或排名发生变化，应视为配置泄露或评分 bug。

稳定性审计用于评估系统是否过度依赖简历包装方式。系统比较 `full_text`、`fact_only_text`、`compressed_text` 三种等价表达下的排序，输出 Top-K consistency、mean rank shift、max rank shift 和 score stability。审计结果只用于提示风险，不反向修改主排名。

时间线一致性审计检查：

- 工作经历日期是否合法；
- 无法解释的全职任职重叠；
- 同公司晋升或岗位调整不视为跳槽异常；
- 顾问、兼职、项目制不直接视为严重重叠；
- 项目日期是否落在任职期间；
- 概要年限与经历计算年限是否差异过大。

运行审计演示：

```bash
python scripts/run_timeline_audit_demo.py
python scripts/run_fairness_audit_demo.py
python scripts/run_robustness_audit_demo.py
```

审计结果保存到：

```text
data/outputs/audit_reports/
```

## 启动 FastAPI

首次运行前初始化 SQLite 数据库：

```bash
python scripts/init_database.py
```

数据库默认写入：

```text
data/evitalent.db
```

数据库只保存文档路径、脱敏文本路径、候选人编号和排序结果路径，不保存未脱敏正文、真实姓名、手机号、婚姻或薪资。

启动后端：

```bash
uvicorn evitalent.api.main:app --reload --port 8000
```

主要接口：

- `GET /api/v1/health`
- `POST /api/v1/resumes/upload`
- `POST /api/v1/resumes/{document_id}/parse`
- `POST /api/v1/resumes/{document_id}/extract`
- `GET /api/v1/fixtures`
- `POST /api/v1/rankings`
- `GET /api/v1/rankings/{ranking_id}`
- `GET /api/v1/reports/{ranking_id}`

真实上传文件需要先调用 parse 完成脱敏，再调用 extract。`POST /api/v1/rankings` 支持 `mode=mock` 和 `mode=extracted`；`mode=extracted` 只读取已经通过 Schema、Pydantic、证据链接和敏感复核的结构化结果，不会重新调用 LLM 生成分数。

## 启动 Streamlit

```bash
streamlit run app/streamlit_app.py
```

页面包括：

- 首页：项目概览、六领域说明和技术流程；
- 简历上传与脱敏预览：批量上传 DOCX/PDF，只显示脱敏文本；
- 结构化抽取：在脱敏后选择 Mock、本地 Ollama 或兼容 API，并展示安全摘要；
- Mock 排名演示：选择领域和候选人，生成 BCS、ECI、Penalty、RankScore；
- 候选人详情：雷达图、指标卡、特征摘要、证据卡片、成果事件和职业时间线；
- 方法说明：权重、公式、缺失值处理和敏感字段隔离原则；
- 报告导出：生成 HTML 排名报告。

Mock 排名演示步骤：

1. 进入 Streamlit 的“Mock 排名演示”页面；
2. 选择领域，例如“人力资源”或“生产”；
3. 选择至少一名候选人，推荐 HR 和 production 使用 3 名候选人演示排序；
4. 点击“生成排名”；
5. 在排名表、RankScore 柱状图、BCS/ECI 对比图和“候选人详情”页面查看解释结果。

页面截图可在完成竞赛材料整理时放入 `data/outputs/html_reports/` 或单独的展示目录；当前仓库预留说明，不提交真实简历截图。

## 放入真实简历

1. 将 DOCX/PDF/TXT 简历放入 `data/raw/`。
2. 运行批处理脱敏：

```bash
python scripts/batch_process_resumes.py
```

3. 脱敏文本会保存到 `data/redacted/`。
4. Stage 5 中真实简历仅可用于脱敏预览；结构化抽取和评分需要等 Stage 6 接入 LLM 或人工结构化结果后再执行。

## DOCX/PDF 解析与脱敏

V1 支持：

- DOCX 解析：读取普通段落和表格内容，适配简历中常见的表格式个人信息、教育经历和工作经历。
- 文本型 PDF 解析：使用 `pypdf` 提取可复制文本。
- 扫描型 PDF：当前不支持 OCR。若 PDF 提取文本为空或过少，系统会提示“PDF 可能为扫描件，V1 当前不支持 OCR，请转换为可复制文本的 PDF 或 DOCX。”

路径约定：

- 原始真实简历：`data/raw/`，该目录已被 `.gitignore` 排除。
- 虚构演示简历：`data/fixtures/source_documents/`。
- 脱敏输出：`data/redacted/`。

运行脱敏演示：

```bash
python scripts/generate_demo_resume_files.py
python scripts/run_redaction_demo.py
```

演示脚本只输出文件名、解析状态、敏感字段类别数量、脱敏文件路径和脱敏后的安全预览，不打印原始手机号、邮箱、薪资等敏感值。

## 运行测试

```bash
pytest -q
```

如果本机 Anaconda 环境中存在第三方 pytest 插件导致启动卡住，可临时禁用外部插件：

Windows PowerShell:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; pytest -q
```

Linux/macOS:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
```

## 当前限制

- V1 是证据驱动排序系统，不等同最终录用决策。
- 销售、研发权重暂为模板，后续需基于更多样例和专家标注校准。
- 大模型抽取仍需要人工抽检。
- Mock 数据用于演示工程链路，不代表真实人才分布。
## 真实本地模型联调验证

普通 `pytest -q` 主要验证规则、Mock 管线和被 mock 的模型调用路径；真实 Ollama 联调必须使用完全虚构的 DOCX 文件，且必须先经过本地解析与脱敏，禁止直接把原始简历正文发送给模型。

Stage 6B 的真实联调脚本固定使用：

- `extraction_mode=local_ollama`
- `provider=local_ollama`
- `model=evitalent-extractor:7b`
- `base_url=http://127.0.0.1:11434`
- `temperature=0`
- `seed=9`

运行连接检查：

```bash
python scripts/check_ollama_connection.py
```

运行三份虚构 DOCX 的端到端联调：

```bash
python scripts/run_real_ollama_docx_e2e_demo.py
```

判断是否真实调用了模型时，查看输出中的 `actual_llm_request_count`、`structure_llm_request_count`、`single_event_llm_request_count`、`total_inference_seconds`、`used_mock_response=false` 和 `used_cached_response=false`。脚本不会打印完整 Prompt、完整模型原始响应、脱敏前正文或虚构敏感字段明文。

可选真实模型集成测试默认不随普通测试运行，需显式开启：

```powershell
$env:RUN_REAL_OLLAMA_TESTS = "true"
python -m pytest -q -m integration tests/integration/test_real_ollama_e2e.py
```

在虚构 DOCX 的真实本地模型验证通过前，不处理真实候选人材料；即使进入真实脱敏简历试跑，也仍然必须遵守“LLM 只解释事实，标准事件类型、方向、评分与排名均由 Python 规则引擎完成”的边界。

## 主办方样本受控分析流程

主办方简历必须放在非 OneDrive 的私有数据目录，例如：

```text
C:\LocalData\EviTalentPrivateData\raw\resumes\
```

代码工程仍保留在仓库目录中，原始文件、脱敏全文、抽取私有结果、证据全文和私有排名结果都只写入 `EVITALENT_PRIVATE_DATA_ROOT` 指向的私有目录，不提交 Git。

建议环境变量：

```powershell
$env:EVITALENT_PRIVATE_DATA_ROOT = "C:\LocalData\EviTalentPrivateData"
$env:RESUME_INPUT_ROOT = "C:\LocalData\EviTalentPrivateData\raw\resumes"
```

首次只运行文件盘点与脱敏 pilot：

```bash
python scripts/audit_official_sample_inventory.py
python scripts/run_official_sample_redaction_pilot.py
```

用户必须人工打开六份 pilot 脱敏文本并确认没有敏感泄露，然后才允许继续：

```bash
python scripts/confirm_official_sample_redaction_review.py --confirm
python scripts/run_official_sample_llm_pilot.py
```

pilot 通过后再执行批处理、固定 V1 排名和安全报告导出：

```bash
python scripts/run_official_sample_batch_extraction.py
python scripts/rank_official_samples_v1.py
python scripts/export_official_sample_safe_report.py
```

如果批处理被中断，使用断点续跑：

```bash
python scripts/run_official_sample_batch_extraction.py --resume
```

所有排名均使用固定 V1 权重，不根据主办方样本修改权重或 RankScore 公式。任何 `failed_redaction`、`failed_safety`、`failed_grounding` 文档不得进入正式排名；结果仅用于赛题分析和辅助评价，不代表最终人才录用结论。

## 面向 HR 使用者的前端工作台

Streamlit 前端已改造为面向招聘专员、HRBP、招聘经理和评委的业务工作台。默认页面使用中文业务语言，不要求使用者理解模型、JSON、Schema、接口或代码模块。

启动方式：

```bash
streamlit run app/streamlit_app.py
```

业务使用步骤：

1. 在“新建分析任务”中填写任务名称、岗位名称，并选择六个评价领域之一。
2. 在“简历导入与隐私检查”中导入 DOCX 简历，或查看主办方样本的脱敏 pilot 状态。
3. 人工确认脱敏文本安全后，才允许进入智能分析流程。
4. 在“分析进度”中查看哪些候选人可纳入比较、哪些需要人工核验。
5. 在“人才排名与对比”中查看匿名排名、综合竞争力指数、能力表现分、材料可信度和风险扣减。
6. 在“候选人详情”中查看核心优势、成果依据状态和待核验事项。
7. 在“报告导出与系统说明”中导出 HTML 分析报告或 CSV 排名摘要。

前端默认不会展示真实姓名、电话、邮箱、出生日期、婚姻或家庭信息、籍贯和详细地址、当前薪资、期望薪资、原始文件名或原始简历全文。页面只展示匿名 `document_id` 或 `candidate_id`，并优先读取安全汇总文件，例如 `inventory_safe_summary.json`、`redaction_pilot_safe_summary.json`、`llm_pilot_safe_summary.json`、`safe_processing_summary.json` 和 `all_domains_safe_summary.json`。

系统会在页面底部和报告中提示：本系统结果基于简历中已披露且可核验的信息，用于辅助评价，不构成最终录用决定。未披露的信息不能视为候选人不具备能力，模型抽取结果仍需要人工核验。

技术验收信息放在默认收起的“技术验收信息”折叠区中。展开后可查看本地智能分析服务状态、是否仅使用脱敏文本、成果依据核验通过率、隐私风险检测数量、推理耗时、是否使用缓存和是否使用 Mock；该区域不会展示 Prompt、JSON、原始模型回复、API key、原始文件路径或私有证据文件路径。

当前限制：

- 销售与研发领域规则仍处于 V1 模板阶段，后续需要更多专家标注校准。
- 模型提取结果仍需人工核验。
- 实际组织应用还需接入权限控制与操作审计。

## 人才分析助手

前端右下角提供“AI 助手”悬浮按钮。点击后会打开“人才分析助手”弹窗，可询问系统使用、评分解释、匿名候选人比较、待核验事项和面试核验建议。助手默认只基于安全匿名分析结果回答，不读取原始简历、不读取原始文件名、不读取身份映射表，也不会输出姓名、电话、邮箱、出生日期、婚姻、薪资、详细地址等敏感信息。

可以询问的问题示例：

- 如何开始一次候选人分析？
- 综合竞争力指数如何计算？
- 解释当前排名前三的主要差异。
- 哪些候选人的材料可信度较高？
- 为某位匿名候选人生成面试核验问题。

助手不会提供的信息：

- 候选人真实身份、联系方式、婚姻家庭、薪资、详细地址；
- 原始文件名或私有文件路径；
- 原始简历全文或未脱敏文本；
- “录用某人”“淘汰某人”等最终决策。

本地助手模型配置示例：

```powershell
$env:ASSISTANT_ENABLED = "true"
$env:ASSISTANT_PROVIDER = "local_ollama"
$env:ASSISTANT_MODEL = "evitalent-extractor:7b"
$env:ASSISTANT_BASE_URL = "http://127.0.0.1:11434"
$env:ASSISTANT_TEMPERATURE = "0.2"
$env:ASSISTANT_SEED = "9"
$env:ASSISTANT_NUM_CTX = "8192"
$env:ASSISTANT_NUM_PREDICT = "1200"
$env:ASSISTANT_TIMEOUT_SECONDS = "180"
$env:ASSISTANT_EMBEDDING_MODEL = "qwen3-embedding:0.6b"
```

手动准备模型：

```bash
ollama pull qwen3-embedding:0.6b
```

创建助手模型别名 `evitalent-assistant:7b` 的 Modelfile：

```text
FROM qwen2.5:7b
PARAMETER temperature 0.2
PARAMETER seed 9
PARAMETER num_ctx 8192
PARAMETER num_predict 1200
```

然后执行：

```bash
ollama create evitalent-assistant:7b -f Modelfile
```

检查模型状态：

```bash
python scripts/check_assistant_models.py
```

构建 fixture 安全索引：

```bash
python scripts/build_safe_assistant_index.py --source fixtures
```

运行安全问答演示：

```bash
python scripts/run_assistant_fixture_demo.py
python scripts/run_assistant_rag_demo.py
```

正式主办方样本索引只能在 official safe results 完成安全批处理后再建立；在此之前，`official_safe_results` 会被拒绝。启动应用：

```bash
streamlit run app/streamlit_app.py
```

数据安全边界：

- AI 助手只基于安全匿名分析结果回答；
- 回答不替代面试、背景调查和录用决策；
- 对未完成安全处理的简历无法提供候选人分析回答；
- 大规模正式部署还需权限、账号与操作审计能力。

## 面试重点分析推荐模块

“面试重点分析推荐”用于把匿名排名结果转化为面试验证重点，帮助 HR 理解候选人为什么值得进一步沟通、哪些成果需要深挖、哪些风险需要核验。该模块不重新评分、不决定录用、不修改六领域权重，也不修改 RankScore 公式。

输入数据来自已脱敏、已结构化、已证据核验的安全结果，包括匿名候选人编号、目标领域、岗位名称、BCS、ECI、Penalty、RankScore、核心优势、风险标签、标准化成果事件、证据编号和安全经历摘要。模块不读取原始 DOCX，不读取未脱敏文本，也不展示真实身份、联系方式、家庭报酬类信息或原始文件标识。

岗位契合条件由 V1 可解释规则识别：结合当前领域权重、高分能力轴、已核验成果事件、核心优势、职责标签和证据可信度，输出 3 到 5 个 `HighFitCondition`。面试重点分析器再生成强项验证、深度追问、成果规模背景、迁移性验证和风险核验等 `InterviewFocusArea`。

问题生成优先使用六领域模板库，按领域和成果类型生成主问题、追问建议、好回答要点和红旗信号。LLM 润色默认关闭；即使开启，也只允许润色问题表达，不得新增简历中不存在的事实，不得改变证据依据。

Safety Guard 会移除包含敏感信息或最终决策表述的问题，避免出现“建议录用”“建议淘汰”等结论。推荐内容仅用于面试辅助，不构成最终录用决定，也不会写回评分结果。

运行 demo：

```bash
python scripts/run_interview_focus_demo.py
```

导出安全推荐：

```bash
python scripts/export_interview_recommendations.py
```
