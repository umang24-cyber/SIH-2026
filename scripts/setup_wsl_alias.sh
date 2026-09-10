#!/usr/bin/env bash
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
grep -qxF 'alias bitkaun="/home/arora/sih-winners/SIH-2026/.venv/bin/bitkaun"' "$HOME/.bashrc" || echo 'alias bitkaun="/home/arora/sih-winners/SIH-2026/.venv/bin/bitkaun"' >> "$HOME/.bashrc"
grep -qxF 'alias sih="cd ~/sih-winners/SIH-2026 && source .venv/bin/activate"' "$HOME/.bashrc" || echo 'alias sih="cd ~/sih-winners/SIH-2026 && source .venv/bin/activate"' >> "$HOME/.bashrc"
echo "Bashrc configuration updated successfully!"
