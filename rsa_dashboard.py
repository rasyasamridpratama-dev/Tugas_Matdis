import math
import re
from html import escape

import streamlit as st

# ============================================================
# RSA STUDIO - Encryption Dashboard
# Jalankan: python -m streamlit run rsa_dashboard.py
# Tip: simpan config.toml sebagai .streamlit/config.toml agar tema terang konsisten.
# ============================================================

st.set_page_config(
    page_title="RSA Studio | Encryption Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

CAESAR, ASCII = "caesar", "ascii"

# ============================================================
# 1. RSA CORE
# ============================================================

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def next_prime(n: int) -> int:
    n = max(n, 2)
    while not is_prime(n):
        n += 1
    return n


def egcd(a: int, b: int):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(e: int, phi: int) -> int:
    g, x, _ = egcd(e, phi)
    if g != 1:
        raise ValueError("e tidak memiliki invers modulo phi(n).")
    return x % phi


def valid_e_list(phi: int, count: int = 20):
    result, e = [], 2
    while len(result) < count and e < phi:
        if math.gcd(e, phi) == 1:
            result.append(e)
        e += 1
    return result


def width(mode):     return 2 if mode == CAESAR else 3
def max_code(mode):  return 26 if mode == CAESAR else 255
def pad_code(mode):  return 26 if mode == CAESAR else 32


def max_block_value(mode, k):
    return int(str(max_code(mode)).zfill(width(mode)) * k)


def sanitize(text, mode):
    if mode == CAESAR:
        text = text.upper()
        return "".join(c for c in text if "A" <= c <= "Z" or c == " ")
    return "".join(c for c in text if ord(c) <= 255)


def char_to_code(c, mode):
    if mode == CAESAR:
        return 26 if c == " " else ord(c) - 65
    return ord(c)


def code_to_char(x, mode):
    if mode == CAESAR:
        return " " if x == 26 else chr(x + 65) if 0 <= x <= 25 else "?"
    return chr(x) if 0 <= x <= 255 else "?"


def encrypt(text, mode, k, e, n):
    w = width(mode)
    clean_text = sanitize(text, mode)
    codes = [char_to_code(c, mode) for c in clean_text]
    padding = 0
    while len(codes) % k:
        codes.append(pad_code(mode))
        padding += 1

    cipher, trace = [], []
    for i in range(0, len(codes), k):
        block = codes[i:i + k]
        chars = "".join(code_to_char(x, mode) for x in block)
        digits = "".join(str(x).zfill(w) for x in block)
        m = int(digits)
        c = pow(m, e, n)
        cipher.append(c)
        trace.append({
            "blok": i // k + 1, "karakter": chars, "kode": digits,
            "m": m, "operasi": f"{m}^{e} mod {n}", "c": c,
        })
    return cipher, trace, clean_text, padding


def decrypt(cipher, mode, k, d, n):
    w = width(mode)
    output, trace = "", []
    for idx, c in enumerate(cipher, 1):
        m = pow(c, d, n)
        digits = str(m).zfill(w * k)
        if len(digits) > w * k:
            chars = "?" * k
        else:
            chunks = [int(digits[j:j + w]) for j in range(0, w * k, w)]
            chars = "".join(code_to_char(x, mode) for x in chunks)
        output += chars
        trace.append({
            "blok": idx, "c": c, "operasi": f"{c}^{d} mod {n}",
            "m": m, "kode": digits, "karakter": chars,
        })
    return output.rstrip(), trace


# ============================================================
# 2. STYLING
#    Palet: petrol (sidebar & hasil), teal = kunci publik / aksi utama,
#    kuningan = kunci privat. Ubah warna di :root.
# ============================================================

def clean(s: str) -> str:
    """Gabung baris HTML tanpa indentasi supaya tidak dianggap code block oleh markdown."""
    return "".join(line.strip() for line in s.splitlines())


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --paper: #F1F5F4;  --card: #FFFFFF;
    --ink: #12262D;    --ink-2: #3F5560;   --muted: #677C85;
    --line: #DAE4E3;   --line-2: #C4D2D1;

    --petrol: #0D2830; --on-dark: #E6F0EF; --on-dark-2: #9DB5B8;
    --brass: #D9A441;

    --pub: #0F7C7A;    --pub-d: #0B5F5D;   --pub-soft: #DDF1EF;   /* kunci publik / aksi utama */
    --priv: #A8650F;   --priv-soft: #F8EBD3;                       /* kunci privat */

    --ok: #1E8A5A; --warn: #B7791F; --err: #C0392B; --info: #2C6E9B;

    --head: 'Bricolage Grotesque', 'Instrument Sans', system-ui, sans-serif;
    --body: 'Instrument Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
    --mono: 'JetBrains Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace;
}

