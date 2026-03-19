#!/usr/bin/env python3
"""
Nova — Multilingual Sobriety Companion  v2.0
Powered by Claude (Anthropic API)

Usage:  python3 nova.py
Deps:   pip install anthropic rich
Key:    export ANTHROPIC_API_KEY=sk-ant-...

New in v2: journal log, mood trends, relapse flow, data export
"""

import os, sys, json, base64, re, time, textwrap
from datetime import datetime, date
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("\n[!] Run: pip install anthropic rich\n"); sys.exit(1)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich import box
    from rich.markup import escape
    from rich.rule import Rule
except ImportError:
    print("\n[!] Run: pip install anthropic rich\n"); sys.exit(1)

# ── XOR ENCRYPTION ────────────────────────────────────────────────────────────
XOR_KEY = "nova-xor-key-v1"

def xor_encrypt(text):
    enc = "".join(chr(ord(c) ^ ord(XOR_KEY[i % len(XOR_KEY)])) for i,c in enumerate(text))
    return base64.b64encode(enc.encode("latin-1")).decode("ascii")

def xor_decrypt(token):
    try:
        dec = base64.b64decode(token.encode("ascii")).decode("latin-1")
        return "".join(chr(ord(c) ^ ord(XOR_KEY[i % len(XOR_KEY)])) for i,c in enumerate(dec))
    except Exception: return ""

# ── STORAGE ───────────────────────────────────────────────────────────────────
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

# ── CONSOLE / THEME ───────────────────────────────────────────────────────────
console = Console()
CN = "sea_green2"; CU = "light_slate_blue"; CW = "dark_orange"
CD = "grey58"; CS = "sandy_brown"; CB = "grey35"; CR = "indian_red"

# ── LANGUAGES ─────────────────────────────────────────────────────────────────
LANGS = {"en": "English", "es": "Español", "fr": "Français"}

