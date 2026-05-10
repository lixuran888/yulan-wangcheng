# 代码结构说明

## 架构

```text
前端交互层
  templates/network_simulator/index.html
    网络画布、结构切换、仿真控制、智能体详情、言论洞察、传播报告

Django API 层
  translator/network_views.py
    state/reset/step/intervention 四类接口

仿真核心层
  translator/simulation_core.py
    NetworkGenerator
    AgentFactory
    SimulationEngine
    AnalysisEngine
```

## 核心模块

### NetworkGenerator

负责生成五类网络拓扑：

- random：陌生人广场
- small_world：熟人圈层
- scale_free：意见领袖平台
- regular：封闭邻里
- community：兴趣部落

### AgentFactory

根据网络结构分配差异化人设，不同网络不会复用同一批智能体分布。每个 Agent 包含人格、角色、状态、立场、情绪、OSI、CPI、记忆等字段。

### SimulationEngine

按时间步推进：

1. 更新 OSI / CPI
2. 为已接触节点计算传播、质疑、辟谣、沉默概率
3. 生成言论记录
4. 沿网络边传播信息
5. 更新情绪、立场、状态
6. 生成动态舆论传播报告

### AnalysisEngine

负责计算网络指标、关键节点、风险社群、情绪趋势、风险等级和干预建议。

## 删除的旧框架

已移除旧 AI Town / Reverie 相关内容：

- 像素地图与移动逻辑
- 专家会议室
- 线上聊天室页面
- Phaser/地图素材
- 嵌套 Reverie 后端
- Selenium、OpenAI、NLP、统计绘图等非 MVP 依赖

当前项目只保留一个轻量 Django Web 壳和纯 Python 仿真核心。
