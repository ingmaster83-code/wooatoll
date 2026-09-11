# -*- coding: utf-8 -*-
"""data/toll.json + gates.json -> 우아통행료(WooaToll) 정적 HTML 생성 (231K+ 페이지 규모)"""
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
BASE_URL = "https://wooatoll.wooahouse.com"
SITE_NAME = "우아통행료"
TODAY = date.today().isoformat()
YEAR = TODAY[:4]
AD_CLIENT = "ca-pub-6464921081676309"

VCLASS_LABEL = ["1종(승용차)", "2종(중형차)", "3종(대형차)", "4종(대형화물)", "5종(대형화물)", "6종(경차)"]

COUPANG_HTML = '''
<div class="coupang-partners" style="margin:28px auto 0;max-width:680px;padding:0 16px;text-align:center;">
  <script src="https://ads-partners.coupang.com/g.js"></script>
  <script>
    new PartnersCoupang.G({"id":980427,"trackingCode":"AF5600192","subId":"toll","template":"carousel","width":"680","height":"140"});
  </script>
</div>
'''
COUPANG_DISCLOSURE = '<p style="margin:6px 0 0;font-size:.68rem;opacity:.5;">이 페이지는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>'

def head_common(root):
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="naver-site-verification" content="0c8baeb462bcd985d686fd0043e23fc99d64a665" />
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={AD_CLIENT}" crossorigin="anonymous"></script>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%9B%A3%EF%B8%8F%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{root}css/style.css">
"""

HEADER_TMPL = """<header class="site-header">
  <div class="header-inner">
    <a href="{root}index.html" class="logo">🛣️ 우아통행료</a>
    <nav>
      <a href="{root}index.html">요금소 검색</a>
      <a href="{root}about.html">소개</a>
    </nav>
  </div>
</header>
"""

MOBILE_AD = f"""<div class="mobile-top-ad">
  <ins class="adsbygoogle" style="display:block;width:100%;min-height:60px" data-ad-client="{AD_CLIENT}" data-ad-slot="7080296704" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>
</div>"""


def ad_banner(slot="7080296704"):
    return (f'<div class="ad-banner"><ins class="adsbygoogle" style="display:block" data-ad-client="{AD_CLIENT}" '
            f'data-ad-slot="{slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
            f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')


def page_head(title, desc, canonical, root, extra_ld=""):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
{head_common(root)}
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="{SITE_NAME}">
{extra_ld}
</head>
"""


def footer_html(root):
    return f"""{COUPANG_HTML}
<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-disclaimer">본 정보는 한국도로공사 통행요금조회 공공데이터를 기반으로 합니다.<br>실제 통행료는 차종·하이패스 할인 등에 따라 달라질 수 있으니 참고용으로 확인하세요.</p>
    {COUPANG_DISCLOSURE}
    <p class="copyright">&copy; {YEAR} 우아통행료 · <a href="https://wooahouse.com" target="_blank">WooaHouse</a> · <a href="{root}privacy.html">개인정보처리방침</a></p>
  </div>
</footer>
</body>
</html>
"""


def fmt_won(v):
    return f"{v:,}원"


def eul_reul(word):
    if not word:
        return "를"
    last = word[-1]
    if not ("가" <= last <= "힣"):
        return "를"
    jong = (ord(last) - ord("가")) % 28
    return "를" if jong == 0 else "을"


def build_intro(dep, arr, charges, dest_count):
    c1 = charges[0]
    cmin, cmax = min(charges), max(charges)
    parts = [f"{dep}에서 {arr}{eul_reul(arr)} 이용할 때 통행료는 1종(승용차) 기준 {fmt_won(c1)}입니다."]
    if cmin != cmax:
        parts.append(f"차종별로는 최저 {fmt_won(cmin)}(6종 경차)부터 최고 {fmt_won(cmax)}(대형화물차)까지 차이가 납니다.")
    if dest_count > 1:
        parts.append(f"{dep}에서는 이곳을 포함해 총 {dest_count}개 목적지의 통행료를 확인할 수 있습니다.")
    parts.append("실제 결제 금액은 하이패스 할인, 명절 면제기간 등에 따라 달라질 수 있으니 참고용으로 확인하세요.")
    return " ".join(parts)