/* ================= Dasar ================= */
.stApp { background: var(--paper); color: var(--ink); font-family: var(--body); color-scheme: light; }
.stApp p, .stApp label, .stApp li, .stApp span, .stApp div, .stApp textarea, .stApp input, .stApp button { font-family: var(--body); }
.stApp [data-testid="stIconMaterial"], .stApp span[class*="material"] { font-family: 'Material Symbols Rounded' !important; }
.stApp p, .stApp li, .stApp .stMarkdown { color: var(--ink); line-height: 1.55; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { font-family: var(--head); color: var(--ink); font-weight: 700; letter-spacing: -.015em; }
.stApp h4 { font-size: 1.08rem; margin-bottom: .55rem; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p { color: var(--muted); }
.stApp div[data-testid="stWidgetLabel"] p, .stApp label p { color: var(--ink-2); font-size: .88rem; font-weight: 600; }
.stApp strong, .stApp b { color: var(--ink); font-weight: 650; }
.stApp .katex { color: var(--ink); }
.stApp hr { border-color: var(--line) !important; }

header[data-testid="stHeader"] { background: transparent; }
header[data-testid="stHeader"] * { color: var(--ink-2); }
.block-container { max-width: 1140px; padding-top: 2rem; padding-bottom: 3rem; }
div[data-testid="stVerticalBlock"] { gap: 1.1rem; }

/* ================= Kartu ================= */
[class*="st-key-card_"], div[data-testid="stForm"] {
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    box-shadow: 0 1px 0 rgba(13,40,48,.04), 0 8px 24px -16px rgba(13,40,48,.18);
}
[class*="st-key-card_"] { padding: 1.3rem 1.5rem; }
div[data-testid="stForm"] { padding: 1.5rem 1.7rem; }
[class*="st-key-card_"][class*="_pub"]  { border-top: 3px solid var(--pub); }
[class*="st-key-card_"][class*="_priv"] { border-top: 3px solid var(--priv); }

/* ================= Header halaman ================= */
.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 1.5rem; flex-wrap: wrap;
    padding-bottom: 1.3rem; margin-bottom: .6rem; border-bottom: 1px solid var(--line-2); }
.page-head h1 { margin: 0 0 .4rem; padding: 0; font-size: clamp(1.8rem, 3.4vw, 2.5rem); line-height: 1.1; }
.page-head p { margin: 0; max-width: 620px; color: var(--ink-2); font-size: 1rem; line-height: 1.55; }

/* ================= Komponen kecil ================= */
.pill { display: inline-block; padding: .32rem .8rem; border-radius: 999px; font-size: .78rem; font-weight: 600; white-space: nowrap;
    color: var(--pub-d); background: var(--pub-soft); border: 1px solid rgba(15,124,122,.28); }
.pill.live::before { content: ""; display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--ok); margin-right: .5rem; }
.sec-title { font-family: var(--head); font-size: 1.2rem; font-weight: 700; letter-spacing: -.01em; margin: 1.6rem 0 .3rem; color: var(--ink); }

/* Kartu metrik */
.mcard { margin-bottom: 1rem; padding: 1.1rem 1.25rem; min-height: 124px; border-radius: 14px; background: var(--card);
    border: 1px solid var(--line); border-top: 3px solid var(--line-2); box-shadow: 0 8px 24px -16px rgba(13,40,48,.18); }
