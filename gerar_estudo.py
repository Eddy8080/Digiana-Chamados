#!/usr/bin/env python3
"""Regenera chamados.html a partir de chamados.md.

Uso:
    python gerar_estudo.py

Requer o pacote `markdown` (pip install markdown). É uma dependência apenas
deste script de documentação — não deve ser adicionada ao requirements.txt
do app Django.

O que o script faz:
  1. Lê chamados.md e converte para HTML (fenced code, tabelas GFM, listas).
  2. Gera automaticamente o índice lateral (#toc) a partir dos títulos
     (H1-H6), com o mesmo algoritmo de slug historicamente usado no arquivo
     (minúsculas, acentos removidos, espaços/underscores viram "-", demais
     símbolos descartados), com desambiguação automática de IDs repetidos.
  3. Envolve blocos de código em <div class="code-block"><span class=
     "lang-badge">...</span>...</div> e tabelas em <div class="tbl-wrap">,
     replicando a estrutura visual usada no arquivo original.
  4. Injeta tudo no mesmo layout/CSS/JS (sidebar fixa, dark/light mode,
     busca no índice, scroll-spy, impressão) e grava chamados.html.

O CSS e o JS do visualizador ficam embutidos neste script como constantes
(CSS / SCRIPT) — eles não dependem do conteúdo do markdown, então editar o
visual do documento consiste em editar essas constantes aqui, não em mexer
manualmente no chamados.html gerado.
"""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from pathlib import Path

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    sys.exit(
        "Dependência ausente: o pacote 'markdown' não está instalado.\n"
        "Instale com:\n\n"
        "    pip install markdown\n"
    )

BASE_DIR = Path(__file__).resolve().parent
MD_PATH = BASE_DIR / "chamados.md"
HTML_PATH = BASE_DIR / "chamados.html"

PAGE_TITLE = "Digiana — Documentação Técnica"
NAV_BRAND = "DIGIANA"
NAV_SUBTITLE = "Sistema de Chamados"
TOPBAR_TITLE = "Digiana — Sistema de Chamados"
TOPBAR_META = "Documentação técnica"
TOC_SECTION_LABEL = "Navegar — role para ver todos os tópicos"


# ──────────────────────────────────────────────────────────────────────────
# Slug de headings — mesmo algoritmo usado historicamente no chamados.html:
# NFKD + remove acentos, minúsculas, espaço/underscore vira separador,
# qualquer outro símbolo (pontuação, barras, parênteses...) é descartado
# sem inserir separador, hifens repetidos colapsam em um só.
# ──────────────────────────────────────────────────────────────────────────
def slugify(value: str, separator: str = "-") -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[\s_]+", separator, value)
    value = re.sub(r"[^a-z0-9" + re.escape(separator) + "]", "", value)
    value = re.sub(re.escape(separator) + "+", separator, value)
    return value.strip(separator)


# ──────────────────────────────────────────────────────────────────────────
# Pós-processamento do HTML convertido
# ──────────────────────────────────────────────────────────────────────────
_CODE_BLOCK_RE = re.compile(
    r'<pre><code(?: class="language-([\w+-]+)")?>(.*?)</code></pre>',
    re.DOTALL,
)


def wrap_code_blocks(body: str) -> str:
    """Envolve cada bloco de código em .code-block + badge de linguagem,
    igual ao padrão visual do chamados.html. Fences sem linguagem (```)
    recebem o rótulo "text", como no arquivo original."""

    def repl(m: re.Match) -> str:
        lang = m.group(1) or "text"
        content = m.group(2)
        return (
            f'<div class="code-block"><span class="lang-badge">{lang}</span>'
            f'<pre><code class="language-{lang}">{content}</code></pre></div>'
        )

    return _CODE_BLOCK_RE.sub(repl, body)


_TABLE_RE = re.compile(r"<table>.*?</table>", re.DOTALL)


def wrap_tables(body: str) -> str:
    return _TABLE_RE.sub(lambda m: f'<div class="tbl-wrap">{m.group(0)}</div>', body)


def normalize_hr(body: str) -> str:
    # python-markdown emite "<hr />"; o arquivo original usa "<hr>".
    return body.replace("<hr />", "<hr>")


# ──────────────────────────────────────────────────────────────────────────
# Índice lateral (#toc), a partir dos toc_tokens do próprio conversor
# ──────────────────────────────────────────────────────────────────────────
def build_toc(tokens: list[dict]) -> str:
    parts = [f'<div class="toc-section-label">{html.escape(TOC_SECTION_LABEL)}</div>']

    def walk(items: list[dict]) -> None:
        for item in items:
            level = item["level"]
            anchor = item["id"]
            label = html.escape(item["name"], quote=True)
            pad = (level - 1) * 14
            parts.append(
                f'<a href="#{anchor}" class="toc-l{level}" '
                f'style="padding-left:{pad}px" title="{label}">{label}</a>'
            )
            walk(item["children"])

    walk(tokens)
    return "\n".join(parts)


