---
name: design_phosphor_icon
description: >
  Find and provide a colored Phosphor icon for a named concept. Not general
  creative/design work.
---

Provide an icon from the official Phosphor Icons library.

Gather two things: the concept the icon should represent, and the color. Ask
what the icon should represent if the user has not said. Ask what color they
want unless they already included one. Accept a color name or hex value. If
they say "purple", "Rasa purple", or "brand purple", use Rasa Purple #5A17EE.
Never put hex values in backticks or code formatting.

Deliver the icon by calling `generate_phosphor_icon` with `icon_query` (the
concept) and `icon_color`. Provide a PNG by default so Slack renders a preview;
only pass a request for SVG when the user explicitly asks for SVG.

This is the ONLY way to deliver an icon. There is no Slack slash command, app,
custom emoji, or self-service page for Phosphor icons, so never tell the user to
run one.

Iterating is normal. When the user asks for a different icon or a different
color (for example "location pin instead", "try a navigation arrow", "make it
navy"), call `generate_phosphor_icon` AGAIN with the NEW `icon_query` and/or
`icon_color` from their latest message. Never re-send the previous icon. Never
claim you uploaded something different from what `icon_query` actually was: the
reply must name the same icon the tool returned in `icon`/`slug`.

When the tool returns:
- If `uploaded_to_slack` is true, confirm in one short line naming the icon and
  color.
- If `error` is `no_confident_match`, nothing was uploaded because Phosphor has
  no icon for that concept. Do not pretend an unrelated icon represents it.
  Name two or three concrete Phosphor icons that could stand in for the idea and
  ask which they want, or ask for a more literal object.
- If it failed, say plainly what failed. When `missing_files_write_scope` is
  true, say the Slack app is missing the `files:write` scope and an admin needs
  to add it and reinstall. Share `phosphor_page` so they are unblocked.
- Offer the returned `alternatives` when the user might want a different match.
