# agents-spec

[English](README.md) | **简体中文**

`agents-spec` 是一个可跨 Agent 使用的 [Agent Skill](https://agentskills.io/)，用于审计和整理共享 Agent 指令、工程 Specs、需求文档与技术决策。

源代码：[github.com/leftzzzz/agents-spec-skill](https://github.com/leftzzzz/agents-spec-skill)

仓库只维护一份权威 Skill：`skills/agents-spec/SKILL.md`。所有兼容 Agent 均加载这份 Skill；各平台清单只负责发现和安装，不复制 Skill 内容。

## 中文支持

Skill 支持中文提示词和中文仓库。Skill 的内部指令使用英文以保持跨平台行为一致，但你可以直接用中文描述任务。

## 一键安装

[`npx skills add`](https://github.com/vercel-labs/skills) CLI 会扫描本仓库的 `skills/` 目录。该 CLI 支持的所有 Agent 都使用同一条安装命令，因此 README 不再维护各平台的专用命令清单。

```bash
npx skills add https://github.com/leftzzzz/agents-spec-skill
```

本仓库目前只有一个 Skill。你也可以通过它的**安装名**明确选择；安装名来自 `SKILL.md` frontmatter 中的 `name:` 字段，而不是目录名：

```bash
npx skills add https://github.com/leftzzzz/agents-spec-skill --skill "agents-spec"
```

安装器负责选择 Agent 和安装范围；未来增加新 Agent 时，由安装器自己的支持清单统一更新。

也可以从本地检出的仓库安装：

```bash
npx skills add ./agents-spec-skill
```

如需手动安装，请将完整的 `skills/agents-spec/` 目录复制到目标 Agent 文档指定的 Skill 目录。

## 使用

安装后直接用自然语言提出任务，例如：

```text
使用 agents-spec 审计这个仓库的 Agent 指令和 Spec 索引。
修改文件前，先报告审计结果并给出迁移方案。
```

不同 Agent 的显式 Skill 调用语法可能不同；自然语言调用适用于所有兼容平台。在 Codex 中也可以直接使用 `$agents-spec`。

目标仓库结构如下：

```text
AGENTS.md
docs/
  specs/
    AGENTS.md
  requirements/
    AGENTS.md
  technical/
    AGENTS.md
```

- `docs/specs/` 保存当前生效的工程标准、契约、策略与不变量。
- `docs/requirements/` 保存产品意图、验收条件与产品决策。
- `docs/technical/` 保存架构、实施方案与技术决策。
- 根 `AGENTS.md` 告诉所有 Agent 应在什么情况下读取或搜索各类文档。
- 平台专用指令文件只作为共享根入口的轻量适配层。

## 审计脚本

随 Skill 提供的审计脚本没有第三方运行时依赖。执行只读结构检查：

```bash
python skills/agents-spec/scripts/audit_agents_md.py /path/to/repository --check
```

为 CI 输出 JSON：

```bash
python skills/agents-spec/scripts/audit_agents_md.py /path/to/repository --check --json
```

仅在用户明确要求补充 Claude 兼容入口后执行：

```bash
python skills/agents-spec/scripts/audit_agents_md.py \
  /path/to/repository \
  --fix \
  --add-claude
```

退出码：`0` 表示结构合规，`1` 表示存在结构违规，`2` 表示调用无效或内部失败。

## 跨平台打包

仓库采用开放的 Agent Skills 目录结构：

```text
skills/agents-spec/
  SKILL.md
  LICENSE.txt
  agents/openai.yaml
  scripts/audit_agents_md.py
```

仓库根目录还提供可选的平台原生元数据：

- `.codex-plugin/plugin.json`
- `.claude-plugin/plugin.json`
- `.cursor-plugin/plugin.json`

这些文件都指向同一个 `skills/` 目录。贡献代码时不得增加平台专用的 `SKILL.md` 副本。

## 开发

```bash
python -m unittest discover -s tests -v
ruff check skills tests
ruff format --check skills tests
skills-ref validate skills/agents-spec
python /path/to/plugin-creator/scripts/validate_plugin.py .
npx --yes @anthropic-ai/claude-code@2.1.229 plugin validate .
```

修改 Skill 契约或审计脚本行为前，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

MIT
