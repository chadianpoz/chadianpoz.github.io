#!/usr/bin/env python3
"""Build the static site into _site/.

Content lives in:
  site.yml                 site settings, links, and RSS feeds to import
  data/publications.yml    publication list
  data/projects.yml        project cards
  content/posts/*.md       writing (native posts and cross-posts)
  content/thesis/*.md      thesis chapters
  content/cv.md            CV page

Run:  python build.py            (build only)
      python build.py --fetch    (also import new posts from RSS feeds in site.yml)
"""
import datetime as dt
import email.utils
import html
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
MD_EXT = ["extra", "smarty", "toc", "sane_lists"]


def load_yaml(p):
    return yaml.safe_load((ROOT / p).read_text(encoding="utf-8"))


def read_md(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        meta = yaml.safe_load(fm) or {}
    return meta, body.strip()


def render_md(body):
    return markdown.markdown(body, extensions=MD_EXT, output_format="html5")


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9\s-]", "", s).strip().lower()
    return re.sub(r"[\s-]+", "-", s)[:80]


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v)[:10])


# ---------- RSS import (Substack, or any RSS/Atom feed) ----------

def fetch_feeds(site):
    posts_dir = ROOT / "content" / "posts"
    existing = set()
    for p in posts_dir.glob("*.md"):
        m, _ = read_md(p)
        if m.get("original_url"):
            existing.add(m["original_url"].rstrip("/"))
    for feed in site.get("feeds", []) or []:
        url, source = feed["url"], feed["source"]
        print(f"fetching {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36", "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"})
            data = urllib.request.urlopen(req, timeout=30).read()
        except Exception as e:  # keep building even if a feed is down
            print(f"  could not fetch: {e}")
            continue
        root = ET.fromstring(data)
        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
        for item in root.iter("item"):
            link = (item.findtext("link") or "").strip()
            if not link or link.rstrip("/") in existing:
                continue
            title = (item.findtext("title") or "Untitled").strip()
            pub = item.findtext("pubDate")
            date = email.utils.parsedate_to_datetime(pub).date() if pub else dt.date.today()
            summary = re.sub("<[^>]+>", "", item.findtext("description") or "").strip()
            body = item.findtext("content:encoded", namespaces=ns) or item.findtext("description") or ""
            fm = {
                "title": title,
                "date": date.isoformat(),
                "source": source,
                "original_url": link,
                "summary": summary[:300],
            }
            name = f"{date.isoformat()}-{slugify(title)}.md"
            (posts_dir / name).write_text(
                "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True) + "---\n\n" + body + "\n",
                encoding="utf-8",
            )
            existing.add(link.rstrip("/"))
            print(f"  imported {name}")


# ---------- build ----------

def build():
    site = load_yaml("site.yml")
    pubs = load_yaml("data/publications.yml")
    projects = load_yaml("data/projects.yml")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["datefmt"] = lambda d: to_date(d).strftime("%B %-d, %Y")
    env.filters["md"] = lambda s: render_md(s or "")
    me = site.get("author_highlight", [])

    def bold_me(authors):
        out = html.escape(authors)
        for name in me:
            out = out.replace(html.escape(name), f"<strong>{html.escape(name)}</strong>")
        return out

    env.filters["bold_me"] = bold_me

    # posts
    posts = []
    for p in sorted((ROOT / "content" / "posts").glob("*.md")):
        meta, body = read_md(p)
        meta["date"] = to_date(meta["date"])
        meta.setdefault("slug", p.stem[11:] if re.match(r"\d{4}-\d{2}-\d{2}-", p.stem) else p.stem)
        meta["html"] = render_md(body) if meta.get("format") != "html" else body
        meta["url"] = meta["original_url"] if meta.get("external") else f"/writing/{meta['slug']}/"
        meta["source_label"] = site["sources"].get(meta.get("source", "site"), {}).get("label", "")
        posts.append(meta)
    posts.sort(key=lambda m: m["date"], reverse=True)

    # thesis chapters
    chapters = []
    for p in sorted((ROOT / "content" / "thesis").glob("*.md")):
        meta, body = read_md(p)
        meta["slug"] = re.sub(r"^\d+-", "", p.stem)
        meta["html"] = render_md(body)
        meta["url"] = f"/thesis/{meta['slug']}/"
        chapters.append(meta)
    thesis_index = next((c for c in chapters if c["slug"] == "index"), None)
    chapters = [c for c in chapters if c["slug"] != "index"]

    cv_meta, cv_body = read_md(ROOT / "content" / "cv.md")

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    (OUT / ".nojekyll").write_text("")

    def write(path, template, **ctx):
        dest = OUT / path.lstrip("/") / "index.html" if not path.endswith(".html") else OUT / path.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        html_out = env.get_template(template).render(site=site, path=path, **ctx)
        dest.write_text(html_out, encoding="utf-8")

    selected = [p for p in pubs["journal"] if p.get("selected")]
    write("/", "home.html", posts=posts[:5], selected=selected, projects=[p for p in projects if p.get("featured")])
    write("/publications/", "publications.html", pubs=pubs)
    write("/projects/", "projects.html", projects=projects)
    write("/photography/", "photography.html", photos=load_yaml("data/photos.yml"))
    write("/writing/", "writing.html", posts=posts)
    local = [p for p in posts if not p.get("external")]
    for i, post in enumerate(local):
        write(post["url"], "post.html", post=post,
              newer=local[i - 1] if i > 0 else None,
              older=local[i + 1] if i + 1 < len(local) else None)
    write("/thesis/", "thesis.html", intro=thesis_index, chapters=chapters)
    for i, ch in enumerate(chapters):
        write(ch["url"], "chapter.html", ch=ch, chapters=chapters,
              prev=chapters[i - 1] if i > 0 else None,
              next=chapters[i + 1] if i + 1 < len(chapters) else None)
    write("/cv/", "page.html", page={"title": cv_meta.get("title", "CV"), "html": render_md(cv_body), "pdf": cv_meta.get("pdf")})
    write("/404.html", "page.html", page={"title": "Page not found", "html": "<p>That page does not exist. <a href='/'>Go to the home page</a>.</p>"})

    # RSS feed of everything on the site
    items = []
    for p in posts[:30]:
        link = p["url"] if p["url"].startswith("http") else site["url"].rstrip("/") + p["url"]
        items.append(
            f"<item><title>{html.escape(p['title'])}</title><link>{link}</link><guid>{link}</guid>"
            f"<pubDate>{email.utils.format_datetime(dt.datetime.combine(p['date'], dt.time(12), dt.timezone.utc))}</pubDate>"
            f"<description>{html.escape(p.get('summary', ''))}</description></item>"
        )
    (OUT / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{html.escape(site['name'])}</title><link>{site['url']}</link>"
        f"<description>{html.escape(site['description'])}</description>{''.join(items)}</channel></rss>",
        encoding="utf-8",
    )
    print(f"built {len(posts)} posts, {len(chapters)} thesis chapters into {OUT}")


if __name__ == "__main__":
    site_cfg = load_yaml("site.yml")
    if "--fetch" in sys.argv:
        fetch_feeds(site_cfg)
    build()
