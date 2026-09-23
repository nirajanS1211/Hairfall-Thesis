"""Tiny LaTeX-subset to OMML (Word equation) converter for the equations used in the thesis."""
import re
from xml.sax.saxutils import escape

GREEK = {"nu": "ν", "phi": "φ", "chi": "χ", "theta": "θ", "Omega": "Ω", "kappa": "κ", "alpha": "α"}
SYMS = {"partial": "∂", "mid": "∣", "subseteq": "⊆", "setminus": "∖", "cdot": "⋅", "times": "×"}
SPACE = {",", ";", "!", "quad", " ", ":"}

RFONT = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/></w:rPr>'


def run(text, upright=False, script=False):
    props = ""
    if upright:
        props += '<m:sty m:val="p"/>'
    if script:
        props += '<m:scr m:val="script"/>'
    rpr = f"<m:rPr>{props}</m:rPr>" if props else ""
    return f'<m:r>{rpr}{RFONT}<m:t xml:space="preserve">{escape(text)}</m:t></m:r>'


def tokenize(s):
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+)", s[i:])
            if m:
                toks.append(("cmd", m.group(1)))
                i += len(m.group(0))
            else:
                nxt = s[i + 1]
                toks.append(("space",) if nxt in ",;!: " else ("char", nxt))
                i += 2
        elif c == "{":
            toks.append(("{",)); i += 1
        elif c == "}":
            toks.append(("}",)); i += 1
        elif c == "^":
            toks.append(("^",)); i += 1
        elif c == "_":
            toks.append(("_",)); i += 1
        elif c == " ":
            i += 1
        else:
            toks.append(("char", c)); i += 1
    return toks


