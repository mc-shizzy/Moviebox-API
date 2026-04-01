import httpx, json

BASE = "http://localhost:8000"

ENDPOINTS = [
    "/",
    "/home",
    "/home/trending",
    "/home/hot",
    "/home/cinema",
    "/home/banner",
    "/home/sections",
    "/tv-series",
    "/movies",
    "/animation",
    "/ranking",
]

def verify_stream_download():
    try:
        q = "oppenheimer"
        search = httpx.get(BASE + "/search", params={"q": q}, timeout=30)
        if search.status_code != 200:
            print(f"\n[FAIL] /search?q={q} => HTTP {search.status_code}")
            return

        movies = search.json().get("movies", [])
        if not movies:
            print(f"\n[FAIL] /search?q={q} => no movies found")
            return

        first = movies[0]
        slug = first.get("slug")
        name = first.get("name")
        if not slug:
            print(f"\n[FAIL] /search?q={q} => first movie missing slug")
            return

        detail = httpx.get(BASE + f"/detail/{slug}", timeout=30)
        if detail.status_code != 200:
            print(f"\n[FAIL] /detail/{slug} => HTTP {detail.status_code}")
            return
        subject_id = detail.json().get("metadata", {}).get("id")
        if not subject_id:
            print(f"\n[FAIL] /detail/{slug} => missing subject id")
            return

        stream = httpx.get(BASE + f"/api/stream/{subject_id}", params={"detail_path": slug}, timeout=30)
        if stream.status_code != 200:
            print(f"\n[FAIL] /api/stream/{subject_id}?detail_path={slug} => HTTP {stream.status_code}")
            return
        source_list = stream.json().get("sources", [])
        if not source_list:
            print(f"\n[FAIL] /api/stream/{subject_id}?detail_path={slug} => no sources")
            return

        source_url = source_list[0].get("url")
        if not source_url:
            print(f"\n[FAIL] /api/stream/{subject_id}?detail_path={slug} => missing source url")
            return

        probe = httpx.get(source_url, timeout=30, follow_redirects=True)
        print(f"\n[STREAM CHECK] title={name!r} slug={slug!r}")
        print(f"  stream endpoint status: {stream.status_code}")
        print(f"  direct stream/download status: {probe.status_code}")
        print(f"  content-type: {probe.headers.get('content-type')}")
        print(f"  bytes received: {len(probe.content)}")
    except Exception as e:
        print(f"\n[FAIL] stream check => {e}")

def check_movies(movies, label):
    total = len(movies)
    with_poster = sum(1 for m in movies if m.get("poster_url"))
    with_name = sum(1 for m in movies if m.get("name"))
    print(f"    movies: {total} | names: {with_name}/{total} | posters: {with_poster}/{total}")
    if movies:
        m = movies[0]
        print(f"    sample: name={m.get('name','?')[:40]!r} | poster={'YES' if m.get('poster_url') else 'NULL'}")

for path in ENDPOINTS:
    url = BASE + path
    try:
        r = httpx.get(url, timeout=30)
        data = r.json()
        status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
        print(f"\n[{status}] {path}")

        # Root
        if path == "/":
            print(f"  endpoints listed: {len(data.get('endpoints', []))}")
            continue

        # Banner
        if path == "/home/banner":
            featured = data.get("featured", [])
            print(f"  featured: {len(featured)}")
            if featured:
                f = featured[0]
                print(f"  sample: name={f.get('name','?')[:40]!r} | poster={'YES' if f.get('poster_url') else 'NULL'}")
            continue

        # Sections list
        if path == "/home/sections":
            secs = data.get("sections", [])
            print(f"  sections: {len(secs)}")
            for s in secs:
                print(f"    - {s['name']!r} ({s['count']} movies)")
            continue

        # Single section (trending/hot/cinema)
        if "movies" in data:
            print(f"  section: {data.get('section','?')!r}")
            check_movies(data["movies"], path)
            continue

        # Multi-section pages (/home, /tv-series, etc.)
        sections = data.get("sections", [])
        print(f"  total_sections: {len(sections)} | poster_map_size: {data.get('poster_map_size', '?')}")
        for s in sections:
            print(f"  [{s['section']!r}] {s['count']} movies")
            check_movies(s.get("movies", []), s["section"])

    except Exception as e:
        print(f"\n[FAIL] {path} => {e}")

print("\n\nDone.")
verify_stream_download()
