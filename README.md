# AnyRouter API 成本监控工具

一个用于实时监控 [AnyRouter](https://anyrouter.top) API 使用成本的 Python 脚本。

## 功能特性

-  自动刷新显示当日 API 使用成本
-  按模型分类统计（Haiku、Sonnet、Opus）
-  彩色进度条可视化显示各模型消耗占比
- ⏱ 可配置刷新间隔和运行时长

## 系统要求

- Python 3.6+
- 网络连接

## 安装步骤

1. **克隆仓库**

```bash
git clone https://github.com/reznovs/anyrouter-cost-monitor.git
cd anyrouter-cost-monitor
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **配置账号**

编辑 `config.json`，填写你的 AnyRouter 账号密码：

```json
{
    "username": "你的用户名",
    "password": "你的密码",
    "refresh_interval": 240,
    "total_duration": 7200
}
```

## 使用方法

运行脚本：

```bash
python api_cost_monitor.py
```

### 配置说明

| 参数               | 说明                 | 默认值        |
| ------------------ | -------------------- | ------------- |
| `username`         | AnyRouter 账号用户名 | 必填          |
| `password`         | AnyRouter 账号密码   | 必填          |
| `refresh_interval` | 刷新间隔（秒）       | 240（4分钟）  |
| `total_duration`   | 总运行时长（秒）     | 7200（2小时） |

### 输出示例

```
============================================================
[Username] your_username
[Time] 2026-01-03 14:30:00
------------------------------------------------------------
总消耗: $1.23

█████████████████████████████████████████████████
┌─────────┬──────────┐
│  模型   │   消耗   │
├─────────┼──────────┤
│ Haiku   │  $0.10   │
│ Sonnet  │  $0.80   │
│ Opus    │  $0.33   │
└─────────┴──────────┘

============================================================
```

## 免责声明

本工具仅用于个人监控 API ,仅供学习研究使用，请遵守法律法规和平台规则，使用后果自负