def gen_route_page(o):
    dep, arr = o["dep"], o["arr"]
    dep_slug, arr_slug = o["depSlug"], o["arrSlug"]
    charges = o["charges"]
    intro = build_intro(dep, arr, charges, o["depDestCount"])

    title = f"{dep}→{arr} 통행료 {YEAR} | {SITE_NAME}"
    desc = f"{dep}에서 {arr}까지 고속도로 통행료. 1종 {fmt_won(charges[0])}, 차종별(1~6종) 요금을 확인하세요."
    canonical = f"{BASE_URL}/{quote(dep_slug)}/{quote(arr_slug)}.html"

    rows = "".join(
        f"<tr><td>{VCLASS_LABEL[i]}</td><td>{fmt_won(charges[i])}</td></tr>" for i in range(6)
    )

    faq_ld = (
        '{"@type":"Question","name":"이 요금이 정확한가요?","acceptedAnswer":{"@type":"Answer",'
        '"text":"한국도로공사 공공데이터 기준이며, 실제 통행료는 하이패스 할인·명절 면제기간 등에 따라 달라질 수 있습니다. 정확한 금액은 한국도로공사 통행요금조회에서 다시 확인하세요."}}'
    )
    extra_ld = f'''  <script type="application/ld+json">
  {{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{faq_ld}]}}
  </script>'''

    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:680px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;">
    <a href="../index.html" style="color:#6B7280;">홈</a> ›
    <a href="index.html" style="color:#6B7280;">{dep}</a> › {arr}
  </nav>
  <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:6px;">🛣️ {dep} → {arr} 통행료</h1>
  <p style="color:#374151;line-height:1.75;margin:12px 0 20px;">{intro}</p>

  {MOBILE_AD}

  <table style="width:100%;border-collapse:collapse;font-size:.95rem;margin:20px 0;">
    <thead><tr style="text-align:left;color:#6B7280;border-bottom:2px solid #E5E7EB;"><th style="padding:8px 6px;">차종</th><th style="padding:8px 6px;">통행료</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <div style="margin:24px 0;padding:14px;background:#F9FAFB;border-radius:10px;font-size:.85rem;color:#6B7280;line-height:1.7;">
    ※ 하이패스 이용 시 자동 결제됩니다. 별도 예매·정산 절차가 없습니다.<br>
    ※ 명절 연휴 등 통행료 면제기간에는 무료입니다.
  </div>

  <details style="margin-top:16px;">
    <summary style="cursor:pointer;font-weight:600;padding:8px 0;">이 요금이 정확한가요?</summary>
    <p style="padding:6px 0;color:#374151;line-height:1.7;">한국도로공사 공공데이터 기준이며, 실제 통행료는 하이패스 할인·명절 면제기간 등에 따라 달라질 수 있습니다.</p>
  </details>

  <div style="margin-top:24px;padding:16px;border:1px dashed #E5E7EB;border-radius:10px;text-align:center;">
    <a href="index.html" style="color:#0D9488;font-weight:600;text-decoration:none;">📍 {dep} 다른 목적지 통행료 보기 →</a>
  </div>
