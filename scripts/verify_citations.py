"""Check that every \bibitem in a LaTeX file corresponds to a real publication.

Hallucinated references are the single most-cited tell of unchecked LLM output, and the
thing arXiv moderators actually look for. This resolves each entry against Crossref and
the arXiv API and reports a match score so a human can eyeball the weak ones.
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "aadityasharma.ca@gmail.com"
UA = f"certified-blind-citation-check/1.0 (mailto:{MAILTO})"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_bibitems(tex):
    body = tex.split(r"\begin{thebibliography}")[-1].split(r"\end{thebibliography}")[0]
    parts = re.split(r"\\bibitem\{([^}]+)\}", body)[1:]
    return [(parts[i], " ".join(parts[i + 1].split())) for i in range(0, len(parts), 2)]


def strip_tex(s):
    s = re.sub(r"\\emph\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\text[a-z]*\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)
    s = s.replace("{", "").replace("}", "").replace("\\", "").replace("~", " ")
    return " ".join(s.split())


def guess_title(raw):
    """Entries look like: 'A. Author, B. Author. Title Of Paper. Venue, year.'"""
    txt = strip_tex(raw)
    txt = re.sub(r"arXiv:\s*[\d.]+v?\d*", "", txt)
    # drop a leading author run: initials-and-surnames up to the first sentence period
    sentences = re.split(r"(?<=[a-z0-9\)])\.\s+", txt)
    for s in sentences:
        words = s.split()
        # an author list is short and dense with single-letter initials
        initials = sum(1 for w in words if re.fullmatch(r"[A-Z]\.(-[A-Z]\.)?,?", w))
        if len(words) >= 5 and initials <= 1:
            return s.strip(" .,")
    return txt[:120]


def crossref(title):
    q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 1, "mailto": MAILTO})
    try:
        items = json.loads(get(f"https://api.crossref.org/works?{q}"))["message"]["items"]
    except Exception as e:
        return None, 0.0, f"crossref error: {e}"
    if not items:
        return None, 0.0, "no crossref hit"
    it = items[0]
    return (it.get("title") or [""])[0], float(it.get("score", 0)), it.get("DOI", "")


def arxiv_lookup(arxiv_id):
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        xml = get(url)
    except Exception as e:
        return None, f"arxiv error: {e}"
    m = re.search(r"<entry>.*?<title>(.*?)</title>", xml, re.S)
    if not m:
        return None, "arxiv id did not resolve"
    return " ".join(m.group(1).split()), ""


def tokens(s):
    return {w for w in re.findall(r"[a-z]{4,}", s.lower())}


def overlap(a, b):
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / max(1, min(len(ta), len(tb)))


def main(path):
    tex = open(path, encoding="utf-8").read()
    entries = parse_bibitems(tex)
    print(f"{len(entries)} bibitems found in {path}\n")
    flagged = []
    for key, raw in entries:
        title = guess_title(raw)
        aid = re.search(r"arXiv:\s*([\d.]+v?\d*)", strip_tex(raw))
        verdict, detail = "", ""

        if aid:
            got, err = arxiv_lookup(aid.group(1))
            if got:
                ov = overlap(title, got)
                verdict = "OK-arxiv" if ov >= 0.4 else "CHECK-arxiv-title-mismatch"
                detail = f"arXiv:{aid.group(1)} -> {got[:70]} (overlap {ov:.2f})"
            else:
                verdict, detail = "FAIL-arxiv", err
            time.sleep(3)  # arXiv API asks for 3s between calls

        if not verdict.startswith("OK"):
            got, score, doi = crossref(title)
            if got:
                ov = overlap(title, got)
                if ov >= 0.5:
                    verdict = "OK-crossref"
                    detail = f"{doi} -> {got[:70]} (overlap {ov:.2f})"
                elif not verdict:
                    verdict = "CHECK-weak-match"
                    detail = f"best crossref hit: {got[:70]} (overlap {ov:.2f})"
            elif not verdict:
                verdict, detail = "CHECK-no-hit", doi
            time.sleep(0.3)

        line = f"[{verdict:28}] {key:16} | {title[:72]}"
        print(line)
        if detail:
            print(f"{'':30}   {detail}")
        if not verdict.startswith("OK"):
            flagged.append((key, title, verdict, detail))

    print(f"\n{'='*100}\nAUTO-VERIFIED: {len(entries)-len(flagged)}/{len(entries)}")
    print(f"NEEDS HUMAN EYES: {len(flagged)}\n")
    for key, title, verdict, detail in flagged:
        print(f"  {key:16} {verdict:28} {title[:60]}")
        if detail:
            print(f"  {'':16} {detail}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "paper/main.tex")
