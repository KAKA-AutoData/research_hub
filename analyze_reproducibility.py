#!/usr/bin/env python3
"""
可复现性分析 - 基于 URL 模式推断
"""
import json
from datetime import datetime

def analyze_reproducibility(entry):
    """分析单个来源的可复现性"""
    url = entry["url"].lower()
    title = entry["title"].lower()
    
    analysis = {
        "code_available": False,
        "data_public": False,
        "run_barrier": "Unknown",
        "risk_notes": []
    }
    
    # GitHub/GitLab 代码仓
    if "github.com" in url or "gitlab" in url:
        analysis["code_available"] = True
        analysis["data_public"] = True  # 通常开源项目数据也公开
        analysis["run_barrier"] = "Low-Medium"
        analysis["risk_notes"].append("Requires git clone + dependency install")
    
    # 论文/学术站点
    elif any(x in url for x in ["arxiv.org", "biorxiv", "medrxiv"]):
        analysis["code_available"] = "Check paper"  # 需要查看论文是否有代码
        analysis["data_public"] = "Check paper"
        analysis["run_barrier"] = "Medium-High"
        analysis["risk_notes"].append("Academic code may be unmaintained")
        analysis["risk_notes"].append("Data access varies by study")
    
    # 数据集平台
    elif any(x in url for x in ["kaggle.com", "huggingface.co/datasets"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["run_barrier"] = "Low"
        analysis["risk_notes"].append("May require platform account")
    
    # 课程/教育
    elif any(x in url for x in ["ocw.mit.edu", "course", "fast.ai"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["run_barrier"] = "Low"
        analysis["risk_notes"].append("Educational resources, well documented")
    
    # 数据库/API
    elif any(x in url for x in ["ncbi", "ensembl", "uniprot", "ebi", "rcsb"]):
        analysis["code_available"] = False  # 这些是服务
        analysis["data_public"] = True
        analysis["run_barrier"] = "Low"
        analysis["risk_notes"].append("Web API/service, not downloadable code")
        analysis["risk_notes"].append("May have rate limits")
    
    # 研究机构
    elif any(x in url for x in ["openai.com", "deepmind", "broadinstitute"]):
        analysis["code_available"] = "Varies"
        analysis["data_public"] = "Varies"
        analysis["run_barrier"] = "Medium"
        analysis["risk_notes"].append("Corporate research, partial code release")
    
    # 工具/框架
    elif any(x in title for x in ["pytorch", "tensorflow", "coq", "isabelle"]):
        analysis["code_available"] = True
        analysis["data_public"] = True
        analysis["run_barrier"] = "Low"
        analysis["risk_notes"].append("Production tools, well maintained")
    
    # 默认
    else:
        analysis["risk_notes"].append("Manual review needed")
    
    return analysis

def main():
    with open("sources/raw_fetched.json", "r") as f:
        data = json.load(f)
    
    enriched = {}
    repro_summary = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    
    for topic, entries in data.items():
        enriched[topic] = []
        for entry in entries:
            if entry["accessibility"]["accessible"]:
                repro = analyze_reproducibility(entry)
                entry["reproducibility"] = repro
                enriched[topic].append(entry)
                
                barrier = repro["run_barrier"].lower()
                if "low" in barrier and "medium" not in barrier:
                    repro_summary["low"] += 1
                elif "high" in barrier:
                    repro_summary["high"] += 1
                elif "medium" in barrier:
                    repro_summary["medium"] += 1
                else:
                    repro_summary["unknown"] += 1
    
    # 保存增强数据
    with open("sources/enriched_sources.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    
    # 生成可复现性报告
    report = f"""# Reproducibility Analysis Report

Generated: {datetime.now().isoformat()}

## Summary

| Barrier Level | Count |
|--------------|-------|
| Low (Easy to reproduce) | {repro_summary['low']} |
| Medium (Some effort required) | {repro_summary['medium']} |
| High (Significant barriers) | {repro_summary['high']} |
| Unknown | {repro_summary['unknown']} |

## Detailed Analysis by Topic

"""
    
    for topic, entries in enriched.items():
        report += f"### {topic.replace('_', ' ').title()}\n\n"
        for entry in entries:
            r = entry["reproducibility"]
            report += f"**{entry['title']}**\n"
            report += f"- URL: {entry['url']}\n"
            report += f"- Code Available: {r['code_available']}\n"
            report += f"- Data Public: {r['data_public']}\n"
            report += f"- Run Barrier: {r['run_barrier']}\n"
            report += f"- Risks: {', '.join(r['risk_notes'])}\n\n"
    
    with open("repro/REPRODUCIBILITY.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 可复现性分析完成")
    print(f"   输出: sources/enriched_sources.json")
    print(f"   报告: repro/REPRODUCIBILITY.md")
    print(f"   统计: {repro_summary}")

if __name__ == "__main__":
    main()
