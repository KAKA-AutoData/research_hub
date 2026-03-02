#!/usr/bin/env python3
"""
生成 Codex 可读索引
"""
import json
from datetime import datetime

def main():
    with open("sources/enriched_sources.json", "r") as f:
        data = json.load(f)
    
    # 统计
    total_entries = sum(len(entries) for entries in data.values())
    topics = list(data.keys())
    
    # 生成 manifest.json (机器可读)
    manifest = {
        "version": "1.0.0",
        "generated_at": datetime.now().isoformat(),
        "total_sources": total_entries,
        "topics": topics,
        "topic_counts": {t: len(v) for t, v in data.items()},
        "files": {
            "raw_data": "sources/raw_fetched.json",
            "enriched_data": "sources/enriched_sources.json",
            "sources_markdown": "sources/SOURCES.md",
            "repro_report": "repro/REPRODUCIBILITY.md",
            "index": "INDEX.md",
            "manifest": "manifest.json"
        }
    }
    
    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # 生成 INDEX.md (人类 + Codex 可读)
    index = f"""# Research Hub Index

> Auto-generated for Codex and human readers  
> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Sources | {total_entries} |
| Topics | {len(topics)} |
| Accessible | {total_entries} |

## Topics

"""
    
    for topic in topics:
        count = len(data[topic])
        index += f"- **{topic.replace('_', ' ').title()}**: {count} sources\n"
    
    index += """
## File Structure

```
research_hub/
├── INDEX.md              # This file
├── manifest.json         # Machine-readable manifest
├── sources/
│   ├── SOURCES.md        # Human-readable source list
│   ├── raw_fetched.json  # Raw fetch results
│   ├── enriched_sources.json  # With reproducibility analysis
│   └── failed_urls.json  # Failed fetches
├── repro/
│   └── REPRODUCIBILITY.md  # Reproducibility report
├── notes/                # For research notes (empty)
└── daily/                # Daily reports
```

## Usage for Codex

### Load all sources
```python
import json
with open('sources/enriched_sources.json') as f:
    sources = json.load(f)
```

### Filter by reproducibility
```python
low_barrier = [
    e for topic in sources.values()
    for e in topic
    if 'Low' in e['reproducibility']['run_barrier']
]
```

### Get by topic
```python
dl_sources = sources.get('deep_learning', [])
```

## Source Categories

"""
    
    for topic, entries in data.items():
        index += f"\n### {topic.replace('_', ' ').title()}\n\n"
        index += "| Title | URL | Barrier | Code | Data |\n"
        index += "|-------|-----|---------|------|------|\n"
        
        for entry in entries:
            r = entry["reproducibility"]
            title_short = entry["title"][:30] + "..." if len(entry["title"]) > 30 else entry["title"]
            index += f"| {title_short} | [Link]({entry['url']}) | {r['run_barrier']} | {r['code_available']} | {r['data_public']} |\n"
    
    index += """
---
*This index is auto-generated. Do not edit manually.*
"""
    
    with open("INDEX.md", "w", encoding="utf-8") as f:
        f.write(index)
    
    print("✅ 索引生成完成")
    print("   INDEX.md - 人类可读索引")
    print("   manifest.json - 机器可读清单")

if __name__ == "__main__":
    main()
