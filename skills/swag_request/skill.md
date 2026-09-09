---
name: swag_request
description: >
  Rasa swag / merch requests - ordering stickers, t-shirts, hoodies, hats,
  customer or community giveaways, event swag, personal employee merch, or
  the merch store link. Activate for "I need swag", "order merch", "stickers
  for a workshop", "swag for customers", "Rasa shop", or similar. Do NOT
  activate for brand colors (design_brand_colors), Phosphor icons
  (design_phosphor_icon), or creative/design requests (design_request).
---

Help with Rasa swag and merch. Keep replies short and Slack-friendly. Do not
invent stock, prices, shipping times, or who will fulfill an order.

**Store and docs (share when useful).**
- Merch store: <https://shop.rasa.com/|shop.rasa.com>
- Internal Notion page: <https://app.notion.com/p/rasa/Rasa-Swag-Merch-Store-2fdb9c0d544a81dfa9bdd69ded626364|Rasa Swag / Merch Store>

If they only want the website or catalog, send shop.rasa.com (and the Notion
link if helpful) and stop.

**First question.** If they have not said the purpose yet, ask once which
bucket this is for:
1. Customer / community
2. Events
3. Personal / employee swag (buy it yourself)

Set `swag_purpose` to `customer_community`, `events`, or `personal` once
they answer (or when it is already clear from the ask).

if: session.swag_request.swag_purpose == 'events'
Tell them to ask the events manager in #events for event swag support.
Keep it short. Offer shop.rasa.com if they only need to browse or buy
themselves. Do not open a Wrangle ticket for them.

if: session.swag_request.swag_purpose == 'personal'
Tell them to go to the merch store themselves:
<https://shop.rasa.com/|shop.rasa.com>
Optionally share the Notion page. No Wrangle ticket needed for personal
buys.

if: session.swag_request.swag_purpose == 'customer_community'
Walk them through opening a Wrangle ticket. Say clearly they should type
`/wrangle` in any Slack channel to start. Then give these steps:

1. In any channel, type `/wrangle` and open a ticket.
2. Choose the **Rasa Swag** inbox.
3. Write a short summary that says it is for a customer or a
   workshop/event/community giveaway.
4. Add details if known: what swag and quantity (e.g. 50 stickers "Hello
   Rasa").
5. Choose a tag.
6. Someone from the Swag team will respond.

Do not create the ticket or ping the Swag team yourself. If they are missing
item/quantity details, ask one short clarifying question before or after
pointing them at `/wrangle`.
