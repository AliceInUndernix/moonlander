"""Pronunciation from the Cambridge Dictionary: IPA text and audio.

For a word the Builder is adding, this downloads the word's page on
dictionary.cambridge.org the way a web browser would (normal browser
headers, one page per word, cached), reads the UK and US IPA and the
addresses of the recordings, and downloads the recordings to play them.

Everything is cached in Plover's config folder (dotterel_pronunciation/),
so each word is fetched once.
"""

import gzip
import html
import json
import os
import re
import shutil
import socket
import subprocess
import threading
import urllib.parse
import urllib.request

SITE = "https://dictionary.cambridge.org"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}
TIMEOUT = 20


def page_url(word):
    """The word's page on the Cambridge Dictionary (also good to open)."""
    slug = urllib.parse.quote(word.strip().lower().replace(" ", "-"))
    return f"{SITE}/dictionary/english/{slug}"


def _cache_dir():
    try:
        from plover.oslayer.config import CONFIG_DIR
    except Exception:
        CONFIG_DIR = os.path.expanduser("~/.config/plover")
    path = os.path.join(CONFIG_DIR, "dotterel_pronunciation")
    os.makedirs(path, exist_ok=True)
    return path


_TAG = re.compile(r"<[^>]+>")


def _block(page, region):
    """The HTML of the first UK or US pronunciation block."""
    m = re.search(r'<span class="%s dpron-i[^"]*"' % region, page)
    if not m:
        return ""
    end = page.find("dpron-i", m.end())
    return page[m.start(): end if end > 0 else m.start() + 3000]


def parse(page):
    """{"uk": {"ipa", "mp3", "ogg"}, "us": {...}} from a Cambridge page."""
    out = {}
    for region in ("uk", "us"):
        block = _block(page, region)
        if not block:
            continue
        info = {}
        ipa = re.search(r'<span class="ipa[^"]*">(.*?)</span>\s*/', block, re.S)
        if ipa:
            info["ipa"] = html.unescape(_TAG.sub("", ipa.group(1))).strip()
        for kind, ext in (("mp3", "audio/mpeg"), ("ogg", "audio/ogg")):
            src = re.search(r'type="%s"\s+src="([^"]+)"' % re.escape(ext), block)
            if src:
                info[kind] = urllib.parse.urljoin(SITE, html.unescape(src.group(1)))
        if info:
            out[region] = info
    return out


def _text(fragment):
    t = html.unescape(_TAG.sub("", fragment))
    return re.sub(r"\s+", " ", t).strip().rstrip(":").strip()


def parse_definitions(page, max_pos=4, per_pos=3):
    """[[part of speech, [[definition, example], …]], …] from a Cambridge
    page: the learner's (UK) dictionary, the first one on the page."""
    # Only the first dictionary on the page (Cambridge Advanced Learner's);
    # the American and Business ones follow it.
    start = page.find('data-id="cald4"')
    if start >= 0:
        nxt = page.find('data-id="', start + 20)
        page = page[start: nxt if nxt > 0 else len(page)]
    out = []
    blocks = re.split(r'<div class="pr entry-body__el', page)
    for block in blocks[1:] if len(blocks) > 1 else blocks:
        pos = re.search(r'<span class="pos dpos"[^>]*>(.*?)</span>', block, re.S)
        pos = _text(pos.group(1)) if pos else ""
        senses = []
        defs = list(re.finditer(r'<div class="def ddef_d db">(.*?)</div>', block, re.S))
        for i, m in enumerate(defs):
            definition = _text(m.group(1))
            if not definition:
                continue
            end = defs[i + 1].start() if i + 1 < len(defs) else len(block)
            ex = re.search(r'<span class="eg deg">(.*?)</span>', block[m.end():end], re.S)
            senses.append([definition, _text(ex.group(1)) if ex else ""])
            if len(senses) >= per_pos:
                break
        if not senses:
            continue
        for item in out:
            if item[0] == pos:
                item[1].extend(senses[: per_pos - len(item[1])])
                break
        else:
            out.append([pos, senses])
        if len(out) >= max_pos:
            break
    return out


def system_env():
    """The environment for running the system's own programs (curl, mpv).

    The Plover AppImage points LD_LIBRARY_PATH (and PATH, Qt and Python
    paths) at its own bundled libraries, such as an older OpenSSL, which
    breaks the system's curl and players. Those entries are taken out.
    """
    env = dict(os.environ)
    appdir = env.get("APPDIR", "")

    def bundled(p):
        return "/.mount_" in p or bool(appdir and p.startswith(appdir))

    for var in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONHOME", "PYTHONPATH",
                "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "GST_PLUGIN_SYSTEM_PATH",
                "GST_PLUGIN_PATH", "GIO_MODULE_DIR", "GDK_PIXBUF_MODULE_FILE",
                "PATH", "XDG_DATA_DIRS"):
        value = env.get(var)
        if value is None:
            continue
        parts = [p for p in value.split(os.pathsep) if p and not bundled(p)]
        if parts:
            env[var] = os.pathsep.join(parts)
        elif var == "PATH":
            env[var] = "/usr/local/bin:/usr/bin:/bin"
        else:
            env.pop(var)
    return env