</div>
"""
    head = page_head(title, desc, canonical, "../", extra_ld)
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../") + "\n" + body + footer_html("../")


def gen_gate_page(dep_name, dep_slug, routes_from):
    routes_from = sorted(routes_from, key=lambda r: r["arr"])
    c1s = [r["charges"][0] for r in routes_from]
    cheapest = min(routes_from, key=lambda r: r["charges"][0])
    priciest = max(routes_from, key=lambda r: r["charges"][0])

    title = f"{dep_name} 통행료 — 목적지 {len(routes_from)}곳 요금 {YEAR} | {SITE_NAME}"
    desc = (f"{dep_name}에서 출발하는 고속도로 통행료 {len(routes_from)}곳. "
            f"{cheapest['arr']} {fmt_won(cheapest['charges'][0])}부터 {priciest['arr']} {fmt_won(priciest['charges'][0])}까지, 차종별(1~6종) 요금을 확인하세요.")
    canonical = f"{BASE_URL}/{quote(dep_slug)}/index.html"

    intro = (f"{dep_name}에서 고속도로로 갈 수 있는 목적지는 총 {len(routes_from)}곳입니다. "
             f"1종(승용차) 기준 통행료는 최저 {cheapest['arr']} {fmt_won(cheapest['charges'][0])}부터 "
             f"최고 {priciest['arr']} {fmt_won(priciest['charges'][0])}까지입니다. "
             f"아래에서 목적지를 찾아 차종별 요금을 확인하세요(1종·6종 표시, 전체 차종은 각 목적지를 눌러 확인).")

    rows = "".join(
        f'<a id="{r["arrSlug"]}" href="#{r["arrSlug"]}" onclick="return toggleRow(this)" '
        f'data-name="{r["arr"]}" '
        f'style="display:block;padding:10px 12px;border:1px solid #E5E7EB;border-radius:8px;margin-bottom:6px;text-decoration:none;color:inherit;">'
        f'<div style="display:flex;justify-content:space-between;">'
        f'<span style="font-weight:600;">{r["arr"]}</span>'
        f'<span style="color:#6B7280;font-size:.85rem;">1종 {fmt_won(r["charges"][0])} · 6종 {fmt_won(r["charges"][5])}</span>'
        f'</div>'
        f'<div class="vclass-detail" style="display:none;margin-top:8px;font-size:.82rem;color:#374151;line-height:1.9;">'
        + "".join(f"{VCLASS_LABEL[i]} {fmt_won(r['charges'][i])}<br>" for i in range(6))
        + "</div></a>"
        for r in routes_from
    )

    body = f"""<div class="container" style="padding:20px 16px 40px;max-width:680px;margin:0 auto;">
  <nav style="font-size:.82rem;color:#6B7280;margin-bottom:14px;"><a href="../index.html" style="color:#6B7280;">홈</a> › {dep_name}</nav>
  <h1 style="font-size:1.4rem;font-weight:800;margin-bottom:6px;">🛣️ {dep_name} 통행료</h1>
  <p style="color:#374151;line-height:1.7;font-size:.9rem;margin-bottom:20px;">{intro}</p>

  {MOBILE_AD}

  <p style="font-size:.8rem;color:#9CA3AF;margin-bottom:8px;">목적지를 누르면 전체 차종(1~6종) 요금이 펼쳐집니다.</p>
  <div>{rows}</div>

  <div style="margin-top:20px;padding:14px;background:#F9FAFB;border-radius:10px;font-size:.85rem;color:#6B7280;line-height:1.7;">
    ※ 하이패스 이용 시 자동 결제됩니다. 실제 통행료는 할인·면제기간에 따라 달라질 수 있습니다.
  </div>
</div>
<script>
function toggleRow(el){{
  var d = el.querySelector('.vclass-detail');
  d.style.display = d.style.display === 'none' ? 'block' : 'none';
  return false;
}}
window.addEventListener('DOMContentLoaded', function(){{
  if(location.hash){{
    var el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if(el){{ el.scrollIntoView({{block:'center'}}); toggleRow(el); }}
  }}
}});
</script>
"""
    head = page_head(title, desc, canonical, "../")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="../") + "\n" + body + footer_html("../")


def gen_index(gates, total_routes, dep_gate_slugs=None):
    title = f"전국 고속도로 통행료 조회 {YEAR} | {SITE_NAME}"
    desc = f"전국 요금소 {len(gates)}곳, {total_routes:,}개 구간의 고속도로 통행료를 차종별로 무료 조회하세요."
    canonical = f"{BASE_URL}/"

    all_options = "".join(f'<option value="{g["slug"]}">{g["name"]}</option>' for g in sorted(gates, key=lambda x: x["name"]))
    dep_pool = [g for g in gates if dep_gate_slugs is None or g["slug"] in dep_gate_slugs]
    dep_options = "".join(f'<option value="{g["slug"]}">{g["name"]}</option>' for g in sorted(dep_pool, key=lambda x: x["name"]))

    body = f"""<div class="hero" style="background:linear-gradient(135deg,#0D9488,#0891B2);color:#fff;padding:44px 16px;text-align:center;">
  <h1 style="font-size:1.7rem;font-weight:800;margin-bottom:8px;">🛣️ 전국 고속도로 통행료 조회</h1>
  <p style="opacity:.92;">출발·도착 요금소를 선택하면 차종별(1~6종) 통행료를 바로 확인할 수 있어요</p>
