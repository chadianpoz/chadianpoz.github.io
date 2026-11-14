"""Convert thesis chapters (LaTeX-made PDF) to HTML-in-Markdown files plus figure images."""
import html
import re
import sys
from pathlib import Path

import pymupdf

PDF = sys.argv[1]
OUT = Path(sys.argv[2])          # site root
IMG_DIR = OUT / "static" / "thesis"
MD_DIR = OUT / "content" / "thesis"
IMG_DIR.mkdir(parents=True, exist_ok=True)
MD_DIR.mkdir(parents=True, exist_ok=True)

doc = pymupdf.open(PDF)

CHAPTERS = [
    # (file stem, title, first pdf index, last pdf index, summary, published)
    ("01-motivation", "1. Motivation", 28, 35,
     "Why salts matter for the search for life on Mars and the ocean worlds, and why they are hard for analytical chemistry.", None),
    ("02-ce-lif-method", "2. A robust CE-LIF method for trace amino acids in hypersaline samples", 36, 55,
     "A capillary electrophoresis method with laser-induced fluorescence that measures trace amino acids directly in magnesium-rich brines.",
     "Seaton, Pozarycki, Nuñez, Stockton (2023), <a href='https://doi.org/10.1021/acsearthspacechem.3c00162'>ACS Earth and Space Chemistry</a>"),
    ("03-evaporitic-brines", "3. Biosignature molecules accumulate and persist in evaporitic brines", 56, 87,
     "At South Bay Salt Works, amino acids and ATP concentrate and persist as seawater evaporates into brine.",
     "Pozarycki et al. (2024), <a href='https://doi.org/10.1089/ast.2023.0122'>Astrobiology</a>"),
    ("04-western-australia", "4. Western Australia acid brine lakes by CE-LIF, µCE-MS, and ATP assay", 88, 105,
     "The same analysis suite applied to 20 acidic and hypersaline lakes in Western Australia.", None),
    ("05-fatty-acids", "5. Fatty acid biosignatures in Mars analog evaporites and clays", 106, 128,
     "Fatty acids in salt crusts and clays, measured by the TMAH thermochemolysis method used on the Curiosity rover, show preservation and detection that depend on mineralogy.", None),
    ("06-perspectives", "6. Perspectives", 129, 150,
     "The need for life detection science, a looser definition of life, searching through chemical space, and life as a behavior (antifragility).", None),
]

BODY_X = (106, 141)
KEEP_HYPHEN = {"self", "non", "co", "multi", "cross", "high", "low", "semi", "anti", "well", "long", "short", "post", "pre", "in", "ex", "time", "salt", "acid", "life", "ice"}
CAP_RE = re.compile(r"^(Figure|Table)\s+([A-Z]?\d+\.\d+):")
CITE_RE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")


ACC = {"˜": "\u0303", "´": "\u0301", "`": "\u0300", "¨": "\u0308", "ˆ": "\u0302", "¸": "\u0327"}


def fix_acc(t):
    import unicodedata
    t = re.sub(r"([˜´`¨ˆ])\s?([A-Za-zıi])", lambda m: unicodedata.normalize("NFC", ("i" if m.group(2) == "ı" else m.group(2)) + ACC[m.group(1)]), t)
    return t


def span_html(s):
    t = html.escape(fix_acc(s["text"]))
    if not t.strip():
        return t
    if s["size"] < 10.5:
        return f"<sup>{t}</sup>" if s["flags"] & 1 else f"<sub>{t}</sub>"
    if "Ital" in s["font"] or s["flags"] & 2:
        return f"<em>{t}</em>"
    return t


def line_text(b, rich=True):
    parts = []
    for l in b["lines"]:
        parts.append("".join(span_html(s) if rich else s["text"] for s in l["spans"]))
    if not rich:
        return fix_acc(" ".join(parts))
    return " ".join(parts)


def link_cites(t):
    def rep(m):
        out = []
        for tok in re.split(r"(\s*,\s*)", m.group(1)):
            mm = re.match(r"(\d+)\s*[–-]\s*(\d+)", tok)
            if mm:
                out.append(f"<a href='/thesis/references/#ref-{mm.group(1)}'>{mm.group(1)}</a>–<a href='/thesis/references/#ref-{mm.group(2)}'>{mm.group(2)}</a>")
            elif tok.strip().isdigit():
                out.append(f"<a href='/thesis/references/#ref-{tok.strip()}'>{tok.strip()}</a>")
            else:
                out.append(tok)
        return "[" + "".join(out) + "]"
    return CITE_RE.sub(rep, t)


