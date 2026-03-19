#!/bin/bash
# ─────────────────────────────────────────────────────────
#  Nova Setup Script
#  Installs deps, sets API key, optionally sets daily cron
# ─────────────────────────────────────────────────────────

set -e
GREEN='\033[0;32m'; AMBER='\033[0;33m'; RESET='\033[0m'; BOLD='\033[1m'

echo ""
echo -e "${GREEN}${BOLD}  n·o·v·a — Setup${RESET}"
echo "  ────────────────────────────"
echo ""

# 1. Python check
if ! command -v python3 &>/dev/null; then
  echo -e "${AMBER}Python 3 not found. Install it from https://python.org${RESET}"; exit 1
fi
echo -e "${GREEN}✓${RESET} Python $(python3 --version | cut -d' ' -f2) found"

# 2. Install deps
echo "  Installing dependencies..."
pip install anthropic rich streamlit plotly pandas -q
echo -e "${GREEN}✓${RESET} Dependencies installed"

# 3. Create nova dir
mkdir -p ~/nova
echo -e "${GREEN}✓${RESET} ~/nova directory ready"

# 4. Copy files (assumes setup.sh is in same folder as nova.py / nova_web.py)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/nova.py" ~/nova/nova.py 2>/dev/null || true
cp "$SCRIPT_DIR/nova_web.py" ~/nova/nova_web.py 2>/dev/null || true
echo -e "${GREEN}✓${RESET} Files copied to ~/nova/"

# 5. Streamlit config (dark theme)
mkdir -p ~/nova/.streamlit
cat > ~/nova/.streamlit/config.toml << 'TOML'
[theme]
base = "dark"
backgroundColor = "#0d0c13"
secondaryBackgroundColor = "#161521"
textColor = "#ddd8cf"
primaryColor = "#6eb8a0"
font = "sans serif"
TOML
echo -e "${GREEN}✓${RESET} Streamlit dark theme configured"

# 6. API Key
echo ""
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo -e "  ${AMBER}Anthropic API key not set in environment.${RESET}"
  echo "  Get one at: https://console.anthropic.com/settings/keys"
  echo -n "  Paste your key (or press Enter to skip): "
  read -r api_key
  if [ -n "$api_key" ]; then
    # Add to shell profile
    PROFILE="$HOME/.zshrc"
    [ -f "$HOME/.bashrc" ] && PROFILE="$HOME/.bashrc"
    echo "" >> "$PROFILE"
    echo "export ANTHROPIC_API_KEY=$api_key" >> "$PROFILE"
    export ANTHROPIC_API_KEY="$api_key"
    echo -e "${GREEN}✓${RESET} API key saved to $PROFILE"
  fi
else
  echo -e "${GREEN}✓${RESET} ANTHROPIC_API_KEY already set"
fi

# 7. Daily reminder cron (optional)
echo ""
echo -e "  ${BOLD}Daily reminder?${RESET}"
echo "  Nova can send a terminal reminder each morning to check in."
echo -n "  Set up daily reminder at 9am? [y/N]: "
read -r setup_cron
if [[ "$setup_cron" =~ ^[Yy]$ ]]; then
  PYTHON_PATH=$(which python3)
  NOVA_PATH="$HOME/nova/nova.py"
  # Write a gentle reminder script
  cat > ~/nova/remind.py << 'PYEOF'
#!/usr/bin/env python3
"""Nova daily reminder — run via cron"""
import subprocess, sys
from datetime import datetime
hour = datetime.now().hour
greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
msg = (
    f"\n  🌿  {greet}. Nova is here when you're ready.\n"
    "  Type: python3 ~/nova/nova.py  to check in.\n"
    "  ────────────────────────────────────────────\n"
    "  Crisis support: 988 (US) · 3114 (France)\n"
    "  https://findahelpline.com\n"
)
print(msg)
PYEOF
  chmod +x ~/nova/remind.py
  # Add cron job (9am daily)
  CRON_JOB="0 9 * * * $PYTHON_PATH $HOME/nova/remind.py >> $HOME/nova/remind.log 2>&1"
  (crontab -l 2>/dev/null | grep -v "nova/remind"; echo "$CRON_JOB") | crontab -
  echo -e "${GREEN}✓${RESET} Daily reminder set for 9:00am"
fi

# 8. Done
echo ""
echo -e "${GREEN}${BOLD}  ✓ Nova is ready!${RESET}"
echo ""
echo "  Terminal app:    python3 ~/nova/nova.py"
echo "  Web app:         cd ~/nova && streamlit run nova_web.py"
echo ""
echo "  ⚠  Not medical or professional advice."
echo "  Crisis support: 988 (US) · 3114 (France)"
echo "  https://findahelpline.com"
echo ""