# ──────────────────────────────────────────────────────────────────────────
# Conversão principal
# ──────────────────────────────────────────────────────────────────────────
def convert(markdown_text: str) -> tuple[str, str]:
    md = markdown.Markdown(
        extensions=[
            "fenced_code",
            "tables",
            "sane_lists",
            TocExtension(slugify=slugify, permalink=False, anchorlink=False),
        ]
    )
    content_html = md.convert(markdown_text)
    content_html = wrap_code_blocks(content_html)
    content_html = wrap_tables(content_html)
    content_html = normalize_hr(content_html)
    toc_html = build_toc(md.toc_tokens)
    return content_html, toc_html


# ──────────────────────────────────────────────────────────────────────────
# CSS do visualizador — não depende do conteúdo do markdown.
# ──────────────────────────────────────────────────────────────────────────
CSS = """
/* ── Variaveis de tema ────────────────────────────────────────────────────── */
:root{
  --bg:#0d1117;--surf:#161b22;--surf2:#21262d;--bord:#30363d;
  --txt:#e6edf3;--muted:#8b949e;--acc:#58a6ff;--acc2:#ffa657;
  --code-bg:#161b22;--code-txt:#e6edf3;
  --bq-bord:#3d444d;--bq-bg:#161b22;
  --tbl-head:#21262d;--tbl-stripe:#0d1117;
  --side-bg:#010409;--side-w:290px;
  --h1:#79c0ff;--h2:#ffa657;--h3:#a5d6ff;--h4:#d2a8ff;
  --badge-bg:#21262d;--badge-txt:#8b949e;
  --link:#58a6ff;
}
[data-theme="light"]{
  --bg:#ffffff;--surf:#f6f8fa;--surf2:#eaeef2;--bord:#d0d7de;
  --txt:#1f2328;--muted:#656d76;--acc:#0969da;--acc2:#cf222e;
  --code-bg:#f6f8fa;--code-txt:#1f2328;
  --bq-bord:#d0d7de;--bq-bg:#f6f8fa;
  --tbl-head:#f6f8fa;--tbl-stripe:#ffffff;
  --side-bg:#f6f8fa;
  --h1:#0550ae;--h2:#cf222e;--h3:#0969da;--h4:#6e40c9;
  --badge-bg:#eaeef2;--badge-txt:#57606a;
  --link:#0969da;
}

/* ── Reset ──────────────────────────────────────────────────────────────────*/
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  background:var(--bg);color:var(--txt);line-height:1.75;font-size:15px;
  display:flex;min-height:100vh;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
#sidebar{
  width:var(--side-w);min-height:100vh;
  background:var(--side-bg);border-right:1px solid var(--bord);
  position:fixed;top:0;left:0;overflow-y:scroll;overflow-x:hidden;
  display:flex;flex-direction:column;
  scrollbar-width:thin;scrollbar-color:var(--muted) var(--surf2);
  z-index:100;
}
#sidebar::-webkit-scrollbar{width:7px}
#sidebar::-webkit-scrollbar-track{background:var(--surf2);border-radius:4px}
#sidebar::-webkit-scrollbar-thumb{background:var(--muted);border-radius:4px}
#sidebar::-webkit-scrollbar-thumb:hover{background:var(--acc)}
#sidebar-header{
  padding:18px 16px 14px;border-bottom:1px solid var(--bord);
  position:sticky;top:0;background:var(--side-bg);z-index:2;
}
#sidebar-header .brand{font-size:13px;font-weight:700;color:var(--acc);letter-spacing:.5px}
#sidebar-header .subtitle{font-size:11px;color:var(--muted);margin-top:2px}
#toc{padding:12px 8px 40px}
.toc-section-label{
  font-size:10px;font-weight:700;color:var(--muted);letter-spacing:1.2px;
  text-transform:uppercase;padding:10px 8px 4px;
}
#toc a{
  display:block;font-size:12.5px;color:var(--muted);text-decoration:none;
  padding:3px 8px;border-radius:5px;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;transition:background .15s,color .15s;
}
#toc a:hover{background:var(--surf2);color:var(--txt)}
#toc a.active{background:var(--surf2);color:var(--acc)}
#toc a.toc-l1{font-weight:700;font-size:13px;color:var(--txt);margin-top:6px}
#toc a.toc-l2{font-weight:600;margin-top:2px}
#toc a.toc-l3{color:var(--muted)}
#toc a.toc-l4{opacity:.8}

/* ── Topbar ──────────────────────────────────────────────────────────────── */
#topbar{
  position:fixed;top:0;left:var(--side-w);right:0;height:52px;
  background:var(--surf);border-bottom:1px solid var(--bord);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 32px;z-index:99;
  backdrop-filter:blur(8px);
}
#topbar .title{font-size:14px;font-weight:600;color:var(--txt)}
#topbar .meta{font-size:12px;color:var(--muted)}
#ctrl{display:flex;gap:10px;align-items:center}
button{
  background:var(--surf2);border:1px solid var(--bord);color:var(--txt);
  font-size:12px;padding:5px 12px;border-radius:6px;cursor:pointer;
  transition:background .15s;
}
button:hover{background:var(--bord)}

/* ── Conteudo principal ──────────────────────────────────────────────────── */
#content{
  margin-left:var(--side-w);margin-top:52px;
  padding:44px 56px 80px;max-width:900px;width:100%;flex:1;
}

/* ── Titulos ─────────────────────────────────────────────────────────────── */
h1{font-size:2rem;color:var(--h1);border-bottom:2px solid var(--bord);padding-bottom:12px;margin:40px 0 20px}
h2{font-size:1.5rem;color:var(--h2);border-bottom:1px solid var(--bord);padding-bottom:8px;margin:36px 0 16px}
h3{font-size:1.2rem;color:var(--h3);margin:28px 0 12px}
h4{font-size:1rem;color:var(--h4);margin:22px 0 10px;font-weight:600}
h5,h6{font-size:.9rem;color:var(--muted);margin:16px 0 8px}

/* ── Paragrafos e texto ───────────────────────────────────────────────────── */
p{margin:10px 0;}
strong{font-weight:700}
em{font-style:italic}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
hr{border:none;border-top:1px solid var(--bord);margin:32px 0}

/* ── Codigo inline ───────────────────────────────────────────────────────── */
code{
  background:var(--code-bg);color:#f47067;
  font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  font-size:.85em;padding:2px 6px;border-radius:4px;
  border:1px solid var(--bord);
}

/* ── Bloco de codigo ─────────────────────────────────────────────────────── */
.code-block{
  position:relative;margin:18px 0;border:1px solid var(--bord);border-radius:8px;
  overflow:hidden;background:var(--code-bg);
}
.lang-badge{
  display:block;padding:5px 14px;background:var(--badge-bg);color:var(--badge-txt);
  font-size:11px;font-family:monospace;font-weight:700;text-transform:lowercase;
  border-bottom:1px solid var(--bord);letter-spacing:.5px;
}
.code-block pre{
  margin:0;padding:16px 20px;overflow-x:auto;
  scrollbar-width:thin;scrollbar-color:var(--bord) transparent;
}
.code-block code{
  background:none;border:none;color:var(--code-txt);
  font-size:.855em;line-height:1.6;padding:0;
  white-space:pre;font-family:"SFMono-Regular",Consolas,monospace;
}

/* ── Tabelas ─────────────────────────────────────────────────────────────── */
.tbl-wrap{overflow-x:auto;margin:18px 0;border-radius:8px;border:1px solid var(--bord)}
table{width:100%;border-collapse:collapse;font-size:.9em}
thead{background:var(--tbl-head)}
th{
  padding:10px 14px;text-align:left;font-weight:600;
  border-bottom:2px solid var(--bord);white-space:nowrap;color:var(--acc)
}
td{padding:9px 14px;border-bottom:1px solid var(--bord)}
tbody tr:last-child td{border-bottom:none}
tbody tr:nth-child(even){background:var(--tbl-stripe)}
tbody tr:hover{background:var(--surf2)}

/* ── Blockquote ──────────────────────────────────────────────────────────── */
blockquote{
  border-left:4px solid var(--acc2);background:var(--bq-bg);
  padding:12px 16px;margin:16px 0;border-radius:0 8px 8px 0;
  color:var(--muted);font-style:italic;
}
blockquote strong{color:var(--acc2)}

/* ── Listas ──────────────────────────────────────────────────────────────── */
ul,ol{padding-left:1.6em;margin:10px 0}
li{margin:4px 0;}
li p{margin:0}

/* ── Barra de pesquisa ──────────────────────────────────────────────────── */
.search-wrap{position:relative;margin-top:10px}
#toc-search{
  width:100%;background:var(--surf2);border:1px solid var(--bord);
  color:var(--txt);font-size:12px;padding:6px 28px 6px 10px;
  border-radius:6px;outline:none;transition:border-color .15s;font-family:inherit;
}
#toc-search:focus{border-color:var(--acc)}
#toc-search::placeholder{color:var(--muted)}
.search-clear{
  position:absolute;right:4px;top:50%;transform:translateY(-50%);
  background:none!important;border:none!important;color:var(--muted);
  font-size:11px;padding:2px 6px;cursor:pointer;display:none;line-height:1;
}
.search-clear:hover{color:var(--txt)!important;background:none!important}
#search-info{font-size:10px;color:var(--muted);padding:5px 0 0;min-height:16px;letter-spacing:.3px}
#search-info.no-result{color:#f47067}
.toc-match-hl{background:var(--acc2);color:#000!important;border-radius:2px;padding:0 2px}

/* ── Impressao ────────────────────────────────────────────────────────────── */
@media print{
  #sidebar,#topbar{display:none!important}
  #content{margin:0;padding:20px;max-width:100%}
  body{display:block;font-size:12pt;color:#000;background:#fff}
  h1,h2,h3,h4{color:#000!important}
  a{color:#000;text-decoration:underline}
  .code-block{border:1px solid #ccc}
  .tbl-wrap{border:1px solid #ccc}
  th{background:#eee!important;color:#000!important}
  tbody tr:nth-child(even){background:#f9f9f9!important}
  pre{white-space:pre-wrap;word-break:break-all}
}

/* ── Responsivo ──────────────────────────────────────────────────────────── */
@media(max-width:900px){
  #sidebar{transform:translateX(-100%);transition:transform .25s}
  #sidebar.open{transform:translateX(0)}
  #topbar{left:0}
  #content{margin-left:0;padding:80px 20px 60px}
  :root{--side-w:0px}
}
"""