def classify(page):
    d = page.get_text("dict")
    items = []
    for b in d["blocks"]:
        x0, y0, x1, y1 = b["bbox"]
        if b["type"] != 0:
            items.append({"kind": "float", "bbox": b["bbox"]})
            continue
        if y0 > 735:  # page number
            continue
        horiz = all(abs(l["dir"][0] - 1) < 0.01 for l in b["lines"])
        plain = line_text(b, rich=False).strip()
        first = b["lines"][0]["spans"][0]
        if not plain:
            continue
        numm = re.match(r"^[A-Z]?\d+(\.\d+)+$", first["text"].strip())
        if horiz and y0 > 450 and 8.5 <= max(sp["size"] for l in b["lines"] for sp in l["spans"]) <= 10.6 and x0 < 130:
            sp0 = b["lines"][0]["spans"][0]
            mark = sp0["text"].strip() if sp0["text"].strip().isdigit() and sp0["size"] < 9 else ""
            body_t = html.escape(plain[len(mark):].strip() if mark else plain)
            items.append({"kind": "footnote", "bbox": b["bbox"], "text": (f"<sup>{mark}</sup> " if mark else "") + body_t})
            continue
        if horiz and numm and ("Medi" in first["font"] or first["text"].count(".") >= 2) and len(plain) < 160 and x1 < 556:
            items.append({"kind": "heading", "bbox": b["bbox"], "plain": plain, "text": plain})
        elif horiz and any("Medi" in sp["font"] for l in b["lines"] for sp in l["spans"]) and not any(c.islower() for c in plain if c.isascii()) and len(plain) > 3 and not numm:
            items.append({"kind": "title", "bbox": b["bbox"], "text": plain})
        elif horiz and CAP_RE.match(plain):
            items.append({"kind": "caption", "bbox": b["bbox"], "text": line_text(b)})
        elif not horiz:
            items.append({"kind": "float", "bbox": b["bbox"], "rot": b["lines"][0]["dir"]})
        elif (BODY_X[0] <= x0 <= BODY_X[1] and x1 <= 556 and len(b["lines"]) == 1
              and 11.5 <= first["size"] <= 12.5):
            heading = "Medi" in first["font"] and re.match(r"^[A-Z]?\d+(\.\d+)+$", first["text"].strip())
            items.append({"kind": "heading" if heading else "body", "bbox": b["bbox"],
                          "text": line_text(b), "plain": plain, "indent": 120 < x0 < 131,
                          "medi": "Medi" in first["font"]})
        elif "Medi" in first["font"] and horiz and first["size"] >= 11.5:
            items.append({"kind": "title", "bbox": b["bbox"], "text": plain})
        else:
            items.append({"kind": "float", "bbox": b["bbox"]})
    for dr in page.get_drawings():
        r = dr["rect"]
        if r.y0 < 735 and (r.width > 3 or r.height > 3) and not (r.height < 2 and 60 < r.width < 200 and r.x0 < 115 and r.y0 > 450):
            items.append({"kind": "float", "bbox": tuple(r)})
    items.sort(key=lambda it: (round(it["bbox"][1]), it["bbox"][0]))
    in_table = False
    for it in items:
        if it["kind"] == "caption" and it["text"].startswith("Table"):
            in_table = True
            it["table_caption"] = True
            continue
        if in_table:
            bodyish = it["kind"] in ("body", "heading") and (it["bbox"][2] - it["bbox"][0] > 300 or it["kind"] == "heading")
            if bodyish or it["kind"] == "caption":
                in_table = False
            else:
                it["kind"] = "table"
    return items


