#!/usr/bin/env python3
"""
Research Hub source fetcher.
Policy: parallel check, 8s timeout, 2 attempts per URL, failure-isolated.
"""
import json
import ssl
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

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
    ],
}

MAX_WORKERS = 20
TIMEOUT_SEC = 8


def check_url(url: str, timeout: int = TIMEOUT_SEC) -> dict:
    headers = {'User-Agent': 'Mozilla/5.0 (ResearchOps/parallel-checker)'}
    req = urllib.request.Request(url, headers=headers, method='HEAD')

    last_error = 'unknown'
    started = time.time()
    for attempt in range(1, 3):
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {
                    'accessible': True,
                    'status': resp.getcode(),
                    'attempts': attempt,
                    'elapsed_ms': int((time.time() - started) * 1000),
                    'last_attempt_ms': int((time.time() - t0) * 1000),
                    'error_type': '',
                }
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 307, 308):
                return {
                    'accessible': True,
                    'status': exc.code,
                    'attempts': attempt,
                    'elapsed_ms': int((time.time() - started) * 1000),
                    'last_attempt_ms': int((time.time() - t0) * 1000),
                    'error_type': '',
                }
            last_error = f'HTTP {exc.code}'
            error_type = 'http_error'
        except Exception as exc:
            last_error = str(exc)[:100]
            error_type = 'network_error'

        if attempt == 1:
            time.sleep(0.35)

    return {
        'accessible': False,
        'status': None,
        'attempts': 2,
        'elapsed_ms': int((time.time() - started) * 1000),
        'last_attempt_ms': 0,
        'error': last_error,
        'error_type': error_type,
    }


def make_entry(topic: str, name: str, url: str, desc: str) -> tuple:
    check = check_url(url)
    entry = {
        'title': name,
        'url': url,
        'description': desc,
        'topic': topic,
        'date_added': datetime.now().isoformat(),
        'accessibility': check,
    }
    fail = None
    if not check.get('accessible'):
        fail = {
            'name': name,
            'url': url,
            'reason': check.get('error', 'Unknown'),
            'error_type': check.get('error_type', 'unknown'),
            'attempts': check.get('attempts', 0),
            'elapsed_ms': check.get('elapsed_ms', 0),
        }
    return topic, entry, fail


def main() -> None:
    started = time.time()
    tasks = []
    for topic, sources in TOPICS.items():
        for name, url, desc in sources:
            tasks.append((topic, name, url, desc))

    results = {k: [] for k in TOPICS.keys()}
    failed_urls = []

    print(f"[{datetime.now().strftime('%H:%M:%S')}] parallel source check start, total={len(tasks)}")

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tasks))) as ex:
        futs = [ex.submit(make_entry, *t) for t in tasks]
        for fut in as_completed(futs):
            topic, entry, fail = fut.result()
            results[topic].append(entry)
            ok = entry['accessibility'].get('accessible')
            status = entry['accessibility'].get('status')
            if ok:
                print(f"  ✅ [{topic}] {entry['title']} ({status})")
            else:
                err = entry['accessibility'].get('error', 'FAIL')
                print(f"  ❌ [{topic}] {entry['title']} ({err})")
                if fail:
                    failed_urls.append(fail)

    # keep stable order by title
    for topic in results:
        results[topic] = sorted(results[topic], key=lambda x: x.get('title', ''))

    Path('sources').mkdir(parents=True, exist_ok=True)
    Path('daily').mkdir(parents=True, exist_ok=True)

    Path('sources/raw_fetched.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    Path('sources/failed_urls.json').write_text(json.dumps(failed_urls, indent=2, ensure_ascii=False), encoding='utf-8')

    md_content = "# Research Sources Database\n\nGenerated: " + datetime.now().isoformat() + "\n\n"
    total_ok = 0
    total_fail = 0
    per_topic = {}

    for topic, entries in results.items():
        md_content += f"## {topic.replace('_', ' ').title()}\n\n"
        ok_count = sum(1 for e in entries if e['accessibility'].get('accessible'))
        fail_count = len(entries) - ok_count
        total_ok += ok_count
        total_fail += fail_count
        per_topic[topic] = {'ok': ok_count, 'fail': fail_count, 'total': len(entries)}

        md_content += f"*Accessible: {ok_count}/{len(entries)}*\n\n"
        for entry in entries:
            status = '✅' if entry['accessibility'].get('accessible') else '❌'
            md_content += f"- {status} [{entry['title']}]({entry['url']}) - {entry['description']}\n"
        md_content += "\n"

    md_content += f"\n---\n**Summary**: {total_ok} accessible, {total_fail} failed\n"
    Path('sources/SOURCES.md').write_text(md_content, encoding='utf-8')

    # telemetry / api usage style report
    error_dist = Counter(x.get('error_type', 'unknown') for x in failed_urls)
    latency_samples = []
    retry_total = 0
    for topic_entries in results.values():
        for entry in topic_entries:
            access = entry.get('accessibility', {})
            latency_samples.append(int(access.get('elapsed_ms', 0) or 0))
            retry_total += max(0, int(access.get('attempts', 1) or 1) - 1)

    elapsed_ms = int((time.time() - started) * 1000)
    today = datetime.now().strftime('%Y-%m-%d')
    api_usage = {
        'generated_at': datetime.now().isoformat(),
        'pipeline': 'research_hub_fetch_sources',
        'parallel_workers': min(MAX_WORKERS, len(tasks)),
        'timeout_sec': TIMEOUT_SEC,
        'elapsed_ms': elapsed_ms,
        'summary': {
            'total_sources': len(tasks),
            'success_count': total_ok,
            'failed_count': total_fail,
            'success_rate': round((total_ok / len(tasks) * 100.0), 2) if tasks else 0.0,
            'retry_total': retry_total,
            'avg_latency_ms': round(sum(latency_samples) / len(latency_samples), 2) if latency_samples else 0,
            'max_latency_ms': max(latency_samples) if latency_samples else 0,
        },
        'by_topic': per_topic,
        'failure_distribution': dict(error_dist),
    }
    Path(f'daily/api-usage-{today}.json').write_text(json.dumps(api_usage, indent=2, ensure_ascii=False), encoding='utf-8')
    Path('daily/api-usage-latest.json').write_text(json.dumps(api_usage, indent=2, ensure_ascii=False), encoding='utf-8')

    # detailed fetch stats
    fetch_stats = {
        'generated_at': datetime.now().isoformat(),
        'elapsed_ms': elapsed_ms,
        'total': len(tasks),
        'success': total_ok,
        'failed': total_fail,
        'failure_distribution': dict(error_dist),
    }
    Path('sources/fetch_stats.json').write_text(json.dumps(fetch_stats, indent=2, ensure_ascii=False), encoding='utf-8')

    print('=' * 60)
    print(f'完成! 总计: {total_ok} 成功, {total_fail} 失败, elapsed_ms={elapsed_ms}')
    print('输出: sources/raw_fetched.json, sources/SOURCES.md, sources/failed_urls.json')
    print(f'API usage: daily/api-usage-{today}.json')


if __name__ == '__main__':
    main()
