# -*- coding: utf-8 -*-
import re, os, shutil, sys, struct
sys.path.insert(0, "/home/claude/ms")
from content import *
TPL = "/home/claude/tpl"; OUT = "/home/claude/ms/unpacked"
FIGDIR = "/mnt/user-data/outputs/project/experiments/2026-09-29_leakage-antropometri-stunting-WHO-official/figures"
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree(TPL, OUT)
doc = open(f"{OUT}/word/document.xml", encoding="utf-8").read()
head = doc[:doc.find("<w:body>") + len("<w:body>")]
body_old = doc[doc.find("<w:body>") + len("<w:body>"):]
sect = re.search(r"<w:sectPr.*?</w:sectPr>", body_old, re.S).group(0)
tpl_items = re.findall(r"<w:p[ >].*?</w:p>|<w:tbl>.*?</w:tbl>", body_old, re.S)
info_tbl = tpl_items[10]; legend_tbl = tpl_items[73]

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
# ---------- citations
order = []
def cite(text):
    def rep(m):
        keys = [k.strip() for k in m.group(1).split(",")]
        nums = []
        for k in keys:
            assert k in REFS, k
            if k not in order: order.append(k)
            nums.append(order.index(k) + 1)
        nums = sorted(nums)
        # compress consecutive runs like [3]–[5]
        out, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1: j += 1
            out.append(f"[{nums[i]}]" if j - i < 2 else f"[{nums[i]}]–[{nums[j]}]")
            if 0 < j - i < 2: out += [f"[{n}]" for n in nums[i + 1:j + 1]]
            i = j + 1
        return ", ".join(out)
    return re.sub(r"\{([a-z0-9_,\s]+)\}", rep, text)

def run(t, b=False, i=False, sz=None, sup=False, hl=False, color=None):
    rp = ""
    if b: rp += "<w:b/><w:bCs/>"
    if i: rp += "<w:i/><w:iCs/>"
    if color: rp += f'<w:color w:val="{color}"/>'
    if sz: rp += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if hl: rp += '<w:highlight w:val="yellow"/>'
    if sup: rp += '<w:vertAlign w:val="superscript"/>'
    return f'<w:r>{"<w:rPr>"+rp+"</w:rPr>" if rp else ""}<w:t xml:space="preserve">{esc(t)}</w:t></w:r>'

ITALIC_TERMS = ["et al.", "Survei Kesehatan Indonesia"]
def rich(t, **kw):
    t = cite(t)
    parts = re.split("(" + "|".join(re.escape(x) for x in ITALIC_TERMS) + ")", t)
    return "".join(run(p, i=(p in ITALIC_TERMS) or kw.get("i", False), **{k: v for k, v in kw.items() if k != "i"}) for p in parts if p)

ORDER = ["pStyle","keepNext","keepLines","pageBreakBefore","widowControl","numPr","pBdr","shd","tabs","spacing","ind","jc","rPr"]
def fix_ppr(ppr):
    items = re.findall(r"<w:(\w+)(?:\s[^>]*)?/>|<w:(\w+)[^>]*>.*?</w:\2>", ppr, re.S)
    parts = re.findall(r"(<w:(\w+)(?:\s[^>]*)?/>|<w:(\w+)[^>]*>.*?</w:\3>)", ppr, re.S)
    parts = [(p[0], p[1] or p[2]) for p in parts]
    parts.sort(key=lambda z: ORDER.index(z[1]) if z[1] in ORDER else 99)
    return "".join(p[0] for p in parts)
def P(inner, ppr=""):
    ppr = fix_ppr(ppr) if ppr else ""
    return f"<w:p>{'<w:pPr>'+ppr+'</w:pPr>' if ppr else ''}{inner}</w:p>"
BODYP = '<w:ind w:firstLine="720"/><w:jc w:val="both"/>'
def empty(): return P("")

# ---------- images
rels = open(f"{OUT}/word/_rels/document.xml.rels", encoding="utf-8").read()
img_id = [200]
def png_size(path):
    with open(path, "rb") as f:
        f.read(16); w, h = struct.unpack(">II", f.read(8))
    return w, h