# ──────────────────────────────────────────────────────────────────────────
# JS do visualizador — tema, scroll-spy, menu mobile e busca no índice.
# Não depende do conteúdo do markdown.
# ──────────────────────────────────────────────────────────────────────────
SCRIPT = """
// ── Restaura tema salvo ──────────────────────────────────────────────────────
(function(){
  try{
    var t=localStorage.getItem('digiana-docs-theme');
    if(t==='light'||t==='dark') document.documentElement.setAttribute('data-theme',t);
  }catch(e){}
})();

// ── Scroll spy ───────────────────────────────────────────────────────────────
var _headings = Array.from(document.querySelectorAll('#content h1,#content h2,#content h3,#content h4'));
var _links    = Array.from(document.querySelectorAll('#toc a'));

function updateActive() {
  var scrollY = window.scrollY + 80;
  var current = null;
  for (var k = 0; k < _headings.length; k++) {
    if (_headings[k].getBoundingClientRect().top + window.scrollY <= scrollY) {
      current = _headings[k].id;
    }
  }
  _links.forEach(function(a) {
    var href = a.getAttribute('href');
    if (href === '#' + current) {
      a.classList.add('active');
      // scroll into view dentro da sidebar
      var rect = a.getBoundingClientRect();
      var sb   = document.getElementById('sidebar');
      if (rect.top < 80 || rect.bottom > window.innerHeight - 20) {
        a.scrollIntoView({block:'nearest', behavior:'smooth'});
      }
    } else {
      a.classList.remove('active');
    }
  });
}
window.addEventListener('scroll', updateActive, {passive: true});
updateActive();

// ── Menu mobile ────────────────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ── Pesquisa no TOC ─────────────────────────────────────────────────────────
(function () {
  var input    = document.getElementById('toc-search');
  var btnClear = document.getElementById('search-clear');
  var infoEl   = document.getElementById('search-info');
  var allLinks = Array.from(document.querySelectorAll('#toc a'));
  var allLabels= Array.from(document.querySelectorAll('.toc-section-label'));

  allLinks.forEach(function(a) {
    a._origHTML = a.innerHTML;
    a._origText = a.textContent.toLowerCase();
  });

  function hlText(html, q) {
    var idx = html.toLowerCase().indexOf(q);
    if (idx === -1) return html;
    return html.slice(0, idx)
      + '<mark class="toc-match-hl">' + html.slice(idx, idx + q.length) + '</mark>'
      + hlText(html.slice(idx + q.length), q);
  }

  function applySearch(raw) {
    var q = raw.trim().toLowerCase();
    btnClear.style.display = q ? 'block' : 'none';
    if (!q) {
      allLinks.forEach(function(a) { a.style.display = ''; a.innerHTML = a._origHTML; });
      allLabels.forEach(function(l) { l.style.display = ''; });
      infoEl.textContent = '';
      infoEl.className = '';
      return;
    }
    var count = 0;
    allLinks.forEach(function(a) {
      if (a._origText.includes(q)) {
        a.style.display = '';
        a.innerHTML = hlText(a._origHTML, q);
        count++;
      } else {
        a.style.display = 'none';
      }
    });
    allLabels.forEach(function(l) {
      var sib = l.nextElementSibling;
      var hasVisible = false;
      while (sib && !sib.classList.contains('toc-section-label')) {
        if (sib.tagName === 'A' && sib.style.display !== 'none') { hasVisible = true; break; }
        sib = sib.nextElementSibling;
      }
      l.style.display = hasVisible ? '' : 'none';
    });
    infoEl.textContent = count
      ? (count + ' resultado' + (count > 1 ? 's' : ''))
      : 'Nenhum resultado';
    infoEl.className = count ? '' : 'no-result';
  }

  input.addEventListener('input', function() { applySearch(input.value); });

  window.clearSearch = function() {
    input.value = '';
    applySearch('');
    input.focus();
  };

  document.addEventListener('keydown', function(e) {
    var active = document.activeElement;
    var isTyping = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA');
    if (!isTyping && e.key === '/') { e.preventDefault(); input.focus(); input.select(); }
    if (e.ctrlKey && e.key === 'f') { e.preventDefault(); input.focus(); input.select(); }
    if (e.key === 'Escape' && active === input) { clearSearch(); }
  });
})();
"""


