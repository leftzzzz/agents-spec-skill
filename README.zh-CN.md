# agents-spec

[English](README.md) | **简体中文**

`agents-spec` 是一个可跨 Agent 使用的 [Agent Skill](https://agentskills.io/)，用于审计和整理共享 Agent 指令、工程 Specs、需求文档与技术决策。

源代码：[github.com/leftzzzz/agents-spec-skill](https://github.com/leftzzzz/agents-spec-skill)

仓库只维护一份权威 Skill：`skills/agents-spec/SKILL.md`。Codex、Claude Code、Cursor、GitHub Copilot、OpenCode 及其他兼容 Agent 均加载这份 Skill；各平台清单只负责发现和安装，不复制 Skill 内容。

## 中文支持

Skill 支持中文提示词和中文仓库。Skill 的内部指令使用英文以保持跨平台行为一致，但你可以直接用中文描述任务。

## 一键安装

安装命令依赖 Node.js 22.20 或更高版本，这是当前 [`skills` CLI](https://github.com/vercel-labs/skills) 的运行要求。

下面的命令均为全局安装，执行一次后可在该 Agent 的所有项目中使用。请选择你正在使用的平台，复制对应的一条命令执行即可。

### Cursor

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent cursor --global --yes
```

### Claude Code

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent claude-code --global --yes
```

### Codex

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent codex --global --yes
```

### GitHub Copilot

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent github-copilot --global --yes
```

### OpenCode

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec --agent opencode --global --yes
```

### 交互式选择其他 Agent

不指定 `--agent` 时，安装器会检测已支持的 Agent，并让你选择安装目标与安装范围：

```bash
npx --yes skills add leftzzzz/agents-spec-skill --skill agents-spec
```

以上单平台命令中的 `--global` 表示全局安装，`--yes` 表示无需交互确认。如需仅在当前项目安装，请先进入项目根目录，再执行对应命令并删除 `--global` 参数。

也可以从本地检出的仓库试装：

```bash
npx --yes skills add ./agents-spec-skill --skill agents-spec
```

手动安装时，将完整的 `skills/agents-spec/` 目录复制到对应位置：

| Agent | 项目级目录 | 全局目录 |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.codex/skills/` |
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| GitHub Copilot | `.agents/skills/` | `~/.copilot/skills/` |
| OpenCode | `.agents/skills/` | `~/.config/opencode/skills/` |

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
