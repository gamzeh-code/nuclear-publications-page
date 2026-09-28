#!/usr/bin/env python3
"""Generate the public news listing, homepage widget and detail pages."""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "news.json"
DETAIL_DIR = ROOT / "news"

MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def valid_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def display_date(iso_date: str) -> str:
    parsed = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return f"{MONTHS[parsed.month]} {parsed.year}"


def paragraphs(value: str) -> str:
    blocks = [part.strip() for part in re.split(r"\n\s*\n", value or "") if part.strip()]
    return "\n".join(f"<p>{esc(part).replace(chr(10), '<br>')}</p>" for part in blocks)


def load_news() -> list[dict]:
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("news.json bir JSON listesi olmalıdır.")

    required = {"slug", "date", "category", "title", "summary"}
    seen: set[str] = set()
    result: list[dict] = []
    for index, item in enumerate(raw, start=1):
        missing = required - set(item)
        if missing:
            raise ValueError(f"{index}. haberde eksik alanlar: {', '.join(sorted(missing))}")
        slug = str(item["slug"]).strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"Geçersiz slug: {slug}")
        if slug in seen:
            raise ValueError(f"Tekrarlanan slug: {slug}")
        seen.add(slug)
        datetime.strptime(str(item["date"]), "%Y-%m-%d")
        if item.get("published", True):
            result.append(item)
    return sorted(result, key=lambda item: (item["date"], item["slug"]), reverse=True)


BASE_CSS = """
:root{--navy:#0a2239;--blue:#0673ad;--muted:#6f7d88;--line:#dbe4ea;--pale:#eef8fb}
*{box-sizing:border-box}html,body{margin:0;padding:0;background:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--navy)}
a{color:inherit}.tag{display:inline-block;color:var(--blue);font-size:9px;font-weight:800;letter-spacing:.075em;text-transform:uppercase}
.date{color:var(--blue);font-size:11px;font-weight:800}.category{margin-left:8px;color:#87949d;font-size:9px;font-weight:800;letter-spacing:.065em;text-transform:uppercase}
.empty{padding:28px;border:1px solid var(--line);border-radius:16px;color:var(--muted);background:#fff}
"""


HEIGHT_SCRIPT = """
<script>
(function(){
  var last=-1,timer=null,type=document.body.dataset.heightMessage;
  function height(){return Math.ceil(document.documentElement.scrollHeight+2)}
  function send(force){if(window.parent===window||!type)return;var h=height();if(h<100)return;if(!force&&Math.abs(h-last)<2)return;last=h;window.parent.postMessage({type:type,height:h},"*")}
  function schedule(force){window.requestAnimationFrame(function(){send(force)})}
  document.addEventListener("DOMContentLoaded",function(){schedule(true)});
  window.addEventListener("load",function(){schedule(true);window.setTimeout(function(){send(true)},250)});
  window.addEventListener("resize",function(){clearTimeout(timer);timer=window.setTimeout(function(){send(false)},120)});
  if("ResizeObserver" in window){new ResizeObserver(function(){send(false)}).observe(document.documentElement)}
})();
</script>
"""


def document(title: str, body: str, css: str, message_type: str) -> str:
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><style>{BASE_CSS}{css}</style></head>
<body data-height-message="{esc(message_type)}">{body}{HEIGHT_SCRIPT}</body></html>
"""


def detail_href(item: dict) -> str:
    external = valid_url(str(item.get("external_url", "")))
    return external or f"news/{esc(item['slug'])}.html"


def generate_latest(items: list[dict]) -> None:
    latest = items[:4]
    if not latest:
        body = '<p class="empty">Henüz yayımlanmış haber bulunmuyor.</p>'
    else:
        feature = next((item for item in latest if item.get("featured")), latest[0])
        others = [item for item in latest if item is not feature]
        image = valid_url(str(feature.get("image_url", "")))
        visual_class = "visual has-image" if image else "visual"
        image_html = f'<div class="visual-logo"><img src="{esc(image)}" alt="{esc(feature.get("image_alt"))}"></div>' if image else ""
        note = esc(feature.get("image_note") or feature.get("kicker") or feature["category"])
        feature_html = f"""
<article class="featured">
  <div class="{visual_class}"><span class="kicker">{esc(feature.get('kicker') or feature['category'])}</span>{image_html}<strong>{note}</strong><span class="year">{esc(str(feature['date'])[:4])}</span></div>
  <div class="copy"><div><span class="date">{display_date(feature['date'])}</span><span class="category">{esc(feature['category'])}</span></div>
  <h3>{esc(feature['title'])}</h3><p>{esc(feature['summary'])}</p>
  <a class="more" href="{detail_href(feature)}" target="_blank" rel="noopener">Haberi incele →</a></div>
</article>"""
        list_html = "".join(f"""
<article class="news-item"><div><span class="date">{display_date(item['date'])}</span><span class="category">{esc(item['category'])}</span></div>
<h4><a href="{detail_href(item)}" target="_blank" rel="noopener">{esc(item['title'])}</a></h4></article>""" for item in others)
        body = f'<div class="latest-wrap">{feature_html}<div class="news-list">{list_html}</div></div>'

    css = """
