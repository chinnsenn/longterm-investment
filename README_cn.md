# MarketFlow

一个基于 QQQ/SPY 相对强度和移动平均线的自适应市场趋势跟踪交易系统。

[English Documentation](README.md)

## 功能特点

- 使用 Yahoo Finance API 进行实时市场数据监控
- 动态 QQQ/SPY 轮动策略
- 基于以下因素的自动交易信号：
  - QQQ/SPY 相对强度比率
  - 移动平均线指标（QQQ MA30/MA50，SPY MA50/MA100）
  - RSI 超买/超卖指标
  - 市场趋势确认
- **市场恐惧指数**：基于 VIX 波动率指数的市场情绪分析
  - 实时 VIX 数据获取和历史百分位分析
  - 五档恐惧等级：极度恐惧、恐惧、中性、贪婪、极度贪婪
  - VIX 趋势分析和恐惧评分（0-100分）
- 多渠道通知（Bark、Telegram）
- 健壮的错误处理和重试机制
- 高效的数据缓存和存储
- 基于市场时间的智能更新间隔

## 安装

1. 克隆仓库：
```bash
git clone git@github.com:chinnsenn/longterm-investment.git
cd longterm-investment
```

2. 创建并激活虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用: .venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 复制并配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件设置你的配置
```

## 使用方法

运行主程序：
```bash
python main.py
```

## Docker 部署

### 使用 Docker

1. 构建 Docker 镜像：
```bash
docker build -t marketflow .
```

2. 运行容器：
```bash
docker run -d \
  --name marketflow \
  --restart unless-stopped \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data:/app/data \
  marketflow
```

3. 查看日志：
```bash
docker logs -f marketflow
```

### 使用 Docker Compose

1. 启动应用：
```bash
docker compose up -d
```

2. 查看日志：
```bash
docker compose logs -f
```

3. 停止应用：
```bash
docker compose down
```

注意：在构建 Docker 镜像之前，请确保已正确配置 `.env` 文件。

## 配置说明

系统可以通过 `.env` 文件进行配置：
- `BARK_API_KEY`：你的 Bark API 密钥
- `BARK_URL`：Bark 服务器地址
- `TELEGRAM_BOT_TOKEN`：你的 Telegram 机器人令牌
- `TELEGRAM_CHAT_ID`：你的 Telegram 聊天 ID
- `DB_PATH`：SQLite 数据库路径
- `RETRY_INTERVAL`：失败操作重试间隔
- 其他可选设置（参见 `.env.example`）

## 策略详情

系统实现了一个基于以下因素的 QQQ 和 SPY 轮动策略：

### 核心策略组件
1. **相对强度分析**：计算并监控 QQQ/SPY 比率
2. **技术指标确认**：
   - 移动平均线：QQQ MA30/MA50，SPY MA50/MA100
   - RSI 指标：识别超买/超卖状态
   - 趋势确认：确保信号可靠性
3. **市场情绪分析**：
   - VIX 恐慌指数实时监控
   - 历史百分位对比
   - 恐惧等级评估（极度恐惧到极度贪婪）

### 交易逻辑
- 当 QQQ/SPY 比率超过阈值时，倾向持有 QQQ
- 当比率低于阈值且 SPY 位于 40 周均线上方时，倾向持有 SPY
- 切换仓位时必须经过 CASH 状态
- 结合恐惧指数辅助判断市场极端情绪

### 通知系统
当产生交易信号或市场情绪变化时，系统会通过 Bark 和 Telegram 同时发送包含以下信息的通知：
- 策略建议和仓位状态
- 技术指标详情
- 市场恐惧指数和情绪分析

## 许可证

MIT 许可证
