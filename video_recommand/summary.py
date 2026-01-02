from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# 1) "판단 근거용" GT 요약 프롬프트 (알고리즘/풀이 영상 특화)
# ============================================================

# LLM 시스템 프롬프트: STT로부터 루브릭용 GT 요약(algo_gt_v1)을 만들라고 지시.
# 알고리즘/풀이 영상에 특화해 근거 기반, 짧은 길이, 고정 스키마 JSON만 허용한다.
ALGO_GT_SYSTEM_PROMPT = """
너는 “알고리즘/풀이 STT → 판단근거용 GT 요약 생성기”다.

입력:
- 강의/풀이 영상의 STT 원문(매우 길고 중복/잡음이 있을 수 있음)

출력 목적:
- DB에 저장할 “Ground Truth(판단 기준 요약)”을 만든다.
- 이 요약은 나중에 사용자가 작성한 요약문을 평가하고,
  어떤 학습 영상을 추천할지 결정하는 근거로 쓰인다.

중요:
- ‘영상 내용 소개 요약’이 아니라, ‘이 영상을 이해했다면 사용자가 말할 수 있어야 하는 최소 기준(루브릭)’을 압축해서 저장하라.
- 추정 금지: 원문에 없는 내용은 반드시 insufficient_evidence로 표시한다.
- 알고리즘/문제풀이 영상이므로, 특히 아래를 강제한다:
  1) 핵심 개념의 "역할" (왜/무엇을 위해 쓰는지)
  2) 동작 흐름의 "결정 지점" (조건 분기/포인터 이동/상태 전이/종료 조건 등)
  3) 언제 쓰는지: 전제조건/문제 구조/적합 신호
  4) 언제 쓰면 안 되는지: 반례/전제 위반/비효율 상황
  5) 복잡도: 시간/공간, 병목 원인(가능하면)
  6) 예제: 숫자 나열이 아니라 “문제 유형/패턴” 중심

출력은 반드시 JSON만.
문자 제한(엄수):
- overall.one_liner <= 200자
- 각 축 summary <= 220자
- bullets/체크리스트 항목 <= 70자, 2~5개
- key_terms: 5~12개
- must_mention_terms: 3~8개
- minimum_user_summary_requirements: 3~6개

스키마(고정):
{
  "overall": {
    "topic": null|string,
    "algorithm_name": null|string,
    "problem_pattern": null|string,
    "one_liner": string,
    "key_terms": [string]
  },
  "axes": {
    "core_concepts": {
      "status": "present|insufficient_evidence",
      "summary": string,
      "must_understand": [string],
      "common_misconceptions": [string]
    },
    "algorithm_flow": {
      "status": "present|insufficient_evidence",
      "summary": string,
      "critical_decisions": [string],
      "stop_conditions": [string]
    },
    "when_to_use": {
      "status": "present|insufficient_evidence",
      "summary": string,
      "signals": [string],
      "prerequisites": [string]
    },
    "when_not_to_use": {
      "status": "present|insufficient_evidence",
      "summary": string,
      "anti_signals": [string],
      "failure_modes": [string]
    },
    "complexity": {
      "status": "present|insufficient_evidence",
      "time": null|string,
      "space": null|string,
      "bottlenecks": [string]
    },
    "examples": {
      "status": "present|insufficient_evidence",
      "summary": string,
      "problem_types": [string],
      "bridge_to_code": [string]
    }
  },
  "evaluation_ready_hints": {
    "must_mention_terms": [string],
    "minimum_user_summary_requirements": [string],
    "recommended_next_video_focus": [string]
  }
}

추가 규칙:
- status가 insufficient_evidence인 축은 문자열 필드는 "" 또는 null, 배열은 []로 한다.
- common_misconceptions / failure_modes는 원문에서 언급된 혼동/주의가 있으면 반영하고,
  없으면 빈 배열로 둔다(추정 금지).
""".strip()