.latest-wrap{display:grid;grid-template-columns:1.12fr .88fr;gap:18px;padding:1px}
.featured,.news-list{border:1px solid var(--line);border-radius:16px;background:#fff;overflow:hidden;transition:transform .2s ease,box-shadow .2s ease}
.featured:hover,.news-list:hover{transform:translateY(-3px);box-shadow:0 13px 30px rgba(24,50,70,.09)}
.featured{display:grid;grid-template-columns:.82fr 1.18fr;min-height:300px}.visual{position:relative;display:flex;flex-direction:column;justify-content:flex-end;min-height:300px;padding:28px;overflow:hidden;background:linear-gradient(145deg,#0b2943,#0f4d6b 68%,#146d8b);color:#fff}
.visual:after{content:"";position:absolute;width:150px;height:150px;right:-58px;bottom:-58px;border:1px solid rgba(132,223,239,.32);border-radius:50%}.visual .year{position:absolute;left:-10px;top:12px;color:rgba(255,255,255,.075);font:700 108px/1 Georgia,serif}
.kicker{position:relative;z-index:1;width:max-content;max-width:100%;margin-bottom:12px;padding:5px 9px;border:1px solid rgba(255,255,255,.22);border-radius:999px;color:#d9f7fb;font-size:9px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.visual strong{position:relative;z-index:1;display:block;max-width:225px;font:500 24px/1.17 Georgia,serif}.visual-logo{position:relative;z-index:1;display:flex;width:205px;padding:12px 14px;margin-bottom:18px;border-radius:14px;background:#fff}.visual-logo img{width:100%;height:auto;object-fit:contain}
.copy{padding:30px 28px}.copy h3{margin:12px 0;color:var(--navy);font-size:20px;line-height:1.38;font-weight:500}.copy p{margin:0;color:var(--muted);font-size:13px;line-height:1.68}.more{display:inline-block;margin-top:18px;color:var(--navy);font-size:12px;font-weight:800;text-decoration:none}.more:hover{color:var(--blue);text-decoration:underline}
.news-list{padding:2px 22px}.news-item{padding:20px 0;border-bottom:1px solid var(--line)}.news-item:last-child{border:0}.news-item h4{margin:7px 0 0;font-size:14px;line-height:1.52;font-weight:500}.news-item h4 a{text-decoration:none}.news-item h4 a:hover{color:var(--blue)}
@media(max-width:900px){.latest-wrap{grid-template-columns:1fr}}@media(max-width:620px){.featured{grid-template-columns:1fr}.visual{min-height:220px}.visual-logo{width:180px}}
"""
    (ROOT / "latest-news.html").write_text(document("Grubumuzdan Haberler", body, css, "latest-news-height"), encoding="utf-8")


def generate_listing(items: list[dict]) -> None:
    cards = "".join(f"""
<article class="card"><div class="card-top"><span class="tag">{esc(item['category'])}</span><span class="date">{display_date(item['date'])}</span></div>
<h2>{esc(item['title'])}</h2><p>{esc(item['summary'])}</p><a href="{detail_href(item)}" target="_blank" rel="noopener">Haberi incele →</a></article>""" for item in items)
    body = f'<main><div class="grid">{cards or "<p class=\"empty\">Henüz yayımlanmış haber bulunmuyor.</p>"}</div></main>'
    css = """
main{padding:1px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.card{display:flex;min-height:245px;flex-direction:column;padding:24px;border:1px solid var(--line);border-top:3px solid #43bfd7;border-radius:16px;background:#fff;transition:transform .2s ease,box-shadow .2s ease}.card:hover{transform:translateY(-4px);box-shadow:0 13px 30px rgba(24,50,70,.10)}.card-top{display:flex;justify-content:space-between;gap:12px}.card h2{margin:18px 0 12px;font:500 20px/1.38 Georgia,serif}.card p{margin:0 0 20px;color:var(--muted);font-size:13px;line-height:1.68}.card>a{margin-top:auto;color:var(--blue);font-size:12px;font-weight:800;text-decoration:none}.card>a:hover{text-decoration:underline}@media(max-width:920px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){.grid{grid-template-columns:1fr}.card{min-height:0}}
"""
    (ROOT / "news.html").write_text(document("Haberlerimiz", body, css, "news-height"), encoding="utf-8")


def generate_details(items: list[dict]) -> None:
    if DETAIL_DIR.exists():
        shutil.rmtree(DETAIL_DIR)
    DETAIL_DIR.mkdir()
    css = """
.detail{max-width:900px;margin:0 auto;padding:34px;border:1px solid var(--line);border-top:3px solid #43bfd7;border-radius:18px;background:#fff}.detail h1{margin:16px 0 18px;font:500 34px/1.22 Georgia,serif}.lead{color:#355267;font-size:16px;line-height:1.7}.content{margin-top:26px;padding-top:22px;border-top:1px solid var(--line);color:#455e6d;font-size:14px;line-height:1.8}.hero{width:100%;max-height:390px;margin:24px 0 0;border-radius:14px;object-fit:contain;background:#f5f8fa}.back{display:inline-block;margin-top:26px;color:var(--blue);font-size:12px;font-weight:800;text-decoration:none}@media(max-width:620px){.detail{padding:24px}.detail h1{font-size:28px}}
"""
    for item in items:
        image = valid_url(str(item.get("image_url", "")))
        image_html = f'<img class="hero" src="{esc(image)}" alt="{esc(item.get("image_alt"))}">' if image else ""
        body = f"""<main class="detail"><div><span class="date">{display_date(item['date'])}</span><span class="category">{esc(item['category'])}</span></div>
<h1>{esc(item['title'])}</h1><p class="lead">{esc(item['summary'])}</p>{image_html}<div class="content">{paragraphs(str(item.get('content') or item['summary']))}</div>
<a class="back" href="../news.html">← Tüm haberler</a></main>"""
        (DETAIL_DIR / f"{item['slug']}.html").write_text(document(item["title"], body, css, ""), encoding="utf-8")


def main() -> None:
    items = load_news()
    generate_latest(items)
    generate_listing(items)
    generate_details(items)
    print(f"{len(items)} haberden latest-news.html, news.html ve ayrıntı sayfaları üretildi.")


if __name__ == "__main__":
    main()
