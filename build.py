#!/usr/bin/env python3
"""Assemble airxpert fragments -> index.html + run verification gates."""
import re, sys, hashlib
from pathlib import Path

SRC = Path(__file__).parent / "src"
OUT = Path(__file__).parent / "index.html"

FRAGS = [f"f{i:02d}.html" for i in range(1, 11)]

def main():
    parts = []
    for name in FRAGS:
        p = SRC / name
        if not p.exists():
            print(f"FAIL missing fragment {name}"); sys.exit(1)
        parts.append(p.read_text(encoding="utf-8").rstrip("\n"))
    html = "\n".join(parts) + "\n"
    OUT.write_text(html, encoding="utf-8", newline="\n")

    fails = []
    # 1. corruption token scan
    CORRUPT = ["shoulder:", "heat:", "dict<", "create-element", "var--black",
               "var-component", "Surabaya:", "eyec(", "rv-dL",
               '<span class="doc">', "-ground", "ground>", "ground-", "ground_"]
    # h18 is only corruption when it's a mangled tag, not SVG path data (M3 12h18)
    if re.search(r"<h18|h18>", html): CORRUPT.append("h18")
    hits = [tok for tok in CORRUPT if tok in html]
    if hits: fails.append(f"corruption tokens: {hits}")

    # 2. address scrub gate (old address must be gone entirely)
    for bad in ["Riverview", "Earlwood NSW", "2206"]:
        if bad in html: fails.append(f"address leak: {bad}")

    # 3. em dash scan
    if "\u2014" in html: fails.append("em dash present")

    # 4. structural balance
    opens = len(re.findall(r"<div\b", html))
    closes = html.count("</div>")
    if opens != closes: fails.append(f"div imbalance {opens}/{closes}")
    so = len(re.findall(r"<section\b", html)); sc = html.count("</section>")
    if so != sc: fails.append(f"section imbalance {so}/{sc}")
    fo = len(re.findall(r"<form\b", html)); fc = html.count("</form>")
    if fo != fc: fails.append(f"form imbalance {fo}/{fc}")
    if html.count("<script") != html.count("</script>"):
        fails.append("script imbalance")
    if html.count("<style") != html.count("</style>"):
        fails.append("style imbalance")

    # 5. required landmarks
    for need in ['id="air"', 'id="book"', 'id="services"', 'id="pricing"',
                 'id="reviews"', 'id="coverage"', 'id="faq"', "</html>",
                 "Sydney NSW 2000", "0450 265 046"]:
        if need not in html: fails.append(f"missing landmark {need}")

    # 6. no orphan corruption-class tags
    if re.search(r"<[a-z]+-ground", html): fails.append("ground-tag artefacts")

    sha = hashlib.sha256(html.encode()).hexdigest()[:16]
    print(f"index.html {len(html)} bytes sha256:{sha}")
    if fails:
        print("FAILURES:")
        for f in fails: print("  -", f)
        sys.exit(1)
    print("ALL GATES PASS")

if __name__ == "__main__":
    main()