# 줄글 요약용 시스템 프롬프트: STT를 짧은 한글 설명(문단+불릿)으로 압축한다.
ALGO_TEXT_SYSTEM_PROMPT = """
너는 “알고리즘/풀이 STT → 간결한 줄글 요약기”다.

요약 목표:
- 한국어로 2~3문단 이내.
- 핵심 아이디어/알고리즘 흐름/사용 조건·주의점/복잡도(있다면)를 자연어로 서술.
- 필요하면 3~5개 불릿으로 핵심 체크포인트를 덧붙인다.

금지/제한:
- 원문에 없는 내용 추정 금지.
- 불필요한 인사말/메타 발언 금지.
- 길이: 전체 900자 이내.
""".strip()

# 텍스트 요약 + 알고리즘 태그 추출용 프롬프트
ALGO_TEXT_WITH_TAGS_PROMPT = """
너는 “알고리즘/풀이 STT → 간결한 줄글 요약 + 알고리즘 태그 추출기”다.

요약 목표:
- 한국어로 2~3문단 이내.
- 핵심 아이디어/알고리즘 흐름/사용 조건·주의점/복잡도(있다면)를 자연어로 서술.
- 필요하면 3~5개 불릿으로 핵심 체크포인트를 덧붙인다.

추가 태그:
- 이 영상에서 다루는 핵심 알고리즘/기법/자료구조를 1~5개 선정해 리스트로 뽑아라.
- 예시: ["BFS", "DFS", "Dijkstra", "Union-Find", "Binary Search", "Greedy", "DP"]
- 원문에 근거가 없으면 빈 리스트 [].

언어 감지:
- 사용된 프로그래밍 언어를 1개 추정해라 (예: Python, Java, C++, JavaScript, Go, etc).
- 근거 없으면 "unknown".

금지/제한:
- 원문에 없는 내용 추정 금지.
- 불필요한 인사말/메타 발언 금지.
- 길이: 전체 900자 이내.

출력 형식:
```
<줄글+불릿 요약 본문>

[tags] tag1, tag2, ...
[lang] python
```
tags 줄에는 쉼표로 구분된 태그들을 적고, 없으면 [tags] 만 적는다.
[lang] 줄에는 감지한 언어 소문자/혼합 표기 그대로 한 단어로 적는다(모르면 unknown).
""".strip()


# ============================================================
# 2) Validation/Normalization (저장 안전성)
# ============================================================

def _clip(s: Optional[str], max_chars: int) -> str:
    # 문자열을 최대 길이로 자르고 넘치면 말줄임표로 표시.
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


def _clip_list(items: Any, max_items: int, max_chars_each: int) -> List[str]:
    # 리스트 길이와 항목 길이를 제한해 안전하게 정규화.
    if not isinstance(items, list):
        return []
    out: List[str] = []
    for x in items:
        sx = _clip(str(x), max_chars_each)
        if sx:
            out.append(sx)
        if len(out) >= max_items:
            break
    return out


def _status(block: Dict[str, Any]) -> str:
    # status 허용값만 통과시키고 나머지는 insufficient_evidence로 처리.
    s = block.get("status")
    return s if s in ("present", "insufficient_evidence") else "insufficient_evidence"


def _empty_if_insufficient(status: str, *, is_complexity: bool = False) -> Dict[str, Any]:
    if is_complexity:
        return {"status": status, "time": None, "space": None, "bottlenecks": []}
    # for other axes, return a minimal empty structure; caller will fill specific keys
    return {"status": status}


def _normalize_categories(raw: Optional[str]) -> List[str]:
    # category 문자열을 구분자(/,|,)로 나눠 깔끔한 리스트로 변환.
    if not raw:
        return []
    parts = re.split(r"[|/,]", str(raw))
    out = [p.strip() for p in parts if p.strip()]
    return out


