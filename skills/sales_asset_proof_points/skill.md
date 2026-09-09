---
name: sales_asset_proof_points
description: >
  Rasa product proof points: customer case-study metrics, analyst recognition,
  deployment speed, quotes, scale, CSAT, why customers choose Rasa, or the
  proof-points PDF. Not KPI guidance, competitor comparisons, or product
  how-tos.
---

Answer questions about Rasa's product proof points from the live Notion page
PDF. Call `get_product_proof_points` for every request - do not answer from
memory.

When the tool succeeds:
- Answer the user's question directly from `proof_points_text` in a short
  Slack-friendly reply (a few bullets or 2-4 sentences).
- Use exact figures, customer names, and analyst designations from the PDF.
- Never invent or combine stats from different studies.
- If the PDF says a figure is directional only or not a production outcome,
  follow that guidance.
- Always include the Notion link:
  <https://app.notion.com/p/rasa/Product-Proof-Points-33eb9c0d544a80839f59e01cfa4c2c0a|Product Proof Points>.
- If `uploaded_to_slack` is true, mention that the PDF is attached in this
  thread. If upload failed, still answer from the text and share the Notion
  link.

If they only ask for the PDF / deck, still call the tool (it uploads the file)
and keep the chat reply to one short line plus the Notion link.
