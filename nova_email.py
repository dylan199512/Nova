#!/usr/bin/env python3
"""Nova Weekly Email — run: python3 nova_email.py --setup"""
import os, sys, smtplib, subprocess, argparse
from datetime import date, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("Run: pip install rich"); sys.exit(1)
sys.path.insert(0, str(Path(__file__).parent))
from nova import load_enc, save_enc, analyze_trend
console = Console()
CN="sea_green2"; CD="grey58"; CW="dark_orange"; CB="grey35"

def build_text(streak, moods, goals):
    today = date.today()
    week_start = today - timedelta(days=7)
    week_moods = [m for m in moods if m.get("date","") >= str(week_start)]
    trend = analyze_trend(moods) if moods else None
    lines = [
        "Nova Weekly Reflection",
        today.strftime("%B %d, %Y"),
        "",
        "Not medical advice. Crisis: 988 (US) · findahelpline.com",
        "",
        f"★ {streak} check-in days",
        "",
    ]
    if trend:
        lines.append(f"Mood average: {trend['avg']}/5")
        if trend["direction"] > 0.4: lines.append("Trend: improving ↑")
        elif trend["direction"] < -0.4: lines.append("Trend: declining ↓ — be gentle with yourself")
        else: lines.append("Trend: stable")
        if trend.get("consec_low",0) >= 3:
            lines.append("⚠ Several low moods this week. Consider reaching out to someone.")
        lines.append("")
    if week_moods:
        lines.append("This week:")
        for m in week_moods[:7]:
            sc = m.get("score",3)
            lines.append(f"  {m.get('date','--')}  {'█'*sc}{'░'*(5-sc)}  {m.get('emoji','')} {m.get('label','')}")
        lines.append("")
    if goals:
        lines.append("Your goals:")
        for g in goals[:8]:
            lines.append(f"  {'[✓]' if g.get('done') else '[ ]'} {g['text']}")
        lines.append("")
    lines += ["You showed up this week. That always matters. 🌿"]
    return "\n".join(lines)

def send_summary():
    config = load_enc("email_config.dat")
    if not config:
        console.print(f"  [{CW}]No config. Run: python3 nova_email.py --setup[/{CW}]"); return
    moods  = load_enc("moods.dat", [])
    goals  = load_enc("goals.dat", [])
    streak = load_enc("streak.dat", 0)
    subject = f"Nova · Weekly reflection · {date.today().strftime('%B %d')}"
    body = build_text(streak, moods, goals)
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = config["from_email"]
    msg["To"] = config["to_email"]
    msg.attach(MIMEText(body, "plain"))
    with console.status("Sending...", spinner="dots"):
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(config["from_email"], config["gmail_app_password"])
            s.sendmail(config["from_email"], config["to_email"], msg.as_string())
    console.print(f"  [{CN}]✓ Sent to {config['to_email']}[/{CN}]")

def setup():
    console.print()
    config = {}
    console.print(f"  [{CD}]You need a Gmail App Password (not your regular password).[/{CD}]")
    console.print(f"  [{CD}]Get one: https://myaccount.google.com/apppasswords[/{CD}]\n")
    config["method"] = "gmail"
    config["from_email"] = Prompt.ask(f"  [{CN}]Your Gmail address[/{CN}]")
    config["gmail_app_password"] = Prompt.ask(f"  [{CN}]Gmail App Password[/{CN}]", password=True)
    config["to_email"] = Prompt.ask(f"  [{CN}]Send to[/{CN}]", default=config["from_email"])
    save_enc("email_config.dat", config)
    console.print(f"  [{CN}]✓ Config saved.[/{CN}]")
    if Confirm.ask(f"\n  [{CN}]Send a test email now?[/{CN}]"): send_summary()
    if Confirm.ask(f"  [{CN}]Schedule weekly email every Sunday 9am?[/{CN}]"): setup_cron()

def setup_cron():
    python = sys.executable
    script = str(Path(__file__).resolve())
    log = str(Path.home() / ".nova" / "email.log")
    job = f"0 9 * * 0 {python} {script} --send >> {log} 2>&1"
    r = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
    existing = r.stdout if r.returncode == 0 else ""
    if "nova_email" in existing:
        console.print(f"  [{CD}]Already scheduled.[/{CD}]"); return
    subprocess.run(f'(crontab -l 2>/dev/null; echo "{job}") | crontab -', shell=True)
    console.print(f"  [{CN}]✓ Scheduled every Sunday at 9am.[/{CN}]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--send",  action="store_true")
    parser.add_argument("--cron",  action="store_true")
    args = parser.parse_args()
    if args.setup: setup()
    elif args.send: send_summary()
    elif args.cron: setup_cron()
    else:
        console.print(f"\n  [{CN}]Nova Email[/{CN}]  --setup  --send  --cron\n")
