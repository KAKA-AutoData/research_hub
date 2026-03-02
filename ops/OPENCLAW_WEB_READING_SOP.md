# OpenClaw 网页阅读 SOP v1.0（实战版）

> **目标**: 稳定抓信息、可复现、失败不阻塞  
> **适用范围**: 网页资料采集、情报跟踪、文档提炼  
> **排除范围**: 账号高风险操作（转账、删帖、改权限）  
> **更新日期**: 2026-03-01

---

## 核心策略

**逐级升级**: `web_fetch` → `web_search+fetch` → `managed browser` → `chrome relay`

**失败策略**: 外网超时 8 秒，最多重试 1 次；仍失败写入 `failed_links`，继续后续任务。

---

## 1) 前置检查（每次任务前 30 秒）

```bash
openclaw gateway health
openclaw channels status --probe
openclaw hooks list
```

- `Gateway Health = OK` 才继续。
- 若要用 `web_search`，先配 key：
  ```bash
  openclaw configure --section web
  ```

---

## 2) 模式选择（决策表）

| 场景 | 工具 | 说明 |
|------|------|------|
| 公开静态网页（文档/博客/公告） | `web_fetch` | 首选，轻量快速 |
| 先找来源再深读 | `web_search` + `web_fetch` | 搜索+提取组合 |
| JS 渲染/点击/滚动/翻页/登录后内容 | `browser` (`openclaw` profile) | 动态页面 |
| 必须复用当前 Chrome 登录态 | `browser` + `chrome` profile | 扩展中继 |

---

## 3) 标准执行流程（8 步）

### Step 1: 收集候选链接
- 先给 5~8 条候选
- 按可信度排序：官方文档 > 论文站 > 技术社区 > 自媒体

### Step 2: 批量浅抓
- 每批 3~5 个链接
- `web_fetch` 提取正文

### Step 3: 正文结构化
每条产出字段：
```json
{
  "title": "标题",
  "url": "链接",
  "publish_date": "发布日期",
  "key_points": ["要点1", "要点2", "..."],
  "evidence": ["证据片段1", "..."],
  "uncertainty": "不确定性说明"
}
```

### Step 4: 自动去重
- URL 去重
- 标题相似度去重（阈值 85%）

### Step 5: 失败回退
- `web_fetch` 失败 → 切 `browser`
- `browser` 失败 → 标记原因并跳过

### Step 6: 证据绑定
- 每条结论必须带 URL
- **无 URL 的句子不进入最终摘要**

### Step 7: 产物落地
- `sources.json`
- `summary.md`
- `failed_links.md`

### Step 8: 验收
统计指标：
- 新增条目数
- 失败数
- 可追溯结论占比（目标 100%）

---

## 4) 三个可直接喂给 OpenClaw 的任务模板

### A. 静态网页快读（web_fetch）

```text
任务：仅使用 web_fetch 抓取以下链接。
规则：
1) extractMode=markdown，maxChars=12000。
2) 超时8秒，失败重试1次，仍失败写 failed_links。
3) 每个链接输出字段：title,url,publish_date,key_points(3-5),evidence_snippets(<=3),uncertainty。
4) 最终输出 sources.json + summary.md + failed_links.md。
```

### B. 先搜再读（web_search+fetch）

```text
任务：先搜索再深读。
步骤：
1) web_search query="<主题>" count=8。
2) 按可信度排序并去重。
3) 对前3条执行 web_fetch 深读。
4) 输出"结论+证据URL"；无URL不允许写结论。
5) 失败按8秒超时+1次重试，继续后续任务。
```

### C. 动态页/登录页（browser）

```text
任务：使用 browser 工具读取 JS/登录页面。
要求：
1) 先 status/start，再 open/snapshot，再 act。
2) 每次关键动作后 snapshot，最终 screenshot。
3) 只做读取与整理，不做高风险变更操作。
4) 输出结构化结果和证据URL，失败写原因并继续。
```

---

## 5) Browser 模式最小命令集

### OpenClaw-managed Browser

```bash
# 检查状态
openclaw browser --browser-profile openclaw status

# 启动浏览器
openclaw browser --browser-profile openclaw start

# 打开页面
openclaw browser --browser-profile openclaw open https://example.com

# 获取快照
openclaw browser --browser-profile openclaw snapshot
```

### Chrome Extension Relay（复用登录态）

```bash
# 安装扩展
openclaw browser extension install

# 查看扩展路径
openclaw browser extension path

# 手动加载：chrome://extensions -> 开发者模式 -> Load unpacked

# 列出已连接标签页
openclaw browser --browser-profile chrome tabs
```

---

## 6) 安全与稳定性基线

| 规则 | 说明 |
|------|------|
| 登录必须手动 | 不要把账号密码喂给模型 |
| 网关保持 loopback + token | 不暴露公网 |
| 禁用高风险 `evaluate` | 除非必须 |
| 浏览器任务设上限 | 单任务最多 N 页，防无限循环 |

---

## 7) 交付标准（验收 5 项）

- [ ] 有 `sources.json`
- [ ] 有 `summary.md`
- [ ] 有 `failed_links.md`
- [ ] 结论全部可追溯 URL
- [ ] 外网失败不阻塞主流程

---

## 参考文档

- [Web Tools](https://docs.openclaw.ai/tools/web)
- [Browser (OpenClaw-managed)](https://docs.openclaw.ai/tools/browser)
- [Chrome Extension](https://docs.openclaw.ai/tools/chrome-extension)
- [Browser Login](https://docs.openclaw.ai/tools/browser-login)
- [Onboarding Wizard](https://docs.openclaw.ai/start/wizard)

---

*Generated from user-provided SOP v1.0*  
*Ready for ResearchOps execution*
