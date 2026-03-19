# Contributing to Nova

Thank you for wanting to help. Nova exists to support people in recovery —
every contribution, however small, has real impact.

---

## Who we want to hear from

- People in recovery or who work alongside people in recovery
- Developers with accessibility or mental health tech experience
- Translators (especially for under-represented languages)
- Designers who can improve the Streamlit UI
- Anyone who has used Nova and wants it to be better

---

## Ground rules

1. **Be kind.** This project touches vulnerable people's lives. The same
   warmth Nova shows users should show up in how we treat each other.

2. **No judgment.** Recovery is non-linear. So is open source contribution.

3. **Disclaimer always.** Any fork or deployment must retain the
   "not medical advice" disclaimer and crisis hotline information.

4. **Privacy first.** Never add analytics, telemetry, or remote logging
   of user conversations or personal data without explicit opt-in.

---

## How to contribute

### Report a bug

Open an issue with:
- What you expected to happen
- What actually happened
- Your OS and Python version
- Steps to reproduce (don't include personal recovery data)

### Add a language

1. Copy the English block in `T = {...}` in both `nova.py` and `nova_web.py`
2. Translate all strings — pay attention to tone, not just literal meaning
3. Add the language code to `LANGS` in both files
4. Add mood label variants to `MOOD_LABELS` in `nova_web.py`
5. Test the full flow in that language
6. Open a PR with the language name in the title

**Priority languages:** Portuguese (Brazil), German, Arabic, Hindi, Mandarin

### Improve Nova's responses

The system prompt lives in `system_prompt()` / `build_system()`.
If you have experience in counseling, recovery support, or clinical psychology
and want to improve how Nova responds — especially the relapse flow or
crisis detection — please open an issue to discuss first.

### Add a feature

Before building, open an issue describing:
- What the feature does
- Who it helps and how
- Whether it touches user data (encryption implications)

Small PRs are easier to review than large ones.

---

## Development setup

```bash
git clone https://github.com/yourusername/nova.git
cd nova

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...

# Terminal
python3 nova.py

# Web
streamlit run nova_web.py
```

---

## What we will not add

- Advertising or sponsorship integrations
- Tracking, analytics, or telemetry without explicit opt-in
- Features that could replace or simulate professional mental health care
- Anything that removes or weakens the disclaimer or crisis resources

---

## License

By contributing, you agree your contributions are licensed under the
project's MIT License. See [LICENSE](LICENSE).

---

*Nova is a first step, not a final answer.*
*Build with that in mind.*
