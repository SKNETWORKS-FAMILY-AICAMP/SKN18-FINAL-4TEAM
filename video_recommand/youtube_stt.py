

from __future__ import annotations
import os
import re
import tempfile
import subprocess
import shutil
import csv
from typing import Any, Dict, List, Optional

from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv


# -----------------------------
# YouTube ID parsing
# -----------------------------
_YT_ID_PATTERNS = [
    re.compile(r"(?:v=)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtu\.be/)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:shorts/)([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:embed/)([A-Za-z0-9_-]{11})"),
]


def extract_youtube_video_id(url: str) -> Optional[str]:
    if not url:
        return None
    for rx in _YT_ID_PATTERNS:
        m = rx.search(url)
        if m:
            return m.group(1)
    return None


def _join_transcript_segments(segments: List[Dict[str, Any]]) -> str:
    # segments: [{"text": "...", "start": 0.0, "duration": 1.2}, ...]
    parts: List[str] = []
    for seg in segments:
        t = (seg.get("text") or "").strip()
        if t:
            parts.append(t)
    return " ".join(parts).strip()


# -----------------------------
# 1) YouTube transcript first
# -----------------------------
def fetch_youtube_transcript(
    video_url: str,
    preferred_langs: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    video_id = extract_youtube_video_id(video_url)
    if not video_id:
        return None

    langs = preferred_langs or ["ko", "en", "en-US", "en-GB"]

    try:
        tlist = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None

        # Prefer manually created
        for lang in langs:
            try:
                transcript = tlist.find_manually_created_transcript([lang])
                break
            except Exception:
                pass

        # Then auto-generated
        if transcript is None:
            for lang in langs:
                try:
                    transcript = tlist.find_generated_transcript([lang])
                    break
                except Exception:
                    pass

        # If still none, give up
        if transcript is None:
            return None

        segments = transcript.fetch()
        text = _join_transcript_segments(segments)

        if not text:
            return None

        return {
            "source": "youtube_transcript",
            "text": text,
            "segments": segments,
            "meta": {
                "video_id": video_id,
                "language": getattr(transcript, "language_code", None),
                "is_generated": getattr(transcript, "is_generated", None),
            },
        }
    except Exception:
        return None


# -----------------------------
# 2) Fallback: yt-dlp audio download (no ffmpeg) + Whisper upload as-is
# -----------------------------
def download_audio_with_ytdlp_no_ffmpeg(video_url: str, out_dir: str) -> str:
    """
    Downloads bestaudio without converting (no ffmpeg).
    Output will be something like audio.webm / audio.m4a depending on source.
    """
    # Try PATH first, then local venv Scripts
    yt_dlp_bin = shutil.which("yt-dlp")
    if not yt_dlp_bin:
        candidate = os.path.join(os.path.dirname(__file__), "..", ".venv", "Scripts", "yt-dlp.exe")
        candidate = os.path.abspath(candidate)
        if os.path.exists(candidate):
            yt_dlp_bin = candidate

    if not yt_dlp_bin:
        raise RuntimeError("yt-dlp is not installed or not on PATH. Install with `pip install yt-dlp`.")

    out_tmpl = os.path.join(out_dir, "audio.%(ext)s")
    subprocess.run(
        [yt_dlp_bin, "-f", "bestaudio/best", "-o", out_tmpl, video_url],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Find downloaded audio.* file
    for fn in os.listdir(out_dir):
        if fn.startswith("audio."):
            return os.path.join(out_dir, fn)

    raise RuntimeError("yt-dlp download succeeded but audio file not found.")


def whisper_transcribe_file_as_is(
    audio_path: str,
    model: str = "whisper-1",
    language_hint: Optional[str] = None,
) -> Dict[str, Any]:
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Export it or add it to a .env file.")

    client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as f:
        # Try verbose_json first (segments sometimes available)
        try:
            resp = client.audio.transcriptions.create(
                model=model,
                file=f,
                response_format="verbose_json",
                language=language_hint,
            )
            text = getattr(resp, "text", None) or resp.get("text", "")
            segments = getattr(resp, "segments", None) or resp.get("segments", [])
            return {
                "source": "whisper",
                "text": (text or "").strip(),
                "segments": segments,
                "meta": {
                    "model": model,
                    "language_hint": language_hint,
                    "input_ext": os.path.splitext(audio_path)[1].lstrip("."),
                },
            }
        except Exception:
            # Fallback to plain text
            f.seek(0)
            resp2 = client.audio.transcriptions.create(
                model=model,
                file=f,
                response_format="text",
                language=language_hint,
            )
            return {
                "source": "whisper",
                "text": str(resp2).strip(),
                "segments": [],
                "meta": {
                    "model": model,
                    "language_hint": language_hint,
                    "input_ext": os.path.splitext(audio_path)[1].lstrip("."),
                    "note": "Segments unavailable (text response_format).",
                },
            }


# -----------------------------
# Main API
# -----------------------------
def get_transcript_youtube_then_whisper(
    video_url: str,
    preferred_langs: Optional[List[str]] = None,
    whisper_model: str = "whisper-1",
    stt_language_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Whisper-only path:
    - Download audio with yt-dlp (no ffmpeg).
    - Transcribe with Whisper (no YouTube transcript fallback).
    """
    with tempfile.TemporaryDirectory() as d:
        audio_path = download_audio_with_ytdlp_no_ffmpeg(video_url, d)
        return whisper_transcribe_file_as_is(
            audio_path,
            model=whisper_model,
            language_hint=stt_language_hint,
        )


def transcribe_csv(
    input_csv: str,
    output_csv: str,
    whisper_model: str = "whisper-1",
    stt_language_hint: Optional[str] = None,
) -> None:
    """
    Read URLs from input_csv and write transcripts to output_csv.
    Expected columns: category, code_lang, url, video_id
    """
    fieldnames = ["category", "code_lang", "url", "video_id", "transcript", "source", "error"]
    with open(input_csv, newline="", encoding="utf-8") as f_in, \
         open(output_csv, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for idx, row in enumerate(reader, start=1):
            url = (row.get("url") or "").strip()
            if not url:
                continue
            try:
                result = get_transcript_youtube_then_whisper(
                    url,
                    whisper_model=whisper_model,
                    stt_language_hint=stt_language_hint,
                )
                text = result.get("text", "").strip()
                source = result.get("source", "")
                err = ""
            except Exception as exc:  # noqa: BLE001
                text = ""
                source = ""
                err = str(exc)

            writer.writerow(
                {
                    "category": row.get("category", ""),
                    "code_lang": row.get("code_lang", ""),
                    "url": url,
                    "video_id": row.get("video_id", ""),
                    "transcript": text,
                    "source": source,
                    "error": err,
                }
            )

            # flush every 100 rows to preserve progress
            if idx % 100 == 0:
                f_out.flush()
                print(f"[progress] processed {idx} rows...")


if __name__ == "__main__":
    # Batch STT: read URLs from CSV and write transcripts
    input_csv = os.path.join(os.path.dirname(__file__), "data", "youtube_urls_cleaned.csv")
    output_csv = os.path.join(os.path.dirname(__file__), "data", "youtube_transcripts.csv")

    transcribe_csv(
        input_csv=input_csv,
        output_csv=output_csv,
        whisper_model="whisper-1",
        stt_language_hint=None,  # auto-detect language
    )
    print(f"Saved transcripts -> {output_csv}")


