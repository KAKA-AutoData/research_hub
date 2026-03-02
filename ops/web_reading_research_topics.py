#!/usr/bin/env python3
"""
ResearchOps Web Reading - 三主题专用执行器
遵循 OpenClaw Web Reading SOP v1.0
"""
import json
import subprocess
import time
from datetime import datetime
from urllib.parse import urlparse
import re

WORKSPACE = "/root/openclaw-workspace/research_hub"
TIMEOUT = 8
MAX_RETRY = 1

def run_cmd(cmd, timeout=TIMEOUT):
    """执行命令，8秒超时，1次重试"""
    for attempt in range(MAX_RETRY + 1):
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "attempt": attempt + 1
            }
        except subprocess.TimeoutExpired:
            if attempt < MAX_RETRY:
                time.sleep(1)
                continue
            return {"success": False, "error": "Timeout", "attempt": attempt + 1}
        except Exception as e:
            if attempt < MAX_RETRY:
                time.sleep(1)
                continue
            return {"success": False, "error": str(e)[:50], "attempt": attempt + 1}

def web_fetch(url, max_chars=12000):
    """使用 web_fetch 抓取网页"""
    cmd = f'openclaw web-fetch "{url}" --max-chars {max_chars} 2>&1'
    return run_cmd(cmd)

def extract_structure(text, url):
    """从文本中提取结构化信息"""
    lines = text.split('\n') if text else []
    
    # 提取标题（第一行或包含特定标记）
    title = lines[0][:100] if lines else "Unknown"
    
    # 提取日期（常见格式）
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{4}/\d{2}/\d{2}',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
    ]
    publish_date = None
    for pattern in date_patterns:
        match = re.search(pattern, text[:2000])
        if match:
            publish_date = match.group()
            break
    
    # 提取关键要点（假设每段是一个要点）
    key_points = []
    for line in lines[1:20]:  # 前20行
        line = line.strip()
        if len(line) > 30 and len(line) < 300:
            key_points.append(line)
        if len(key_points) >= 5:
            break
    
    return {
        "title": title,
        "url": url,
        "publish_date": publish_date or "Unknown",
        "key_points": key_points[:5],
        "evidence": [text[:500]] if text else [],
        "uncertainty": "Auto-extracted, manual review recommended"
    }

def process_topic(topic_name, urls):
    """处理单个主题的 URL 列表"""
    print(f"\n{'='*60}")
    print(f"[Topic] {topic_name}")
    print(f"{'='*60}")
    
    sources = []
    failed = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Fetching: {url[:60]}...")
        
        result = web_fetch(url)
        
        if result["success"] and result["stdout"]:
            structured = extract_structure(result["stdout"], url)
            sources.append(structured)
            print(f"  ✅ Success: {structured['title'][:50]}...")
        else:
            error_msg = result.get('error', result.get('stderr', 'Unknown')[:50])
            failed.append({"url": url, "reason": error_msg})
            print(f"  ❌ Failed: {error_msg}")
        
        time.sleep(0.5)  # 礼貌延迟
    
    return sources, failed

def main():
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    # 三主题候选链接（按可信度排序）
    topics = {
        "deep_learning": [
            "https://pytorch.org/tutorials/",
            "https://www.tensorflow.org/guide",
            "https://huggingface.co/docs/transformers",
            "https://paperswithcode.com/methods",
            "https://distill.pub/2020/"
        ],
        "bioinformatics": [
            "https://www.bioconductor.org/packages/release/BiocViews.html",
            "https://satijalab.org/seurat/articles/get_started.html",
            "https://scanpy.readthedocs.io/en/stable/tutorials.html",
            "https://bioconda.github.io/",
            "https://www.ncbi.nlm.nih.gov/home/documentation/"
        ],
        "computational_theory": [
            "https://leanprover.github.io/theorem_proving_in_lean4/",
            "https://softwarefoundations.cis.upenn.edu/",
            "https://coq.inria.fr/documentation",
            "https://cvc5.github.io/docs/",
            "https://smtlib.cs.uiowa.edu/examples.shtml"
        ]
    }
    
    all_sources = {}
    all_failed = []
    
    # 前置检查
    print("[Pre-check] Gateway health...")
    health = run_cmd("openclaw gateway health", timeout=5)
    if not health["success"]:
        print("❌ Gateway not healthy, aborting")
        return
    print("✅ Gateway OK\n")
    
    # 处理每个主题
    for topic, urls in topics.items():
        sources, failed = process_topic(topic, urls)
        all_sources[topic] = sources
        all_failed.extend([{**f, "topic": topic} for f in failed])
    
    # 保存产物
    output_base = f"{WORKSPACE}/sources/web_reading_{timestamp}"
    
    # sources.json
    with open(f"{output_base}.json", "w", encoding="utf-8") as f:
        json.dump(all_sources, f, indent=2, ensure_ascii=False)
    
    # summary.md
    with open(f"{output_base}_summary.md", "w", encoding="utf-8") as f:
        f.write(f"# Web Reading Summary - {datetime.now().isoformat()}\n\n")
        total = sum(len(s) for s in all_sources.values())
        f.write(f"Total sources: {total}\n\n")
        for topic, sources in all_sources.items():
            f.write(f"## {topic.replace('_', ' ').title()} ({len(sources)})\n\n")
            for s in sources:
                f.write(f"- [{s['title'][:60]}]({s['url']})\n")
            f.write("\n")
    
    # failed_links.md
    with open(f"{output_base}_failed.md", "w", encoding="utf-8") as f:
        f.write(f"# Failed Links - {datetime.now().isoformat()}\n\n")
        f.write(f"Total failed: {len(all_failed)}\n\n")
        for item in all_failed:
            f.write(f"- `{item['url']}` ({item['topic']}): {item['reason']}\n")
    
    # 输出统计
    print(f"\n{'='*60}")
    print("[Summary]")
    print(f"{'='*60}")
    total_success = sum(len(s) for s in all_sources.values())
    total_attempted = sum(len(urls) for urls in topics.values())
    print(f"Success: {total_success}/{total_attempted}")
    print(f"Failed: {len(all_failed)}")
    print(f"Traceability: {(total_success/max(total_attempted,1)*100):.1f}%")
    print(f"\nOutputs:")
    print(f"  - {output_base}.json")
    print(f"  - {output_base}_summary.md")
    print(f"  - {output_base}_failed.md")

if __name__ == "__main__":
    main()