def _extract_tags_from_text(text: str) -> List[str]:
    """
    요약 텍스트 하단의 "[tags] a, b, c" 라인을 파싱하여 리스트로 반환.
    없거나 비어 있으면 [] 반환.
    """
    if not text:
        return []
    lines = text.strip().splitlines()
    tag_line = None
    for ln in reversed(lines[-3:]):  # 끝부분 3줄 정도에서 태그 찾기
        if ln.lower().startswith("[tags]"):
            tag_line = ln
            break
    if not tag_line:
        return []
    tag_str = tag_line[len("[tags]"):].strip()
    if not tag_str:
        return []
    return [t.strip() for t in re.split(r"[|/,]", tag_str) if t.strip()]


def _extract_lang_from_text(text: str) -> str:
    """
    요약 텍스트 하단의 "[lang] python" 형태를 찾아 언어 문자열을 반환.
    없으면 "unknown".
    """
    if not text:
        return "unknown"
    lines = text.strip().splitlines()
    for ln in reversed(lines[-3:]):  # 끝부분 3줄 정도에서 탐색
        if ln.lower().startswith("[lang]"):
            lang = ln[len("[lang]"):].strip()
            return lang or "unknown"
    return "unknown"


# LLM 응답을 스키마/길이 제한에 맞춰 정규화하고 부족한 축은 비워둔다.
def normalize_algo_gt(raw_obj: Dict[str, Any]) -> Dict[str, Any]:
    overall = raw_obj.get("overall") or {}
    axes = raw_obj.get("axes") or {}
    hints = raw_obj.get("evaluation_ready_hints") or {}

    # overall
    norm_overall = {
        "topic": overall.get("topic") or None,
        "algorithm_name": overall.get("algorithm_name") or None,
        "problem_pattern": overall.get("problem_pattern") or None,
        "one_liner": _clip(str(overall.get("one_liner") or ""), 200),
        "key_terms": _clip_list(overall.get("key_terms"), max_items=12, max_chars_each=40),
    }

    # axes
    norm_axes: Dict[str, Any] = {}

    # core_concepts
    b = axes.get("core_concepts") or {}
    st = _status(b)
    if st == "insufficient_evidence":
        norm_axes["core_concepts"] = {
            **_empty_if_insufficient(st),
            "summary": "",
            "must_understand": [],
            "common_misconceptions": [],
        }
    else:
        norm_axes["core_concepts"] = {
            "status": "present",
            "summary": _clip(str(b.get("summary") or ""), 220),
            "must_understand": _clip_list(b.get("must_understand"), 5, 70),
            "common_misconceptions": _clip_list(b.get("common_misconceptions"), 5, 70),
        }

    # algorithm_flow
    b = axes.get("algorithm_flow") or {}
    st = _status(b)
    if st == "insufficient_evidence":
        norm_axes["algorithm_flow"] = {
            **_empty_if_insufficient(st),
            "summary": "",
            "critical_decisions": [],
            "stop_conditions": [],
        }
    else:
        norm_axes["algorithm_flow"] = {
            "status": "present",
            "summary": _clip(str(b.get("summary") or ""), 220),
            "critical_decisions": _clip_list(b.get("critical_decisions"), 5, 70),
            "stop_conditions": _clip_list(b.get("stop_conditions"), 5, 70),
        }

    # when_to_use
    b = axes.get("when_to_use") or {}
    st = _status(b)
    if st == "insufficient_evidence":
        norm_axes["when_to_use"] = {
            **_empty_if_insufficient(st),
            "summary": "",
            "signals": [],
            "prerequisites": [],
        }
    else:
        norm_axes["when_to_use"] = {
            "status": "present",
            "summary": _clip(str(b.get("summary") or ""), 220),
            "signals": _clip_list(b.get("signals"), 5, 70),
            "prerequisites": _clip_list(b.get("prerequisites"), 5, 70),
        }

    # when_not_to_use
    b = axes.get("when_not_to_use") or {}
    st = _status(b)
    if st == "insufficient_evidence":
        norm_axes["when_not_to_use"] = {
            **_empty_if_insufficient(st),
            "summary": "",
            "anti_signals": [],
            "failure_modes": [],
        }
    else:
        norm_axes["when_not_to_use"] = {
            "status": "present",
            "summary": _clip(str(b.get("summary") or ""), 220),
            "anti_signals": _clip_list(b.get("anti_signals"), 5, 70),
            "failure_modes": _clip_list(b.get("failure_modes"), 5, 70),
        }

    # complexity
    b = axes.get("complexity") or {}
    st = _status(b)
    if st == "insufficient_evidence":
        norm_axes["complexity"] = _empty_if_insufficient(st, is_complexity=True)
    else:
        norm_axes["complexity"] = {
            "status": "present",
            "time": _clip(str(b.get("time")), 60) if b.get("time") else None,
            "space": _clip(str(b.get("space")), 60) if b.get("space") else None,
            "bottlenecks": _clip_list(b.get("bottlenecks"), 5, 70),
        }

    # examples
    b = axes.get("examples") or {}
    st = _status(b)
    if st == "insufficient_evidence":
        norm_axes["examples"] = {
            **_empty_if_insufficient(st),
            "summary": "",
            "problem_types": [],
            "bridge_to_code": [],
        }
    else:
        norm_axes["examples"] = {
            "status": "present",
            "summary": _clip(str(b.get("summary") or ""), 220),
            "problem_types": _clip_list(b.get("problem_types"), 5, 70),
            "bridge_to_code": _clip_list(b.get("bridge_to_code"), 5, 70),
        }

    # hints
    norm_hints = {
        "must_mention_terms": _clip_list(hints.get("must_mention_terms"), 8, 40),
        "minimum_user_summary_requirements": _clip_list(hints.get("minimum_user_summary_requirements"), 6, 90),
        "recommended_next_video_focus": _clip_list(hints.get("recommended_next_video_focus"), 6, 70),
    }

    return {
        "version": "algo_gt_v1",
        "overall": norm_overall,
        "axes": norm_axes,
        "evaluation_ready_hints": norm_hints,
        "meta": {"created_at": datetime.now(timezone.utc).isoformat()},
    }


