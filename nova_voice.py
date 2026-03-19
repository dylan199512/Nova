#!/usr/bin/env python3
"""Nova Voice — run: python3 nova_voice.py"""
import os, sys, tempfile, time
from pathlib import Path
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
except ImportError:
    print("Run: pip install sounddevice soundfile numpy"); sys.exit(1)
try:
    import whisper
except ImportError:
    print("Run: pip install openai-whisper"); sys.exit(1)
from rich.console import Console
from rich.prompt import Prompt
console = Console()
sys.path.insert(0, str(Path(__file__).parent))
from nova import Nova, CN, CD, CB, load_enc, save_enc, LANGS
WHISPER_MODEL = None
SAMPLE_RATE = 16000
def load_whisper():
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        with console.status("Loading Whisper (first run ~140MB)...", spinner="dots"):
            WHISPER_MODEL = whisper.load_model("base")
    return WHISPER_MODEL
def record(max_sec=30, thresh=0.01, sil_dur=1.8):
    console.print(f"\n  [{CN}]🎙  Listening… speak now[/{CN}]")
    chunks=[]; silent=0; speaking=False; frames=0
    fpc=int(SAMPLE_RATE*0.1); need=int(sil_dur/0.1)
    def cb(d,f,t,s):
        nonlocal silent,speaking
        chunks.append(d.copy())
        rms=__import__('numpy').sqrt(__import__('numpy').mean(d**2))
        if rms>thresh: speaking=True; silent=0
        elif speaking: silent+=1
    with sd.InputStream(samplerate=SAMPLE_RATE,channels=1,blocksize=fpc,callback=cb):
        while frames<max_sec*10:
            time.sleep(0.1); frames+=1
            if speaking and silent>=need: break
    if not chunks: return None
    return __import__('numpy').concatenate(chunks).flatten()
def transcribe(audio, lang="en"):
    model=load_whisper()
    with console.status("Transcribing...", spinner="dots"):
        with tempfile.NamedTemporaryFile(suffix=".wav",delete=False) as f:
            sf.write(f.name, audio, SAMPLE_RATE); p=f.name
        r=model.transcribe(p, language=lang, fp16=False)
        os.unlink(p)
    return r["text"].strip()
class VoiceNova(Nova):
    def voice_chat(self):
        console.print(f"\n  [grey58]Enter = 🎙 speak | type = keyboard | back = menu[/grey58]\n")
        while True:
            try: u=Prompt.ask(f"[{CN}]You[/{CN}]")
            except (KeyboardInterrupt,EOFError): break
            if u.strip().lower() in("back","b","menu","exit"): break
            if not u.strip():
                audio=record()
                if audio is None or len(audio)<SAMPLE_RATE*0.3:
                    console.print("  [grey58]Didn't catch that.[/grey58]"); continue
                u=transcribe(audio, self.lang)
                if not u: console.print("  [grey58]Couldn't transcribe.[/grey58]"); continue
                console.print(f"  [grey58]Heard:[/grey58] [{CN}]{u}[/{CN}]")
            self.user_says(u); self.nova_says(self.ask_nova(u))
    def run(self):
        prefs=load_enc("prefs.dat",{})
        if "lang" not in prefs:
            self.lang=Prompt.ask("Language",choices=list(LANGS.keys()),default="en")
            prefs["lang"]=self.lang; save_enc("prefs.dat",prefs)
        self.setup(); load_whisper()
        self.header(); self.nova_says(self.t("greeting"))
        while True:
            self.header()
            console.print("  [grey58]1[/grey58] 🎙 Voice  [grey58]2[/grey58] 💬 Text  [grey58]3[/grey58] 🎯 Mood  [grey58]4[/grey58] 🌬 Breathing  [grey58]0[/grey58] Exit\n")
            c=Prompt.ask(f"  [{CN}]>[/{CN}]",default="1").strip()
            if c=="1": self.voice_chat()
            elif c=="2": self.chat()
            elif c=="3": self.mood_checkin()
            elif c=="4": self.breathing()
            elif c=="0": break
if __name__=="__main__":
    try: VoiceNova().run()
    except KeyboardInterrupt: sys.exit(0)
