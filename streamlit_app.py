import re
import concurrent.futures
import pandas as pd
import requests
import streamlit as st

# ── Bot user agents ───────────────────────────────────────────────────────────
BOTS = {
    # Search engines
    "Googlebot":            ("Search", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    "Googlebot-Mobile":     ("Search", "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    "Bingbot":              ("Search", "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"),
    "DuckDuckBot":          ("Search", "DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)"),
    "YandexBot":            ("Search", "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)"),
    "Baiduspider":          ("Search", "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"),
    "PetalBot":             ("Search", "Mozilla/5.0 (compatible; PetalBot; +https://aspiegel.com/petalbot)"),
    # SEO tools
    "AhrefsBot":            ("SEO",    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)"),
    "AhrefsSiteAudit":      ("SEO",    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/) AhrefsSiteAudit"),
    "SemrushBot":           ("SEO",    "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)"),
    "DotBot":               ("SEO",    "Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot)"),
    "MJ12bot":              ("SEO",    "Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)"),
    "Rogerbot":             ("SEO",    "Mozilla/5.0 (compatible; Rogerbot/1.0; +http://www.moz.com/help/pro/what-is-rogerbot)"),
    "SEOkicks":             ("SEO",    "Mozilla/5.0 (compatible; SEOkicks; +https://www.seokicks.de/robot.html)"),
    "DataForSeoBot":        ("SEO",    "Mozilla/5.0 (compatible; DataForSeoBot/1.0; +https://dataforseo.com/dataforseo-bot)"),
    "BLEXBot":              ("SEO",    "Mozilla/5.0 (compatible; BLEXBot/1.0; +http://webmeup-crawler.com/)"),
    "ScreamingFrog":        ("SEO",    "Screaming Frog SEO Spider/19.0"),
    "Sitebulb":             ("SEO",    "Mozilla/5.0 (compatible; Sitebulb/1.0; +https://sitebulb.com)"),
    "SERankingBot":         ("SEO",    "Mozilla/5.0 (compatible; SERanking Bot/1.0; +http://seranking.com/bot.html)"),
    "audisto":              ("SEO",    "Mozilla/5.0 (compatible; audisto bot; +https://audisto.com/)"),
    # AI crawlers
    "GPTBot":               ("AI",     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"),
    "ChatGPT-User":         ("AI",     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"),
    "Google-Extended":      ("AI",     "Mozilla/5.0 (compatible; Google-Extended/1.0; +http://www.google.com/bot.html)"),
    "ClaudeBot":            ("AI",     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0; +claudebot@anthropic.com"),
    "PerplexityBot":        ("AI",     "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot"),
    "YouBot":               ("AI",     "Mozilla/5.0 (compatible; YouBot; +https://about.you.com/youbot/)"),
    "Applebot":             ("AI",     "Mozilla/5.0 (compatible; Applebot/0.1; +http://www.apple.com/go/applebot)"),
    "Applebot-Extended":    ("AI",     "Mozilla/5.0 (compatible; Applebot-Extended/0.1; +http://www.apple.com/go/applebot)"),
    "Bytespider":           ("AI",     "Mozilla/5.0 (compatible; Bytespider; spider-feedback@bytedance.com) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.0.0"),
    "CCBot":                ("AI",     "CCBot/2.0 (https://commoncrawl.org/faq/)"),
    "FacebookBot":          ("AI",     "FacebookBot/1.0 (+https://developers.facebook.com/docs/sharing/webmasters/facebookbot/)"),
    "Meta-ExternalAgent":   ("AI",     "Meta-ExternalAgent/1.1 (+(https://developers.facebook.com/docs/sharing/webmasters/facebookbot/))"),
    "Diffbot":              ("AI",     "Mozilla/5.0 (compatible; Diffbot/0.1; +http://www.diffbot.com)"),
    # Reference
    "Browser":              ("Ref",    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"),
}

MAX_URLS = 20
TIMEOUT  = 20


def normalize(url: str) -> str:
    return url if re.match(r"^https?://", url, re.I) else "https://" + url


def fetch(bot_name: str, category: str, ua: str, url: str) -> dict:
    try:
        r = requests.get(
            url,
            headers={"User-Agent": ua, "Accept": "*/*"},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        return {
            "URL":          url,
            "Bot":          bot_name,
            "Category":     category,
            "Status":       r.status_code,
            "Hops":         len(r.history) or "─",
            "Server":       r.headers.get("Server", "─"),
            "X-Robots-Tag": r.headers.get("X-Robots-Tag", "─"),
            "Final URL":    r.url if r.url != url else "─",
        }
    except requests.exceptions.Timeout:
        return {"URL": url, "Bot": bot_name, "Category": category, "Status": "Timeout",  "Hops": "─", "Server": "─", "X-Robots-Tag": "─", "Final URL": "─"}
    except requests.exceptions.ConnectionError:
        return {"URL": url, "Bot": bot_name, "Category": category, "Status": "ConnErr",  "Hops": "─", "Server": "─", "X-Robots-Tag": "─", "Final URL": "─"}
    except Exception as e:
        return {"URL": url, "Bot": bot_name, "Category": category, "Status": type(e).__name__, "Hops": "─", "Server": "─", "X-Robots-Tag": "─", "Final URL": "─"}


def check_urls(urls: list[str]) -> pd.DataFrame:
    tasks = [
        (name, cat, ua, url)
        for url in urls
        for name, (cat, ua) in BOTS.items()
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(fetch, name, cat, ua, url) for name, cat, ua, url in tasks]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Sort by original URL order, then bot order
    url_order = {u: i for i, u in enumerate(urls)}
    bot_order = {b: i for i, b in enumerate(BOTS.keys())}
    results.sort(key=lambda r: (url_order[r["URL"]], bot_order[r["Bot"]]))
    return pd.DataFrame(results)


def status_color(val):
    if isinstance(val, int):
        if val == 200:
            return "color: green"
        if val in (301, 302):
            return "color: orange"
        if val >= 400:
            return "color: red"
    if isinstance(val, str) and val not in ("─",):
        return "color: red"
    return ""


# ── UI ────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Bot Checker", page_icon="🤖", layout="wide")

st.title("🤖 Bot Checker")
st.caption("Check how URLs respond to search engine, SEO, and AI crawlers. Up to 20 URLs at once.")

url_input = st.text_area(
    "Enter URLs (one per line, up to 20)",
    placeholder="https://example.com\nhttps://another.com/page",
    height=150,
)

if st.button("Check", type="primary") and url_input.strip():
    raw = [u.strip() for u in url_input.strip().splitlines() if u.strip()]
    if len(raw) > MAX_URLS:
        st.warning(f"Only the first {MAX_URLS} URLs will be checked.")
        raw = raw[:MAX_URLS]

    urls = [normalize(u) for u in raw]
    n_bots = len(BOTS)
    st.markdown(f"Checking **{len(urls)} URL{'s' if len(urls) > 1 else ''}** × **{n_bots} bots** = **{len(urls) * n_bots} requests**")

    with st.spinner("Running checks…"):
        st.session_state["df"] = check_urls(urls)
        st.session_state["urls"] = urls

if "df" not in st.session_state:
    st.stop()

df   = st.session_state["df"]
urls = st.session_state["urls"]

st.success("Done.")

# ── Summary metrics ───────────────────────────────────────────────────────
total   = len(df)
ok      = (df["Status"] == 200).sum()
blocked = df["Status"].isin([403, 429]).sum()
errors  = df["Status"].apply(lambda x: isinstance(x, str) and x not in ("─",)).sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total requests", total)
c2.metric("200 OK", int(ok))
c3.metric("Blocked (403/429)", int(blocked))
c4.metric("Errors", int(errors))

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    url_filter = st.selectbox("Filter by URL", ["All"] + urls)
with col2:
    categories = ["All"] + sorted(df["Category"].unique().tolist())
    cat_filter = st.radio("Filter by category", categories, horizontal=True)

display_df = df.copy()
if url_filter != "All":
    display_df = display_df[display_df["URL"] == url_filter]
if cat_filter != "All":
    display_df = display_df[display_df["Category"] == cat_filter]

# Hide URL column when filtered to a single URL
cols = display_df.columns.tolist() if url_filter == "All" else [c for c in display_df.columns if c != "URL"]

st.dataframe(
    display_df[cols].style.applymap(status_color, subset=["Status"]),
    use_container_width=True,
    hide_index=True,
)

# ── Download ──────────────────────────────────────────────────────────────
st.download_button(
    "⬇ Download CSV",
    data=df.to_csv(index=False),
    file_name="bot_check_results.csv",
    mime="text/csv",
)