</div>

<div class="container" style="padding:20px 16px 40px;max-width:680px;margin:0 auto;">
  {MOBILE_AD}

  <div style="background:#F9FAFB;border-radius:12px;padding:18px;margin:16px 0 28px;">
    <label style="font-size:.85rem;font-weight:600;color:#374151;">출발 요금소</label>
    <select id="depSel" style="width:100%;padding:10px;margin:6px 0 12px;border-radius:8px;border:1px solid #E5E7EB;">
      <option value="">선택하세요</option>{dep_options}
    </select>
    <label style="font-size:.85rem;font-weight:600;color:#374151;">도착 요금소</label>
    <select id="arrSel" style="width:100%;padding:10px;margin:6px 0 12px;border-radius:8px;border:1px solid #E5E7EB;">
      <option value="">선택하세요</option>{all_options}
    </select>
    <button onclick="goRoute()" style="width:100%;padding:12px;border:none;border-radius:8px;background:#0D9488;color:#fff;font-weight:700;cursor:pointer;">통행료 조회</button>
    <p id="err" style="display:none;color:#DC2626;font-size:.82rem;margin-top:8px;">출발·도착 요금소를 모두 선택해주세요.</p>
  </div>

  <p style="font-size:.85rem;color:#6B7280;">전국 {len(gates)}개 요금소, {total_routes:,}개 구간의 통행료 정보를 제공합니다.</p>

  {ad_banner()}
</div>
<script>
function goRoute(){{
  var d = document.getElementById('depSel').value;
  var a = document.getElementById('arrSel').value;
  if(!d || !a || d === a){{document.getElementById('err').style.display='block';return;}}
  location.href = d + '/index.html#' + a;
}}
</script>
"""
    head = page_head(title, desc, canonical, "")
    return head + "<body>\n\n" + HEADER_TMPL.format(root="") + "\n" + body + footer_html("")


def main():
    routes = json.loads((DATA_DIR / "toll.json").read_text(encoding="utf-8"))
    gates = json.loads((DATA_DIR / "gates.json").read_text(encoding="utf-8"))
    print(f"{len(routes):,}개 구간, {len(gates)}개 요금소 로드")

    by_dep = defaultdict(list)
    for r in routes:
        by_dep[(r["dep"], r["depSlug"])].append(r)

    generated = 0
    url_paths = ["index.html", "about.html"]
    for (dep_name, dep_slug), rlist in by_dep.items():
        gate_dir = DOCS_DIR / dep_slug
        gate_dir.mkdir(parents=True, exist_ok=True)
        (gate_dir / "index.html").write_text(gen_gate_page(dep_name, dep_slug, rlist), encoding="utf-8")
        url_paths.append(f"{dep_slug}/index.html")
        generated += 1

    dep_slugs = {dep_slug for (_, dep_slug) in by_dep.keys()}
    (DOCS_DIR / "index.html").write_text(gen_index(gates, len(routes), dep_slugs), encoding="utf-8")
    generated += 1

    gen_sitemap(url_paths)
    print(f"\n총 {generated:,}개 페이지 생성 완료 (요금소 허브페이지 {len(by_dep)}개 + 홈, 구간 {len(routes):,}개는 각 허브페이지 안에 텍스트로 포함)")


def gen_sitemap(paths):
    urls = "\n".join(
        f"  <url><loc>{BASE_URL}/{quote(p)}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>"
        for p in paths
    )
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n"
    (DOCS_DIR / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"  sitemap: {len(paths):,}개 URL")


if __name__ == "__main__":
    main()