def image(fname, width_cm):
    img_id[0] += 1; rid = f"rId{img_id[0]}"
    shutil.copy(f"{FIGDIR}/{fname}", f"{OUT}/word/media/{fname}")
    global rels
    rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{fname}"/></Relationships>')
    w, h = png_size(f"{FIGDIR}/{fname}")
    cx = int(width_cm * 360000); cy = int(cx * h / w)
    n = img_id[0]
    return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{n}" name="Figure {n}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{n}" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')

# ---------- tables (IEEE style: rules on top, below header, bottom)
def table(title, widths_cm, rows, sz=16):
    tw = [int(w * 567) for w in widths_cm]; total = sum(tw)
    x = P(rich(title), '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/>')
    x += f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="57" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'
    x += "".join(f'<w:gridCol w:w="{w}"/>' for w in tw) + "</w:tblGrid>"
    for ri, r in enumerate(rows):
        x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>"
        for ci, c in enumerate(r):
            top = '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>' if ri == 0 else ""
            bot = ('<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>' if ri == 0 else
                   '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>' if ri == len(rows) - 1 else "")
            x += (f'<w:tc><w:tcPr><w:tcW w:w="{tw[ci]}" w:type="dxa"/><w:tcBorders>{top}<w:left w:val="nil"/>{bot}<w:right w:val="nil"/></w:tcBorders><w:vAlign w:val="center"/></w:tcPr>'
                  + P(rich(c, b=(ri == 0), sz=sz), f'<w:jc w:val="{"left" if ci == 0 else "center"}"/><w:spacing w:before="20" w:after="20"/>' + ("<w:keepNext/>" if ri < len(rows) - 1 else "")) + "</w:tc>")
        x += "</w:tr>"
    return x + "</w:tbl>" + empty()

# ---------- equations (OMML)
def mr(t, it=True):
    return f'<m:r>{"" if it else "<m:rPr><m:sty m:val=\"p\"/></m:rPr>"}<m:t xml:space="preserve">{esc(t)}</m:t></m:r>'
def frac(n, d): return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"
def sup(b, e): return f"<m:sSup><m:e>{b}</m:e><m:sup>{e}</m:sup></m:sSup>"
def sub(b, s): return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"
def paren(x): return f"<m:d><m:e>{x}</m:e></m:d>"
EQ = {
 "haz": mr("HAZ") + mr("=", False) + frac(sup(paren(frac(mr("y"), mr("M(t)"))), mr("L(t)")) + mr("−1", False), mr("L(t)") + mr("·", False) + mr("S(t)")),
 "infl": mr("Inflation") + mr("=", False) + mr("100", False) + mr("×", False) + frac(sub(mr("AUC"), mr("leaky")) + mr("−", False) + sub(mr("AUC"), mr("B")), sub(mr("AUC"), mr("B")) + mr("−0.5", False)) + mr("%", False),
}
eqn = [0]
def equation(key):
    eqn[0] += 1
    return P(f'<w:r><w:tab/></w:r><m:oMath>{EQ[key]}</m:oMath><w:r><w:tab/><w:t>({eqn[0]})</w:t></w:r>',
             '<w:tabs><w:tab w:val="center" w:pos="4394"/><w:tab w:val="right" w:pos="8789"/></w:tabs><w:spacing w:before="120" w:after="120"/>')

# ---------- front matter
x = ""
x += P(run(TITLE, sz=32), '<w:pStyle w:val="Title"/>')
x += empty()
au = ""
for k, (n, a) in enumerate(AUTHORS):
    au += run(n, b=True) + run(a, b=True, sup=True) + (run(", ", b=True) if k < len(AUTHORS) - 1 else "")
x += P(au, '<w:jc w:val="center"/>')
for a, t in AFFIL: x += P(run(a, sz=16, sup=True) + run(t, sz=16), '<w:jc w:val="center"/>')
x += empty()

# info table: edit template cells
cells = re.findall(r"<w:tc>.*?</w:tc>", info_tbl, re.S)
def set_cell(tbl, cell, new_paras):
    tcpr = re.search(r"<w:tcPr>.*?</w:tcPr>", cell, re.S).group(0)
    return tbl.replace(cell, "<w:tc>" + tcpr + new_paras + "</w:tc>", 1)