PAGE_SKELETON = """<!DOCTYPE html>
<html lang="pt-br" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
__CSS__
</style>
</head>
<body>
<!-- Sidebar -->
<nav id="sidebar">
  <div id="sidebar-header">
    <div class="brand">__BRAND__</div>
    <div class="subtitle">__SUBTITLE__</div>
    <div class="search-wrap">
      <input id="toc-search" type="text" placeholder="&#128269; Buscar no manual..." autocomplete="off" spellcheck="false">
      <button class="search-clear" id="search-clear" onclick="clearSearch()" title="Limpar busca">&#10005;</button>
    </div>
    <div id="search-info"></div>
  </div>
  <div id="toc">
__TOC__
  </div>
</nav>
<!-- ── Topbar ──────────────────────────────────────────────────────────── -->
<div id="topbar">
  <div>
    <span class="title">__TOPBAR_TITLE__</span>
    <span class="meta" style="margin-left:12px">__TOPBAR_META__</span>
  </div>
  <div id="ctrl">
    <button onclick="(function(){var h=document.documentElement;var t=h.getAttribute('data-theme');var next=t==='dark'?'light':'dark';h.setAttribute('data-theme',next);try{localStorage.setItem('digiana-docs-theme',next);}catch(e){}}())">&#9728; / &#127769;</button>
    <button onclick="window.print()">Imprimir</button>
    <button onclick="toggleSidebar()" style="display:none" id="btn-menu">&#9776;</button>
  </div>
</div>

<!-- Conteudo -->
<div id="content">
__CONTENT__
</div>
<script>
__SCRIPT__
</script>
</body>
</html>
"""


