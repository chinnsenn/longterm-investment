# MarketFlow

一个基于 QQQ/SPY 相对强度和移动平均线的自适应市场趋势跟踪交易系统。

[English Documentation](README.md)

## 功能特点

- 使用 Yahoo Finance API 进行实时市场数据监控
- 动态 QQQ/SPY 轮动策略
- 基于以下因素的自动交易信号：
  - QQQ/SPY 相对强度比率
  - 移动平均线指标（QQQ MA30/MA50，SPY MA50/MA100）
  - 市场趋势确认
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
1. 相对强度比较（QQQ/SPY 比率）
2. 移动平均线确认：
   - QQQ：30日和50日移动平均线
   - SPY：50日和100日移动平均线
3. 市场趋势验证

当产生交易信号时，系统会通过 Bark 和 Telegram 同时发送通知。

## 许可证

MIT 许可证