t = info_tbl
t = t.replace("<w:t>(10 PT)</w:t>", "<w:t></w:t>").replace(" (10 PT)", "")
# cell index: 0 ArticleInfo,1,2 ABSTRACT | 3 history,4,5 abstract | 6 keywords,7,8 | 9,10,11 license | 12 corresponding
t = set_cell(t, cells[5], P(rich(ABSTRACT, sz=18), '<w:spacing w:before="120"/><w:jc w:val="both"/>'))
t = set_cell(t, cells[6], P(run("Keywords:", b=True, i=True), '<w:spacing w:before="120" w:after="120"/><w:jc w:val="both"/>')
             + "".join(P(run(k), '<w:jc w:val="both"/>') for k in KEYWORDS))
corr = (P(run("Corresponding Author:", b=True, i=True), '<w:spacing w:before="120" w:after="120"/>')
        + P(run("Ahmad Dedi Jubaedi")) + P(run("Faculty of Computer Science, Universitas Serang Raya"))
        + P(run("Serang, Banten, Indonesia")) + P(run("Email: dedi@unsera.ac.id"), '<w:spacing w:after="120"/>'))
t = set_cell(t, cells[12], corr)
x += t + empty()

# ---------- body
fign = [0]
for blk in BODY:
    k = blk[0]
    if k == "h1":
        x += P(run(blk[1], b=True), '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="15"/></w:numPr><w:tabs><w:tab w:val="left" w:pos="426"/></w:tabs><w:spacing w:before="240" w:after="120"/><w:ind w:left="426" w:hanging="426"/><w:keepNext/>')
    elif k == "h2":
        x += P(run(blk[1], b=True), '<w:spacing w:before="180" w:after="60"/><w:keepNext/>')
    elif k == "p":
        x += P(rich(blk[1]), BODYP)
    elif k == "note":
        x += P(run(blk[1], hl=True, i=True), '<w:jc w:val="both"/><w:spacing w:before="60" w:after="60"/>')
    elif k == "eq":
        x += equation(blk[1])
    elif k == "fig":
        x += P(image(blk[1], blk[2]), '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="120"/>')
        x += P(rich(blk[3]), '<w:jc w:val="center"/><w:spacing w:before="60" w:after="120"/>')
    elif k == "tbl":
        ttl, w, rows = TABLES[blk[1]]
        x += table(ttl, w, rows, sz=14 if blk[1] == "perf" else 16)

# ---------- back matter
def sec(title): return empty() + P(run(title, b=True), '<w:jc w:val="both"/><w:keepNext/>')
x += sec("FUNDING INFORMATION")
x += P(run("Authors state no funding involved."), BODYP)
x += sec("AUTHOR CONTRIBUTIONS STATEMENT")
x += P(run("This journal uses the Contributor Roles Taxonomy (CRediT) to recognize individual author contributions, reduce authorship disputes, and facilitate collaboration."), BODYP)
roles = ["C", "M", "So", "Va", "Fo", "I", "R", "D", "O", "E", "Vi", "Su", "P", "Fu"]
alloc = {"Ahmad Dedi Jubaedi": {"C", "M", "So", "Fo", "I", "D", "O", "Vi", "P"},
         "Pulung Nurtantio Andono": {"C", "M", "Va", "E", "Su"},
         "Nova Rijati": {"M", "Va", "E", "Su"},
         "Ahmad Zainul Fanani": {"Va", "R", "E", "Su"}}
rows = [["Name of Author"] + roles] + [[n] + ["✓" if r in alloc[n] else "" for r in roles] for n, _ in AUTHORS]
x += table("", [3.8] + [0.8] * 14, rows, sz=16).replace(P(rich(""), '<w:keepNext/><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/>'), "", 1)
x += legend_tbl + empty()
x += sec("CONFLICT OF INTEREST STATEMENT")
x += P(run("Authors state no conflict of interest."), BODYP)
x += sec("ETHICAL APPROVAL")
x += P(run("This study is a secondary analysis of de-identified data from the 2023 Indonesian Health Survey, collected by the Ministry of Health of the Republic of Indonesia under its own ethical clearance and informed-consent procedures. The research related to human use has been complied with all the relevant national regulations and institutional policies in accordance with the tenets of the Helsinki Declaration. ") + run("[Insert data-use permission / ethical clearance number.]", hl=True), BODYP)
x += sec("DATA AVAILABILITY")
x += P(run("The data that support the findings of this study are available from the Health Development Policy Agency (BKPK), Ministry of Health of the Republic of Indonesia. Restrictions apply to the availability of these data, which were used under license for this study. The analysis code, feature lists, exclusion list, and result tables are available from the corresponding author, [initials: ADJ], upon reasonable request. ") + run("[Optionally add a public code repository URL.]", hl=True), BODYP)

