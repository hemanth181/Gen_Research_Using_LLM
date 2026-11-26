from datetime import datetime
from pathlib import Path

def save_report(question: str, report: str, findings: list[dict]) -> Path:
    out = Path("output")
    out.mkdir(exist_ok=True)
    path = out / f"research_report_{datetime.now():%Y%m%d_%H%M%S}.md"
    sources = []
    for finding in findings:
        for item in finding.get("results", []):
            if item.get("url"):
                sources.append(f"- {item.get('title','Source')} — {item['url']}")
    content = f"# Research report\n\n**Question:** {question}\n\n{report}\n\n## Retrieved source links\n\n" + ("\n".join(dict.fromkeys(sources)) or "No source links were retrieved.")
    path.write_text(content, encoding="utf-8")
    return path
