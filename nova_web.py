"""
Nova Web — Streamlit UI
Run: streamlit run nova_web.py
Deps: pip install streamlit anthropic plotly pandas
"""

import os, json, base64, time, textwrap
from datetime import datetime, date
from pathlib import Path

import streamlit as st

try:
    import anthropic
except ImportError:
    st.error("Run: pip install anthropic"); st.stop()

try:
    import plotly.express as px
    import pandas as pd
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ── XOR ENCRYPTION (same key as nova.py — shared storage) ────────────────────
XOR_KEY = "nova-xor-key-v1"

def xor_encrypt(text):
    enc = "".join(chr(ord(c) ^ ord(XOR_KEY[i % len(XOR_KEY)])) for i,c in enumerate(text))
    return base64.b64encode(enc.encode("latin-1")).decode("ascii")

def xor_decrypt(token):
    try:
        dec = base64.b64decode(token.encode("ascii")).decode("latin-1")
        return "".join(chr(ord(c) ^ ord(XOR_KEY[i % len(XOR_KEY)])) for i,c in enumerate(dec))
    except Exception: return ""

DATA_DIR = Path.home() / ".nova"
DATA_DIR.mkdir(exist_ok=True)

def save_enc(filename, data):
    (DATA_DIR / filename).write_text(
        xor_encrypt(json.dumps(data, ensure_ascii=False)), encoding="ascii")

