#!/usr/bin/env python3
"""
Research Ops 资料抓取脚本
约束: 8秒超时, 1次重试, 失败不阻塞
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
import ssl

# 禁用 SSL 验证（部分站点需要）
ssl._create_default_https_context = ssl._create_unverified_context

TOPICS = {
    "deep_learning": [
        ("PyTorch", "https://pytorch.org", "Deep learning framework"),
        ("TensorFlow", "https://tensorflow.org", "ML platform by Google"),
        ("Hugging Face", "https://huggingface.co", "AI model repository"),
        ("Papers With Code", "https://paperswithcode.com", "ML papers with code"),
        ("ArXiv CS.LG", "https://arxiv.org/list/cs.LG/recent", "Machine learning papers"),
        ("OpenAI Research", "https://openai.com/research", "OpenAI publications"),
        ("DeepMind", "https://deepmind.google/research", "DeepMind research"),
        ("Distill.pub", "https://distill.pub", "ML explanations"),
        ("Fast.ai", "https://fast.ai", "Practical deep learning"),
        ("MIT 6.S191", "https://introtodeeplearning.com", "MIT deep learning course"),
    ],
    "bioinformatics": [
        ("NCBI", "https://ncbi.nlm.nih.gov", "National Center for Biotechnology"),
        ("Ensembl", "https://ensembl.org", "Genome browser"),
        ("UniProt", "https://uniprot.org", "Protein knowledgebase"),
        ("PDB", "https://rcsb.org", "Protein Data Bank"),
        ("Bioconductor", "https://bioconductor.org", "Bioinformatics packages"),
        ("Galaxy Project", "https://galaxyproject.org", "Data analysis platform"),
        ("Kaggle Genomics", "https://kaggle.com/datasets?tags=13204-genomics", "Genomic datasets"),
        ("Broad Institute", "https://broadinstitute.org", "Genomics research"),
        ("EBI", "https://ebi.ac.uk", "European Bioinformatics Institute"),
        ("1000 Genomes", "https://internationalgenome.org", "Human genetic variation"),
    ],
    "computational_theory": [
        ("Complexity Zoo", "https://complexityzoo.net", "Complexity classes reference"),
        ("Stanford Encyclopedia of Philosophy - Logic", "https://plato.stanford.edu/entries/logic-computational", "Computational logic"),
        ("MIT OCW Algorithms", "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011", "Algorithm course"),
        ("TAOCP", "https://www-cs-faculty.stanford.edu/~knuth/taocp.html", "Knuth's algorithms"),
        ("ECCC", "https://eccc.weizmann.ac.il", "Electronic Colloquium on Computational Complexity"),
        ("CS Theory StackExchange", "https://cstheory.stackexchange.com", "Theory Q&A"),
        ("Lambda Calculus", "https://plato.stanford.edu/entries/lambda-calculus", "Lambda calculus"),
        ("Type Theory", "https://homotopytypetheory.org", "Homotopy type theory"),
        ("Coq Proof Assistant", "https://coq.inria.fr", "Formal proof management"),
        ("Isabelle/HOL", "https://isabelle.in.tum.de", "Proof assistant"),
    ]
}

def check_url(url, timeout=8):
    """检查 URL 可访问性，8秒超时"""
    headers = {'User-Agent': 'Mozilla/5.0 (ResearchOps/1.0)'}
    req = urllib.request.Request(url, headers=headers, method='HEAD')
    
    for attempt in range(2):  # 原始请求 + 1次重试
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {
                    "accessible": True,
                    "status": resp.getcode(),
                    "attempts": attempt + 1
                }
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307, 308):  # 重定向视为成功
                return {"accessible": True, "status": e.code, "attempts": attempt + 1}
            if attempt == 0:
                time.sleep(1)
                continue
            return {"accessible": False, "error": f"HTTP {e.code}", "attempts": attempt + 1}
        except Exception as e:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"accessible": False, "error": str(e)[:50], "attempts": attempt + 1}
    
    return {"accessible": False, "error": "Max retries exceeded", "attempts": 2}

def main():
    results = {}
    failed_urls = []
    
    for topic, sources in TOPICS.items():
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 处理主题: {topic}")
        topic_results = []
        
        for name, url, desc in sources:
            print(f"  检查: {name}...", end=" ", flush=True)
            check = check_url(url)
            
            entry = {
                "title": name,
                "url": url,
                "description": desc,
                "topic": topic,
                "date_added": datetime.now().isoformat(),
                "accessibility": check
            }
            
            if check["accessible"]:
                print(f"✅ ({check.get('status', 'OK')})")
            else:
                print(f"❌ ({check.get('error', 'FAIL')})")
                failed_urls.append({"name": name, "url": url, "reason": check.get("error", "Unknown")})
            
            topic_results.append(entry)
            time.sleep(0.5)  # 礼貌延迟
        
        results[topic] = topic_results
    
    # 保存 JSON
    with open("sources/raw_fetched.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 生成 Markdown
    md_content = "# Research Sources Database\n\nGenerated: " + datetime.now().isoformat() + "\n\n"
    total_ok = 0
    total_fail = 0
    
    for topic, entries in results.items():
        md_content += f"## {topic.replace('_', ' ').title()}\n\n"
        ok_count = sum(1 for e in entries if e["accessibility"]["accessible"])
        fail_count = len(entries) - ok_count
        total_ok += ok_count
        total_fail += fail_count
        
        md_content += f"*Accessible: {ok_count}/{len(entries)}*\n\n"
        
        for entry in entries:
            status = "✅" if entry["accessibility"]["accessible"] else "❌"
            md_content += f"- {status} [{entry['title']}]({entry['url']}) - {entry['description']}\n"
        md_content += "\n"
    
    md_content += f"\n---\n**Summary**: {total_ok} accessible, {total_fail} failed\n"
    
    with open("sources/SOURCES.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # 保存失败记录
    with open("sources/failed_urls.json", "w", encoding="utf-8") as f:
        json.dump(failed_urls, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"完成! 总计: {total_ok} 成功, {total_fail} 失败")
    print(f"输出: sources/raw_fetched.json, sources/SOURCES.md")
    print(f"失败记录: sources/failed_urls.json")

if __name__ == "__main__":
    main()
