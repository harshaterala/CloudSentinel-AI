"""Knowledge base registry for RAG retrieval.

Sources:
1. Inline curated knowledge snippets in this module.
2. Local markdown benchmark/playbook docs under backend/knowledge_base/*.
"""

from __future__ import annotations

from pathlib import Path


INLINE_DOCUMENTS = [
    {
        "title": "Public Storage Misconfiguration",
        "content": (
            "Publicly accessible object storage can leak sensitive data and trigger compliance exposure. "
            "Remediation includes blocking public access, enforcing encryption, and enabling access logs."
        ),
        "tags": ["storage", "public_access", "compliance"],
        "category": "cloud_baselines",
        "source": "inline",
    },
    {
        "title": "Over-Permissive Identity Controls",
        "content": (
            "Wildcard IAM permissions violate least privilege and can amplify blast radius after compromise. "
            "Remediate by scoping actions/resources, enforcing MFA, and auditing privileged identities."
        ),
        "tags": ["iam", "least_privilege", "mfa"],
        "category": "cis",
        "source": "inline",
    },
    {
        "title": "Exposure Duration Amplifies Risk",
        "content": (
            "Long-lived misconfigurations increase probability of exploit attempts and successful compromise. "
            "Time-to-remediate should be tracked as a critical risk multiplier."
        ),
        "tags": ["exposure", "ttm", "security"],
        "category": "nist",
        "source": "inline",
    },
    {
        "title": "Cloud Cost Waste Signals",
        "content": (
            "Idle, oversized, and orphaned resources are primary cloud waste drivers. "
            "Use utilization, spend, and ownership metadata to prioritize optimization actions."
        ),
        "tags": ["cost", "finops", "right_sizing"],
        "category": "cost_optimization",
        "source": "inline",
    },
]


def _parse_doc_title(markdown_text: str, fallback: str) -> str:
    first = markdown_text.strip().splitlines()
    if not first:
        return fallback
    header = first[0].strip()
    if header.startswith("#"):
        return header.lstrip("#").strip() or fallback
    return fallback


def _load_markdown_docs() -> list[dict]:
    base_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
    if not base_dir.exists():
        return []

    docs: list[dict] = []
    for md_file in sorted(base_dir.rglob("*.md")):
        category = md_file.parent.name
        content = md_file.read_text(encoding="utf-8")
        title = _parse_doc_title(content, md_file.stem.replace("_", " ").title())
        docs.append(
            {
                "title": title,
                "content": content,
                "tags": [category],
                "category": category,
                "source": str(md_file.relative_to(base_dir.parent)).replace("\\", "/"),
            }
        )
    return docs


KNOWLEDGE_DOCUMENTS = INLINE_DOCUMENTS + _load_markdown_docs()
