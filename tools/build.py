#!/usr/bin/env python3
"""Builds the Miga recipe packs: one ZIP per pack in dist/ and catalog.json at the root.

Each pack lives in packs/<id>/: pack.yaml (metadata and recipes, see README.md), cover.jpg (square,
shown in the catalogue) and book-cover.jpg (portrait, the book cover inside the app). Recipe photos
live in photos/<topic>/ (shared by the Spanish and English packs) and are named by a recipe's
"photo"; each one must be listed in photos/<topic>/credits.yaml with its source, author and licence:
public domain, CC0, CC BY or CC BY-SA. For the CC ones the attribution is added to the recipe notes. The ZIP uses the app's export
format: manifest.json (a library export with one book) plus the book cover and the recipe photos.

Builds are reproducible: the same pack.yaml and images always give the same ZIP, so a pack only
changes when its content does. Raise "version" in pack.yaml after changing a pack, so the apps
that installed it are offered the update.

Usage: python3 tools/build.py   (needs PyYAML: pip install pyyaml)
"""
import hashlib
import json
import re
import sys
import unicodedata
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "packs"
DIST = ROOT / "dist"
PHOTOS = ROOT / "photos"
# Photo licences: free of conditions, or needing only attribution (and share-alike, which a cropped
# copy keeps). Non-commercial, no-derivatives and GFDL-only photos are not accepted.
NO_ATTRIBUTION_LICENSES = {"CC0 1.0", "Public domain"}
ATTRIBUTION_LICENSE = re.compile(r"^CC BY(-SA)? (2\.0|2\.5|3\.0|4\.0)$")
# The author links to the photo's page, as a Markdown link the app shows as tappable text.
PHOTO_CREDIT = {"es": "📷 Foto: [{author}]({source}) · {license}",
                "en": "📷 Photo: [{author}]({source}) · {license}"}
SCHEMA_VERSION = 5
DIFFICULTIES = {"EASY", "MEDIUM", "HARD"}
LANGUAGES = {"es", "en"}
# Fixed timestamp for every ZIP entry, so that builds are reproducible.
ZIP_DATE = (2026, 1, 1, 0, 0, 0)
# Stable namespace for uids: the same pack and recipe name always give the same uid, so an update
# replaces the recipe in the app instead of adding a copy.
NAMESPACE = uuid.UUID("8d0f6c1e-5b8e-4a59-9a3c-6f4e8b1d2c70")


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def fail(message: str):
    sys.exit(f"error: {message}")


def ingredient(item, where):
    if not isinstance(item, list) or len(item) < 3:
        fail(f"{where}: an ingredient is [name, quantity, unit] or [name, quantity, unit, optional]")
    name, quantity, unit = item[0], item[1], item[2]
    # A name with a comma must be quoted in YAML, or it splits into several fields.
    if len(item) > 4 or (len(item) == 4 and item[3] != "optional") or not (quantity is None or isinstance(quantity, (int, float))):
        fail(f"{where}: {item} is not [name, quantity, unit(, optional)]; quote names that contain commas")
    optional = len(item) == 4
    return {
        "name": str(name),
        "quantity": float(quantity) if quantity is not None else None,
        "unit": unit,
        "optional": optional,
    }


def ingredient_groups(groups, where):
    return [
        {"name": group.get("group"), "ingredients": [ingredient(item, where) for item in group["items"]]}
        for group in groups
    ]


def step_groups(steps, where):
    if all(isinstance(step, str) for step in steps):
        return [{"name": None, "instructions": steps}]
    groups = []
    for group in steps:
        if not isinstance(group, dict) or "items" not in group:
            fail(f"{where}: steps are a list of texts or of groups with 'group' and 'items'")
        groups.append({"name": group.get("group"), "instructions": group["items"]})
    return groups


def load_credits():
    """Every photos/<topic>/credits.yaml, keyed by "<topic>/<file>" as recipes name their photos."""
    credits = {}
    for path in sorted(PHOTOS.glob("*/credits.yaml")):
        for name, credit in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).items():
            credits[f"{path.parent.name}/{name}"] = credit
    return credits


def recipe_photo(raw, where, credits):
    """The recipe's photo file and its credit, checked against the credits files; None without one."""
    name = raw.get("photo")
    if name is None:
        return None
    path = (PHOTOS / name).resolve()
    if not path.is_relative_to(PHOTOS.resolve()) or not path.is_file() or path.suffix.lower() != ".jpg":
        fail(f"{where}: photo {name} is not a .jpg in photos/")
    credit = credits.get(name)
    if not credit or not credit.get("source") or not credit.get("author"):
        fail(f"{where}: photo {name} needs an entry with source and author in photos/<topic>/credits.yaml")
    license_name = credit.get("license")
    if license_name not in NO_ATTRIBUTION_LICENSES and not ATTRIBUTION_LICENSE.match(str(license_name)):
        fail(f"{where}: photo {name} has licence {license_name}; only CC0 1.0, Public domain, CC BY or CC BY-SA")
    return path, credit