.mcard.pub  { border-top-color: var(--pub); }
.mcard.priv { border-top-color: var(--priv); }
.mhead { display: flex; align-items: center; gap: .6rem; margin-bottom: .75rem; }
.mico { width: 26px; height: 26px; border-radius: 7px; display: grid; place-items: center; flex: none;
    background: #E3ECEB; color: var(--ink); font-weight: 700; font-size: .85rem; }
.mico.pub  { background: var(--pub-soft);  color: var(--pub-d); }
.mico.priv { background: var(--priv-soft); color: var(--priv); }
.mlabel { font-size: .84rem; font-weight: 600; color: var(--muted); }
.stApp .mvalue { font-family: var(--head); font-size: clamp(1.45rem, 2.4vw, 2rem); font-weight: 700; color: var(--ink);
    overflow-wrap: anywhere; line-height: 1.1; font-variant-numeric: tabular-nums; letter-spacing: -.02em; }
.mnote { font-size: .8rem; margin-top: .45rem; color: var(--muted); }

/* Baris key-value */
.kvrow { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; padding: .7rem 0; border-bottom: 1px solid var(--line); font-size: .93rem; }
.kvrow:last-child { border-bottom: none; padding-bottom: 0; }
.kvrow span { color: var(--muted); }
.kvrow b { color: var(--ink); font-family: var(--mono); font-size: .86rem; font-weight: 500; text-align: right; overflow-wrap: anywhere; }

/* Kartu aksi cepat */
.stApp .qa-title { font-family: var(--head); font-size: 1.1rem; font-weight: 700; color: var(--ink); margin-bottom: .3rem; }
.qa-desc { color: var(--ink-2); font-size: .92rem; line-height: 1.55; margin-bottom: .9rem; min-height: 4.6em; }

/* Langkah (urutan nyata, jadi bernomor) */
.stepcard { display: flex; gap: 1rem; align-items: flex-start; padding: 1.05rem 1.3rem; margin-bottom: .7rem; border-radius: 14px; background: var(--card); border: 1px solid var(--line); }
.stepnum { flex: none; width: 36px; height: 36px; border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: .9rem; background: var(--petrol); color: var(--brass); }
.stepcard b { color: var(--ink); }
.stepcard .d { color: var(--ink-2); font-size: .93rem; margin-top: .15rem; line-height: 1.55; }

/* Notifikasi */
.notice { display: flex; gap: .75rem; align-items: flex-start; padding: .85rem 1.05rem; margin: .2rem 0; border-radius: 10px; font-size: .94rem; line-height: 1.55;
    color: var(--ink); background: var(--card); border: 1px solid var(--line); border-left-width: 4px; }
.notice .ic { flex: none; width: 20px; height: 20px; border-radius: 50%; display: grid; place-items: center; font-size: .72rem; font-weight: 700; color: #fff; margin-top: 2px; }
.notice b { color: var(--ink); }
.notice.ok   { border-left-color: var(--ok);   background: #EAF6EF; }  .notice.ok .ic   { background: var(--ok); }
.notice.err  { border-left-color: var(--err);  background: #FBECEA; }  .notice.err .ic  { background: var(--err); }
.notice.warn { border-left-color: var(--warn); background: #FAF1DE; }  .notice.warn .ic { background: var(--warn); }
.notice.info { border-left-color: var(--info); background: #E8F1F8; }  .notice.info .ic { background: var(--info); }

/* ================= Sidebar ================= */
section[data-testid="stSidebar"] { background: var(--petrol) !important; border-right: none; }
section[data-testid="stSidebar"] > div { background: transparent !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12) !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * { color: var(--on-dark-2) !important; }
.brand { display: flex; align-items: center; gap: .8rem; padding: .3rem .2rem 1.4rem; }
.brand .logo { width: 40px; height: 40px; border-radius: 11px; display: grid; place-items: center; background: var(--brass); color: var(--petrol); font-family: var(--head); font-size: 1.25rem; font-weight: 700; }
.stApp .brand .t { font-family: var(--head); font-size: 1.2rem; font-weight: 700; color: #fff; line-height: 1.1; }
.brand .s { font-size: .78rem; color: var(--on-dark-2); margin-top: .25rem; }
.side-label { font-size: .8rem; font-weight: 600; color: var(--on-dark-2); margin: .3rem .3rem .5rem; }
.side-info { display: flex; justify-content: space-between; gap: .5rem; padding: .28rem .3rem; font-size: .86rem; color: var(--on-dark-2); }
.side-info b { color: var(--on-dark); font-family: var(--mono); font-size: .8rem; font-weight: 500; }
section[data-testid="stSidebar"] .pill { color: var(--on-dark); background: rgba(255,255,255,.08); border-color: rgba(255,255,255,.18); }

/* ================= Tombol ================= */
.stApp div.stButton, .stApp div.stDownloadButton { width: 100%; }
.stApp div.stButton > button, .stApp div.stDownloadButton > button, .stApp div[data-testid="stFormSubmitButton"] > button {
    width: 100%; border-radius: 8px; font-weight: 600; padding: .62rem 1.2rem; transition: background .15s ease, border-color .15s ease;
    background: var(--card); border: 1px solid var(--line-2); color: var(--ink); box-shadow: none;
}
.stApp div.stButton > button p, .stApp div.stDownloadButton > button p, .stApp div[data-testid="stFormSubmitButton"] > button p { color: inherit; }
.stApp div.stButton > button:hover, .stApp div.stDownloadButton > button:hover { border-color: var(--pub); color: var(--pub-d); background: var(--pub-soft); }
.stApp div.stButton > button:focus-visible, .stApp div.stDownloadButton > button:focus-visible { outline: 3px solid rgba(15,124,122,.35); outline-offset: 2px; }
.stApp div.stButton > button[kind="primary"], .stApp div.stButton > button[data-testid="stBaseButton-primary"],
.stApp div[data-testid="stFormSubmitButton"] > button { background: var(--pub); border: 1px solid var(--pub); color: #fff; }
.stApp div.stButton > button[kind="primary"]:hover, .stApp div.stButton > button[data-testid="stBaseButton-primary"]:hover,
.stApp div[data-testid="stFormSubmitButton"] > button:hover { background: var(--pub-d); border-color: var(--pub-d); color: #fff; }

/* Tombol navigasi sidebar */
section[data-testid="stSidebar"] div.stButton > button {
    justify-content: flex-start !important; text-align: left !important; padding: .64rem 1rem !important; border-radius: 8px !important;
    background: transparent !important; border: 1px solid transparent !important; color: var(--on-dark-2) !important;
}
section[data-testid="stSidebar"] div.stButton > button p { color: inherit !important; font-weight: 500; text-align: left; }
section[data-testid="stSidebar"] div.stButton > button:hover { background: rgba(255,255,255,.07) !important; color: #fff !important; border-color: transparent !important; }
section[data-testid="stSidebar"] div.stButton > button[kind="primary"],
section[data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] {
    background: rgba(217,164,65,.14) !important; color: #fff !important; border-color: transparent !important; box-shadow: inset 3px 0 0 var(--brass) !important;
}
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
section[data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] p { font-weight: 650; }

/* ================= Input ================= */
.stApp div[data-baseweb="input"], .stApp div[data-baseweb="textarea"], .stApp div[data-baseweb="select"] > div {
    background: #fff !important; border: 1px solid var(--line-2) !important; border-radius: 8px !important;
}
.stApp div[data-baseweb="input"] > div, .stApp div[data-baseweb="textarea"] > div { background: transparent !important; }
.stApp textarea, .stApp input { color: var(--ink) !important; -webkit-text-fill-color: var(--ink); }
.stApp textarea { font-family: var(--mono); font-size: .92rem; }
.stApp textarea::placeholder, .stApp input::placeholder { color: var(--muted) !important; -webkit-text-fill-color: var(--muted); opacity: 1; }
.stApp div[data-baseweb="input"]:focus-within, .stApp div[data-baseweb="textarea"]:focus-within, .stApp div[data-baseweb="select"]:focus-within > div {
    border-color: var(--pub) !important; box-shadow: 0 0 0 3px rgba(15,124,122,.18);
}
.stApp div[data-baseweb="select"] * { color: var(--ink) !important; }
.stApp div[data-baseweb="select"] svg { fill: var(--ink-2) !important; }
.stApp div[data-testid="stNumberInput"] button { background: transparent !important; color: var(--ink-2) !important; border: none !important; }
.stApp div[data-testid="stNumberInput"] button:hover { color: var(--pub-d) !important; background: var(--pub-soft) !important; }

/* Dropdown (dirender di luar .stApp) */
div[data-baseweb="popover"] { font-family: var(--body); }
div[data-baseweb="popover"] > div, ul[role="listbox"], div[data-baseweb="menu"] { background: #fff !important; border: 1px solid var(--line-2); border-radius: 10px; }
li[role="option"] { background: transparent !important; color: var(--ink) !important; }
li[role="option"] * { color: var(--ink) !important; }
li[role="option"]:hover, li[role="option"][aria-selected="true"] { background: var(--pub-soft) !important; }

/* Radio horizontal */
.stApp div[role="radiogroup"] { gap: .5rem; }
.stApp div[role="radiogroup"] > label { padding: .5rem 1rem; border-radius: 8px; cursor: pointer; border: 1px solid var(--line-2); background: #fff; transition: border-color .15s ease, background .15s ease; }
.stApp div[role="radiogroup"] > label:hover { border-color: var(--pub); }
.stApp div[role="radiogroup"] > label:has(input:checked) { border-color: var(--pub); background: var(--pub-soft); }
.stApp div[role="radiogroup"] > label p { color: var(--ink); }

/* ================= Expander & kode ================= */
.stApp div[data-testid="stExpander"] details { background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
.stApp div[data-testid="stExpander"] summary { padding: .8rem 1.1rem; }
.stApp div[data-testid="stExpander"] summary p, .stApp div[data-testid="stExpander"] summary span { color: var(--ink) !important; font-weight: 600; }
.stApp div[data-testid="stExpander"] summary svg { color: var(--ink-2); }
.stApp div[data-testid="stCode"] pre, .stApp div[data-testid="stCode"] code { background: #EAF2F1 !important; color: var(--ink) !important; border-radius: 8px; font-family: var(--mono) !important; font-size: .88rem; }
.stApp div[data-testid="stCode"] pre { border: 1px solid var(--line); }
.stApp div[data-testid="stCode"] span { color: var(--ink) !important; }

/* ================= Tabel langkah ================= */
.table-wrap { overflow-x: auto; margin: .2rem 0 .4rem; }
.table-inner { min-width: 680px; }
.thead { display: grid; gap: .8rem; padding: 0 1rem .6rem; margin-bottom: .5rem; font-size: .8rem; font-weight: 600; color: var(--muted); border-bottom: 1px solid var(--line-2); }
.trow { display: grid; gap: .8rem; align-items: center; padding: .6rem 1rem; margin-bottom: .4rem; border-radius: 10px; background: var(--card); border: 1px solid var(--line); }
.trow:hover { border-color: var(--pub); }
.idx { width: 30px; height: 30px; border-radius: 50%; display: grid; place-items: center; background: var(--petrol); color: var(--brass); font-weight: 700; font-size: .82rem; }
.stApp .charchip { display: inline-block; padding: .2rem .65rem; border-radius: 6px; width: fit-content; background: var(--pub-soft); color: var(--pub-d);
    font-family: var(--mono); font-weight: 600; font-size: .88rem; }
.stApp .val { font-family: var(--mono); font-size: .84rem; color: var(--ink); overflow-wrap: anywhere; }

/* ================= Hasil (satu momen yang menonjol) ================= */
.result-card { padding: 1.5rem 1.7rem; border-radius: 14px; background: var(--petrol); border-left: 5px solid var(--brass); }
.result-card .lbl { font-size: .84rem; font-weight: 600; color: var(--brass); margin-bottom: .5rem; }
.stApp .result-card .out { font-family: var(--head); font-size: clamp(1.4rem, 2.6vw, 2rem); font-weight: 600; color: #fff; overflow-wrap: anywhere; white-space: pre-wrap; line-height: 1.3; }
.footer { text-align: center; color: var(--muted); font-size: .8rem; padding-top: .4rem; }

@media (max-width: 768px) {
    .block-container { padding: 1rem 1rem 2rem; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# 3. SESSION STATE
# ============================================================
if "cfg" not in st.session_state:
    p0, q0 = 61, 53
    phi0, e0 = (p0 - 1) * (q0 - 1), 17
    st.session_state.cfg = {
        "mode": CAESAR, "k": 2, "p": p0, "q": q0,
        "n": p0 * q0, "phi": phi0, "e": e0, "d": mod_inverse(e0, phi0),
    }
for key, default in (("last_cipher", ""), ("last_plain", ""), ("last_trace", []),
                     ("page", "dashboard"), ("flash", "")):
    st.session_state.setdefault(key, default)

cfg = st.session_state.cfg
MODE_NAME = {CAESAR: "Caesar Cipher Text", ASCII: "ASCII (3 digit)"}

PAGES = [
    ("dashboard", "◈", "Dashboard"),
    ("enkripsi", "↗", "Enkripsi"),
    ("dekripsi", "↙", "Dekripsi"),
    ("kunci", "⚙", "Pengaturan Kunci"),
    ("proses", "⌘", "Proses RSA"),
    ("panduan", "ⓘ", "Panduan"),
]


def go(page_id: str):
    st.session_state.page = page_id


# ============================================================
# 4. KOMPONEN UI
# ============================================================
_card_counter = 0


def card(tone=""):
    """Kartu yang membungkus widget Streamlit. tone: "pub" (teal) atau "priv" (kuningan)."""
    global _card_counter
    _card_counter += 1
    try:
        return st.container(key=f"card_{_card_counter}" + (f"_{tone}" if tone else ""))
    except TypeError:  # Streamlit lama tanpa parameter key
        return st.container(border=True)


def page_header(kicker, title, description, badge=None):
    badge_html = f'<span class="pill">{escape(badge)}</span>' if badge else ""
    st.markdown(clean(f"""
    <div class="page-head">
      <div>
        <h1>{escape(title)}</h1>
        <p>{escape(description)}</p>
      </div>
      {badge_html}
    </div>
    """), unsafe_allow_html=True)


def metric_card(symbol, label, value, note=""):
    tone = {"e": "pub", "d": "priv"}.get(symbol, "")  # e = kunci publik, d = kunci privat
    st.markdown(clean(f"""
    <div class="mcard {tone}">
      <div class="mhead"><span class="mico {tone}">{escape(symbol)}</span><span class="mlabel">{escape(label.capitalize())}</span></div>
      <div class="mvalue">{value}</div>
      <div class="mnote">{escape(note)}</div>
    </div>
    """), unsafe_allow_html=True)


NOTICE_ICON = {"ok": "✓", "err": "✕", "warn": "!", "info": "i"}


def notice(kind, text_html):
    """Notifikasi sendiri (warna & kontras terkontrol). text_html boleh berisi <b>."""
    st.markdown(clean(f'<div class="notice {kind}"><span class="ic">{NOTICE_ICON[kind]}</span>'
                      f'<div>{text_html}</div></div>'), unsafe_allow_html=True)


def section_title(text):
    st.markdown(f'<div class="sec-title">{escape(text)}</div>', unsafe_allow_html=True)


def kv_rows(rows):
    st.markdown(clean("".join(f'<div class="kvrow"><span>{escape(k)}</span><b>{v}</b></div>' for k, v in rows)),
                unsafe_allow_html=True)


COL_WEIGHT = {"blok": "56px", "operasi": "1.8fr"}


def trace_table(rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    tpl = "grid-template-columns: " + " ".join(COL_WEIGHT.get(c, "minmax(0,1fr)") for c in cols) + ";"
    head = "".join(f"<span>{escape(c)}</span>" for c in cols)
    body = ""
    for r in rows:
        cells = []
        for c in cols:
            v = r[c]
            if c == "blok":
                cells.append(f'<span class="idx">{escape(str(v))}</span>')
            elif c == "karakter":
                cells.append(f'<span class="charchip">{escape(str(v).replace(" ", "␣"))}</span>')
            else:
                cells.append(f'<span class="val">{escape(str(v))}</span>')
        body += f'<div class="trow" style="{tpl}">{"".join(cells)}</div>'
    st.markdown(clean(f'<div class="table-wrap"><div class="table-inner">'
                      f'<div class="thead" style="{tpl}">{head}</div>{body}</div></div>'),
                unsafe_allow_html=True)


def flash_message():
    if st.session_state.flash:
        notice("ok", escape(st.session_state.flash))
        st.session_state.flash = ""


def active_config_card():
    with card():
        st.markdown("#### Parameter aktif")
        kv_rows([
            ("Metode encoding", escape(MODE_NAME[cfg["mode"]])),
            ("Ukuran blok", f"{cfg['k']} karakter"),
            ("Kunci publik (e, n)", f"({cfg['e']:,}, {cfg['n']:,})"),
            ("Kunci privat (d, n)", f"({cfg['d']:,}, {cfg['n']:,})"),
        ])


# ============================================================
# 5. SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(clean("""
    <div class="brand">
      <div class="logo">R</div>
      <div><div class="t">RSA Studio</div><div class="s">Ruang kerja enkripsi</div></div>
    </div>
    <div class="side-label">Menu</div>
    """), unsafe_allow_html=True)

    for pid, icon, label in PAGES:
        st.button(f"{icon}   {label}", key=f"nav_{pid}", on_click=go, args=(pid,),
                  type="primary" if st.session_state.page == pid else "secondary")

    st.divider()
    st.markdown(clean(f"""
    <div class="side-label">Status</div>
    <div style="margin:.1rem .3rem .8rem"><span class="pill live">RSA engine aktif</span></div>
    <div class="side-info"><span>Encoding</span><b>{'Caesar' if cfg['mode'] == CAESAR else 'ASCII'}</b></div>
    <div class="side-info"><span>Ukuran blok</span><b>{cfg['k']} karakter</b></div>
    <div class="side-info"><span>Modulus n</span><b>{cfg['n']:,}</b></div>
    """), unsafe_allow_html=True)

page = st.session_state.page
BADGE = f"{MODE_NAME[cfg['mode']]} · blok {cfg['k']}"

# ============================================================
# 6. HALAMAN
# ============================================================

# ------------------------- Dashboard -------------------------
if page == "dashboard":
    page_header("SECURE MESSAGE SYSTEM", "RSA Encryption Dashboard",
                "Kelola kunci, enkripsi pesan, dan dekripsi ciphertext dalam satu workspace.", BADGE)

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("n", "MODULUS", f"{cfg['n']:,}", "p × q")
    with c2: metric_card("φ", "TOTIENT φ(n)", f"{cfg['phi']:,}", "(p − 1) × (q − 1)")
    with c3: metric_card("e", "EKSPONEN PUBLIK", f"{cfg['e']:,}", "Bagian dari kunci publik")
    with c4: metric_card("d", "EKSPONEN PRIVAT", f"{cfg['d']:,}", "Bagian dari kunci privat")

    with card():
        st.markdown("#### Konfigurasi aktif")
        k1, k2 = st.columns(2, gap="large")
        with k1:
            kv_rows([
                ("Metode encoding", escape(MODE_NAME[cfg["mode"]])),
                ("Ukuran blok", f"{cfg['k']} karakter"),
                ("Bilangan prima", f"p = {cfg['p']:,} · q = {cfg['q']:,}"),
            ])
        with k2:
            kv_rows([
                ("Kunci publik (e, n)", f"({cfg['e']:,}, {cfg['n']:,})"),
                ("Kunci privat (d, n)", f"({cfg['d']:,}, {cfg['n']:,})"),
                ("Syarat modulus", f"n &gt; {max_block_value(cfg['mode'], cfg['k']):,}"),
            ])
    with card():
        st.markdown("#### Aktivitas terakhir")
        if st.session_state.last_cipher:
            notice("ok", "Ciphertext berhasil dibuat.")
            st.code(st.session_state.last_cipher, language=None)
        else:
            notice("info", "Belum ada proses enkripsi pada sesi ini.")

    section_title("Mulai gunakan RSA Studio")
    a, b, c = st.columns(3, gap="large")
    for col, title, desc, target, btn in (
        (a, "Enkripsi", "Ubah plaintext menjadi ciphertext menggunakan kunci publik.", "enkripsi", "Buka Enkripsi"),
        (b, "Dekripsi", "Kembalikan ciphertext menjadi pesan yang dapat dibaca.", "dekripsi", "Buka Dekripsi"),
        (c, "Pelajari proses", "Lihat perhitungan modular exponentiation per blok.", "proses", "Buka Proses RSA"),
    ):
        with col:
            with card():
                st.markdown(f'<div class="qa-title">{title}</div><div class="qa-desc">{desc}</div>', unsafe_allow_html=True)
                st.button(btn, key=f"quick_{target}", on_click=go, args=(target,))

# ------------------------- Enkripsi -------------------------
elif page == "enkripsi":
    page_header("MESSAGE PROTECTION", "Enkripsi Pesan",
                "Masukkan pesan yang ingin diamankan. Karakter diubah menjadi blok angka, lalu diproses dengan RSA.", BADGE)

    left, right = st.columns([1.5, 1], gap="large")
    with left:
        with card():
            st.markdown("#### Plaintext")
            plaintext = st.text_area("Pesan", placeholder="Contoh: HELLO WORLD", height=140, label_visibility="collapsed")
            st.caption("Caesar hanya menerima A–Z dan spasi (huruf kecil otomatis menjadi kapital). "
                       "ASCII menerima karakter dengan kode 0–255.")
            do_encrypt = st.button("Enkripsi sekarang", type="primary", key="do_enc")
    with right:
        active_config_card()

    if do_encrypt:
        clean_text_in = sanitize(plaintext, cfg["mode"])
        need = max_block_value(cfg["mode"], cfg["k"])
        if not clean_text_in:
            notice("err", "Masukkan teks yang memiliki karakter yang didukung.")
        elif cfg["n"] <= need:
            notice("err", f"Modulus n harus lebih besar dari nilai blok maksimum (<b>{need:,}</b>). "
                          "Perbarui p, q, atau ukuran blok.")
        else:
            cipher, trace, clean_text, padding = encrypt(plaintext, cfg["mode"], cfg["k"], cfg["e"], cfg["n"])
            st.session_state.last_cipher = " ".join(map(str, cipher))
            st.session_state.last_plain = clean_text
            st.session_state.last_trace = trace
            notice("ok", "Enkripsi berhasil diselesaikan.")

            with card():
                st.markdown("#### Hasil ciphertext")
                st.code(st.session_state.last_cipher, language=None)
                st.download_button("Unduh ciphertext (.txt)", st.session_state.last_cipher,
                                   file_name="ciphertext_rsa.txt", mime="text/plain", key="dl_cipher")
            r1, r2, r3 = st.columns(3)
            with r1: metric_card("#", "JUMLAH BLOK", str(len(cipher)), "blok terenkripsi")
            with r2: metric_card("A", "KARAKTER VALID", str(len(clean_text)), "karakter diproses")
            with r3: metric_card("␣", "PADDING", str(padding), "karakter spasi ditambahkan")
            with st.expander("Detail proses setiap blok", expanded=True):
                trace_table(trace)
    elif st.session_state.last_cipher:
        with card():
            st.markdown("#### Ciphertext terakhir")
            st.code(st.session_state.last_cipher, language=None)

# ------------------------- Dekripsi -------------------------
elif page == "dekripsi":
    page_header("MESSAGE RECOVERY", "Dekripsi Pesan",
                "Masukkan ciphertext untuk mengembalikan pesan menggunakan kunci privat yang sesuai.", BADGE)

    left, right = st.columns([1.5, 1], gap="large")
    with left:
        with card():
            st.markdown("#### Ciphertext")
            ciphertext_text = st.text_area("Ciphertext", value=st.session_state.last_cipher,
                                           placeholder="Contoh: 1234 5678 9012", height=140,
                                           label_visibility="collapsed")
            st.caption("Pisahkan angka dengan spasi, koma, atau baris baru. "
                       "Ciphertext dari enkripsi terakhir otomatis tersedia.")
            do_decrypt = st.button("Dekripsi sekarang", type="primary", key="do_dec")
    with right:
        active_config_card()

    if do_decrypt:
        nums = [int(v) for v in re.findall(r"\d+", ciphertext_text)]
        if not nums:
            notice("err", "Ciphertext kosong atau tidak berisi angka yang valid.")
        elif any(c >= cfg["n"] for c in nums):
            notice("err", "Ada nilai ciphertext yang lebih besar atau sama dengan n. "
                          "Periksa kembali ciphertext dan konfigurasi kunci.")
        else:
            plain, trace = decrypt(nums, cfg["mode"], cfg["k"], cfg["d"], cfg["n"])
            st.session_state.last_plain = plain
            notice("ok", "Dekripsi selesai.")
            st.markdown(clean(f'<div class="result-card"><div class="lbl">Hasil plaintext</div>'
                              f'<div class="out">{escape(plain) if plain else "(kosong)"}</div></div>'),
                        unsafe_allow_html=True)
            st.download_button("Unduh plaintext (.txt)", plain, file_name="plaintext_rsa.txt",
                               mime="text/plain", key="dl_plain")
            with st.expander("Detail dekripsi per blok", expanded=True):
                trace_table(trace)

# ------------------------- Pengaturan kunci -------------------------
elif page == "kunci":
    page_header("KEY MANAGEMENT", "Pengaturan Kunci RSA",
                "Atur metode encoding, ukuran blok, bilangan prima p dan q, serta eksponen publik e.", BADGE)
    flash_message()
    notice("warn", "Mengubah pengaturan akan mengganti pasangan kunci aktif. "
                   "Gunakan konfigurasi yang sama saat melakukan dekripsi.")

    with st.form("key_settings_form"):
        st.markdown("#### 1. Encoding & ukuran blok")
        a, b = st.columns(2)
        with a:
            mode_label = st.selectbox("Metode encoding", ["Caesar Cipher Text", "ASCII (3 digit)"],
                                      index=0 if cfg["mode"] == CAESAR else 1)
        with b:
            k = st.selectbox("Ukuran blok", [1, 2, 3], index=cfg["k"] - 1)
        selected_mode = CAESAR if mode_label.startswith("Caesar") else ASCII
        need = max_block_value(selected_mode, k)
        lo = math.isqrt(need) + 2
        notice("info", f"Nilai blok maksimum <b>{need:,}</b>, jadi syaratnya <b>p × q &gt; {need:,}</b>. "
                       f"Contoh pasangan aman: p = {next_prime(lo):,} dan q = {next_prime(lo * 2):,}.")

        st.markdown("#### 2. Bilangan prima")
        pcol, qcol = st.columns(2)
        with pcol:
            p = st.number_input("Bilangan prima p", min_value=2, max_value=10**9, value=int(cfg["p"]), step=1)
        with qcol:
            q = st.number_input("Bilangan prima q", min_value=2, max_value=10**9, value=int(cfg["q"]), step=1)

        st.markdown("#### 3. Eksponen publik")
        e_mode = st.radio("Cara menentukan e", ["Otomatis (nilai terkecil yang valid)", "Manual"], horizontal=True)
        e_manual = st.number_input("Nilai e (untuk mode manual)", min_value=2, max_value=10**12,
                                   value=int(cfg["e"]), step=1)
        submitted = st.form_submit_button("Simpan konfigurasi & generate key")

    if submitted:
        errors = []
        p, q = int(p), int(q)
        if not is_prime(p): errors.append("p bukan bilangan prima.")
        if not is_prime(q): errors.append("q bukan bilangan prima.")
        if p == q: errors.append("p dan q tidak boleh sama.")
        n_new, phi_new = p * q, (p - 1) * (q - 1)
        if n_new <= need: errors.append(f"p × q harus lebih besar dari {need:,}; saat ini {n_new:,}.")
        e_new = None
        if not errors:
            if e_mode.startswith("Otomatis"):
                cands = valid_e_list(phi_new, 1)
                if cands:
                    e_new = cands[0]
                else:
                    errors.append("Tidak ditemukan kandidat e yang valid.")
            else:
                e_new = int(e_manual)
                if not (1 < e_new < phi_new):
                    errors.append("e harus memenuhi 1 &lt; e &lt; φ(n).")
                elif math.gcd(e_new, phi_new) != 1:
                    errors.append(f"gcd(e, φ(n)) harus 1 (saat ini {math.gcd(e_new, phi_new)}).")
        if errors:
            for err in errors:
                notice("err", err)
        else:
            st.session_state.cfg = {
                "mode": selected_mode, "k": int(k), "p": p, "q": q,
                "n": n_new, "phi": phi_new, "e": e_new, "d": mod_inverse(e_new, phi_new),
            }
            st.session_state.last_cipher = ""
            st.session_state.last_plain = ""
            st.session_state.last_trace = []
            st.session_state.flash = "Konfigurasi berhasil disimpan dan pasangan kunci baru telah dibuat."
            st.rerun()

    section_title("Kunci aktif")
    a, b = st.columns(2, gap="large")
    with a:
        with card("pub"):
            st.markdown("**Kunci publik**")
            st.code(f"(e, n) = ({cfg['e']}, {cfg['n']})", language=None)
    with b:
        with card("priv"):
            st.markdown("**Kunci privat**")
            st.code(f"(d, n) = ({cfg['d']}, {cfg['n']})", language=None)

# ------------------------- Proses RSA -------------------------
elif page == "proses":
    page_header("MATHEMATICAL WORKFLOW", "Visualisasi Proses RSA",
                "Pelajari bagaimana pesan diubah menjadi angka dan diproses menggunakan aritmetika modular.", BADGE)

    section_title("Alur algoritma")
    steps = [
        ("1", "Encoding", "Setiap karakter diubah menjadi kode angka sesuai metode Caesar atau ASCII."),
        ("2", "Blocking", f"Kode karakter dikelompokkan menjadi blok berukuran {cfg['k']} karakter."),
        ("3", "Encryption", f"Setiap blok m dihitung dengan c = m^e mod n, dengan e = {cfg['e']:,}."),
        ("4", "Decryption", f"Ciphertext dihitung kembali dengan m = c^d mod n, dengan d = {cfg['d']:,}."),
        ("5", "Decoding", "Angka hasil dekripsi dipecah kembali menjadi kode karakter."),
    ]
    for number, title, desc in steps:
        st.markdown(clean(f'<div class="stepcard"><div class="stepnum">{number}</div>'
                          f'<div><b>{escape(title)}</b><div class="d">{escape(desc)}</div></div></div>'),
                    unsafe_allow_html=True)

    section_title("Rumus inti")
    l, r = st.columns(2, gap="large")
    with l:
        with card("pub"):
            st.markdown("**Enkripsi**")
            st.latex(r"c = m^e \bmod n")
            st.caption("Mengubah pesan numerik menjadi ciphertext.")
    with r:
        with card("priv"):
            st.markdown("**Dekripsi**")
            st.latex(r"m = c^d \bmod n")
            st.caption("Mengembalikan ciphertext menjadi pesan numerik.")

    section_title("Detail blok dari aktivitas terakhir")
    if st.session_state.last_trace:
        trace_table(st.session_state.last_trace)
    else:
        notice("info", "Belum ada aktivitas enkripsi. Jalankan enkripsi untuk melihat tabel perhitungan blok.")

    with st.expander("Matematika pembentukan kunci"):
        st.latex(r"n = p \times q")
        st.latex(r"\phi(n) = (p-1)(q-1)")
        st.latex(r"\gcd(e,\phi(n)) = 1")
        st.latex(r"d = e^{-1} \bmod \phi(n)")
        st.write("Kunci publik adalah (e, n), sedangkan kunci privat adalah (d, n).")

# ------------------------- Panduan -------------------------
elif page == "panduan":
    page_header("GETTING STARTED", "Panduan Penggunaan",
                "Petunjuk singkat menggunakan RSA Studio dari konfigurasi kunci hingga pertukaran pesan.")
    with st.expander("1. Atur konfigurasi kunci", expanded=True):
        st.write("Buka **Pengaturan Kunci**, pilih encoding dan ukuran blok. Masukkan dua bilangan prima berbeda, "
                 "p dan q. Pastikan hasil p × q lebih besar daripada nilai blok maksimum. "
                 "Pilih e otomatis atau masukkan secara manual.")
    with st.expander("2. Lakukan enkripsi"):
        st.write("Buka menu **Enkripsi**, tulis pesan, lalu tekan tombol Enkripsi. Salin atau unduh ciphertext yang dihasilkan.")
    with st.expander("3. Lakukan dekripsi"):
        st.write("Buka menu **Dekripsi**, masukkan ciphertext dan gunakan konfigurasi kunci yang sama. "
                 "Tekan Dekripsi untuk memperoleh plaintext.")
    with st.expander("4. Pahami encoding"):
        st.markdown(
            "- **Caesar Cipher Text:** A=00, B=01, ..., Z=25, spasi=26. Huruf diubah menjadi kapital.\n"
            "- **ASCII:** setiap karakter direpresentasikan dengan tiga digit (rentang kode 0–255).\n"
            "- **Padding:** blok terakhir dilengkapi kode spasi jika jumlah karakter tidak habis dibagi ukuran blok."
        )
    notice("warn", "<b>Catatan keamanan:</b> aplikasi ini adalah implementasi RSA sederhana untuk pembelajaran. "
                   "RSA textbook tanpa padding aman seperti OAEP tidak boleh dipakai untuk melindungi data sensitif.")
    section_title("Informasi teknis")
    st.code("pip install streamlit\npython -m streamlit run rsa_dashboard.py", language="bash")

st.markdown("---")
st.markdown('<div class="footer">RSA Studio · Built with Python & Streamlit · Educational Cryptography Dashboard</div>',
            unsafe_allow_html=True)