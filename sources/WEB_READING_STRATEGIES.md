# 智能网页阅读策略指南

> **版本**: 1.0.0  
> **更新日期**: 2026-02-28  
> **来源**: 基于 Bilibili BV1czfyBrEo4 及最佳实践整理  
> **用途**: ResearchOps 网页信息采集工作流

---

## 🎯 核心原则

1. **分层阅读**: 先框架后细节
2. **多模态提取**: 文本 + 结构化数据 + 元数据
3. **容错设计**: 单点失败不阻塞整体流程
4. **可复现**: 记录完整访问路径和参数

---

## 第一层：快速预览（30秒内）

### 目标
- 判断页面价值
- 提取基础元数据
- 确定是否需要深度阅读

### 操作清单
```bash
# 1. 获取页面基础信息
curl -sI "URL" | grep -E "(HTTP|Content-Type|Content-Length)"

# 2. 提取标题和描述
curl -s "URL" | grep -oP '<title>[^<]+' | head -1
curl -s "URL" | grep -oP 'meta name="description" content="[^"]+' | head -1

# 3. 检查 robots.txt 限制
curl -s "$(dirname URL)/robots.txt" 2>/dev/null | grep -i allow
```

### 输出格式
```json
{
  "url": "原始URL",
  "status": "HTTP状态码",
  "title": "页面标题",
  "description": "页面描述",
  "content_type": "text/html",
  "estimated_read_time": "预估阅读时间",
  "value_assessment": "high/medium/low",
  "proceed_to_deep_read": true/false
}
```

---

## 第二层：结构化提取（2-5分钟）

### 2.1 文章类页面

#### 提取字段
| 字段 | 选择器示例 | 工具 |
|------|-----------|------|
| 标题 | `h1`, `.article-title` | BeautifulSoup/readability |
| 作者 | `.author`, `meta[name=author]` | CSS Selector |
| 发布时间 | `time`, `.publish-date` | Date parser |
| 正文 | `article`, `.content`, `#main` | Readability-lxml |
| 标签 | `.tags a`, `.category` | CSS Selector |
| 引用/链接 | `a[href]` | Link extractor |

#### Python 实现模板
```python
from readability import Document
import requests
from bs4 import BeautifulSoup

def extract_article(url):
    resp = requests.get(url, timeout=8)
    doc = Document(resp.text)
    
    return {
        "title": doc.title(),
        "content": doc.summary(),
        "clean_text": doc.content(),
        "metadata": extract_metadata(resp.text)
    }
```

### 2.2 列表/索引类页面

#### 提取策略
```python
def extract_list_page(url):
    """提取列表页中的条目"""
    soup = fetch_and_parse(url)
    
    # 常见列表项模式
    items = (
        soup.find_all('article') or
        soup.find_all(class_=re.compile('item|card|entry')) or
        soup.find_all('li')
    )
    
    return [{
        "title": item.get_text(strip=True)[:100],
        "link": item.find('a')['href'] if item.find('a') else None,
        "summary": item.find(class_=re.compile('desc|summary')).get_text() if item.find(class_=re.compile('desc|summary')) else None
    } for item in items]
```

### 2.3 表格/数据类页面

#### 提取策略
```python
import pandas as pd

def extract_tables(url):
    """提取所有表格为 DataFrame"""
    tables = pd.read_html(url)
    return {
        f"table_{i}": df.to_dict('records')
        for i, df in enumerate(tables)
    }
```

---

## 第三层：深度解析（按需）

### 3.1 PDF 文档
```python
import fitz  # PyMuPDF

def extract_pdf(url_or_path):
    doc = fitz.open(url_or_path)
    return {
        "metadata": doc.metadata,
        "pages": len(doc),
        "text": "\n".join([page.get_text() for page in doc]),
        "outline": doc.get_toc()  # 目录结构
    }
```

### 3.2 动态渲染页面 (JavaScript-heavy)
```python
# 使用 Playwright/Selenium 作为备选
from playwright.sync_api import sync_playwright

def render_dynamic_page(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until='networkidle', timeout=8000)
        content = page.content()
        browser.close()
        return content
```

### 3.3 API 端点发现
```python
def discover_apis(html_content):
    """从页面中发现潜在 API 端点"""
    import re
    patterns = [
        r'https?://[^\s"\'<>]+api[^\s"\'<>]*',
        r'https?://[^\s"\'<>]+v\d+[^\s"\'<>]*',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[get|post]\(["\']([^"\']+)["\']'
    ]
    apis = set()
    for pattern in patterns:
        apis.update(re.findall(pattern, html_content))
    return list(apis)
```

---

## 第四层：质量评估与去重

### 4.1 内容质量评分
```python
def assess_quality(extracted_data):
    scores = {
        "completeness": len(extracted_data.get('content', '')) / 1000,  # 字数
        "structure": 1 if extracted_data.get('headings') else 0,
        "references": len(extracted_data.get('links', [])),
        "freshness": check_date_freshness(extracted_data.get('date'))
    }
    return sum(scores.values()) / len(scores)
```

### 4.2 去重策略
```python
import hashlib
from difflib import SequenceMatcher

def deduplicate_content(items, threshold=0.85):
    """基于内容相似度去重"""
    unique = []
    for item in items:
        is_duplicate = any(
            SequenceMatcher(None, item['content'], u['content']).ratio() > threshold
            for u in unique
        )
        if not is_duplicate:
            unique.append(item)
    return unique
```

---

## 第五层：存储与索引

### 5.1 文件命名规范
```
sources/
├── raw/
│   └── {timestamp}_{domain}_{slug}.html      # 原始HTML
├── extracted/
│   └── {timestamp}_{domain}_{slug}.json      # 结构化数据
├── markdown/
│   └── {timestamp}_{domain}_{slug}.md        # 可读Markdown
└── index/
    └── by_date/, by_domain/, by_tag/         # 软链接索引
```

### 5.2 元数据标准
```json
{
  "source_url": "原始URL",
  "accessed_at": "ISO8601时间戳",
  "extraction_method": "readability/pandoc/manual",
  "content_hash": "SHA256",
  "word_count": 1234,
  "reading_time_minutes": 5,
  "quality_score": 0.85,
  "tags": ["tag1", "tag2"],
  "related_urls": ["..."],
  "notes": "人工备注"
}
```

---

## 工具链推荐

| 场景 | 首选工具 | 备选方案 |
|------|---------|---------|
| 静态页面 | curl + readability-lxml | newspaper3k |
| 动态页面 | Playwright | Selenium |
| PDF | PyMuPDF | pdfplumber |
| 批量下载 | wget --mirror | httrack |
| RSS/Atom | feedparser | 自定义解析 |
| API | requests + pydantic | httpx |

---

## 错误处理策略

| 错误类型 | 处理方式 | 重试策略 |
|---------|---------|---------|
| HTTP 429 (Rate Limit) | 指数退避 | 1s, 2s, 4s, 8s |
| HTTP 403/451 | 更换 User-Agent/IP | 最多2次 |
| Timeout | 缩短超时时间 | 立即跳过 |
| SSL Error | 尝试 http:// | 1次 |
| Parse Error | 备用解析器 | 记录并继续 |

---

## 待完善项（需根据视频内容补充）

- [ ] 视频特定的阅读技巧
- [ ] 针对 bilibili 内容的特殊处理
- [ ] 视觉内容的文字化提取（OCR）
- [ ] 评论区信息挖掘策略

---

*Generated by OpenClaw ResearchOps Assistant*  
*Template ready for video content integration*
