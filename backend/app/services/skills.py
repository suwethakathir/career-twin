"""Skill ontology / knowledge graph (small seed; extend or load from DB)."""
import re

GRAPH = {
    "python": ["fastapi", "flask", "django", "rest apis", "pandas", "numpy", "data science"],
    "javascript": ["react", "node.js", "typescript"],
    "cloud": ["aws", "azure", "gcp"],
    "aws": ["ec2", "s3", "lambda"],
    "devops": ["docker", "kubernetes", "ci/cd", "linux"],
    "databases": ["sql", "postgresql", "mongodb"],
    "machine learning": ["pytorch", "tensorflow", "scikit-learn", "nlp"],
}
PREREQ = {"kubernetes": ["docker"], "docker": ["linux"], "aws": ["linux"], "fastapi": ["python", "rest apis"],
          "react": ["javascript"], "pytorch": ["python"], "ci/cd": ["git"]}
ALIASES = {"js": "javascript", "reactjs": "react", "k8s": "kubernetes", "postgres": "postgresql",
           "sklearn": "scikit-learn", "nodejs": "node.js", "amazon web services": "aws",
           "rest api": "rest apis", "restful": "rest apis", "cicd": "ci/cd", "ml": "machine learning"}
EXTRA = ["java", "c++", "git", "html", "css", "tailwind", "communication", "leadership"]

PARENT: dict[str, set] = {}
for p, kids in GRAPH.items():
    for k in kids:
        PARENT.setdefault(k, set()).add(p)
ALL = set(GRAPH) | set(PARENT) | set(EXTRA)
_TERMS = sorted(ALL | set(ALIASES), key=len, reverse=True)
_RX = {t: re.compile(r"(?<![\w+#.])" + re.escape(t) + r"(?![\w+#])", re.I) for t in _TERMS}

def extract_skills(text: str) -> dict[str, int]:
    """canonical skill -> mention count"""
    out: dict[str, int] = {}
    for t, rx in _RX.items():
        n = len(rx.findall(text))
        if n:
            c = ALIASES.get(t, t)
            out[c] = out.get(c, 0) + n
    return out

def similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if b in GRAPH.get(a, []) or a in GRAPH.get(b, []) or (PARENT.get(a, set()) & PARENT.get(b, set())):
        return 0.6
    return 0.0