def render_page(content_html: str, toc_html: str) -> str:
    page = PAGE_SKELETON
    page = page.replace("__TITLE__", html.escape(PAGE_TITLE))
    page = page.replace("__BRAND__", html.escape(NAV_BRAND))
    page = page.replace("__SUBTITLE__", html.escape(NAV_SUBTITLE))
    page = page.replace("__TOPBAR_TITLE__", html.escape(TOPBAR_TITLE))
    page = page.replace("__TOPBAR_META__", html.escape(TOPBAR_META))
    page = page.replace("__CSS__", CSS.strip("\n"))
    page = page.replace("__SCRIPT__", SCRIPT.strip("\n"))
    page = page.replace("__TOC__", toc_html)
    page = page.replace("__CONTENT__", content_html)
    return page


def main() -> None:
    if not MD_PATH.exists():
        sys.exit(f"Arquivo não encontrado: {MD_PATH}")

    markdown_text = MD_PATH.read_text(encoding="utf-8")
    content_html, toc_html = convert(markdown_text)
    page = render_page(content_html, toc_html)
    HTML_PATH.write_text(page, encoding="utf-8")

    print(f"OK — {HTML_PATH.name} regenerado a partir de {MD_PATH.name}")
    print(f"  {len(markdown_text):,} caracteres de markdown -> {len(page):,} caracteres de HTML")


if __name__ == "__main__":
    main()
