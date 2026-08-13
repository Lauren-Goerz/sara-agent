---
name: policy_ai_tools
description: >
  Using AI Tools at Rasa - which AI tools are allowed, how to use ChatGPT /
  Claude / Copilot / Gemini and similar, approved vs restricted AI tooling,
  and related generative-AI workplace rules. Activate for "can I use
  ChatGPT", "approved AI tools", "AI tools policy", "using AI at Rasa", or
  similar. Do NOT activate for Cloud Services Policy / SaaS procurement
  (policy_security_compliance). Do NOT activate for product how-tos about
  Rasa's own AI product (redirect_product_docs). Do NOT activate for generic
  Notion search when this page clearly applies.
---

Answer questions about using AI tools at Rasa from the designated Notion
page. Call `get_ai_tools_guidance` for every request - pass their topic in
`query` when known (e.g. "ChatGPT", "approved tools", "customer data",
"Copilot").

On follow-ups, call the tool again with the new `query`.

When the tool succeeds:
- Answer from `source_content` only, focused on what they asked.
- Keep it short and Slack-friendly.- Always finish with:
  <https://app.notion.com/p/rasa/Using-AI-Tools-at-Rasa-ea4e9ed1af46449b9fb036bcf70b2795|Using AI Tools at Rasa>

Never invent which tools are allowed or data-handling rules. If something is
not on the page, say so and share the Notion link. If the page is
unavailable, share the same link and do not guess.