def load_enc(filename, fallback=None):
    p = DATA_DIR / filename
    if not p.exists(): return fallback
    try: return json.loads(xor_decrypt(p.read_text(encoding="ascii")))
    except Exception: return fallback

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nova · Sobriety Companion",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #0d0c13; color: #ddd8cf; }
section[data-testid="stSidebar"] { background-color: #161521; border-right: 1px solid rgba(255,255,255,0.07); }
section[data-testid="stSidebar"] * { color: #ddd8cf !important; }

.nova-logo { font-size: 28px; font-weight: 300; letter-spacing: 0.18em; color: #6eb8a0; margin-bottom: 4px; }
.nova-logo span { color: #c97d4e; }
.nova-tag { font-size: 11px; color: #433f54; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 16px; }
.streak-box { background: #1e1d2b; border: 1px solid rgba(255,255,255,0.07); border-radius: 10px;
              padding: 12px; text-align: center; margin: 12px 0; }
.streak-num { font-size: 36px; color: #c97d4e; line-height: 1; }
.streak-lbl { font-size: 10px; color: #433f54; text-transform: uppercase; letter-spacing: 0.1em; }
.mood-section { margin: 12px 0; font-size: 11px; color: #6b6780; text-transform: uppercase;
                letter-spacing: 0.1em; margin-bottom: 6px; }
.disc { font-size: 10px; color: #433f54; line-height: 1.6; padding: 8px 10px;
        background: #161521; border-radius: 6px; border-left: 3px solid #c97d4e; margin-top: 8px; }
.disc a { color: #6eb8a0; text-decoration: none; }
.gentle-badge { display: inline-block; padding: 3px 10px; background: rgba(201,125,78,0.12);
               border: 1px solid rgba(201,125,78,0.3); border-radius: 20px;
               font-size: 10px; color: #c97d4e; letter-spacing: 0.05em; margin-bottom: 8px; }
.goal-item { display: flex; align-items: flex-start; gap: 8px; padding: 5px 0;
             font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.stChatMessage { background: transparent !important; }
[data-testid="stChatMessageContent"] { color: #ddd8cf; }
.stTextInput > div > div { background: #1e1d2b !important; border-color: rgba(255,255,255,0.1) !important; }
.stTextInput input { color: #ddd8cf !important; }
div[data-testid="stTabs"] button { color: #6b6780 !important; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #6eb8a0 !important; border-bottom-color: #6eb8a0 !important; }
.stButton button { background: transparent; border: 1px solid rgba(255,255,255,0.1);
                   color: #ddd8cf; border-radius: 8px; transition: all 0.2s; font-size: 20px;
                   padding: 8px 0; width: 100%; }
.stButton button:hover { border-color: #6eb8a0; color: #6eb8a0; background: rgba(110,184,160,0.1); }
.send-btn button { background: #6eb8a0 !important; color: #0d0c13 !important;
                   border: none !important; border-radius: 10px !important; font-size: 14px !important; }
.stTextArea textarea { background: #1e1d2b !important; color: #ddd8cf !important;
                       border-color: rgba(255,255,255,0.1) !important; }
.stSelectbox > div { background: #1e1d2b !important; }
.stSelectbox label { color: #6b6780 !important; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    prefs = load_enc("prefs.dat", {})
    defaults = {
        "messages": [],
        "support": False,
        "lang": prefs.get("lang", "en"),
        "api_key": prefs.get("api_key","") or os.environ.get("ANTHROPIC_API_KEY",""),
        "goals": load_enc("goals.dat", []),
        "moods": load_enc("moods.dat", []),
        "journal_entries": load_enc("journal.dat", []),
        "streak": load_enc("streak.dat", 0),
        "last_date": load_enc("checkdate.dat", ""),
        "greeted": False,
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v

init_state()
ss = st.session_state

# ── LANG STRINGS ──────────────────────────────────────────────────────────────
LANG_NAMES = {"en":"English","es":"Español","fr":"Français"}
MOOD_LABELS = {
    "en": {"5":("😊","Great"),"4":("🙂","Good"),"3":("😐","Okay"),"2":("😔","Low"),"1":("😰","Hard")},
    "es": {"5":("😊","Genial"),"4":("🙂","Bien"),"3":("😐","Regular"),"2":("😔","Bajo"),"1":("😰","Muy mal")},
    "fr": {"5":("😊","Super"),"4":("🙂","Bien"),"3":("😐","Correct"),"2":("😔","Bas"),"1":("😰","Difficile")},
}
MOOD_MSGS = {
    "en": {"5":"I'm feeling great today 😊","4":"I'm feeling good today 🙂","3":"I'm feeling okay 😐","2":"I'm feeling low today 😔","1":"I'm really struggling right now 😰"},
    "es": {"5":"Me siento genial hoy 😊","4":"Me siento bien hoy 🙂","3":"Me siento regular 😐","2":"Me siento bajo hoy 😔","1":"Estoy luchando mucho ahora mismo 😰"},
    "fr": {"5":"Je me sens super aujourd'hui 😊","4":"Je me sens bien 🙂","3":"Je me sens correct 😐","2":"Je me sens bas aujourd'hui 😔","1":"J'ai vraiment du mal en ce moment 😰"},
}
PLACEHOLDERS = {"en":"Talk to Nova…","es":"Habla con Nova…","fr":"Parlez à Nova…"}
GOAL_EMPTY = {"en":"No goals yet — add one below","es":"Sin objetivos aún","fr":"Pas encore d'objectifs"}
CRISIS = (
    "**Crisis support:**\n"
    "- 988 Lifeline (US): call or text 988\n"
    "- SAMHSA: 1-800-662-4357\n"
    "- Crisis Text: HOME to 741741\n"
    "- France: 3114\n"
    "- [findahelpline.com](https://findahelpline.com)"
)

# ── TREND ANALYSIS ────────────────────────────────────────────────────────────
def analyze_trend(moods):
    if len(moods) < 2: return None
    recent = [m["score"] for m in moods[:14]]
    avg = sum(recent)/len(recent)
    n = len(recent)
    newer = sum(recent[:n//2])/(n//2) if n>=4 else avg
    older = sum(recent[n//2:])/(n-n//2) if n>=4 else avg
    consec_low = 0
    for m in moods:
        if m["score"] <= 2: consec_low += 1
        else: break
    return {"avg":round(avg,1),"direction":newer-older,"consec_low":consec_low,"count":n}

def trend_context(moods):
    t = analyze_trend(moods)
    if not t: return ""
    parts = [f"[MOOD CONTEXT] Recent avg: {t['avg']}/5 over {t['count']} entries."]
    if t["direction"] > 0.4: parts.append("Trending up.")
    elif t["direction"] < -0.4: parts.append("Trending down — be extra warm.")
    if t["consec_low"] >= 3:
        parts.append(f"{t['consec_low']} consecutive low moods — gently suggest professional support.")
    return " ".join(parts)

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
def build_system():
    lang_name = LANG_NAMES[ss.lang]
    tc = trend_context(ss.moods)
    return f"""You are Nova, a compassionate multilingual sobriety support companion.

LANGUAGE: Always respond in {lang_name}.

DISCLAIMER: Include verbatim at the very start of your FIRST response only:
"⚠  This is not medical or professional advice. If you're going through a difficult time, please consider speaking with someone you trust or a qualified professional."

{tc}

ROLE: Non-judgmental companion for people in recovery. Help with check-ins, grounding, breathing, affirmations, journaling, goals. Shame-free relapse support.

SUPPORT MODE: {"ACTIVE — extra warmth, shorter sentences, offer grounding immediately." if ss.support else "INACTIVE — warm encouraging tone."}

LIMITS: Not a therapist. Never diagnose. For crisis: 988 (US), 3114 (France), findahelpline.com.
Keep responses concise, warm, human. Short paragraphs. No walls of text."""

# ── LOG MOOD ──────────────────────────────────────────────────────────────────
def log_mood(score):
    em, lb = MOOD_LABELS[ss.lang][str(score)]
    entry = {"score":score,"emoji":em,"label":lb,
             "time":datetime.now().strftime("%H:%M"),"date":str(date.today())}
    ss.moods.insert(0, entry)
    if len(ss.moods) > 90: ss.moods = ss.moods[:90]
    save_enc("moods.dat", ss.moods)
    if score <= 2: ss.support = True
    today = str(date.today())
    if ss.last_date != today:
        if ss.last_date:
            prev = date.fromisoformat(ss.last_date)
            ss.streak = ss.streak+1 if (date.today()-prev).days==1 else 1
        else: ss.streak = 1
        ss.last_date = today
        save_enc("streak.dat", ss.streak)
        save_enc("checkdate.dat", today)
    msg = MOOD_MSGS[ss.lang][str(score)]
    ss.messages.append({"role":"user","content":msg})

# ── SAVE LANG ─────────────────────────────────────────────────────────────────
def save_lang(l):
    ss.lang = l
    prefs = load_enc("prefs.dat",{}); prefs["lang"]=l; save_enc("prefs.dat",prefs)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="nova-logo">n<span>·</span>ova</div>', unsafe_allow_html=True)
    st.markdown('<div class="nova-tag">sobriety companion</div>', unsafe_allow_html=True)

    if ss.support:
        st.markdown('<div class="gentle-badge">♡ gentle mode active</div>', unsafe_allow_html=True)

    # Language
    lang_choice = st.selectbox("Language", list(LANG_NAMES.keys()),
                               format_func=lambda x: LANG_NAMES[x],
                               index=list(LANG_NAMES.keys()).index(ss.lang),
                               label_visibility="collapsed")
    if lang_choice != ss.lang: save_lang(lang_choice)

    # API Key
    if not ss.api_key:
        key_in = st.text_input("Anthropic API Key", type="password",
                               placeholder="sk-ant-...")
        if key_in:
            ss.api_key = key_in
            prefs = load_enc("prefs.dat",{}); prefs["api_key"]=key_in; save_enc("prefs.dat",prefs)

    # Streak
    st.markdown(
        f'<div class="streak-box">'
        f'<div class="streak-num">{ss.streak}</div>'
        f'<div class="streak-lbl">check-in days</div>'
        f'</div>', unsafe_allow_html=True)

    # Mood buttons
    st.markdown('<div class="mood-section">How are you feeling?</div>', unsafe_allow_html=True)
    ml = MOOD_LABELS[ss.lang]
    cols = st.columns(5)
    for i, sc in enumerate([5,4,3,2,1]):
        em, lb = ml[str(sc)]
        if cols[i].button(em, key=f"mb_{sc}", help=lb, use_container_width=True):
            log_mood(sc)
            st.rerun()

    # Goals
    st.markdown("---")
    st.markdown('<div class="mood-section">Today\'s goals</div>', unsafe_allow_html=True)
    if not ss.goals:
        st.caption(GOAL_EMPTY[ss.lang])
    else:
        for i, g in enumerate(ss.goals):
            col1, col2 = st.columns([0.1, 0.9])
            done = g.get("done", False)
            check = col1.checkbox("", value=done, key=f"g_{g['id']}", label_visibility="collapsed")
            if check != done:
                ss.goals[i]["done"] = check
                save_enc("goals.dat", ss.goals)
                st.rerun()
            label = f"~~{g['text']}~~" if done else g["text"]
            col2.markdown(f'<div style="font-size:12px;color:{"#433f54" if done else "#ddd8cf"};padding-top:4px">{label}</div>', unsafe_allow_html=True)

    new_goal = st.text_input("Add goal", placeholder="A small goal…", label_visibility="collapsed")
    if new_goal and st.button("+ Add", use_container_width=True):
        ss.goals.append({"id":int(time.time()*1000),"text":new_goal.strip(),"done":False})
        save_enc("goals.dat", ss.goals)
        st.rerun()

    # Disclaimer
    st.markdown(
        '<div class="disc">⚠ Not medical advice. Crisis: '
        '<a href="https://988lifeline.org">988</a> · '
        '<a href="https://findahelpline.com">findahelpline.com</a></div>',
        unsafe_allow_html=True)

# ── MAIN TABS ─────────────────────────────────────────────────────────────────
tab_chat, tab_journal, tab_trends, tab_export = st.tabs(["💬 Chat", "📓 Journal", "📊 Trends", "📤 Export"])

# ── CHAT TAB ──────────────────────────────────────────────────────────────────
with tab_chat:
    if not ss.api_key:
        st.warning("Please enter your Anthropic API key in the sidebar to start chatting.")
        st.stop()

    # Quick action pills
    lang = ss.lang
    quick = {
        "en": [("🌬️","Breathing","Guide me through a box breathing exercise"),
               ("🌱","Grounding","Walk me through 5-4-3-2-1 grounding"),
               ("✨","Affirmation","Give me a personal affirmation for my recovery journey"),
               ("🆘","Relapse","I'm struggling with a relapse and need support")],
        "es": [("🌬️","Respiración","Guíame en un ejercicio de respiración"),
               ("🌱","Anclaje","Guíame en el ejercicio 5-4-3-2-1"),
               ("✨","Afirmación","Dame una afirmación personal para mi recuperación"),
               ("🆘","Recaída","Estoy luchando con una recaída y necesito apoyo")],
        "fr": [("🌬️","Respiration","Guide-moi dans un exercice de respiration"),
               ("🌱","Ancrage","Guide-moi dans l'exercice 5-4-3-2-1"),
               ("✨","Affirmation","Donne-moi une affirmation personnelle pour ma guérison"),
               ("🆘","Rechute","Je lutte avec une rechute et j'ai besoin de soutien")],
    }
    qa_cols = st.columns(len(quick[lang]))
    for i, (em, lb, prompt) in enumerate(quick[lang]):
        if qa_cols[i].button(f"{em} {lb}", key=f"qa_{i}", use_container_width=True):
            ss.messages.append({"role":"user","content":prompt})
            if "rechute" in prompt.lower() or "relapse" in prompt.lower() or "recaída" in prompt.lower():
                ss.support = True

    # Display messages
    for msg in ss.messages:
        role = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(role, avatar="🌿" if role=="assistant" else "👤"):
            st.write(msg["content"])

    # Auto-greet
    if not ss.greeted and not ss.messages:
        greet = {
            "en": "Hello, I'm Nova 🌿\n\nI'm here as a quiet companion for your recovery journey — for check-ins, grounding moments, or just to listen.\n\n*⚠ This is not medical or professional advice. If you're struggling, please speak with someone you trust or a qualified professional.*\n\nHow are you feeling right now?",
            "es": "Hola, soy Nova 🌿\n\nEstoy aquí como compañera discreta para tu recuperación — para check-ins, momentos de calma o simplemente escuchar.\n\n*⚠ Esto no es consejo médico ni profesional. Si estás en dificultades, habla con alguien de confianza.*\n\n¿Cómo te sientes ahora mismo?",
            "fr": "Bonjour, je suis Nova 🌿\n\nJe suis ici comme compagne discrète pour votre rétablissement — pour des bilans, des moments d'ancrage ou simplement écouter.\n\n*⚠ Ceci n'est pas un conseil médical ou professionnel. Si vous traversez des difficultés, parlez à une personne de confiance.*\n\nComment vous sentez-vous en ce moment ?",
        }
        ss.messages.append({"role":"assistant","content":greet[ss.lang]})
        ss.greeted = True
        st.rerun()

    # If there's a pending user message (from mood button or quick action), respond
    if ss.messages and ss.messages[-1]["role"] == "user":
        user_msg = ss.messages[-1]["content"]
        # Crisis detection
        severe = ["suicide","kill myself","end it","self-harm","me tuer","suicidio"]
        if any(w in user_msg.lower() for w in severe):
            with st.chat_message("assistant", avatar="🌿"):
                st.warning(CRISIS)
        with st.chat_message("assistant", avatar="🌿"):
            try:
                client = anthropic.Anthropic(api_key=ss.api_key)
                msgs_clean = []
                for m in ss.messages[-20:]:
                    if msgs_clean and msgs_clean[-1]["role"] == m["role"]:
                        msgs_clean[-1]["content"] += "\n" + m["content"]
                    else: msgs_clean.append(dict(m))
                while msgs_clean and msgs_clean[0]["role"] == "assistant": msgs_clean.pop(0)
                placeholder = st.empty()
                full = ""
                with client.messages.stream(
                    model="claude-sonnet-4-20250514", max_tokens=1000,
                    system=build_system(), messages=msgs_clean) as stream:
                    for text in stream.text_stream:
                        full += text
                        placeholder.markdown(full + "▌")
                placeholder.markdown(full)
                ss.messages.append({"role":"assistant","content":full})
                # Save to journal if it's a journaling response
                if any(w in user_msg.lower() for w in ["journal","diary","reflect","diario","journal"]):
                    entry = {"text":user_msg,"nova_reply":full,
                             "ts":datetime.now().isoformat(),"date":str(date.today()),
                             "time":datetime.now().strftime("%H:%M")}
                    ss.journal_entries.insert(0,entry)
                    save_enc("journal.dat", ss.journal_entries)
            except anthropic.AuthenticationError:
                st.error("Invalid API key. Update it in the sidebar.")
            except Exception as e:
                st.info("I'm here with you. Let's breathe together: in 4… hold 4… out 4. You are not alone.")
                ss.messages.append({"role":"assistant","content":"I'm here with you. You're not alone."})

    # Chat input
    if prompt := st.chat_input(PLACEHOLDERS[ss.lang]):
        crisis_words = ["struggling","relapse","craving","relapsed","slip","urge","recaída","rechute"]
        if any(w in prompt.lower() for w in crisis_words): ss.support = True
        ss.messages.append({"role":"user","content":prompt})
        st.rerun()

# ── JOURNAL TAB ───────────────────────────────────────────────────────────────
with tab_journal:
    st.markdown("### 📓 Journal")
    jlabels = {"en":"Write a new entry:","es":"Escribe una nueva entrada:","fr":"Écrivez une nouvelle entrée:"}
    st.markdown(f"*{jlabels[ss.lang]}*")
    entry_text = st.text_area("Your entry", height=120, placeholder={
        "en":"What's on your mind today?",
        "es":"¿Qué tienes en mente hoy?",
        "fr":"Qu'avez-vous en tête aujourd'hui ?"}[ss.lang],
        label_visibility="collapsed")
    col1, col2 = st.columns([1,1])
    if col1.button("💾 Save entry", use_container_width=True) and entry_text.strip():
        entry = {"text":entry_text.strip(),"nova_reply":"",
                 "ts":datetime.now().isoformat(),"date":str(date.today()),
                 "time":datetime.now().strftime("%H:%M")}
        ss.journal_entries.insert(0, entry)
        save_enc("journal.dat", ss.journal_entries)
        st.success("Entry saved.")
    if col2.button("🌿 Ask Nova for a prompt", use_container_width=True):
        ss.messages.append({"role":"user","content":"Give me a gentle journaling prompt for my recovery journey today."})
        st.switch_page if hasattr(st,"switch_page") else None
        st.rerun()

    st.markdown("---")
    st.markdown("**Past entries:**")
    if not ss.journal_entries:
        st.caption("No journal entries yet.")
    else:
        for e in ss.journal_entries[:20]:
            with st.expander(f"{e.get('date','--')} · {e.get('time','--')}"):
                st.write(e.get("text",""))
                if e.get("nova_reply"):
                    st.markdown(f"*Nova: {e['nova_reply'][:300]}{'…' if len(e.get('nova_reply',''))>300 else ''}*")

# ── TRENDS TAB ────────────────────────────────────────────────────────────────
with tab_trends:
    st.markdown("### 📊 Mood Trends")
    if not ss.moods:
        st.caption("No mood data yet. Log your first check-in using the sidebar buttons.")
    else:
        trend = analyze_trend(ss.moods)
        if trend:
            c1,c2,c3 = st.columns(3)
            c1.metric("Average Mood", f"{trend['avg']}/5")
            direction_str = "↑ Improving" if trend["direction"]>0.4 else ("↓ Declining" if trend["direction"]<-0.4 else "→ Stable")
            c2.metric("Trend", direction_str)
            c3.metric("Entries Logged", len(ss.moods))
            if trend["consec_low"] >= 3:
                st.warning(f"⚠ You've logged {trend['consec_low']} consecutive low moods. Consider reaching out to someone you trust.")

        if HAS_PLOTLY and len(ss.moods) >= 2:
            df = pd.DataFrame(reversed(ss.moods[:30]))
            df["date_time"] = df["date"] + " " + df["time"]
            fig = px.line(df, x="date_time", y="score", markers=True,
                          title="Your mood over time",
                          labels={"date_time":"Date","score":"Mood (1–5)"},
                          color_discrete_sequence=["#6eb8a0"])
            fig.update_layout(
                plot_bgcolor="#161521", paper_bgcolor="#0d0c13",
                font_color="#ddd8cf", title_font_color="#6eb8a0",
                yaxis=dict(range=[0.5,5.5],tickvals=[1,2,3,4,5],
                           ticktext=["😰 Hard","😔 Low","😐 Okay","🙂 Good","😊 Great"],
                           gridcolor="#262537"),
                xaxis=dict(gridcolor="#262537"),
                showlegend=False)
            fig.add_hrect(y0=0.5,y1=2.5,fillcolor="#c46060",opacity=0.06,line_width=0)
            fig.add_hrect(y0=2.5,y1=3.5,fillcolor="#c97d4e",opacity=0.06,line_width=0)
            fig.add_hrect(y0=3.5,y1=5.5,fillcolor="#6eb8a0",opacity=0.06,line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Simple text chart fallback
            st.markdown("**Last 14 moods (oldest → newest)**")
            bars = ["▁","▂","▃","▄","▅","▆","▇","█"]
            recent = list(reversed(ss.moods[:14]))
            row = " ".join(bars[min(m["score"]-1,7)] for m in recent)
            st.code(row)

        st.markdown("**Recent check-ins:**")
        for m in ss.moods[:15]:
            sc = m.get("score",3)
            color = "#6eb8a0" if sc>=4 else ("#c97d4e" if sc==3 else "#c46060")
            bar = "█"*sc + "░"*(5-sc)
            st.markdown(
                f'<div style="display:flex;gap:12px;padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:12px">'
                f'<span style="color:#433f54">{m.get("date","--")} {m.get("time","--")}</span>'
                f'<span>{m.get("emoji","")}</span>'
                f'<span style="color:{color};font-family:monospace">{bar}</span>'
                f'<span style="color:#6b6780">{m.get("label","")}</span>'
                f'</div>', unsafe_allow_html=True)

# ── EXPORT TAB ────────────────────────────────────────────────────────────────
with tab_export:
    st.markdown("### 📤 Export My Data")
    st.caption("Download a readable copy of your Nova data. Your data never leaves your device.")

    if st.button("📥 Generate Export", use_container_width=True):
        today = str(date.today())
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "  NOVA — Personal Recovery Export",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            f"CHECK-IN STREAK: {ss.streak} days\n",
            "── GOALS ─────────────────────────────────────────",
        ]
        if ss.goals:
            for g in ss.goals:
                lines.append(f"  {'[DONE]' if g.get('done') else '[    ]'}  {g['text']}")
        else: lines.append("  No goals recorded.")
        lines.append("\n── MOOD HISTORY ──────────────────────────────────")
        if ss.moods:
            t = analyze_trend(ss.moods)
            if t: lines.append(f"  Average (last {t['count']}): {t['avg']}/5")
            for m in ss.moods[:60]:
                bar = "█"*m.get("score",0)+"░"*(5-m.get("score",0))
                lines.append(f"  {m.get('date','--')} {m.get('time','--')}  {bar}  {m.get('emoji','')} {m.get('label','')}")
        else: lines.append("  No mood entries.")
        lines.append("\n── JOURNAL ───────────────────────────────────────")
        if ss.journal_entries:
            for e in ss.journal_entries:
                lines.append(f"\n  [{e.get('date','--')} {e.get('time','--')}]")
                lines.append(f"  You: {e.get('text','')}")
                if e.get("nova_reply"):
                    lines.append(f"  Nova: {e['nova_reply'][:300]}")
        else: lines.append("  No journal entries.")
        lines += ["","━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                  "  Crisis support: 988 (US) · 3114 (France)","  https://findahelpline.com",
                  "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        content = "\n".join(lines)
        st.download_button(
            label="⬇ Download export.txt",
            data=content.encode("utf-8"),
            file_name=f"nova_export_{today}.txt",
            mime="text/plain",
            use_container_width=True)

    st.markdown("---")
    st.markdown("**Data stored locally at:** `~/.nova/`")
    st.markdown("All files are XOR-encrypted. Nothing is sent to any server except your messages to Claude.")
    if st.button("🗑 Clear all data", use_container_width=True):
        if st.checkbox("I understand this will delete all my Nova data"):
            for f in DATA_DIR.glob("*.dat"): f.unlink()
            for key in ["goals","moods","journal_entries","streak","messages","greeted","support"]:
                if key in ss: del ss[key]
            st.success("All data cleared."); st.rerun()
