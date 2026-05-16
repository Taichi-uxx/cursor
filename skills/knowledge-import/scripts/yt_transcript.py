#!/usr/bin/env python3
"""YouTube動画のメタデータ + 文字起こしを yt-dlp で取得する。

使い方:
    python3 yt_transcript.py <youtube_url>

標準出力フォーマット:
    --- METADATA ---
    title: ...
    uploader: ...
    upload_date: YYYYMMDD   (yymm判定に使う。空なら不明)
    url: ...
    --- TRANSCRIPT ---
    <プレーンテキストの文字起こし>

字幕優先順位: 手動ja → 自動ja → 手動en → 自動en → その他先頭
"""
import sys
import subprocess
import json
import tempfile
import glob
import os
import re
import html


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_vtt(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    ts_re = re.compile(r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->")
    tag_re = re.compile(r"<[^>]+>")
    out = []
    for ln in raw.splitlines():
        s = ln.strip()
        if s in ("WEBVTT", ""):
            continue
        if ts_re.search(ln):
            continue
        if s.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if re.fullmatch(r"\d+", s):
            continue
        text = html.unescape(tag_re.sub("", ln)).strip()
        if not text:
            continue
        if out and out[-1] == text:
            continue
        out.append(text)
    # 自動字幕にありがちなローリング重複を畳む
    deduped = []
    for t in out:
        if deduped and (t in deduped[-1] or deduped[-1] in t):
            if len(t) > len(deduped[-1]):
                deduped[-1] = t
            continue
        deduped.append(t)
    return "\n".join(deduped)


def pick_vtt(vtts):
    for pref in (".ja.", ".ja-", ".en.", ".en-"):
        for v in vtts:
            if pref in os.path.basename(v):
                return v
    return vtts[0] if vtts else None


def main():
    if len(sys.argv) < 2:
        print("ERROR: URL required", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]

    r = run(["yt-dlp", "--skip-download", "--dump-json", url])
    if r.returncode != 0:
        print(f"ERROR: yt-dlp metadata failed: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    meta = json.loads(r.stdout)
    title = meta.get("title", "")
    uploader = meta.get("uploader") or meta.get("channel", "")
    upload_date = meta.get("upload_date", "") or ""

    tmp = tempfile.mkdtemp()
    out_tmpl = os.path.join(tmp, "sub")
    run([
        "yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
        "--sub-langs", "ja,ja-orig,en,en-orig", "--sub-format", "vtt/best",
        "-o", out_tmpl, url,
    ])
    vtts = sorted(glob.glob(os.path.join(tmp, "*.vtt")))
    vtt = pick_vtt(vtts)
    transcript = parse_vtt(vtt) if vtt else ""

    print("--- METADATA ---")
    print(f"title: {title}")
    print(f"uploader: {uploader}")
    print(f"upload_date: {upload_date}")
    print(f"url: {url}")
    print("--- TRANSCRIPT ---")
    if transcript.strip():
        print(transcript)
    else:
        print("(字幕を取得できませんでした。字幕/自動字幕が無い、または地域制限の可能性があります。)")


if __name__ == "__main__":
    main()
