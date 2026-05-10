# 舆澜网城：多网络结构下的多智能体舆论传播仿真系统

本项目基于 Generative Agents / AI Town 思路重构，用于研究不同网络结构下的多智能体舆论传播。系统用复杂网络约束“谁和谁交流”，用传播动力学约束“是否传播、质疑、辟谣或沉默”，用大语言模型结合人设、记忆和社会关系生成具体发言。

## 当前重点

当前版本优先实现并验证：

- 社区网络结构；
- 社区感知加权复杂阈值模型；
- 原版 Stanford 小镇人设、记忆流与对话记忆接入；
- DeepSeek / 本地 OpenAI-compatible 模型对话生成；
- 舆论言论流、个体指标、传播证据与研究报告弹窗。

## 启动方式

```bash
pip install -r requirements.txt
python run_project.py --port 8000
```

打开：

```text
http://127.0.0.1:8000/
```

如需先执行 Django 迁移：

```bash
python run_project.py --migrate
```

## API Key 配置

仓库不会保存真实 API Key。需要调用 DeepSeek 时，请在本机环境变量中配置：

```bash
set DEEPSEEK_API_KEY=你的key
```

如果使用本地模型，可以在后端配置中切换到本地 OpenAI-compatible 服务，例如 Ollama / vLLM。

## 主要目录

```text
environment/frontend_server/
  translator/simulation_core.py        仿真核心、网络生成、传播动力学、人设记忆、LLM 对话
  translator/network_views.py          页面和 API 入口
  templates/network_simulator/index.html
                                      前端可视化界面

generative_agents-main/reverie/backend_server/
  persona/memory_structures/           Stanford 原版记忆结构
  persona/cognitive_modules/           原版认知模块
  persona/prompt_template/             原版 prompt 与 LLM 调用相关代码

实验记录/                              实验说明、校准方式、方法论说明
```

## 研究用途

项目用于探索：

- 不同网络结构如何影响舆论传播；
- 社区内部强化和跨社区桥接如何改变扩散路径；
- 人设、记忆、关系和情绪如何影响智能体发言；
- LLM 生成式智能体如何与传统传播动力学结合；
- 如何为生成式社会仿真提供可解释证据链。

## 注意事项

- 正式实验前建议固定随机种子，并缓存 LLM 输出。
- 不要把真实 API Key、数据库、临时仿真输出上传到仓库。
- 当前社区划分仍以人工设定为主，后续可用 LFR 基准图或真实社交网络数据校准。

