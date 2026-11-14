# chadianpoz.github.io

Personal site: about, publications, projects, writing, PhD thesis, and CV.

## How it works

`build.py` turns the files below into a static site in `_site/`. A GitHub Action builds and deploys it on every push to `main`, and once a day to pick up new Substack posts.

| What | Where |
|---|---|
| Site name, nav, social links, RSS feeds to import | `site.yml` |
| Publications | `data/publications.yml` |
| Projects | `data/projects.yml` |
| Posts and cross-posts | `content/posts/YYYY-MM-DD-slug.md` |
| Thesis overview and chapters | `content/thesis/00-index.md`, `01-chapter-name.md`, ... |
| CV | `content/cv.md` |
| Styles, images, PDFs | `static/` |

## Add a post

Make a file in `content/posts/` named `YYYY-MM-DD-slug.md`:

```
---
title: "Post title"
date: 2026-11-14
source: x            # site, deleon, substack, or x
original_url: "https://x.com/..."   # leave out for posts that only live here
summary: "One sentence for lists and link previews."
---

Post text in Markdown.
```

Substack posts import themselves: put your feed (`https://NAME.substack.com/feed`) under `feeds:` in `site.yml`.

## Preview locally

```
pip install jinja2 markdown pyyaml
python build.py
python -m http.server -d _site 8000
```

## One-time GitHub setting

Repository Settings > Pages > Build and deployment > Source: **GitHub Actions**.