x += sec("REFERENCES")
unused = [k for k in REFS if k not in order]
assert not unused, unused
for n, k in enumerate(order, 1):
    x += P(run(f"[{n}]", sz=16) + "<w:r><w:rPr><w:sz w:val=\"16\"/></w:rPr><w:tab/></w:r>" + rich(REFS[k].replace(" et al.", " et al."), sz=16),
           '<w:widowControl w:val="0"/><w:tabs><w:tab w:val="left" w:pos="426"/></w:tabs><w:ind w:left="426" w:hanging="426"/><w:jc w:val="both"/>')

x += sec("BIOGRAPHIES OF AUTHORS")
emails = {"Ahmad Dedi Jubaedi": "dedi@unsera.ac.id", "Pulung Nurtantio Andono": "pulung@dsn.dinus.ac.id",
          "Nova Rijati": "nova@dosen.dinus.ac.id", "Ahmad Zainul Fanani": "a.zainul.fanani@dsn.dinus.ac.id"}
aff = {"1": "the Faculty of Computer Science, Universitas Serang Raya, Banten, Indonesia", "2": "the Faculty of Computer Science, Universitas Dian Nuswantoro, Semarang, Indonesia"}
brows = []
bt = '<w:tbl><w:tblPr><w:tblW w:w="8789" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid><w:gridCol w:w="1700"/><w:gridCol w:w="7089"/></w:tblGrid>'
for n, a in AUTHORS:
    orcid = " ORCID: 0000-0002-6574-5236." if n == "Ahmad Dedi Jubaedi" else " ORCID: [to be added]."
    txt = (P(run(n, b=True) + run(f" is with {aff[a]}.{orcid} ") + run("[Add degrees, research interests, Google Scholar, Scopus ID, and WoS ResearcherID.]", hl=True)
             + run(f" He/she can be contacted at email: {emails[n]}."), '<w:jc w:val="both"/>'))
    bt += ('<w:tr><w:tc><w:tcPr><w:tcW w:w="1700" w:type="dxa"/><w:tcBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders><w:vAlign w:val="center"/></w:tcPr>'
           + P(run("[Photo]", hl=True), '<w:jc w:val="center"/>') + '</w:tc><w:tc><w:tcPr><w:tcW w:w="7089" w:type="dxa"/><w:tcBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders></w:tcPr>'
           + txt + P("") + "</w:tc></w:tr>")
x += bt + "</w:tbl>" + empty()

doc_new = head + x + sect + "</w:body></w:document>"
if "xmlns:m=" not in head:
    doc_new = doc_new.replace("<w:document ", '<w:document xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" ', 1)
open(f"{OUT}/word/document.xml", "w", encoding="utf-8").write(doc_new)
open(f"{OUT}/word/_rels/document.xml.rels", "w", encoding="utf-8").write(rels)
# footer short title
f2 = open(f"{OUT}/word/footer2.xml", encoding="utf-8").read()
f2 = f2.replace("<w:t>Paper’s should be the fewest possible</w:t>", "<w:t>Anthropometric data leakage inflates machine</w:t>")
f2 = f2.replace('<w:t xml:space="preserve">that accurately describe </w:t>', '<w:t xml:space="preserve">learning performance </w:t>')
f2 = f2.replace("<w:t>(First Author)</w:t>", "<w:t>(Ahmad Dedi Jubaedi)</w:t>")
open(f"{OUT}/word/footer2.xml", "w", encoding="utf-8").write(f2)
print("refs:", len(order), "figs/eqs ok")
