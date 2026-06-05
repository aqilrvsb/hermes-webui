#!/bin/sh
# Auto-seed OmniRoute with every provider key already present in the environment, so it
# becomes the single loaded gateway (with fallback) WITHOUT a manual dashboard step and
# WITHOUT an outage when Hermes' default is pointed at it. Idempotent: skips providers
# already connected. Runs in the background at boot (waits for OmniRoute to come up).
OMNI="http://127.0.0.1:20128"

# wait for OmniRoute (Next.js app, ~30-60s cold start)
i=0
while [ $i -lt 90 ]; do
  curl -fsS "$OMNI/v1/models" >/dev/null 2>&1 && break
  i=$((i+1)); sleep 2
done
existing=$(curl -fsS "$OMNI/api/providers" 2>/dev/null || echo "")

seed() { # $1 = omniroute provider id, $2 = api key value, $3 = friendly name
  [ -n "$2" ] || return 0
  if printf '%s' "$existing" | grep -q "\"provider\":\"$1\""; then
    echo "omni-seed: $1 already connected"; return 0
  fi
  if curl -fsS -X POST "$OMNI/api/providers" -H 'Content-Type: application/json' \
       -d "{\"provider\":\"$1\",\"name\":\"$3\",\"apiKey\":\"$2\"}" >/dev/null 2>&1; then
    echo "omni-seed: connected $1"
  else
    echo "omni-seed: FAILED $1"
  fi
}

# Map Hermes' standard provider env vars -> OmniRoute provider ids
seed openrouter "$OPENROUTER_API_KEY" "OpenRouter"
seed anthropic  "$ANTHROPIC_API_KEY"  "Anthropic"
seed openai     "$OPENAI_API_KEY"     "OpenAI"
seed gemini     "${GEMINI_API_KEY:-$GOOGLE_API_KEY}" "Gemini"
seed deepseek   "$DEEPSEEK_API_KEY"   "DeepSeek"
seed minimax    "$MINIMAX_API_KEY"    "MiniMax"
seed xai        "$XAI_API_KEY"        "xAI"
seed mistral    "$MISTRAL_API_KEY"    "Mistral"
seed glm        "$GLM_API_KEY"        "GLM / Z.AI"
seed kimi       "$KIMI_API_KEY"       "Kimi"
seed groq       "$GROQ_API_KEY"       "Groq"
seed together   "$TOGETHER_API_KEY"   "Together AI"
seed cerebras   "$CEREBRAS_API_KEY"   "Cerebras"
seed fireworks  "$FIREWORKS_API_KEY"  "Fireworks AI"
seed perplexity "$PERPLEXITY_API_KEY" "Perplexity"
echo "omni-seed: done ($(printf '%s' "$existing" | grep -o '"provider"' | wc -l) pre-existing)"