def table_html(page, rect):
    words = [w for w in page.get_text("words") if pymupdf.Rect(w[:4]).intersects(rect)]
    if not words:
        return ""
    # column boundaries: x gaps not covered by any word
    spans = sorted((w[0], w[2]) for w in words)
    cols, cur = [], list(spans[0])
    for x0, x1 in spans[1:]:
        if x0 > cur[1] + 6:
            cols.append(cur); cur = [x0, x1]
        else:
            cur[1] = max(cur[1], x1)
    cols.append(cur)
    def col_of(w):
        for i, (x0, x1) in enumerate(cols):
            if w[0] <= x1 + 1:
                return i
        return len(cols) - 1
    # row bands from horizontal rules, if the table has them
    rules = sorted({round(d["rect"].y0) for d in page.get_drawings()
                    if d["rect"].height < 2 and d["rect"].width > 60 and rect.x0 - 5 <= d["rect"].x0 and d["rect"].y0 > rect.y0 - 30 and d["rect"].y0 < rect.y1 + 5})
    def band(w):
        if len(rules) < 3:
            return round(w[3] / 4)
        yc = (w[1] + w[3]) / 2
        return sum(1 for r in rules if r < yc)
    rows = {}
    for w in sorted(words, key=lambda w: (w[3], w[0])):
        rows.setdefault(band(w), {}).setdefault(col_of(w), []).append(w)
    out = ["<div class='table-wrap'><table>"]
    for ri, key in enumerate(sorted(rows)):
        cells = []
        for c in range(len(cols)):
            ws = rows[key].get(c, [])
            lines, last_y = [], None
            for w in ws:
                if last_y is not None and abs(w[3] - last_y) < 4:
                    lines[-1].append(fix_acc(w[4]))
                else:
                    lines.append([fix_acc(w[4])])
                last_y = w[3]
            text = " ".join(" ".join(l) for l in lines) if len(rules) < 3 or c == 0 else "<br>".join(html.escape(" ".join(l)) for l in lines)
            cells.append(text if "<br>" in text else html.escape(text))
        tag = "th" if ri == 0 else "td"
        out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
    out.append("</table></div>")
    return "".join(out)


def convert(stem, title, a, b, summary, published):
    out = []
    para = []
    notes = []
    fig_n = [0]

    def flush():
        if para:
            text = ""
            for t in para:
                if text.endswith("-") and t[:1].islower():
                    prev = re.split(r"[\s(]", text[:-1])[-1].lower()
                    text = (text + t) if prev in KEEP_HYPHEN else text[:-1] + t
                else:
                    text = (text + " " + t) if text else t
            out.append(f"<p>{link_cites(text)}</p>")
            para.clear()

    for pi in range(a, b + 1):
        page = doc[pi]
        items = classify(page)
        i = 0
        while i < len(items):
            it = items[i]
            k = it["kind"]
            if k == "title":
                i += 1
                continue
            if k == "footnote":
                t = it["text"]
                if notes and not re.match(r"^\s*<sup>\d", t):
                    notes[-1] += " " + t
                else:
                    notes.append(t)
                i += 1
                continue
            if k == "heading":
                flush()
                # merge following medium-weight lines (wrapped heading)
                text = it["plain"]
                while i + 1 < len(items) and items[i + 1]["kind"] == "body" and items[i + 1].get("medi"):
                    i += 1
                    text += " " + items[i]["plain"]
                num = text.split(" ", 1)[0]
                level = "h2" if num.count(".") == 1 else "h3"
                out.append(f"<{level}>{html.escape(text)}</{level}>")
                i += 1
                continue
            if k == "body":
                if it["indent"]:
                    flush()
                para.append(it["text"])
                if it["bbox"][2] < 500:  # short last line ends the paragraph
                    flush()
                i += 1
                continue
            # float group: consecutive float/caption items
            flush()
            group = [it]
            j = i + 1
            while j < len(items) and items[j]["kind"] in ("float", "caption", "table"):
                group.append(items[j])
                j += 1
            caps = [g for g in group if g["kind"] == "caption"]
            tbl = [g for g in group if g["kind"] == "table" and not g.get("rot")]
            if tbl and not any(g.get("rot") for g in group):
                for c in caps:
                    out.append(f"<p class='caption'>{link_cites(c['text'])}</p>")
                tr = pymupdf.Rect(min(g["bbox"][0] for g in tbl), min(g["bbox"][1] for g in tbl),
                                  max(g["bbox"][2] for g in tbl), max(g["bbox"][3] for g in tbl))
                out.append(table_html(page, tr))
                i = j
                continue
            region = [g for g in group if g["kind"] in ("float", "table")]
            if region:
                x0 = min(g["bbox"][0] for g in region)
                y0 = min(g["bbox"][1] for g in region)
                x1 = max(g["bbox"][2] for g in region)
                y1 = max(g["bbox"][3] for g in region)
                rect = pymupdf.Rect(max(60, x0 - 4), max(40, y0 - 4), min(560, x1 + 4), min(738, y1 + 4))
                if rect.height > 8 and rect.width > 8:
                    fig_n[0] += 1
                    rot = 0
                    for g in region:
                        if g.get("rot"):
                            rot = -90 if g["rot"][1] < 0 else 90
                    pix = page.get_pixmap(clip=rect, dpi=170)
                    name = f"{stem[:2]}-{fig_n[0]:02d}.png"
                    if rot:
                        from PIL import Image
                        import io
                        im = Image.open(io.BytesIO(pix.tobytes("png"))).rotate(rot, expand=True)
                        im.save(IMG_DIR / name, optimize=True)
                    else:
                        pix.save(IMG_DIR / name)
                    capt = " ".join(c["text"] for c in caps)
                    alt = html.escape(re.sub("<[^>]+>", "", capt)[:200]) or "Figure"
                    small = "" if rect.height > 60 else " class='inline-eq'"
                    out.append(f"<figure{small}><img src='/thesis/{name}' alt='{alt}' loading='lazy'>"
                               + (f"<figcaption>{link_cites(capt)}</figcaption>" if capt else "") + "</figure>")
                    caps = []
            for c in caps:
                out.append(f"<p class='caption'>{link_cites(c['text'])}</p>")
            i = j
    flush()
    if notes:
        out.append("<div class='footnotes'><h2>Notes</h2>" + "".join(f"<p>{link_cites(n)}</p>" for n in notes) + "</div>")
    fm = [f'title: "{title}"', f'summary: "{summary}"']
    if published:
        fm.append(f'published: "{published}"')
    (MD_DIR / f"{stem}.md").write_text("---\n" + "\n".join(fm) + "\n---\n\n" + "\n\n".join(out) + "\n", encoding="utf-8")
    print(stem, fig_n[0], "figures", len(out), "blocks")


