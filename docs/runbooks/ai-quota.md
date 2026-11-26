# Runbook: assistant near its daily limit

**Signal:** "Assistant near its daily cap" (80% of `AI_DAILY_CAP`, 800 by
default) or "Assistant near the provider's daily tokens" (80% of Groq's free
200,000 tokens a day).

**What users see:** nothing yet. At the cap, `/v1/ask` answers 429 "as many
questions as it can today"; when Groq runs out it answers 429 to us and the
question box says the assistant cannot reach its model. Every other part of
the site works without the assistant.

## Check, in order

1. **Is it real traffic or one visitor?** Dashboard, "Assistant questions per
   hour": a flat line of `limited` means the per-visitor limit (10 an hour) is
   doing its job. A steep climb of `answered` and `refused` is real use.
2. **Is the live evaluation running?** Actions, `ai-eval`: each run makes about
   20 model calls on the same Groq quota. Do not start it by hand on a busy day.
3. **Too much?** Set `AI_ENABLED=false` on Render (the kill switch). The
   question box hides itself; nothing else changes. Set it back the next day.
4. **Every day?** Lower `AI_DAILY_CAP`, or add a fallback provider
   (`AI_FALLBACK_BASE_URL`, `AI_FALLBACK_MODEL`, `AI_FALLBACK_API_KEY`, for
   example Cloudflare Workers AI's free allocation). Never a paid tier (rule 1).

Today's count lives in the service's memory: a restart on Render's free plan
resets it, so Groq's own limit is the backstop. Both counts reset at 00:00 UTC.