def notes_with_credit(notes, credit, language):
    """The recipe notes, plus the attribution a CC BY / BY-SA photo requires."""
    if credit is None or credit["license"] in NO_ATTRIBUTION_LICENSES:
        return notes
    # Brackets in the author and parentheses in the address would break the Markdown link.
    author = credit["author"].replace("[", "(").replace("]", ")")
    source = credit["source"].replace("(", "%28").replace(")", "%29").replace(" ", "%20")
    line = PHOTO_CREDIT[language].format(author=author, license=credit["license"], source=source)
    return f"{notes}\n\n{line}" if notes else line


HEALTH_LEVELS = {"GREEN", "YELLOW", "RED"}


def fingerprint(ingredients, steps):
    """The app's HealthFingerprint: SHA-256 of the ingredients and steps, written the same way."""
    text = ""
    for group in ingredients:
        text += (group["name"] or "") + "|"
        for item in group["ingredients"]:
            quantity = "null" if item["quantity"] is None else repr(float(item["quantity"]))
            text += f"{item['name']},{quantity},{item['unit'] or ''};"
    text += "##"
    for group in steps:
        text += (group["name"] or "") + "|"
        for instruction in group["instructions"]:
            text += instruction + ";"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def health_and_nutrition(raw, where, ingredients, steps, analyzed_at):
    """The fixed health rating and nutrition per serving of a recipe. Every pack recipe has them,
    so the app never sends pack recipes to the cooking assistant."""
    health, nutrition = raw.get("health"), raw.get("nutrition")
    if not (isinstance(health, list) and len(health) == 2 and health[0] in HEALTH_LEVELS
            and isinstance(health[1], str) and health[1].strip()):
        fail(f"{where}: health must be [GREEN|YELLOW|RED, \"description\"]")
    if not (isinstance(nutrition, list) and len(nutrition) == 4
            and all(isinstance(v, (int, float)) and v >= 0 for v in nutrition) and isinstance(nutrition[0], int)):
        fail(f"{where}: nutrition must be [kcal, protein g, carbs g, fat g] per serving")
    digest = fingerprint(ingredients, steps)
    return (
        {"colorLevel": health[0], "description": " ".join(health[1].split()), "fingerprint": digest, "analyzedAt": analyzed_at},
        {"caloriesPerServing": nutrition[0], "proteinGrams": float(nutrition[1]), "carbsGrams": float(nutrition[2]),
         "fatGrams": float(nutrition[3]), "fingerprint": digest, "analyzedAt": analyzed_at},
    )


def recipe(pack, raw, book_name, photo, analyzed_at):
    where = f"{pack['id']} / {raw.get('name')}"
    defaults = pack.get("defaults", {})
    difficulty = raw.get("difficulty", "MEDIUM")
    if difficulty not in DIFFICULTIES:
        fail(f"{where}: difficulty must be one of {sorted(DIFFICULTIES)}")
    ingredients = ingredient_groups(raw["ingredients"], where)
    steps = step_groups(raw["steps"], where)
    health, nutrition = health_and_nutrition(raw, where, ingredients, steps, analyzed_at)
    return {
        "version": SCHEMA_VERSION,
        "uid": str(uuid.uuid5(NAMESPACE, f"{pack['id']}/{slug(raw['name'])}")),
        "name": raw["name"],
        "recipeBookName": book_name,
        "categoryName": raw.get("category"),
        "difficulty": difficulty,
        "prepTimeMinutes": raw.get("prep"),
        "cookTimeMinutes": raw.get("cook"),
        "servings": raw.get("servings", 4),
        "notes": notes_with_credit(raw.get("notes", ""), photo[1] if photo else None, pack["language"]),
        "source": raw.get("source", defaults.get("source", "")),
        "isFavorite": False,
        "ingredientGroups": ingredients,
        "stepGroups": steps,
        "tags": raw.get("tags", []),
        "utensils": raw.get("utensils", []),
        "photos": [{"fileName": "0.jpg", "isCover": True}] if photo else [],
        "health": health,
        "nutrition": nutrition,
        "origin": raw.get("origin", defaults.get("origin")),
        "originCountry": raw.get("originCountry", defaults.get("originCountry")),
    }