def _extract_json(text: str) -> Dict[str, Any]:
    # 텍스트 주변 잡음을 무시하고 JSON 객체만 추출.
    text = (text or "").strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("Model output does not contain a JSON object.")
    return json.loads(m.group(0))


# ============================================================
# 3) LLM interface + Single Node
# ============================================================

@dataclass
class LLM:
    """
    너희 get_llm("summary") 같은 어댑터로 교체.
    요구사항: invoke(messages=[{role, content}, ...], response_format="json_object"|None) -> str
    """
    def invoke(self, messages: List[Dict[str, str]], *, response_format: Optional[str] = "json_object") -> str:  # pragma: no cover
        raise NotImplementedError


def algo_gt_summary_node(state: Dict[str, Any], llm: LLM) -> Dict[str, Any]:
    """
    단일 노드:
    input:
      - state["stt_text"] : str (필수)
      - state.get("topic_hint") : Optional[str]
      - state.get("compression_level") : 1|2|3 (옵션, 기본 2)
    output:
      - state["algo_gt_summary"] : dict (DB 저장용)
    """
    stt_text = state.get("stt_text")
    if not isinstance(stt_text, str) or not stt_text.strip():
        raise ValueError("algo_gt_summary_node requires non-empty state['stt_text'] (str).")

    topic_hint = state.get("topic_hint")
    compression_level = state.get("compression_level", 2)
    if compression_level not in (1, 2, 3):
        compression_level = 2

    user_prompt = f"""[강의 STT 원문]
                    {stt_text}

                    [옵션]
                    - topic_hint: {topic_hint}
                    - compression_level: {compression_level} (1=덜 압축, 2=기본, 3=초압축)

                    [요청]
                    알고리즘/풀이 영상 STT로부터 DB에 저장할 “판단근거용 GT 요약(algo_gt_v1)”을 생성해라.
                    ‘소개 요약’이 아니라 ‘이해했다면 말할 수 있어야 하는 최소 기준(루브릭)’을 축별로 압축해라.
                    원문에 없는 내용은 추정하지 말고 해당 축을 insufficient_evidence로 처리해라.
                    반드시 JSON만 출력해라.
        """.strip()

    raw = llm.invoke(
        messages=[
            {"role": "system", "content": ALGO_GT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    obj = _extract_json(raw)
    norm = normalize_algo_gt(obj)

    new_state = dict(state)
    new_state["algo_gt_summary"] = norm
    return new_state


# ============================================================
# 4) OpenAI adapter + CSV batch summarization
# ============================================================

class OpenAIChatLLM(LLM):
    """
    Simple OpenAI Chat Completions adapter that satisfies the LLM interface above.
    """

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None, temperature: float = 0.0) -> None:
        load_dotenv()
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set. Export it or add it to a .env file.")
        self._client = OpenAI(api_key=key)
        self._model = model
        self._temperature = temperature

    def invoke(self, messages: List[Dict[str, str]], *, response_format: Optional[str] = "json_object") -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            response_format={"type": response_format} if response_format else None,
        )
        content = resp.choices[0].message.content
        if not content:
            raise ValueError("Model returned empty content.")
        return content


def summarize_transcript_text(
    transcript: str,
    llm: LLM,
    *,
    topic_hint: Optional[str] = None,
    compression_level: int = 2,
) -> Dict[str, Any]:
    """
    Convenience wrapper: run algo_gt_summary_node and return the normalized summary dict.
    """
    out_state = algo_gt_summary_node(
        {
            "stt_text": transcript,
            "topic_hint": topic_hint,
            "compression_level": compression_level,
        },
        llm,
    )
    return out_state["algo_gt_summary"]


def summarize_transcript_text_plain(
    transcript: str,
    llm: LLM,
    *,
    topic_hint: Optional[str] = None,
    compression_level: int = 2,
) -> str:
    """
    STT를 줄글/불릿 요약으로 반환한다.
    """
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("summarize_transcript_text_plain requires non-empty transcript (str).")

    user_prompt = f"""[강의 STT 원문]
    {transcript}

    [옵션]
    - topic_hint: {topic_hint}
    - compression_level: {compression_level} (1=덜 압축, 2=기본, 3=초압축)

    [요청]
    위 프롬프트(ALGO_TEXT_SYSTEM_PROMPT) 지침에 따라 900자 이내 한국어 줄글 요약과 핵심 불릿을 작성하라.
    """.strip()

    raw = llm.invoke(
        messages=[
            {"role": "system", "content": ALGO_TEXT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=None,
    )
    return raw.strip()


def summarize_transcript_text_plain_with_tags(
    transcript: str,
    llm: LLM,
    *,
    topic_hint: Optional[str] = None,
    compression_level: int = 2,
) -> Dict[str, Any]:
    """
    STT를 줄글/불릿 요약으로 반환하고, 요약 본문에서 [tags], [lang] 라인을 함께 생성하도록 LLM에 요청한다.
    Returns: {"text": 요약본문, "tags": [태그 리스트], "lang": "python" | "unknown" ...}
    """
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("summarize_transcript_text_plain_with_tags requires non-empty transcript (str).")

    user_prompt = f"""[강의 STT 원문]
    {transcript}

    [옵션]
    - topic_hint: {topic_hint}
    - compression_level: {compression_level} (1=덜 압축, 2=기본, 3=초압축)

    [요청]
    ALGO_TEXT_WITH_TAGS_PROMPT 지침에 따라 900자 이내 한국어 줄글 요약과 [tags] 라인을 포함하라.
    """.strip()

    raw = llm.invoke(
        messages=[
            {"role": "system", "content": ALGO_TEXT_WITH_TAGS_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=None,
    )
    text_out = raw.strip()
    tags = _extract_tags_from_text(text_out)
    lang = _extract_lang_from_text(text_out)
    return {"text": text_out, "tags": tags, "lang": lang}


def summarize_csv(
    input_csv: str,
    output_csv: str,
    *,
    model: str = "gpt-4o-mini",
    topic_hint_column: Optional[str] = None,
    compression_level: int = 2,
    max_rows: Optional[int] = None,
    output_format: str = "text",  # "json" | "text"
) -> None:
    """
    Read transcripts from input_csv, summarize each row, and write to output_csv.
    New columns:
      - algo_gt_summary: JSON string(algo_gt_v1) 또는 줄글 요약 텍스트
      - summary_error: error message if summarization failed
      - categories: LLM이 추출한 태그 리스트(JSON 문자열)
      - llm_code_lang: LLM이 감지한 코드 언어(문자열)
    """
    llm = OpenAIChatLLM(model=model)
    with open(input_csv, newline="", encoding="utf-8") as f_in, open(output_csv, "w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header.")

        resolved_topic_hint_column = topic_hint_column if topic_hint_column and topic_hint_column in reader.fieldnames else None

        out_fieldnames = reader.fieldnames + ["algo_gt_summary", "summary_error", "categories", "llm_code_lang"]
        writer = csv.DictWriter(f_out, fieldnames=out_fieldnames)
        writer.writeheader()

        for idx, row in enumerate(reader, start=1):
            if max_rows is not None and idx > max_rows:
                break

            transcript = (row.get("transcript") or "").strip()
            topic_hint = (row.get(resolved_topic_hint_column, "") or None) if resolved_topic_hint_column else None

            if not transcript:
                row["algo_gt_summary"] = ""
                row["summary_error"] = "empty transcript"
                writer.writerow(row)
                continue

            try:
                if output_format == "text":
                    summary_text_obj = summarize_transcript_text_plain_with_tags(
                        transcript,
                        llm,
                        topic_hint=topic_hint,
                        compression_level=compression_level,
                    )
                    row["algo_gt_summary"] = summary_text_obj["text"]
                    row["categories"] = json.dumps(summary_text_obj.get("tags", []), ensure_ascii=False)
                    row["llm_code_lang"] = summary_text_obj.get("lang", "unknown")
                else:
                    summary_obj = summarize_transcript_text(
                        transcript,
                        llm,
                        topic_hint=topic_hint,
                        compression_level=compression_level,
                    )
                    row["algo_gt_summary"] = json.dumps(summary_obj, ensure_ascii=False)
                    # JSON 요약에서는 태그를 추출하지 않으므로 빈 리스트
                    row["categories"] = json.dumps([], ensure_ascii=False)
                    row["llm_code_lang"] = "unknown"
                row["summary_error"] = ""
            except Exception as exc:  # noqa: BLE001
                row["algo_gt_summary"] = ""
                row["summary_error"] = str(exc)
                row["categories"] = json.dumps([], ensure_ascii=False)
                row["llm_code_lang"] = "unknown"

            writer.writerow(row)

            if idx % 10 == 0:
                f_out.flush()
                print(f"[progress] summarized {idx} rows...")


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    input_csv = os.path.join(base_dir, "data", "youtube_transcripts_cleaned.csv")
    output_csv = os.path.join(base_dir, "data", "youtube_summaries_texts.csv")

    output_format = os.environ.get("SUMMARY_OUTPUT_FORMAT", "text").lower()
    if output_format not in ("json", "text"):
        output_format = "text"

    summarize_csv(
        input_csv=input_csv,
        output_csv=output_csv,
        model=os.environ.get("SUMMARY_MODEL", "gpt-4o-mini"),
        topic_hint_column=None,
        compression_level=2,
        output_format=output_format,
    )
    print(f"Saved summaries -> {output_csv}")

