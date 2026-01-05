# AnyRouter API 成本监控工具

一个用于实时监控 [AnyRouter](https://anyrouter.top) API 使用成本的 Python 脚本。

## 功能特性

-  自动刷新显示当日 API 使用成本
-  按模型分类统计（Haiku、Sonnet、Opus）
-  彩色进度条可视化显示各模型消耗占比
-  可配置刷新间隔和运行时长

## 系统要求

- Python 3.6+
- 网络连接（需访问 anyrouter.top）

### 依赖库

- `requests` - HTTP 请求库
- `urllib3` - HTTP 客户端（requests 的依赖）

所有依赖已在 `requirements.txt` 中列出，通过 `pip install -r requirements.txt` 安装。

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

- 复制示例配置文件并编辑：

```bash
# Windows
copy config.example.json config.json

# Linux/Mac
cp config.example.json config.json
```

- 完成上一步后，编辑 `config.json`，填写你的 AnyRouter 账号密码：

```json
{
    "_comment": "配置说明: 复制此文件为 config.json 并填写你的账号信息",
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

| 参数               | 说明                                   | 默认值        | 单位 |
| ------------------ | -------------------------------------- | ------------- | ---- |
| `username`         | AnyRouter 账号用户名                   | 必填          | -    |
| `password`         | AnyRouter 账号密码                     | 必填          | -    |
| `refresh_interval` | 数据刷新间隔（每次刷新会重新获取数据） | 240（4分钟）  | 秒   |
| `total_duration`   | 程序总运行时长（超时后自动退出）       | 7200（2小时） | 秒   |

**时间参数示例**：
- `refresh_interval`: 240 = 每 4 分钟刷新一次
- `total_duration`: 7200 = 运行 2 小时后自动退出
- 如需长期运行，可将 `total_duration` 设为较大值（如 86400 = 24小时）

### 输出示例

```
==================================================
[Username] your_username
[Time] 2026-01-03 14:30:00
--------------------------------------------------
总消耗: $1.23

██████████████████████████████████████████████████
┌─────────┬──────────┐
│  模型   │   消耗   │
├─────────┼──────────┤
│ Haiku   │  $0.10   │
│ Sonnet  │  $0.80   │
│ Opus    │  $0.33   │
└─────────┴──────────┘

==================================================
刷新:240s
```

## FAQ

### 登录失败怎么办？

如果出现登录失败，请检查：

1. **用户名密码是否正确**
   - 确认 `config.json` 中的用户名和密码正确

2. **网络连接问题**
   - 确保可以访问 https://anyrouter.top
   - 检查防火墙或代理设置

3. **阿里云 CDN 防护策略更新**
   - AnyRouter 使用阿里云 CDN 防护，映射表可能会更新
   - 程序会自动重试，等待 30 秒后重新登录

### 如何长期运行？

默认运行 2 小时后自动退出。如需长期运行：

```json
{
    "total_duration": 86400  // 24小时 = 86400秒
}
```

或使用系统服务/计划任务定期启动脚本。

### 为什么要定期刷新 Cookie？

AnyRouter 的登录凭证有时效性，程序在每次刷新时会重新登录以获取最新的 Cookie，确保请求不会因凭证过期而失败。


## 免责声明

本工具仅用于个人监控 API ,仅供学习研究使用，请遵守法律法规和平台规则，使用后果自负

## 相关链接

- [AnyRouter 官网](https://anyrouter.top)
- [项目仓库](https://github.com/reznovs/anyrouter-cost-monitor)

