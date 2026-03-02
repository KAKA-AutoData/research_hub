# Research Hub Index

> Auto-generated for Codex and human readers  
> Generated: 2026-03-03 03:49:28

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Sources | 21 |
| Topics | 3 |
| Accessible | 21 |

## Topics

- **Deep Learning**: 5 sources
- **Bioinformatics**: 8 sources
- **Computational Theory**: 8 sources

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


### Deep Learning

| Title | URL | Barrier | Code | Data |
|-------|-----|---------|------|------|
| PyTorch | [Link](https://pytorch.org) | Low | True | True |
| ArXiv CS.LG | [Link](https://arxiv.org/list/cs.LG/recent) | Medium-High | Check paper | Check paper |
| Distill.pub | [Link](https://distill.pub) | Unknown | False | False |
| Fast.ai | [Link](https://fast.ai) | Low | True | True |
| MIT 6.S191 | [Link](https://introtodeeplearning.com) | Unknown | False | False |

### Bioinformatics

| Title | URL | Barrier | Code | Data |
|-------|-----|---------|------|------|
| NCBI | [Link](https://ncbi.nlm.nih.gov) | Low | False | True |
| UniProt | [Link](https://uniprot.org) | Low | False | True |
| PDB | [Link](https://rcsb.org) | Low | False | True |
| Bioconductor | [Link](https://bioconductor.org) | Unknown | False | False |
| Galaxy Project | [Link](https://galaxyproject.org) | Unknown | False | False |
| Broad Institute | [Link](https://broadinstitute.org) | Medium | Varies | Varies |
| EBI | [Link](https://ebi.ac.uk) | Low | False | True |
| 1000 Genomes | [Link](https://internationalgenome.org) | Unknown | False | False |

### Computational Theory

| Title | URL | Barrier | Code | Data |
|-------|-----|---------|------|------|
| Complexity Zoo | [Link](https://complexityzoo.net) | Unknown | False | False |
| MIT OCW Algorithms | [Link](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011) | Low | True | True |
| TAOCP | [Link](https://www-cs-faculty.stanford.edu/~knuth/taocp.html) | Unknown | False | False |
| ECCC | [Link](https://eccc.weizmann.ac.il) | Unknown | False | False |
| Lambda Calculus | [Link](https://plato.stanford.edu/entries/lambda-calculus) | Unknown | False | False |
| Type Theory | [Link](https://homotopytypetheory.org) | Unknown | False | False |
| Coq Proof Assistant | [Link](https://coq.inria.fr) | Low | True | True |
| Isabelle/HOL | [Link](https://isabelle.in.tum.de) | Low | True | True |

---
*This index is auto-generated. Do not edit manually.*
