# Changelog

## Unreleased

- Renamed from "Collander" to "Colander", the actual spelling of the kitchen strainer. Existing installs keep working:
  - Settings are now `COLANDER_*`. The old `COLLANDER_*` names still work, in the environment and in `.env`; new names win when both are set, and the log lists any old names in use.
  - The image is now `ghcr.io/gudlyf/colander`. Releases are also published to `ghcr.io/gudlyf/collander`, so an unchanged `compose.yaml` keeps updating.
  - `compose.yaml` names its volume `colander-data`. To keep using your existing volume with the new file, set `COLANDER_DATA_VOLUME=collander-data` in `.env`. See [Upgrading from Collander](README.md#upgrading-from-collander).
  - `collander.db` is renamed to `colander.db` on first start. After that, don't go back to a 1.x image, which would start with an empty database.
  - Backups saying `collander-bundle` still import, and saved per-device choices (library view, keep screen on) carry over.
  - Everyone is signed out once, because the session cookie was renamed.
- Fixed: a recipe's source showed only when it had a link. A source name on its own, such as a cookbook, now shows too. Links without `https://` open correctly instead of breaking the page.

## 1.1.2 (2026-11-15)

- Fixed: AI check, import and photo transcription failed with "The model's response did not match the expected format" when the AI model didn't follow the expected JSON layout. This mostly affected Ollama cloud models, which ignore the requested format. The instructions now spell out the exact layout, a retry tells the model what it got wrong, and slightly different field names (such as "line" instead of "text") are accepted. Icon descriptions and icon checks get the same layout instructions, and an icon check reply in the wrong layout no longer counts as a pass.
- Fixed: when several imports finished at once and added the same new tag, all but one of them could fail.

## 1.1.1 (2026-11-14)

- The keep-screen-on button is labelled, remembered on each device, and turns itself back on when you return to the app. Over plain HTTP it explains that browsers need HTTPS for it.

## 1.1.0 (2026-11-14)

- Recipe icons: recipes without a photo can get a simple AI-made icon in the style of the app's logo, drawn as SVG by the configured AI model (any provider, including Ollama), painted by a local Stable Diffusion server with the AUTOMATIC1111 API (A1111, Forge, sd-server), or by an OpenAI or Google image model. For painted icons, the AI model describes how the dish looks, then a vision-capable model checks each icon for stray text and for whether it shows the dish, repainting if needed. Make one per recipe, all missing ones at once from Settings, or automatically for new recipes. New settings `COLLANDER_IMAGE_PROVIDER`, `COLLANDER_IMAGE_MODEL`, `COLLANDER_IMAGE_BASE_URL`, `COLLANDER_IMAGE_STEPS` and `COLLANDER_IMAGE_CFG_SCALE`.
- Steps have checkboxes like ingredients; tapping anywhere on a step ticks it.
- Modifying an ingredient or step starts from its current wording.
- Fixed: long links in notes pushed the notes past the edge of the screen on phones.
- Settings shows the version and commit of the running build.
- `COLLANDER_DATA_VOLUME` chooses the data volume or folder without editing `compose.yaml`.
- Frontend dependency updates for security alerts (React Router 7, Vite 6.4, Vitest 5).

## 1.0.0 (2026-11-13)

First release.

- Recipes with ingredients, steps, groups, notes, tags, ratings and favorites.
- Modifications that keep the original visible: change, leave out, or add ingredients and steps.
- Scaling (½×, 2×, 3×, custom) with kitchen-fraction formatting.
- Full-text search (SQLite FTS5) with phrases, exclusions, tag and status filters.
- Import from links (schema.org, then AI), photos (vision AI), pasted text, Evernote `.enex`, and JSON bundles.
- Background import queue for links, photos and text.
- Optional AI check: tidies formatting and flags problems without changing quantities or wording.
- AI providers: Anthropic, OpenAI and compatible servers, Google Gemini, Ollama.
- Single-password sign-in, JSON backup and restore, CLI tools.
- Multi-architecture Docker image (`linux/amd64`, `linux/arm64`) published to `ghcr.io/gudlyf/collander`, and a Compose file.
- Recipe library in card or list view.