class P:
    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def group(self):
        """Parse {...} and return omml string."""
        tok = self.next()
        assert tok[0] == "{", tok
        out = self.seq(stop=lambda k: k is not None and k[0] == "}")
        self.next()  # }
        return out

    def seq(self, stop, until_op=False):
        out = []
        while self.peek() is not None and not stop(self.peek()):
            tok = self.peek()
            if until_op and tok[0] == "char" and tok[1] in "+=":
                break
            out.append(self.atom())
        return "".join(out)

    def scripts(self, base):
        sub = sup = None
        while self.peek() is not None and self.peek()[0] in ("_", "^"):
            kind = self.next()[0]
            if self.peek()[0] == "{":
                arg = self.group()
            else:
                arg = self.atom_plain()
            if kind == "_":
                sub = arg
            else:
                sup = arg
        if sub is not None and sup is not None:
            return f"<m:sSubSup><m:e>{base}</m:e><m:sub>{sub}</m:sub><m:sup>{sup}</m:sup></m:sSubSup>"
        if sub is not None:
            return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"
        if sup is not None:
            return f"<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>"
        return base

    def atom_plain(self):
        tok = self.next()
        if tok[0] == "char":
            return run(tok[1])
        if tok[0] == "cmd":
            n = tok[1]
            if n in GREEK:
                return run(GREEK[n])
            if n in SYMS:
                return run(SYMS[n])
        return ""

    def atom(self):
        tok = self.next()
        k = tok[0]
        if k == "space":
            return ""
        if k == "{":
            self.i -= 1
            return self.scripts(self.group())
        if k == "char":
            return self.scripts(run(tok[1]))
        if k == "cmd":
            n = tok[1]
            if n in ("big", "Big", "bigg", "Bigg"):
                return ""
            if n in GREEK:
                return self.scripts(run(GREEK[n]))
            if n in SYMS:
                return self.scripts(run(SYMS[n]))
            if n == "quad":
                return ""
            if n in ("text", "mathrm"):
                self.next()  # {
                txt = ""
                while self.peek()[0] != "}":
                    t2 = self.next()
                    txt += t2[1] if t2[0] == "char" else " "
                self.next()
                return self.scripts(run(txt, upright=True))
            if n == "mathcal":
                self.next()
                letter = self.next()[1]
                self.next()
                return self.scripts(run(letter, script=True))
            if n == "hat":
                inner = self.group()
                base = f'<m:acc><m:accPr><m:chr m:val="̂"/></m:accPr><m:e>{inner}</m:e></m:acc>'
                return self.scripts(base)
            if n == "frac":
                num = self.group()
                den = self.group()
                return self.scripts(f"<m:f><m:num>{num}</m:num><m:den>{den}</m:den></m:f>")
            if n == "sqrt":
                inner = self.group()
                return self.scripts(f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{inner}</m:e></m:rad>')
            if n in ("sum", "int"):
                sub = sup = None
                while self.peek() is not None and self.peek()[0] in ("_", "^"):
                    kind = self.next()[0]
                    arg = self.group() if self.peek()[0] == "{" else self.atom_plain()
                    if kind == "_":
                        sub = arg
                    else:
                        sup = arg
                operand = self.seq(stop=lambda k2: k2 is not None and k2[0] == "}", until_op=True)
                chr_ = "∑" if n == "sum" else "∫"
                lim = '<m:limLoc m:val="undOvr"/>' if n == "sum" else '<m:limLoc m:val="subSup"/>'
                subhide = '<m:subHide m:val="1"/>' if sub is None else ""
                suphide = '<m:supHide m:val="1"/>' if sup is None else ""
                return (f'<m:nary><m:naryPr><m:chr m:val="{chr_}"/>{lim}{subhide}{suphide}</m:naryPr>'
                        f'<m:sub>{sub or ""}</m:sub><m:sup>{sup or ""}</m:sup><m:e>{operand}</m:e></m:nary>')
            if n == "left":
                beg = self.next()
                beg_c = beg[1] if beg[0] == "char" else "("
                inner_parts = []
                while not (self.peek()[0] == "cmd" and self.peek()[1] == "right"):
                    inner_parts.append(self.atom())
                self.next()  # \right
                end = self.next()
                end_c = end[1] if end[0] == "char" else ")"
                base = f'<m:d><m:dPr><m:begChr m:val="{escape(beg_c)}"/><m:endChr m:val="{escape(end_c)}"/></m:dPr><m:e>{"".join(inner_parts)}</m:e></m:d>'
                return self.scripts(base)
            if n == "right":
                return ""
            # unknown command: render name as upright text
            return self.scripts(run(n, upright=True))
        if k in ("^", "_"):
            return ""
        if k == "}":
            return ""
        return ""


def latex_to_omml(latex):
    toks = tokenize(latex)
    p = P(toks)
    body = p.seq(stop=lambda k: False)
    return f'<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">{body}</m:oMath>'


if __name__ == "__main__":
    from lxml import etree
    tests = [r"F_m(x) = F_{m-1}(x) + \nu\, h_m(x)",
             r"\mathcal{L}^{(t)} = \sum_{i} L\big(y_i,\; F_{t-1}(x_i) + h_t(x_i)\big) + \Omega(h_t)",
             r"r_{im} = -\left[\frac{\partial L\big(y_i, F(x_i)\big)}{\partial F(x_i)}\right]_{F = F_{m-1}}",
             r"\phi_j = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!\,(|F|-|S|-1)!}{|F|!}\Big[f_{S \cup \{j\}}(x) - f_S(x)\Big]",
             r"\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{Q K^{T}}{\sqrt{d_k}}\right) V",
             r"P(y_{test} \mid x_{test}, \mathcal{D}_{train}) = \int P(y_{test} \mid x_{test}, \theta)\, P(\theta \mid \mathcal{D}_{train})\, d\theta",
             r"\text{MAE} = \frac{1}{N}\sum_{i=1}^{N} \left| \hat{y}_i - y_i \right|",
             r"\chi^2 = \frac{(|b - c| - 1)^2}{b + c}"]
    for t in tests:
        x = latex_to_omml(t)
        etree.fromstring(x)
        print("ok", t[:40])
