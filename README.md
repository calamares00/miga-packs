# Packs de recetas para Miga

Libros de recetas listos para instalar en [Miga](https://miga.calamares.org) desde
**Ajustes › Packs de recetas**. Un pack se instala como un libro más; sus recetas no se editan,
pero puedes copiar las que quieras a tus libros, y cuando sale una versión nueva la app ofrece
actualizarlo.

Cada pack está en español y en inglés; la app muestra los del idioma en que la usas.

| Pack | Idioma | Recetas | Descarga |
| :--- | :---: | :---: | :--- |
| 🌮 [Cocina mexicana](packs/cocina-mexicana/pack.yaml) | es | 20 | [cocina-mexicana-v1.zip](dist/cocina-mexicana-v1.zip) |
| 🌮 [Mexican cooking](packs/mexican-cooking/pack.yaml) | en | 20 | [mexican-cooking-v1.zip](dist/mexican-cooking-v1.zip) |
| 🫒 [Cocina mediterránea](packs/cocina-mediterranea/pack.yaml) | es | 20 | [cocina-mediterranea-v1.zip](dist/cocina-mediterranea-v1.zip) |
| 🫒 [Mediterranean cooking](packs/mediterranean-cooking/pack.yaml) | en | 20 | [mediterranean-cooking-v1.zip](dist/mediterranean-cooking-v1.zip) |
| 🎄 [Especial Navidad](packs/especial-navidad/pack.yaml) | es | 22 | [especial-navidad-v1.zip](dist/especial-navidad-v1.zip) |
| 🎄 [Christmas special](packs/christmas-special/pack.yaml) | en | 22 | [christmas-special-v1.zip](dist/christmas-special-v1.zip) |

Las recetas se redactaron con ayuda de un asistente de IA. Si ves algún error,
abre un issue o un pull request.

## Usar este catálogo

El catálogo oficial de la app (`https://miga.calamares.org/packs/catalog.json`) ya incluye estos
packs. Para usar directamente este repositorio, pon `calamares00/miga-packs` en
**Ajustes › Packs de recetas › Catálogo alternativo**: la app lee `catalog.json` de la rama `main`.

## Estructura

```
catalog.json                  catálogo que lee la app (generado)
dist/<id>-v<versión>.zip      un ZIP por pack, en el formato de exportación de Miga (generado)
packs/<id>/pack.yaml          datos y recetas del pack
packs/<id>/cover.jpg          portada cuadrada, para el catálogo
packs/<id>/book-cover.jpg     portada vertical (0,72), la del libro en la app
tools/build.py                genera dist/ y catalog.json
tools/render_covers.mjs       dibuja las portadas a partir de pack.yaml
```

## Crear o cambiar un pack

1. Edita `packs/<id>/pack.yaml` (o crea una carpeta nueva con el mismo formato).
2. Si cambias un pack ya publicado, sube su `version` para que las apps ofrezcan la actualización.
3. Genera los ZIP y el catálogo y súbelos junto con el YAML:

   ```bash
   pip install pyyaml
   python3 tools/build.py
   ```

4. Opcional: redibuja las portadas (necesita Node y Playwright con Chromium):

   ```bash
   node tools/render_covers.mjs
   ```

El CI comprueba que todos los packs son válidos y que `dist/` y `catalog.json` están al día. El
build es reproducible: el mismo YAML da siempre el mismo ZIP.

### Formato de `pack.yaml`

```yaml
id: cocina-mexicana              # igual que el nombre de la carpeta; no cambia nunca
version: 1                       # súbelo en cada cambio publicado
updated: 2026-10-30
language: es                     # "es" o "en": la app muestra los packs de su idioma
name: Cocina mexicana            # nombre del libro en la app
description: Texto del catálogo.
author: Miga
authorGithub: calamares00
cover: {emoji: "🌮", title: Cocina mexicana, colors: ["#c2410c", "#f59e0b"]}
defaults:                        # valores para todas las recetas que no los indiquen
  origin: México
  originCountry: MX              # ISO 3166-1 alfa-2
  source: Pack «Cocina mexicana» de Miga
recipes:
  - name: Guacamole
    category: Salsas             # mejor una de las categorías de la app (Entrantes, Ensaladas,
                                 # Sopas y cremas, Arroces, Pastas, Legumbres, Verduras, Carnes,
                                 # Pescados y mariscos, Huevos, Panes y masas, Salsas, Postres, Bebidas)
    difficulty: EASY             # EASY, MEDIUM o HARD
    prep: 10                     # minutos
    cook: 0
    servings: 4
    tags: [vegetariana]
    utensils: [Batidora]         # equipamiento especial, con los nombres de la app
    notes: Texto libre.
    ingredients:
      - group: Opcional, nombre del grupo
        items:
          - [aguacates maduros, 3, null]         # [nombre, cantidad, unidad]
          - [cilantro picado, 2, cucharada]
          - [chile serrano, 1, null, optional]   # ingrediente opcional
          - [sal, null, null]                    # sin cantidad
    steps:                       # una lista de pasos, o grupos con "group" e "items"
      - Machaca los aguacates.
      - Mezcla con el resto.
```

- Las unidades van en singular (`cucharada`, `diente`, `taza`, `g`, `ml`…): la app las pone en
  plural según la cantidad. El nombre del ingrediente se muestra tal cual, así que va en plural si
  se cuenta más de uno sin unidad (`[huevos, 4, null]`).
- Un pack en dos idiomas son dos carpetas, cada una con su `id` y su `language`
  (`cocina-mexicana` y `mexican-cooking`). En inglés, las categorías y el equipamiento van con los
  nombres ingleses de la app (Starters, Soups, Meat, Desserts…; Oven, Blender…) y las unidades
  como `tbsp`, `tsp`, `clove`, `bunch`, `pinch`, `sprig`, `slice`, `g`, `ml`.
- Un nombre con comas va entre comillas: `["trofie, linguine o espaguetis", 400, g]`.
- Los identificadores de libro y recetas salen del `id` del pack y del nombre de cada receta:
  si cambias el nombre de una receta, la app la tratará como una receta nueva.

## Licencia

Las recetas y las portadas se publican bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es).
Los scripts de `tools/`, bajo [GPL-3.0](LICENSE).