def _describe(exc):
    """A readable reason, even for errors with no message (a timeout)."""
    text = str(exc).strip()
    name = type(exc).__name__
    if isinstance(exc, (TimeoutError, socket.timeout)) or "timed out" in text:
        return f"no answer in {TIMEOUT} seconds"
    return f"{name}: {text}" if text else name


def _get_urllib(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return data, r.geturl()


def _get_curl(url):
    """curl copes with what urllib sometimes can't (HTTP/2, odd proxies)."""
    curl = shutil.which("curl", path=system_env().get("PATH"))
    if not curl:
        raise OSError("curl is not installed")
    cmd = [curl, "-sS", "-L", "--compressed", "--max-time", str(TIMEOUT * 2),
           "-w", "\n%{http_code} %{url_effective}"]
    for k, v in HEADERS.items():
        cmd += ["-H", f"{k}: {v}"]
    out = subprocess.run(cmd + [url], capture_output=True, timeout=TIMEOUT * 2 + 5, env=system_env())
    if out.returncode != 0:
        raise OSError(out.stderr.decode("utf-8", "replace").strip() or f"curl exit {out.returncode}")
    body, _, tail = out.stdout.rpartition(b"\n")
    code, _, final = tail.decode().partition(" ")
    if not code.startswith("2"):
        raise OSError(f"HTTP {code}")
    return body, final or url


def _get(url):
    """Download url: curl first (Cambridge answers it over HTTP/2 at once,
    while Python's HTTP/1.1 request can hang), then urllib."""
    reasons = []
    for how in (_get_curl, _get_urllib):
        try:
            return how(url)
        except Exception as exc:
            reasons.append(f"{'curl' if how is _get_curl else 'python'}: {_describe(exc)}")
    raise OSError("; ".join(reasons))


def _load_cache():
    path = os.path.join(_cache_dir(), "words.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


_LOCK = threading.Lock()


def _save(word, info):
    with _LOCK:
        cache = _load_cache()
        cache[word] = info
        path = os.path.join(_cache_dir(), "words.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=0)
        os.replace(tmp, path)


def _download_audio(word, region, info):
    """Download the recording; returns the local file or None."""
    for kind in ("mp3", "ogg"):
        url = info.get(kind)
        if not url:
            continue
        name = re.sub(r"[^a-z0-9]+", "_", word.lower()) + f"_{region}.{kind}"
        path = os.path.join(_cache_dir(), name)
        if not os.path.exists(path):
            data, _final = _get(url)
            with open(path, "wb") as f:
                f.write(data)
        info.setdefault("files", {})[kind] = path
        return path
    return None


def cached(word):
    """The cached pronunciation of a word (no network), or None."""
    return _load_cache().get(word.strip().lower())


def lookup(word):
    """Pronunciation of word (cached). Network and parsing happen here.

    Returns {"word", "url", "uk": {...}, "us": {...}} or {"error": "..."}.
    """
    word = word.strip()
    key = word.lower()
    cache = _load_cache()
    if key in cache and (cache[key].get("uk") or cache[key].get("us")) and "defs" in cache[key]:
        return cache[key]
    old = cache.get(key)  # cached before definitions were read: fetch again
    url = page_url(word)
    try:
        data, final = _get(url)
    except Exception as exc:
        return {"word": word, "url": url, "error": f"could not reach Cambridge ({exc})"}
    page = data.decode("utf-8", "replace")
    info = {"word": word, "url": url}
    info.update(parse(page))
    try:
        info["defs"] = parse_definitions(page)
    except Exception:
        info["defs"] = []
    if not (info.get("uk") or info.get("us")):
        info["error"] = "not in the Cambridge Dictionary"
        return info
    for region in ("uk", "us"):
        if region in info:
            if old and old.get(region, {}).get("files"):
                files = {k: v for k, v in old[region]["files"].items() if os.path.exists(v)}
                if files:
                    info[region]["files"] = files
                    continue
            try:
                _download_audio(key, region, info[region])
            except Exception:
                pass
    _save(key, info)
    return info


def play(path):
    """Play an audio file with whatever the system has. True if started."""
    if not path or not os.path.exists(path):
        return False
    players = [["mpv", "--no-video", "--really-quiet"],
               ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
               None,  # Qt's own player
               ["pw-play"], ["paplay"], ["xdg-open"]]
    for cmd in players:
        if cmd is None:
            if _play_qt(path):
                return True
            continue
        if shutil.which(cmd[0], path=system_env().get("PATH")):
            try:
                subprocess.Popen(cmd + [path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=system_env(),
                                 start_new_session=True)
                return True
            except OSError:
                continue
    return False


_PLAYER = None


def _play_qt(path):
    global _PLAYER
    try:
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
        except ImportError:
            return False
        if _PLAYER is None:
            player = QMediaPlayer()
            out = QAudioOutput()
            out.setVolume(1.0)
            player.setAudioOutput(out)
            _PLAYER = (player, out)
        player = _PLAYER[0]
        player.stop()
        player.setSource(QUrl.fromLocalFile(path))
        player.play()
        return True
    except Exception:
        return False