def write_entry(zip_file, name, data):
    # Stored, not deflated: compressed bytes depend on the zlib version, which would make the CI
    # check (.github/workflows/check.yml) fail on another machine. JPEGs barely compress anyway.
    info = zipfile.ZipInfo(name, ZIP_DATE)
    info.compress_type = zipfile.ZIP_STORED
    zip_file.writestr(info, data)


def build_pack(pack_dir: Path):
    pack = yaml.safe_load((pack_dir / "pack.yaml").read_text(encoding="utf-8"))
    pack_id, version = pack["id"], int(pack["version"])
    if pack_id != pack_dir.name:
        fail(f"{pack_dir.name}: id in pack.yaml must match the folder name")
    # The app lists the packs in its own language (and those without one).
    language = pack.get("language")
    if language not in LANGUAGES:
        fail(f"{pack_id}: language must be one of {sorted(LANGUAGES)}")
    # Every pack belongs to a series (World cuisine, Specials...), which the app uses to group them.
    series = pack.get("series")
    if not isinstance(series, str) or not series.strip():
        fail(f"{pack_id}: series is required (e.g. \"Cocina del mundo\" or \"World cuisine\")")
    # The Spanish and English versions of a pack share a family: the install counter adds them up.
    family = pack.get("family")
    if not isinstance(family, str) or not family.strip():
        fail(f"{pack_id}: family is required (the Spanish pack id, the same in both languages)")
    book_uid = str(uuid.uuid5(NAMESPACE, f"{pack_id}/book"))
    book_cover = pack_dir / "book-cover.jpg"
    credits = load_credits()
    photos = [recipe_photo(raw, f"{pack_id} / {raw.get('name')}", credits) for raw in pack["recipes"]]
    updated = datetime(2026, 1, 1, tzinfo=timezone.utc) if "updated" not in pack else \
        datetime.combine(pack["updated"], datetime.min.time(), tzinfo=timezone.utc)
    analyzed_at = int(updated.timestamp() * 1000)
    recipes = [recipe(pack, raw, pack["name"], photo, analyzed_at) for raw, photo in zip(pack["recipes"], photos)]
    names = [r["name"] for r in recipes]
    if len(set(names)) != len(names):
        fail(f"{pack_id}: two recipes share a name")

    manifest = {
        "version": SCHEMA_VERSION,
        "exportedAt": int(updated.timestamp() * 1000),
        "books": [{
            "uid": book_uid,
            "name": pack["name"],
            "coverPhotoFileName": "cover.jpg" if book_cover.exists() else None,
        }],
        "recipes": recipes,
        "shoppingTemplates": [],
        "shoppingStores": [],
    }

    DIST.mkdir(exist_ok=True)
    zip_name = f"{pack_id}-v{version}.zip"
    with zipfile.ZipFile(DIST / zip_name, "w") as zip_file:
        write_entry(zip_file, "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        if book_cover.exists():
            write_entry(zip_file, f"books/{book_uid}/cover.jpg", book_cover.read_bytes())
        for r, photo in zip(recipes, photos):
            if photo:
                write_entry(zip_file, f"recipes/{r['uid']}/0.jpg", photo[0].read_bytes())

    entry = {
        "id": pack_id,
        "name": pack["name"],
        "series": series.strip(),
        "family": family.strip(),
        "author": pack.get("author", ""),
        "authorGithub": pack.get("authorGithub"),
        "description": " ".join(pack.get("description", "").split()),
        "coverImageUrl": f"packs/{pack_id}/cover.jpg" if (pack_dir / "cover.jpg").exists() else None,
        "latestVersion": version,
        "recipeCount": len(recipes),
        "downloadUrl": f"dist/{zip_name}",
        "language": language,
    }
    photo_count = sum(1 for p in photos if p)
    print(f"{pack_id} v{version}: {len(recipes)} recetas, {photo_count} fotos -> dist/{zip_name}")
    return entry


def main():
    entries = [build_pack(d) for d in sorted(PACKS.iterdir()) if (d / "pack.yaml").exists()]
    keep = {Path(e["downloadUrl"]).name for e in entries}
    for old in DIST.glob("*.zip"):
        if old.name not in keep:
            old.unlink()
    families = {}
    for e in entries:
        key = (e["family"], e["language"])
        if key in families:
            fail(f"{e['id']}: family {e['family']} already has a {e['language']} pack ({families[key]})")
        families[key] = e["id"]
    catalog = {"schemaVersion": 1, "packs": entries}
    (ROOT / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"catalog.json: {len(entries)} packs")


if __name__ == "__main__":
    main()