T = {
"en": {
  "greeting": (
    "⚠  This is not medical or professional advice.\n"
    "   If you're struggling, please speak with someone you trust\n"
    "   or a qualified professional.\n\n"
    "Hello, I'm Nova 🌿  A quiet companion for your recovery journey.\n"
    "I'm here for check-ins, grounding moments, or just to listen.\n\n"
    "How are you feeling right now?"),
  "mood_prompt": "How are you feeling?",
  "mood_labels": {"1":("😰","Struggling"),"2":("😔","Low"),"3":("😐","Okay"),"4":("🙂","Good"),"5":("😊","Great")},
  "menu_title": "What would you like to do?",
  "menu": [
    ("1","💬","Chat with Nova"),
    ("2","🎯","Log mood check-in"),
    ("3","📋","Goals"),
    ("4","📓","Journal"),
    ("5","🌬️","Breathing exercise"),
    ("6","🌱","Grounding (5-4-3-2-1)"),
    ("7","✨","Affirmation"),
    ("8","📊","Mood trends"),
    ("9","🆘","Relapse support"),
    ("e","📤","Export my data"),
    ("s","⚙️ ","Settings"),
    ("0","🚪","Exit"),
  ],
  "support_notice": "💛 Gentle mode is active — I'm here with you.",
  "farewell": "Take care of yourself. You showed up today — that matters. 🌿",
  "days_label": "check-in days", "no_goals": "No goals yet. Small steps count.",
  "no_moods": "No mood entries yet.", "goal_prompt": "A small goal (or Enter to skip)",
  "goal_added": "Goal added ✓",
  "journal_menu": ["n","Write new entry","p","Browse past entries","b","Back"],
  "no_journal": "No journal entries yet.",
  "export_done": "Exported to",
  "settings_lang": "Change language","settings_key": "Update API key","settings_clear": "Clear all data",
  "confirm_clear": "Are you sure? This deletes all Nova data.","cleared": "All data cleared.",
  "relapse_intro": (
    "This is a safe space. No judgment here — only support.\n\n"
    "Recovery isn't a straight line. One difficult moment doesn't erase\n"
    "everything you've built.\n\n"
    "I'm here. Can you tell me a little about what happened?"),
  "crisis": (
    "\n🆘  Crisis Resources:\n"
    "    · 988 Suicide & Crisis Lifeline (US): call or text 988\n"
    "    · SAMHSA Helpline: 1-800-662-4357\n"
    "    · Crisis Text Line: text HOME to 741741\n"
    "    · International: https://findahelpline.com\n"),
  "mood_msgs": {
    "5":"I just logged that I'm feeling great today 😊",
    "4":"I'm feeling pretty good today 🙂",
    "3":"I'm feeling okay, just checking in 😐",
    "2":"I'm feeling low today 😔",
    "1":"I'm really struggling right now and need support 😰"},
  "trend_labels": {
    "up": "📈 Mood trending upward — keep going.",
    "down": "📉 Mood trending lower — Nova will be extra gentle.",
    "stable": "〰  Mood holding steady.",
    "low_streak": "⚠  You've logged several low moods in a row. Consider reaching out to someone you trust."},
},
"es": {
  "greeting": (
    "⚠  Esto no es consejo médico ni profesional.\n"
    "   Si estás en dificultades, habla con alguien de confianza\n"
    "   o un profesional calificado.\n\n"
    "Hola, soy Nova 🌿  Una compañera discreta para tu recuperación.\n"
    "Estoy aquí para check-ins, momentos de calma o simplemente escuchar.\n\n"
    "¿Cómo te sientes ahora mismo?"),
  "mood_prompt": "¿Cómo te sientes?",
  "mood_labels": {"1":("😰","Muy mal"),"2":("😔","Bajo"),"3":("😐","Regular"),"4":("🙂","Bien"),"5":("😊","Genial")},
  "menu_title": "¿Qué quieres hacer?",
  "menu": [
    ("1","💬","Hablar con Nova"),("2","🎯","Registrar estado de ánimo"),
    ("3","📋","Objetivos"),("4","📓","Diario"),
    ("5","🌬️","Respiración"),("6","🌱","Anclaje (5-4-3-2-1)"),
    ("7","✨","Afirmación"),("8","📊","Tendencias de ánimo"),
    ("9","🆘","Apoyo ante recaída"),("e","📤","Exportar mis datos"),
    ("s","⚙️ ","Configuración"),("0","🚪","Salir"),
  ],
  "support_notice": "💛 Modo suave activo — estoy aquí contigo.",
  "farewell": "Cuídate. Apareciste hoy — eso importa. 🌿",
  "days_label": "días de check-in","no_goals": "Sin objetivos aún. Los pequeños pasos cuentan.",
  "no_moods": "Sin registros de estado de ánimo.","goal_prompt": "Un pequeño objetivo (o Enter para saltar)",
  "goal_added": "Objetivo añadido ✓",
  "journal_menu": ["n","Nueva entrada","p","Ver entradas anteriores","b","Volver"],
  "no_journal": "Sin entradas de diario aún.",
  "export_done": "Exportado a",
  "settings_lang": "Cambiar idioma","settings_key": "Actualizar clave API","settings_clear": "Borrar todos los datos",
  "confirm_clear": "¿Seguro? Esto borra todos los datos de Nova.","cleared": "Todos los datos borrados.",
  "relapse_intro": (
    "Este es un espacio seguro. Sin juicios — solo apoyo.\n\n"
    "La recuperación no es una línea recta. Un momento difícil no borra\n"
    "todo lo que has construido.\n\n"
    "Estoy aquí. ¿Puedes contarme un poco lo que pasó?"),
  "crisis": (
    "\n🆘  Recursos de crisis:\n"
    "    · Línea 988 (EEUU): llama o escribe al 988\n"
    "    · SAMHSA: 1-800-662-4357\n"
    "    · SMS de crisis: escribe HOLA al 741741\n"
    "    · Internacional: https://findahelpline.com\n"),
  "mood_msgs": {
    "5":"Acabo de registrar que me siento genial hoy 😊",
    "4":"Me siento bastante bien hoy 🙂",
    "3":"Me siento regular, solo haciendo check-in 😐",
    "2":"Me siento bajo hoy 😔",
    "1":"Estoy luchando mucho ahora mismo y necesito apoyo 😰"},
  "trend_labels": {
    "up": "📈 Estado de ánimo mejorando — sigue adelante.",
    "down": "📉 Estado de ánimo bajando — Nova estará más atenta.",
    "stable": "〰  Estado de ánimo estable.",
    "low_streak": "⚠  Has registrado varios estados bajos seguidos. Considera hablar con alguien de confianza."},
},
"fr": {
  "greeting": (
    "⚠  Ceci n'est pas un conseil médical ou professionnel.\n"
    "   Si vous traversez des difficultés, parlez à une personne\n"
    "   de confiance ou un professionnel qualifié.\n\n"
    "Bonjour, je suis Nova 🌿  Une compagne discrète pour votre rétablissement.\n"
    "Je suis ici pour des bilans, des moments d'ancrage ou simplement écouter.\n\n"
    "Comment vous sentez-vous en ce moment ?"),
  "mood_prompt": "Comment vous sentez-vous ?",
  "mood_labels": {"1":("😰","Très difficile"),"2":("😔","Bas"),"3":("😐","Correct"),"4":("🙂","Bien"),"5":("😊","Super")},
  "menu_title": "Que voulez-vous faire ?",
  "menu": [
    ("1","💬","Parler avec Nova"),("2","🎯","Bilan d'humeur"),
    ("3","📋","Objectifs"),("4","📓","Journal"),
    ("5","🌬️","Respiration"),("6","🌱","Ancrage (5-4-3-2-1)"),
    ("7","✨","Affirmation"),("8","📊","Tendances d'humeur"),
    ("9","🆘","Soutien rechute"),("e","📤","Exporter mes données"),
    ("s","⚙️ ","Paramètres"),("0","🚪","Quitter"),
  ],
  "support_notice": "💛 Mode doux actif — je suis là avec vous.",
  "farewell": "Prenez soin de vous. Vous êtes venu(e) aujourd'hui — ça compte. 🌿",
  "days_label": "jours de bilans","no_goals": "Pas encore d'objectifs. Les petits pas comptent.",
  "no_moods": "Pas encore de bilans d'humeur.","goal_prompt": "Un petit objectif (ou Entrée pour passer)",
  "goal_added": "Objectif ajouté ✓",
  "journal_menu": ["n","Nouvelle entrée","p","Voir les entrées passées","b","Retour"],
  "no_journal": "Pas encore d'entrées de journal.",
  "export_done": "Exporté vers",
  "settings_lang": "Changer la langue","settings_key": "Mettre à jour la clé API","settings_clear": "Effacer toutes les données",
  "confirm_clear": "Êtes-vous sûr(e) ? Cela supprime toutes les données Nova.","cleared": "Toutes les données effacées.",
  "relapse_intro": (
    "C'est un espace sûr. Aucun jugement ici — seulement du soutien.\n\n"
    "La guérison n'est pas une ligne droite. Un moment difficile n'efface pas\n"
    "tout ce que vous avez construit.\n\n"
    "Je suis là. Pouvez-vous me dire un peu ce qui s'est passé ?"),
  "crisis": (
    "\n🆘  Ressources de crise:\n"
    "    · Numéro prévention suicide (France): 3114\n"
    "    · SAMHSA (USA): 1-800-662-4357\n"
    "    · International: https://findahelpline.com\n"),
  "mood_msgs": {
    "5":"Je viens d'enregistrer que je me sens super aujourd'hui 😊",
    "4":"Je me sens plutôt bien aujourd'hui 🙂",
    "3":"Je me sens correct, juste un bilan 😐",
    "2":"Je me sens bas aujourd'hui 😔",
    "1":"J'ai vraiment du mal en ce moment et j'ai besoin de soutien 😰"},
  "trend_labels": {
    "up": "📈 Humeur en hausse — continuez ainsi.",
    "down": "📉 Humeur en baisse — Nova sera plus attentive.",
    "stable": "〰  Humeur stable.",
    "low_streak": "⚠  Plusieurs bilans bas d'affilée. Envisagez de parler à quelqu'un de confiance."},
},
}