def references(a, b):
    entries = []
    cur = None
    for pi in range(a, b + 1):
        for blk in doc[pi].get_text("dict")["blocks"]:
            if blk["type"] != 0 or blk["bbox"][1] > 735:
                continue
            lines = ["".join(sp["text"] for sp in l["spans"]).strip() for l in blk["lines"]]
            if lines[0] == "REFERENCES":
                continue
            m = re.match(r"^\[(\d+)\]$", lines[0])
            if m:
                cur = [int(m.group(1)), ""]
                entries.append(cur)
                lines = lines[1:]
            if cur is None:
                continue
            for t in lines:
                if cur[1].endswith("-") and t[:1].islower():
                    cur[1] = cur[1][:-1] + t
                else:
                    cur[1] = (cur[1] + " " + t).strip()
    items = []
    for n, t in entries:
        t = html.escape(t)
        t = re.sub(r"(https?://\S+?)([.,]?)(?=\s|$)", r"<a href='\1'>\1</a>\2", t)
        t = re.sub(r"\bdoi:\s*(10\.\S+?)([.,]?)(?=\s|$)", r"<a href='https://doi.org/\1'>doi:\1</a>\2", t)
        items.append(f"<li id='ref-{n}' value='{n}'>{t}</li>")
    (MD_DIR / "99-references.md").write_text(
        '---\ntitle: "References"\nsummary: "All references cited in the thesis."\n---\n\n<ol class=\'refs\'>\n'
        + "\n".join(items) + "\n</ol>\n", encoding="utf-8")
    print("references", len(items))


for c in CHAPTERS:
    convert(*c)
references(206, 237)

# Summary page text, for the thesis index
s = []
for blk in doc[27].get_text("dict")["blocks"]:
    if blk["type"] == 0 and blk["bbox"][1] < 735:
        t = line_text(blk).strip()
        if t != "SUMMARY":
            s.append((blk["bbox"][0] > 120, t))
paras, cur = [], ""
for indent, t in s:
    if indent and cur:
        paras.append(cur); cur = t
    else:
        cur = cur[:-1] + t if cur.endswith("-") and t[:1].islower() else (cur + " " + t).strip()
paras.append(cur)
(Path(OUT) / "thesis_summary.txt").write_text("\n\n".join(paras), encoding="utf-8")
