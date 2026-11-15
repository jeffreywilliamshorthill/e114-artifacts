#!/usr/bin/env python3
"""Anomaly scan of the enans cells (answer-in-English instruction): did the output actually
come back in English? Flags: language of gen (stopword vote), echo-of-prompt (5-gram overlap),
degeneracy (repeated 4-gram fraction), empty. Prints per surface x lang compliance + flagged rows."""
import json, os, re
from collections import Counter, defaultdict

D = os.path.dirname(os.path.abspath(__file__))
STOP = {
 "en": {"the","is","of","and","to","in","that","it","you","a","not","what","this","are","when"},
 "es": {"el","la","de","que","y","en","es","un","se","no","cuando","lo","una","por","con"},
 "fr": {"le","la","de","que","et","en","est","un","ne","je","vous","les","des","pas","une"},
 "sw": {"ni","ya","wa","na","kwa","katika","hii","kuwa","si","kama","huu","wako","yako","hilo","cha"},
}

def words(t): return re.findall(r"[a-zà-ÿ']+", t.lower())

def lang_vote(t):
    ws = words(t)
    if not ws: return "none", 0.0
    votes = {l: sum(1 for w in ws if w in s) for l, s in STOP.items()}
    tot = sum(votes.values())
    if tot == 0: return "unknown", 0.0
    best = max(votes, key=votes.get)
    return best, votes[best] / max(1, tot)

def ngrams(ws, n=5): return {tuple(ws[i:i+n]) for i in range(len(ws)-n+1)}

def rep4(t):
    ws = words(t)
    gs = [tuple(ws[i:i+4]) for i in range(len(ws)-3)]
    if len(gs) < 8: return 0.0
    c = Counter(gs)
    return sum(v for v in c.values() if v > 1) / len(gs)

def main():
    tr = {}
    for lang in ("es","fr","sw"):
        for r in json.load(open(f"{D}/{lang}.json")):
            tr[(lang, r["pair_id"], r["class"])] = r["tr"]
    stats = defaultdict(Counter); flagged = []
    for surf in ("base","hauhau"):
        root = f"{D}/raw/cap_trans_{surf}"
        for name in sorted(os.listdir(root)):
            m = re.match(r"^(.+)_(FIRE|NOFIRE)_(es|fr|sw)_enans$", name)
            if not m: continue
            pair, cls, lang = m.groups()
            try: g = open(f"{root}/{name}/generated_text.txt", errors="replace").read().strip()
            except FileNotFoundError: g = ""
            key = (surf, lang)
            if not g:
                stats[key]["empty"] += 1; flagged.append((surf,lang,pair,cls,"EMPTY","")); continue
            lv, conf = lang_vote(g)
            src = tr[(lang, pair, cls)]
            ov = 0.0
            gw, sw_ = words(g), words(src)
            if len(gw) >= 5 and len(sw_) >= 5:
                gn = ngrams(gw); ov = len(gn & ngrams(sw_)) / max(1, len(gn))
            r4 = rep4(g)
            if ov > 0.5: stats[key]["echo"] += 1; tag = "ECHO"
            elif r4 > 0.5: stats[key]["degenerate"] += 1; tag = "DEGEN"
            elif lv == "en": stats[key]["english"] += 1; tag = None
            elif lv == lang: stats[key]["stayed_in_lang"] += 1; tag = "STAYED"
            else: stats[key]["other_lang_" + lv] += 1; tag = "LANG:" + lv
            if tag and tag not in ("STAYED",):
                flagged.append((surf, lang, pair, cls, tag, g[:110].replace("\n"," ")))
            elif tag == "STAYED" and len(flagged) < 400:
                flagged.append((surf, lang, pair, cls, tag, g[:80].replace("\n"," ")))
    for key in sorted(stats):
        tot = sum(stats[key].values())
        parts = ", ".join(f"{k} {v}" for k, v in stats[key].most_common())
        print(f"{key[0]:>6} {key[1]}: n={tot} | {parts}")
    print(f"\nflagged rows: {len(flagged)} (ECHO/DEGEN/EMPTY/other-lang shown first, STAYED sampled)")
    order = {"EMPTY":0,"DEGEN":1,"ECHO":2}
    for surf, lang, pair, cls, tag, snip in sorted(flagged, key=lambda x: order.get(x[4], 3))[:40]:
        print(f"  {surf} {lang} {pair} {cls} [{tag}] {snip}")

if __name__ == "__main__":
    main()
