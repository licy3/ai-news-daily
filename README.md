# 📰 ai-news-daily

每日自动抓取国际 & 国内 AI 科技资讯，翻译后推送到**微信**（Server酱）和/或**飞书**。

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🌍 国际 AI 资讯 | 每日从 MIT TR、VentureBeat、TechCrunch 等 7 个英文源抓取最多 20 条资讯 |
| 🇨🇳 国内 AI 资讯 | 从机器之心、量子位、36氪等 10 个中文源抓取最多 10 条资讯 |
| 🌐 自动翻译 | 使用腾讯云机器翻译将英文标题、摘要翻译为中文（可选） |
| 📱 微信推送 | 通过 Server酱 推送到微信（可选） |
| 🔔 飞书推送 | 通过飞书自定义机器人 Webhook 推送富文本消息（可选） |
| ⏰ 定时执行 | 每天北京时间 08:00 自动运行（GitHub Actions） |

> 微信和飞书至少配置一个即可运行。

---

## 🚀 快速开始

### 第一步：Fork 本仓库

点击右上角 **Fork**，将仓库复制到你的 GitHub 账号下。

### 第二步：配置 GitHub Secrets

进入你 Fork 后的仓库，依次点击：**Settings → Secrets and variables → Actions → New repository secret**，按下表添加所需的 Secret。

| Secret 名称 | 是否必填 | 说明 |
|-------------|----------|------|
| `FEISHU_WEBHOOK_URL` | 二选一 | 飞书自定义机器人的 Webhook 地址（见下方配置指南） |
| `SERVERCHAN_SENDKEY` | 二选一 | Server酱的 SendKey（微信推送，见下方配置指南） |
| `TENCENT_SECRET_ID` | 可选 | 腾讯云 SecretId（用于英文翻译） |
| `TENCENT_SECRET_KEY` | 可选 | 腾讯云 SecretKey（用于英文翻译） |

> `FEISHU_WEBHOOK_URL` 和 `SERVERCHAN_SENDKEY` 至少填一个，否则脚本会报错退出。翻译功能不填则自动跳过。

### 第三步：手动触发一次验证

进入 **Actions → AI News Daily Push → Run workflow**，点击绿色按钮手动运行，检查日志是否显示推送成功。

---

## 🔔 飞书配置指南

飞书使用**自定义机器人（Custom Bot）**通过 Webhook 接收消息，无需审批，免费使用。

### 1. 创建飞书群组（或使用已有群）

飞书自定义机器人只能添加到**群聊**中，若只想自己接收，可以创建一个只有自己的群。

### 2. 在群中添加自定义机器人

1. 打开目标飞书群，点击右上角 **···** → **设置**
2. 选择 **机器人** → **添加机器人**
3. 选择 **自定义机器人**，填写机器人名称（例如：`AI日报`），点击**添加**
4. 复制生成的 **Webhook 地址**，格式如下：

   ```
   https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

   > ⚠️ **安全提示**：Webhook 地址相当于密码，请勿泄露。建议在飞书机器人设置中开启**签名校验**（本项目当前不使用签名，留空即可正常工作）。

### 3. 将 Webhook 地址保存到 GitHub Secrets

在仓库 **Settings → Secrets and variables → Actions** 中新建：

- **Name**：`FEISHU_WEBHOOK_URL`
- **Secret**：粘贴上一步复制的完整 Webhook 地址

### 4. 验证效果

手动触发 Actions 后，飞书群中将收到如下格式的消息：

```
📰 AI科技日报 (2026-03-16)

🤖 过去24小时：20 条国际资讯，10 条国内资讯
──────────────────────────────
🌍 国际AI科技资讯
1. [OpenAI 发布 o3 模型](https://...)
   EN: OpenAI releases o3 model
   💡 OpenAI 今日正式发布...
   🔗 TechCrunch  🕐 2026-03-16 06:30
...
──────────────────────────────
🇨🇳 国内AI科技资讯
1. [百度文心一言重大更新](https://...)
   💡 百度今日宣布...
   🔗 机器之心  🕐 2026-03-16 07:00
```

---

## 📱 微信推送配置指南（Server酱）

1. 访问 [Server酱官网](https://sct.ftqq.com/) 并用 GitHub 账号登录
2. 点击 **SendKey** → 复制你的 SendKey（格式：`SCT...`）
3. 在手机微信中关注 **方糖** 公众号（Server酱的推送渠道）
4. 将 SendKey 保存到 GitHub Secrets，名称为 `SERVERCHAN_SENDKEY`

---

## 🌐 腾讯云翻译配置指南（可选）

不配置时跳过翻译，国际新闻只显示英文原标题。

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 前往 **访问管理 → API密钥管理** → 新建密钥，获取 `SecretId` 和 `SecretKey`
3. 开通 **机器翻译（TMT）** 服务（每月有免费额度）
4. 将两个值分别保存到 GitHub Secrets：`TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`

---

## ⚙️ GitHub Actions 定时配置

默认每天 UTC 00:00（北京时间 08:00）运行。如需修改，编辑 `.github/workflows/ai_news_push.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'   # UTC 00:00 = 北京时间 08:00
```

> ⚠️ GitHub 对长期无提交的仓库会暂停定时任务。本项目每次运行都会向 `news/` 目录提交一个 Markdown 文件来保持仓库活跃。

---

## 🛠️ 常见问题

**Q: Actions 运行成功但飞书没收到消息？**
- 检查 Webhook 地址是否完整、无多余空格
- 在飞书群设置中确认机器人仍在群内（机器人被移除后 Webhook 失效）
- 查看 Actions 日志中 `飞书消息推送` 一行的输出

**Q: 飞书提示"token不合法"？**
- 重新进入群设置，删除旧机器人后重新创建，复制新的 Webhook 地址

**Q: 推送内容没有中文翻译？**
- 未配置腾讯云密钥时自动跳过翻译，属于正常行为

**Q: GitHub Actions 定时任务停止运行了？**
- 进入 **Actions** 页面，点击工作流名称，查看是否有"This workflow was disabled"提示，点击 **Enable workflow** 重新启用
