"""Audit: verify every arXiv ID cited in paper/references/*.md actually exists.

No-hallucinated-citations rule. Scrapes arXiv IDs from the reference markdown,
queries the arXiv API in one batch, and reports for each ID whether it resolves,
its canonical title/first-author/year, and flags any that are missing or
future-dated (after the current month). Also emits a verified BibTeX file.
"""

from __future__ import annotations

import glob
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

REF_DIR = os.path.join(os.path.dirname(__file__), "..", "paper", "references")
BIB_OUT = os.path.join(os.path.dirname(__file__), "..", "paper", "references", "verified.bib")
CUR_YYMM = 2606  # June 2026; IDs with yymm > this are future-dated -> suspicious
ARXIV_API = "http://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}

# No trailing \b: arXiv entry URLs end with a version suffix (e.g. 2403.12031v2),
# and \b fails between the trailing digit and 'v'.
ID_RE = re.compile(r"(\d{4}\.\d{4,5})")


def _valid_arxiv(aid: str) -> bool:
    """Real arXiv IDs are YYMM.NNNNN with month 01-12; filters DOI-digit fragments."""
    mm = int(aid[2:4])
    return 1 <= mm <= 12


def collect_ids() -> dict[str, list[str]]:
    ids: dict[str, list[str]] = {}
    for f in sorted(glob.glob(os.path.join(REF_DIR, "*.md"))):
        text = open(f).read()
        for m in ID_RE.findall(text):
            if _valid_arxiv(m):
                ids.setdefault(m, []).append(os.path.basename(f))
    return ids


def fetch(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    # batch in chunks of 50
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        q = urllib.parse.urlencode({"id_list": ",".join(chunk), "max_results": len(chunk)})
        with urllib.request.urlopen(f"{ARXIV_API}?{q}", timeout=60) as r:
            root = ET.fromstring(r.read())
        for e in root.findall("a:entry", NS):
            idurl = e.findtext("a:id", default="", namespaces=NS)
            m = ID_RE.search(idurl)
            if not m:
                continue
            aid = m.group(1)
            title = " ".join(e.findtext("a:title", "", NS).split())
            authors = [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)]
            published = e.findtext("a:published", "", NS)[:10]
            out[aid] = {"title": title, "authors": authors, "published": published}
    return out


DOI_RE = re.compile(r"10\.\d{4,9}/[^\s)\]\"'>,]+")


def collect_dois() -> dict[str, list[str]]:
    dois: dict[str, list[str]] = {}
    for f in sorted(glob.glob(os.path.join(REF_DIR, "*.md"))):
        for m in DOI_RE.findall(open(f).read()):
            doi = m.rstrip(".)")
            dois.setdefault(doi, []).append(os.path.basename(f))
    return dois


def verify_doi(doi: str) -> str | None:
    """Return the BibTeX from doi.org content negotiation, or None if unresolved."""
    req = urllib.request.Request(f"https://doi.org/{doi}",
                                 headers={"Accept": "application/x-bibtex"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
        return body if "@" in body else None
    except Exception:
        return None


def yymm(aid: str) -> int:
    return int(aid.split(".")[0])


def main():
    ids = collect_ids()
    print(f"found {len(ids)} unique arXiv IDs across {len(set(sum(ids.values(), [])))} files")
    meta = fetch(list(ids))

    ok, missing, future = [], [], []
    for aid in sorted(ids):
        if aid not in meta:
            missing.append(aid)
        elif yymm(aid) > CUR_YYMM:
            future.append(aid)
        else:
            ok.append(aid)

    print(f"\n[OK] {len(ok)} resolved:")
    for aid in ok:
        m = meta[aid]
        a0 = m["authors"][0].split()[-1] if m["authors"] else "?"
        print(f"  {aid}  {m['published']}  {a0} et al. — {m['title'][:64]}")
    if future:
        print(f"\n[FUTURE-DATED >{CUR_YYMM}] {len(future)} (verify they exist / submission-window OK):")
        for aid in future:
            m = meta.get(aid, {})
            print(f"  {aid}  {m.get('published','?')}  {m.get('title','RESOLVED-BUT-FUTURE')[:64]}")
    if missing:
        print(f"\n[!! NOT FOUND ON ARXIV] {len(missing)} — possible fabrication, files: ")
        for aid in missing:
            print(f"  {aid}  cited in {ids[aid]}")

    # emit verified bibtex (resolved only)
    with open(BIB_OUT, "w") as f:
        for aid in ok + future:
            m = meta[aid]
            last = m["authors"][0].split()[-1].lower() if m["authors"] else "anon"
            yr = m["published"][:4]
            key = f"{last}{yr}_{aid.replace('.', '')}"
            auth = " and ".join(m["authors"])
            f.write(f"@article{{{key},\n  title={{{m['title']}}},\n  author={{{auth}}},\n"
                    f"  year={{{yr}}},\n  eprint={{{aid}}},\n  archivePrefix={{arXiv}}\n}}\n\n")
    # append DOI-only citations (no arXiv)
    dois = collect_dois()
    doi_ok, doi_bad = [], []
    bib_extra = []
    for doi in sorted(dois):
        bib = verify_doi(doi)
        if bib:
            doi_ok.append(doi); bib_extra.append(bib.strip())
        else:
            doi_bad.append(doi)
    with open(BIB_OUT, "a") as f:
        f.write("\n% --- DOI-verified (non-arXiv) ---\n")
        for b in bib_extra:
            f.write(b + "\n\n")
    print(f"\n[DOI] {len(doi_ok)}/{len(dois)} resolved via doi.org:")
    for d in doi_ok:
        print(f"  OK  {d}")
    if doi_bad:
        print(f"[DOI !! UNRESOLVED] {len(doi_bad)}:")
        for d in doi_bad:
            print(f"  {d}  in {dois[d]}")

    print(f"\nwrote verified BibTeX ({len(ok)+len(future)+len(doi_ok)} entries) -> {BIB_OUT}")
    print(f"SUMMARY arXiv: {len(ok)} ok, {len(future)} future, {len(missing)} missing | "
          f"DOI: {len(doi_ok)} ok, {len(doi_bad)} unresolved")


if __name__ == "__main__":
    main()