# ── TREND ANALYSIS ────────────────────────────────────────────────────────────
def analyze_trend(moods):
    if len(moods) < 2: return None
    recent = [m["score"] for m in moods[:14]]
    avg = sum(recent) / len(recent)
    n = len(recent)
    newer = sum(recent[:n//2]) / (n//2) if n >= 4 else avg
    older = sum(recent[n//2:]) / (n - n//2) if n >= 4 else avg
    direction = newer - older  # positive = improving (recent > older)
    low_streak = sum(1 for m in moods if m["score"] <= 2)
    consec_low = 0
    for m in moods:
        if m["score"] <= 2: consec_low += 1
        else: break
    return {"avg": round(avg,1), "direction": direction,
            "low_streak": low_streak, "consec_low": consec_low,
            "count": len(recent), "scores": recent}

def trend_for_prompt(moods):
    t = analyze_trend(moods)
    if not t: return ""
    parts = [f"[MOOD CONTEXT] Recent avg: {t['avg']}/5 over {t['count']} entries."]
    if t["direction"] > 0.4: parts.append("Trend: improving.")
    elif t["direction"] < -0.4: parts.append("Trend: declining — be extra warm.")
    if t["consec_low"] >= 3:
        parts.append(f"Alert: {t['consec_low']} consecutive low moods — gently suggest professional support.")
    return " ".join(parts)

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
def system_prompt(lang, support, moods):
    lang_name = LANGS[lang]
    trend_ctx = trend_for_prompt(moods)
    return f"""You are Nova, a compassionate multilingual sobriety support companion in a terminal app.

LANGUAGE: Always respond in {lang_name}. Do not switch languages.

DISCLAIMER: Include verbatim at the very start of your FIRST response only:
"⚠  This is not medical or professional advice. If you're going through a difficult time, please consider speaking with someone you trust or a qualified professional."

{trend_ctx}

ROLE:
- Non-judgmental companion for people in recovery or struggling with sobriety
- Help with mood check-ins, grounding, breathing, affirmations, journaling
- Set small realistic daily goals
- Offer relapse support that is shame-free and warm

SUPPORT MODE: {"ACTIVE — shorter sentences, extra warmth, slower pace. Offer grounding immediately." if support else "INACTIVE — warm, encouraging daily companion tone."}

EXERCISES:
- Box breathing: inhale 4, hold 4, exhale 4, hold 4
- 4-7-8: inhale 4, hold 7, exhale 8
- 5-4-3-2-1 grounding: 5 seen, 4 heard, 3 felt, 2 smelled, 1 tasted
- Affirmations: personal, recovery-specific — not generic
- Journaling: one gentle open-ended prompt at a time

RELAPSE RESPONSE:
1. Validate without shame ("That takes courage to share.")
2. Recovery is non-linear — one slip doesn't erase progress
3. Ask what they need right now
4. Offer a grounding moment
5. Point toward support network or professional

LIMITS:
- NOT a therapist, counselor, or medical provider
- Never diagnose or recommend medications
- Crisis resources: 988 (US), 3114 (France), findahelpline.com
- Plain text only — no markdown ** or ## (terminal output)
- Short paragraphs, generous spacing, speak like a caring grounded friend"""

# ── NOVA CLASS ────────────────────────────────────────────────────────────────
class Nova:
    def __init__(self):
        self.lang = "en"; self.support = False
        self.history = []; self.goals = []; self.moods = []
        self.journal_entries = []; self.streak = 0
        self.last_date = ""; self.client = None; self.api_key = ""

    def t(self, k): return T[self.lang].get(k, T["en"].get(k, ""))

    # ── SETUP ──────────────────────────────────────────────────────────────────
    def setup(self):
        prefs = load_enc("prefs.dat", {})
        self.lang = prefs.get("lang", "en")
        self.api_key = prefs.get("api_key", "") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            console.print()
            console.print(Panel(
                "[bold]Nova needs your Anthropic API key.[/bold]\n\n"
                f"Get one at: [{CN}]https://console.anthropic.com/settings/keys[/{CN}]\n"
                f"Or set: [dim]export ANTHROPIC_API_KEY=sk-ant-...[/dim]",
                title=f"[bold {CN}]API Key Required[/bold {CN}]",
                border_style=CB, padding=(1,2)))
            self.api_key = Prompt.ask(f"\n[{CN}]Paste your API key[/{CN}]", password=True).strip()
            if not self.api_key: console.print("[red]No key. Exiting.[/red]"); sys.exit(1)
            prefs["api_key"] = self.api_key; save_enc("prefs.dat", prefs)
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.goals = load_enc("goals.dat", [])
        self.moods = load_enc("moods.dat", [])
        self.journal_entries = load_enc("journal.dat", [])
        self.streak = load_enc("streak.dat", 0)
        self.last_date = load_enc("checkdate.dat", "")
        today = str(date.today())
        if self.last_date and self.last_date != today:
            prev = date.fromisoformat(self.last_date)
            self.streak = self.streak + 1 if (date.today()-prev).days == 1 else 1
            save_enc("streak.dat", self.streak)

    # ── HEADER ─────────────────────────────────────────────────────────────────
    def header(self):
        console.print(); console.rule(style=CB)
        t = Text()
        t.append("  n", style=f"bold {CN}"); t.append("·", style=f"bold {CW}")
        t.append("o·v·a  ", style=f"bold {CN}")
        t.append(f"  {LANGS[self.lang]}", style=CD)
        if self.support: t.append("  ♡ gentle mode", style=CW)
        console.print(t, justify="center")
        if self.streak > 0:
            filled = min(self.streak, 28)
            bar = f"[{CS}]{'●'*filled}[/{CS}][{CD}]{'○'*(28-filled)}[/{CD}]"
            console.print(f"  [{CS}]★ {self.streak}[/{CS}] [{CD}]{self.t('days_label')}[/{CD}]  {bar}", justify="center")
        console.rule(style=CB); console.print()

    # ── MENU ───────────────────────────────────────────────────────────────────
    def show_menu(self):
        console.print(f"  [{CD}]{self.t('menu_title')}[/{CD}]\n")
        for key, icon, label in self.t("menu"):
            s = CN if key == "1" else CD
            console.print(f"    [{s}]{key}[/{s}]  {icon}  {label}")
        console.print()

    # ── BUBBLES ────────────────────────────────────────────────────────────────
    def nova_says(self, text):
        lines = []
        for para in text.split("\n"):
            if not para.strip(): lines.append("")
            else: lines.extend(textwrap.wrap(para, width=66))
        console.print(Panel("\n".join(lines), title=f"[bold {CN}]Nova[/bold {CN}]",
                            title_align="left", border_style=CN, padding=(0,2)))

    def user_says(self, text):
        console.print(Panel(f"[{CU}]{escape(textwrap.fill(text, 60))}[/{CU}]",
                            title=f"[bold {CU}]You[/bold {CU}]",
                            title_align="right", border_style=CU, padding=(0,2)))

    # ── CLAUDE CALL ────────────────────────────────────────────────────────────
    def ask_nova(self, user_msg, system_override=None):
        crisis_words = ["struggling","relapse","relapsed","craving","slip","slipped",
                        "urge","give up","hopeless","ayudame","recaida","antojo",
                        "je lutte","envie de","rechute"]
        if any(w in user_msg.lower() for w in crisis_words):
            self.support = True
            console.print(f"\n  [{CW}]{self.t('support_notice')}[/{CW}]")
        severe = ["kill","suicide","end it","self-harm","hurt myself","matar","suicidio","me tuer"]
        if any(w in user_msg.lower() for w in severe):
            console.print(self.t("crisis"), style=CW)
        self.history.append({"role":"user","content":user_msg})
        msgs = self.history[-20:]
        while msgs and msgs[0]["role"] == "assistant": msgs.pop(0)
        clean = []
        for m in msgs:
            if clean and clean[-1]["role"] == m["role"]: clean[-1]["content"] += "\n"+m["content"]
            else: clean.append(dict(m))
        sys = system_override or system_prompt(self.lang, self.support, self.moods)
        try:
            with console.status(f"[{CD}]Nova is thinking…[/{CD}]", spinner="dots"):
                resp = self.client.messages.create(
                    model="claude-sonnet-4-20250514", max_tokens=1000,
                    system=sys, messages=clean)
            reply = resp.content[0].text
        except anthropic.AuthenticationError:
            reply = "I couldn't connect — your API key may be invalid. Go to Settings (s) to update it."
        except Exception:
            reply = self._fallback()
        self.history.append({"role":"assistant","content":reply})
        today = str(date.today())
        if self.last_date != today:
            self.last_date = today; save_enc("checkdate.dat", today)
        return reply

    def _fallback(self):
        return {"en":"I'm here with you.\n\nLet's breathe: in 4… hold 4… out 4.\n\nYou are not alone.",
                "es":"Estoy aquí contigo.\n\nRespiremos: inhala 4… aguanta 4… exhala 4.\n\nNo estás solo/a.",
                "fr":"Je suis là avec vous.\n\nRespirons: inspirez 4… retenez 4… expirez 4.\n\nVous n'êtes pas seul(e)."
               }.get(self.lang,"I'm here with you.")

    # ── CHAT ───────────────────────────────────────────────────────────────────
    def chat(self):
        console.print(f"\n  [{CD}]Type your message and press Enter. 'back' to return to menu.[/{CD}]\n")
        while True:
            try: user_in = Prompt.ask(f"[{CU}]You[/{CU}]")
            except (KeyboardInterrupt, EOFError): break
            if user_in.strip().lower() in ("back","b","menu","exit","quit","salir","retour"): break
            if not user_in.strip(): continue
            self.user_says(user_in); self.nova_says(self.ask_nova(user_in))

    # ── MOOD CHECK-IN ──────────────────────────────────────────────────────────
    def mood_checkin(self):
        console.print(f"\n  [{CD}]{self.t('mood_prompt')}[/{CD}]\n")
        labels = self.t("mood_labels")
        for k,(em,lb) in sorted(labels.items()):
            c = CN if k in("4","5") else (CW if k=="3" else CR)
            console.print(f"    [{c}]{k}[/{c}]  {em}  {lb}")
        console.print()
        choice = Prompt.ask(f"  [{CN}]Your mood (1-5)[/{CN}]", choices=["1","2","3","4","5"])
        em, lb = labels[choice]
        entry = {"score":int(choice),"emoji":em,"label":lb,
                 "time":datetime.now().strftime("%H:%M"),"date":str(date.today())}
        self.moods.insert(0, entry)
        if len(self.moods) > 90: self.moods = self.moods[:90]
        save_enc("moods.dat", self.moods)
        if int(choice) <= 2:
            self.support = True; console.print(f"\n  [{CW}]{self.t('support_notice')}[/{CW}]")
        prompt = self.t("mood_msgs")[choice]
        self.user_says(prompt); self.nova_says(self.ask_nova(prompt))

    # ── GOALS ──────────────────────────────────────────────────────────────────
    def manage_goals(self):
        while True:
            console.print()
            if not self.goals:
                console.print(f"  [{CD}]{self.t('no_goals')}[/{CD}]")
            else:
                for i,g in enumerate(self.goals,1):
                    done = f"[{CN}]✓[/{CN}]" if g.get("done") else "○"
                    s = CD if g.get("done") else "default"
                    console.print(f"  {done}  [{CD}]{i}.[/{CD}]  [{s}]{g['text']}[/{s}]")
            console.print(f"\n  [{CD}]a[/{CD}] add  [{CD}]d#[/{CD}] toggle  [{CD}]x#[/{CD}] delete  [{CD}]back[/{CD}]")
            cmd = Prompt.ask(f"\n  [{CN}]>[/{CN}]").strip().lower()
            if cmd in ("back","b","menu","exit"): break
            elif cmd == "a":
                txt = Prompt.ask(f"  [{CN}]{self.t('goal_prompt')}[/{CN}]")
                if txt.strip():
                    self.goals.append({"id":int(time.time()*1000),"text":txt.strip(),"done":False})
                    save_enc("goals.dat",self.goals)
                    console.print(f"  [{CN}]{self.t('goal_added')}[/{CN}]")
            elif re.match(r"^d\d+$",cmd):
                i=int(cmd[1:])-1
                if 0<=i<len(self.goals):
                    self.goals[i]["done"] = not self.goals[i]["done"]
                    save_enc("goals.dat",self.goals)
            elif re.match(r"^x\d+$",cmd):
                i=int(cmd[1:])-1
                if 0<=i<len(self.goals):
                    r=self.goals.pop(i); save_enc("goals.dat",self.goals)
                    console.print(f"  [{CD}]Removed: {r['text']}[/{CD}]")

    # ── JOURNAL ────────────────────────────────────────────────────────────────
    def journal(self):
        while True:
            console.print(f"\n  [{CD}]n[/{CD}] write new  [{CD}]p[/{CD}] browse past  [{CD}]back[/{CD}]")
            cmd = Prompt.ask(f"\n  [{CN}]>[/{CN}]").strip().lower()
            if cmd in ("back","b","menu","exit"): break
            elif cmd == "n": self._write_journal()
            elif cmd == "p": self._browse_journal()

    def _write_journal(self):
        console.print(f"\n  [{CD}]Type your entry, or 'prompt' to get a question from Nova. 'back' to cancel.[/{CD}]\n")
        user_in = Prompt.ask(f"[{CU}]You[/{CU}]")
        if user_in.strip().lower() in ("back","b"): return
        if user_in.strip().lower() in ("prompt","invite","ayuda","exercice"):
            user_in = "Give me a gentle journaling prompt for my recovery journey today."
        self.user_says(user_in)
        reply = self.ask_nova(user_in)
        self.nova_says(reply)
        # Save the journal entry
        entry = {"text": user_in, "nova_reply": reply,
                 "ts": datetime.now().isoformat(), "date": str(date.today()),
                 "time": datetime.now().strftime("%H:%M")}
        self.journal_entries.insert(0, entry)
        if len(self.journal_entries) > 200: self.journal_entries = self.journal_entries[:200]
        save_enc("journal.dat", self.journal_entries)
        console.print(f"\n  [{CD}]Entry saved. Continue writing? (Enter to skip)[/{CD}]")
        more = Prompt.ask(f"[{CU}]You[/{CU}]")
        if more.strip():
            self.user_says(more); self.nova_says(self.ask_nova(more))
            more_entry = {"text": more, "nova_reply": self.history[-1]["content"],
                          "ts": datetime.now().isoformat(), "date": str(date.today()),
                          "time": datetime.now().strftime("%H:%M")}
            self.journal_entries.insert(0, more_entry)
            save_enc("journal.dat", self.journal_entries)

    def _browse_journal(self):
        console.print()
        if not self.journal_entries:
            console.print(f"  [{CD}]{self.t('no_journal')}[/{CD}]"); return
        entries_per_page = 5
        page = 0
        while True:
            start = page * entries_per_page
            batch = self.journal_entries[start:start+entries_per_page]
            if not batch: break
            for i, e in enumerate(batch, start+1):
                console.print(f"\n  [{CS}]{e['date']} {e['time']}[/{CS}]")
                console.print(Panel(
                    textwrap.fill(e["text"], 60),
                    border_style=CB, padding=(0,2)))
            total = len(self.journal_entries)
            shown = min(start+entries_per_page, total)
            console.print(f"\n  [{CD}]Showing {start+1}–{shown} of {total}  [/{CD}]", end="")
            if shown < total:
                console.print(f"[{CD}]  'n' next page  'back' to return[/{CD}]")
                cmd = Prompt.ask(f"  [{CN}]>[/{CN}]").strip().lower()
                if cmd == "n": page += 1
                else: break
            else:
                Prompt.ask(f"  [{CD}]Press Enter to return[/{CD}]", default=""); break

    # ── MOOD TRENDS ────────────────────────────────────────────────────────────
    def mood_trends(self):
        console.print()
        if not self.moods:
            console.print(f"  [{CD}]{self.t('no_moods')}[/{CD}]")
            Prompt.ask(f"  [{CD}]Press Enter[/{CD}]", default=""); return

        trend = analyze_trend(self.moods)

        # Summary stats
        if trend:
            avg_c = CN if trend["avg"] >= 3.5 else (CW if trend["avg"] >= 2.5 else CR)
            console.print(f"  [{CD}]7-day average:[/{CD}]  [{avg_c}]{trend['avg']}/5[/{avg_c}]   "
                          f"[{CD}]Entries tracked:[/{CD}] [{CS}]{len(self.moods)}[/{CS}]")
            if trend["direction"] > 0.4:
                console.print(f"  [{CN}]{self.t('trend_labels')['up']}[/{CN}]")
            elif trend["direction"] < -0.4:
                console.print(f"  [{CW}]{self.t('trend_labels')['down']}[/{CW}]")
            else:
                console.print(f"  [{CD}]{self.t('trend_labels')['stable']}[/{CD}]")
            if trend["consec_low"] >= 3:
                console.print(f"\n  [{CR}]{self.t('trend_labels')['low_streak']}[/{CR}]")

        # ASCII chart (last 21 days)
        console.print(f"\n  [{CD}]Last {min(21,len(self.moods))} moods  (oldest → newest)[/{CD}]\n")
        recent = list(reversed(self.moods[:21]))
        bars = ["▁","▂","▃","▄","▅","▆","▇","█"]
        row = "  "
        for m in recent:
            sc = m["score"]
            bar = bars[min(sc-1, 7)]
            c = CN if sc >= 4 else (CW if sc == 3 else CR)
            row += f"[{c}]{bar}[/{c}] "
        console.print(row)
        console.print(f"  [{CD}]😰 1   😔 2   😐 3   🙂 4   😊 5[/{CD}]")

        # Recent table
        console.print()
        tbl = Table(show_header=True, header_style=CD, box=box.SIMPLE, padding=(0,2))
        tbl.add_column("Date",style=CD,width=12); tbl.add_column("Time",style=CD,width=7)
        tbl.add_column("",width=4); tbl.add_column("Mood",width=14); tbl.add_column("",width=12)
        for e in self.moods[:10]:
            sc = e.get("score",3)
            c = CN if sc>=4 else (CW if sc==3 else CR)
            bar = f"[{c}]{'█'*sc}[/{c}][{CD}]{'░'*(5-sc)}[/{CD}]"
            tbl.add_row(e.get("date","--"),e.get("time","--"),e.get("emoji",""),e.get("label",""),bar)
        console.print(tbl)
        Prompt.ask(f"  [{CD}]Press Enter to return[/{CD}]", default="")

    # ── RELAPSE SUPPORT ────────────────────────────────────────────────────────
    def relapse_flow(self):
        self.support = True
        console.print(f"\n  [{CW}]{self.t('support_notice')}[/{CW}]")
        self.nova_says(self.t("relapse_intro"))
        # Show crisis resources
        console.print(self.t("crisis"), style=CD)
        # Structured conversation loop
        console.print(f"  [{CD}]I'm listening. Type your message, or 'back' when ready.[/{CD}]\n")
        step = 0
        while True:
            try: user_in = Prompt.ask(f"[{CU}]You[/{CU}]")
            except (KeyboardInterrupt, EOFError): break
            if user_in.strip().lower() in ("back","b","menu","exit","quit"): break
            if not user_in.strip(): continue
            self.user_says(user_in)
            # Inject relapse-specific context
            relapse_sys = system_prompt(self.lang, True, self.moods) + (
                "\n\nRELAPSE CONTEXT: The user has just disclosed a relapse or slip. "
                "Follow this exact sequence across your responses:\n"
                f"Step {step+1}. " + [
                    "First: validate their feelings, zero judgment. Acknowledge courage to share.",
                    "Remind them recovery is non-linear. One slip doesn't erase their progress.",
                    "Ask: what do they need right now? Offer a grounding exercise.",
                    "Gently ask about their support network. Anyone they trust they can reach out to?",
                    "Warm close: remind them you're here, and point to professional help if needed.",
                ][min(step, 4)]
            )
            reply = self.ask_nova(user_in, system_override=relapse_sys)
            self.nova_says(reply)
            step = min(step+1, 4)

    # ── EXPORT ─────────────────────────────────────────────────────────────────
    def export_data(self):
        today = str(date.today())
        out_path = DATA_DIR / f"nova_export_{today}.txt"
        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "  NOVA — Personal Recovery Export",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "  This file contains your private Nova data.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            f"CHECK-IN STREAK: {self.streak} days\n",
        ]
        # Goals
        lines.append("── GOALS ─────────────────────────────────────────")
        if self.goals:
            for g in self.goals:
                status = "[DONE]" if g.get("done") else "[    ]"
                lines.append(f"  {status}  {g['text']}")
        else:
            lines.append("  No goals recorded.")
        lines.append("")
        # Moods
        lines.append("── MOOD HISTORY ──────────────────────────────────")
        if self.moods:
            trend = analyze_trend(self.moods)
            if trend:
                lines.append(f"  Average (last {trend['count']}): {trend['avg']}/5")
            for m in self.moods[:50]:
                bar = "█" * m.get("score",0) + "░" * (5-m.get("score",0))
                lines.append(f"  {m.get('date','--')} {m.get('time','--')}  {bar}  {m.get('emoji','')} {m.get('label','')}")
        else:
            lines.append("  No mood entries recorded.")
        lines.append("")
        # Journal
        lines.append("── JOURNAL ENTRIES ───────────────────────────────")
        if self.journal_entries:
            for e in self.journal_entries:
                lines.append(f"\n  [{e.get('date','--')} {e.get('time','--')}]")
                lines.append(f"  You: {e.get('text','')}")
                lines.append(f"  Nova: {e.get('nova_reply','')[:200]}{'...' if len(e.get('nova_reply',''))>200 else ''}")
        else:
            lines.append("  No journal entries recorded.")
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("  Not medical or professional advice.")
        lines.append("  Crisis support: 988 (US) · 3114 (France)")
        lines.append("  https://findahelpline.com")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"\n  [{CN}]{self.t('export_done')}:[/{CN}]")
        console.print(f"  [{CS}]{out_path}[/{CS}]\n")
        Prompt.ask(f"  [{CD}]Press Enter to return[/{CD}]", default="")

    # ── QUICK ACTIONS ──────────────────────────────────────────────────────────
    def breathing(self):
        p = "Guide me step by step through a box breathing exercise right now."
        self.user_says("Breathing exercise"); self.nova_says(self.ask_nova(p))

    def grounding(self):
        p = "Walk me gently through a 5-4-3-2-1 grounding exercise right now."
        self.user_says("5-4-3-2-1 grounding"); self.nova_says(self.ask_nova(p))

    def affirmation(self):
        p = "Give me a warm personal affirmation for my recovery journey today."
        self.user_says("Affirmation"); self.nova_says(self.ask_nova(p))

    # ── SETTINGS ───────────────────────────────────────────────────────────────
    def settings(self):
        console.print()
        console.print(f"  [{CD}]1[/{CD}]  {self.t('settings_lang')}")
        console.print(f"  [{CD}]2[/{CD}]  {self.t('settings_key')}")
        console.print(f"  [{CD}]3[/{CD}]  {self.t('settings_clear')}")
        console.print(f"  [{CD}]0[/{CD}]  Back\n")
        cmd = Prompt.ask(f"  [{CN}]>[/{CN}]", choices=["0","1","2","3"])
        if cmd == "1":
            console.print()
            for code,name in LANGS.items(): console.print(f"  [{CD}]{code}[/{CD}]  {name}")
            nl = Prompt.ask(f"  [{CN}]Language[/{CN}]", choices=list(LANGS.keys()), default=self.lang)
            self.lang = nl; prefs = load_enc("prefs.dat",{}); prefs["lang"]=nl; save_enc("prefs.dat",prefs)
        elif cmd == "2":
            k = Prompt.ask(f"  [{CN}]New API key[/{CN}]", password=True).strip()
            if k:
                self.api_key=k; self.client=anthropic.Anthropic(api_key=k)
                prefs=load_enc("prefs.dat",{}); prefs["api_key"]=k; save_enc("prefs.dat",prefs)
                console.print(f"  [{CN}]Key updated.[/{CN}]")
        elif cmd == "3":
            if Confirm.ask(f"  [{CW}]{self.t('confirm_clear')}[/{CW}]"):
                for f in DATA_DIR.glob("*.dat"): f.unlink()
                self.goals=[]; self.moods=[]; self.streak=0; self.history=[]
                self.journal_entries=[]; console.print(f"  [{CN}]{self.t('cleared')}[/{CN}]")

    # ── MAIN LOOP ──────────────────────────────────────────────────────────────
    def run(self):
        prefs = load_enc("prefs.dat",{})
        if "lang" not in prefs:
            console.print(); console.rule(style=CB)
            console.print(Text("  n·o·v·a  ", style=f"bold {CN}"), justify="center")
            console.rule(style=CB)
            console.print(f"\n  [bold]Choose your language / Elige tu idioma / Choisissez votre langue[/bold]\n")
            for code,name in LANGS.items(): console.print(f"    [{CN}]{code}[/{CN}]  {name}")
            console.print()
            self.lang = Prompt.ask(f"  [{CN}]Language[/{CN}]", choices=list(LANGS.keys()), default="en")
            prefs["lang"]=self.lang; save_enc("prefs.dat",prefs)
        self.setup()
        self.header(); self.nova_says(self.t("greeting"))
        while True:
            self.header(); self.show_menu()
            choice = Prompt.ask(f"  [{CN}]>[/{CN}]", default="1").strip().lower()
            if   choice=="1": self.chat()
            elif choice=="2": self.mood_checkin()
            elif choice=="3": self.manage_goals()
            elif choice=="4": self.journal()
            elif choice=="5": self.breathing()
            elif choice=="6": self.grounding()
            elif choice=="7": self.affirmation()
            elif choice=="8": self.mood_trends()
            elif choice=="9": self.relapse_flow()
            elif choice=="e": self.export_data()
            elif choice=="s": self.settings()
            elif choice=="0":
                console.print()
                console.print(Panel(f"[{CN}]{self.t('farewell')}[/{CN}]",border_style=CN,padding=(1,4)))
                console.print(); break

if __name__ == "__main__":
    try: Nova().run()
    except KeyboardInterrupt:
        console.print(f"\n\n  [{CD}]Goodbye. Take care of yourself. 🌿[/{CD}]\n"); sys.exit(0)
