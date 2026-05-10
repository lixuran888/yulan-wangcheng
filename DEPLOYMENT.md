# 部署说明

## 环境

- Python 3.9 或 3.10
- Django 2.2

## 安装

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 启动

```bash
python run_project.py --port 8000
```

访问：

```text
http://127.0.0.1:8000/
```

## 说明

当前版本不依赖旧地图素材、Reverie 后端、Selenium、外部 LLM API 或真实平台采集接口。所有网络拓扑、智能体状态和分析报告都由本地仿真核心生成。
