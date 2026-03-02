#!/usr/bin/env python3
"""
复现性预检 - Round 2
"""
import json
from datetime import datetime

def analyze_repro(entry):
    url = entry["url"].lower()
    title = entry["title"].lower()
    tags = [t.lower() for t in entry.get("tags", [])]
    
    analysis = {
        "code_available": False,
        "data_public": False,
        "license": "Unknown",
        "repro_difficulty": "Unknown",
        "risks": []
    }
    
    # GitHub/GitLab → 代码公开
    if "github.com" in url or "gitlab" in url:
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["license"] = "Check repo LICENSE file"
        analysis["repro_difficulty"] = "Low-Medium"
        analysis["risks"].append("Dependency management (requirements.txt/setup.py)")
    
    # 框架/工具官方站点
    elif any(x in url for x in ["pytorch.org", "keras.io", "jax", "mlflow", "wandb"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["license"] = "Open Source (Apache/BSD/MIT)"
        analysis["repro_difficulty"] = "Low"
        analysis["risks"].append("Well maintained, good documentation")
    
    # 学术会议/论文
    elif any(x in url for x in ["neurips.cc", "openreview.net", "arxiv.org"]):
        analysis["code_available"] = "Paper-dependent"
        analysis["data_public"] = "Paper-dependent"
        analysis["license"] = "Varies"
        analysis["repro_difficulty"] = "Medium-High"
        analysis["risks"].append("Code may not be released")
        analysis["risks"].append("Data access restricted")
    
    # 课程材料
    elif any(x in url for x in [".edu", "course", "cs231n", "cs285"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["license"] = "Educational Use"
        analysis["repro_difficulty"] = "Low"
        analysis["risks"].append("Assignments may have solutions withheld")
    
    # 生物数据库
    elif any(x in url for x in ["ncbi", "ebi.ac.uk", "genome.ucsc", "gtexportal"]):
        analysis["code_available"] = False  # 这些是服务
        analysis["data_public"] = True
        analysis["license"] = "Public Domain/CC0"
        analysis["repro_difficulty"] = "Low"
        analysis["risks"].append("API rate limits apply")
        analysis["risks"].append("Large data downloads")
    
    # 生物信息学工具
    elif any(x in tags for x in ["tool", "single-cell"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["license"] = "GPL/Artistic License (check repo)"
        analysis["repro_difficulty"] = "Medium"
        analysis["risks"].append("R/Python dependency conflicts")
        analysis["risks"].append("Bioconductor version compatibility")
    
    # 定理证明器/形式化验证
    elif any(x in tags for x in ["prover", "theorem", "verification", "solver"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["license"] = "Open Source (BSD/MIT)"
        analysis["repro_difficulty"] = "Medium-High"
        analysis["risks"].append("Steep learning curve")
        analysis["risks"].append("Proof scripts require expertise")
    
    # 编程语言
    elif "language" in tags:
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["license"] = "Open Source"
        analysis["repro_difficulty"] = "Low-Medium"
        analysis["risks"].append("Compiler/interpreter setup required")
    
    return analysis

def main():
    with open("sources/round2_raw.json", "r") as f:
        data = json.load(f)
    
    enriched = {}
    stats = {"low": 0, "medium": 0, "high": 0}
    
    for topic, entries in data.items():
        enriched[topic] = []
        for entry in entries:
            repro = analyze_repro(entry)
            entry["reproducibility_notes"] = repro
            enriched[topic].append(entry)
            
            diff = repro["repro_difficulty"].lower()
            if "low" in diff and "medium" not in diff:
                stats["low"] += 1
            elif "high" in diff:
                stats["high"] += 1
            else:
                stats["medium"] += 1
    
    # 保存
    with open("sources/round2_enriched.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    
    # 生成报告
    report = f"""# Reproducibility Analysis - Round 2

Generated: {datetime.now().isoformat()}

## Distribution

| Difficulty | Count |
|------------|-------|
| Low | {stats['low']} |
| Medium | {stats['medium']} |
| High | {stats['high']} |

## Details

"""
    for topic, entries in enriched.items():
        report += f"### {topic.replace('_', ' ').title()}\n\n"
        for e in entries:
            r = e["reproducibility_notes"]
            report += f"**{e['title']}**\n"
            report += f"- Code: {r['code_available']} | Data: {r['data_public']} | License: {r['license']}\n"
            report += f"- Difficulty: {r['repro_difficulty']}\n"
            report += f"- Risks: {', '.join(r['risks'])}\n\n"
    
    with open("repro/REPRODUCIBILITY_ROUND2.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 复现性分析完成")
    print(f"   Low: {stats['low']}, Medium: {stats['medium']}, High: {stats['high']}")

if __name__ == "__main__":
    main()
