# Miga recipe packs

Recipe books that the Miga app installs from **Settings › Recipe packs**. See `README.md` for the
`pack.yaml` format.

## Conventions

- Commits, pull requests, code comments and technical docs are written in **English**. Recipes are
  written in the language of their pack.
- Every pack exists in Spanish and English: two folders, each with its own `id` and `language`
  (`cocina-mexicana` / `mexican-cooking`). Change both when changing one.
- Spanish packs use the app's Spanish category and equipment names (Entrantes, Postres, Horno…);
  English packs use the English ones (Starters, Desserts, Oven…).
- Units are singular (`cucharada`, `tbsp`, `diente`, `clove`): the app makes them plural. Names of
  things counted without a unit are written in plural when there is more than one
  (`[huevos, 4, null]`). Quote names that contain commas.
- After changing a published pack, raise its `version` so installed copies get the update. Do not
  rename recipes casually: the recipe uid comes from its name.
- Every pack has a `series` (required by `tools/build.py`), used by the app to group packs:
  "Cocina del mundo" / "World cuisine", "Cocina de cada día" / "Everyday cooking",
  "Electrodomésticos" / "Kitchen appliances", "Especiales" / "Specials". Reuse an existing series
  before creating a new one; both languages of a pack belong to the matching series.
- Covers carry no recipe count. Redraw them with `node tools/render_covers.mjs`.
- Recipe photos: real photos of the dish, **public domain or CC0 only** (no CC BY / BY-SA), in
  `photos/<topic>/<dish>.jpg`, 4:3 at 1280x960, JPEG without EXIF, each with its source, author and
  licence in `photos/credits.yaml` (the build refuses anything else). Look at a photo before using
  it: the file name is not enough. Both languages of a pack point to the same file.
- Country packs form the "Cocina del mundo: <país>" / "World cuisine: <country>" series, with
  `kicker` on the cover. Recipes must be real, traditional dishes (no inventions) and must not
  repeat a dish already in another pack of the same language.
- Quote YAML values that contain ": " (names like "Cocina del mundo: México", sources, notes).
- Pack descriptions do not state how many recipes the pack has.
- Always run `python3 tools/build.py` and commit `dist/` and `catalog.json`; CI fails if they are
  out of date.
- When packs or versions change, update `packs/catalog.json` in `calamares00/miga-web` (absolute
  raw.githubusercontent.com URLs).
