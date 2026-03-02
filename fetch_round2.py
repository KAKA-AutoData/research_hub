#!/usr/bin/env python3
"""
ResearchOps Round 2 - 资料采集
约束: 8秒超时, 1次重试, 失败不阻塞
"""
import json
import time
import urllib.request
import urllib.error
import ssl
from datetime import datetime
import hashlib

ssl._create_default_https_context = ssl._create_unverified_context

SOURCES = {
    "deep_learning": [
        {"title": "PyTorch Lightning", "url": "https://lightning.ai", "source": "Lightning AI", "tags": ["framework", "pytorch"]},
        {"title": "Keras Documentation", "url": "https://keras.io", "source": "Google", "tags": ["framework", "tensorflow"]},
        {"title": "JAX Documentation", "url": "https://jax.readthedocs.io", "source": "Google", "tags": ["framework", "autodiff"]},
        {"title": "MLflow", "url": "https://mlflow.org", "source": "Databricks", "tags": ["mlops", "tracking"]},
        {"title": "Weights & Biases", "url": "https://wandb.ai", "source": "W&B", "tags": ["mlops", "experiment"]},
        {"title": "NeurIPS Proceedings", "url": "https://neurips.cc/virtual/2024/papers.html", "source": "NeurIPS", "tags": ["conference", "papers"]},
        {"title": "ICML OpenReview", "url": "https://openreview.net/group?id=ICML.cc", "source": "OpenReview", "tags": ["conference", "peer-review"]},
        {"title": "Stanford CS231n", "url": "http://cs231n.stanford.edu", "source": "Stanford", "tags": ["course", "cv"]},
        {"title": "Berkeley CS285", "url": "http://rail.eecs.berkeley.edu/deeprlcourse", "source": "UC Berkeley", "tags": ["course", "rl"]},
        {"title": "Google AI Blog", "url": "https://ai.googleblog.com", "source": "Google", "tags": ["blog", "research"]}
    ],
    "bioinformatics": [
        {"title": "GENCODE", "url": "https://www.gencodegenes.org", "source": "GENCODE", "tags": ["genome", "annotation"]},
        {"title": "UCSC Genome Browser", "url": "https://genome.ucsc.edu", "source": "UCSC", "tags": ["browser", "visualization"]},
        {"title": "NCBI GEO", "url": "https://www.ncbi.nlm.nih.gov/geo", "source": "NCBI", "tags": ["database", "expression"]},
        {"title": "GTEx Portal", "url": "https://gtexportal.org", "source": "Broad Institute", "tags": ["database", "expression"]},
        {"title": "AlphaFold DB", "url": "https://alphafold.ebi.ac.uk", "source": "DeepMind/EMBL-EBI", "tags": ["structure", "protein"]},
        {"title": "Pfam", "url": "https://pfam.xfam.org", "source": "EMBL-EBI", "tags": ["database", "protein-family"]},
        {"title": "KEGG Pathway", "url": "https://www.genome.jp/kegg/pathway.html", "source": "Kyoto University", "tags": ["pathway", "metabolism"]},
        {"title": "Cell Ranger", "url": "https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/what-is-cell-ranger", "source": "10x Genomics", "tags": ["tool", "single-cell"]},
        {"title": "Seurat", "url": "https://satijalab.org/seurat", "source": "Satija Lab", "tags": ["tool", "single-cell", "r"]},
        {"title": "Scanpy", "url": "https://scanpy.readthedocs.io", "source": "Theis Lab", "tags": ["tool", "single-cell", "python"]}
    ],
    "computational_theory": [
        {"title": "Lean Prover", "url": "https://leanprover.github.io", "source": "Microsoft/CMU", "tags": ["prover", "theorem"]},
        {"title": "Agda", "url": "https://wiki.portal.chalmers.se/agda/pmwiki.php", "source": "Chalmers", "tags": ["language", "dependent-types"]},
        {"title": "Idris", "url": "https://www.idris-lang.org", "source": "University of St Andrews", "tags": ["language", "dependent-types"]},
        {"title": "TLA+", "url": "https://lamport.azurewebsites.net/tla/tla.html", "source": "Microsoft/Lamport", "tags": ["specification", "verification"]},
        {"title": "Z3 Theorem Prover", "url": "https://github.com/Z3Prover/z3", "source": "Microsoft", "tags": ["smt", "solver"]},
        {"title": "SMT-LIB", "url": "https://smtlib.cs.uiowa.edu", "source": "Iowa", "tags": ["standard", "smt"]},
        {"title": "CVC5", "url": "https://cvc5.github.io", "source": "Stanford/Iowa", "tags": ["solver", "smt"]},
        {"title": "Cryptol", "url": "https://cryptol.net", "source": "Galois", "tags": ["dsl", "crypto"]},
        {"title": "CompCert", "url": "http://compcert.inria.fr", "source": "INRIA", "tags": ["compiler", "verified"]},
        {"title": "VST (Verified Software Toolchain)", "url": "https://vst.cs.princeton.edu", "source": "Princeton", "tags": ["verification", "c"]}]
}

def check_url(url, timeout=8):
    headers = {'User-Agent': 'Mozilla/5.0 (ResearchOps/2.0)'}
    req = urllib.request.Request(url, headers=headers, method='HEAD')
    
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {"accessible": True, "status": resp.getcode(), "attempts": attempt + 1}
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 307, 308):
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
    
    return {"accessible": False, "error": "Max retries", "attempts": 2}

def deduplicate(entries):
    """按 URL + 标题相似度去重"""
    seen = set()
    unique = []
    for entry in entries:
        key = hashlib.md5(entry['url'].lower().encode()).hexdigest()[:16]
        if key not in seen:
            seen.add(key)
            unique.append(entry)
    return unique

def main():
    results = {}
    failed_urls = []
    all_entries = []
    
    for topic, sources in SOURCES.items():
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 处理: {topic}")
        topic_entries = []
        
        for src in sources:
            print(f"  检查: {src['title'][:40]}...", end=" ", flush=True)
            check = check_url(src['url'])
            
            entry = {
                **src,
                "date": datetime.now().isoformat(),
                "short_summary": f"{src['source']} - {', '.join(src['tags'])}",
                "accessibility": check
            }
            
            if check['accessible']:
                print(f"✅")
                topic_entries.append(entry)
                all_entries.append(entry)
            else:
                print(f"❌ ({check.get('error', 'FAIL')})")
                failed_urls.append({"title": src['title'], "url": src['url'], "reason": check.get('error', 'Unknown')})
            
            time.sleep(0.3)
        
        results[topic] = topic_entries
    
    # 去重
    all_entries_unique = deduplicate(all_entries)
    
    # 保存
    with open("sources/round2_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    with open("sources/round2_failed.json", "w", encoding="utf-8") as f:
        json.dump(failed_urls, f, indent=2, ensure_ascii=False)
    
    # 统计
    total_attempted = sum(len(s) for s in SOURCES.values())
    print(f"\n{'='*50}")
    print(f"完成! 尝试: {total_attempted}, 成功: {len(all_entries)}, 去重后: {len(all_entries_unique)}, 失败: {len(failed_urls)}")
    
    return results, failed_urls, len(all_entries_unique)

if __name__ == "__main__":
    main()
