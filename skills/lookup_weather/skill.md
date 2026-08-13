---
name: lookup_weather
description: >
  Weather forecast for a city or place - "what's the weather in Munich",
  "forecast for Berlin this week", "is it going to rain in London
  tomorrow", temperature, or similar. Activate for those. Do NOT activate
  for travel booking policy (policy_business_travel) or work-abroad policy
  (policy_work_abroad) unless they clearly want the weather.
---

Answer weather questions with `get_weather_forecast`.

Pass:
- `place`: the city or place they named (Munich, Berlin, London…)
- `days`: how many days ahead they want (default 7 for "this week"; use 1-3
  for today/tomorrow)

When the tool succeeds, give a short Slack-friendly summary: highs/lows,
conditions, and rain chance when useful. Mention the place and that the
source is Open-Meteo. If the place is ambiguous or missing, ask one
clarifying question. Never invent temperatures or conditions.
