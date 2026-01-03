import pandas as pd
from youtubesearchpython import VideosSearch
import httpx
import time

DOMAIN_NAME = "live_coding"
MAX_RESULTS_PER_KEYWORD = 700
MIN_DURATION_SECONDS = 300  # ⏱️ 최소 5분 (300초) 설정

# 🚫 [제외 키워드] (영문 노이즈 제거)
EXCLUDED_KEYWORDS = [
    "behavioral", "tell me about yourself", "salary", "negotiation", 
    "resume", "hr interview", "soft skills only", "culture fit", 
    "manager interview", "career advice", "day in the life", "vlog",
    "how i got into", "my experience", "offer", "internship application",
    "#shorts", "shorts", "music", "lo-fi", "gameplay"
]

# ✅ [영문 키워드] (English Search Rules)
search_rules = {
    "REQUIREMENT_CHECK": [
        "Handling ambiguous coding interview questions",
        "Clarifying input output constraints interview",
        "Google coding interview asking questions",
        "Defining scope in technical interview",
        "Meta coding interview requirement gathering",
    ],
    "LOGIC_DESIGN": [
        "Brute force to optimized solution interview",
        "Algorithm brainstorming session interview",
        "Choosing right data structure interview",
        "High level approach coding interview",
        "Diagramming solution before coding",
    ],
    "THINK_ALOUD": [
        "Narrating thought process coding interview",
        "Filling silence in coding interview",
        "Collaborative problem solving interview",
        "Engaging with interviewer technical round",
        "Mock interview communication feedback",
    ],
    "CRISIS_MGMT": [
        "Brain freeze during coding interview",
        "Recovering from wrong approach interview",
        "Troubleshooting algorithm without running code",
        "Coding interview getting stuck strategies",
        "Fixing logic error in whiteboard interview",
    ],
    "CODE_VERIFICATION": [
        "Big O analysis in coding interview",
        "Walking through test cases interview",
        "Manual code tracing technique",
        "Self-correcting code in interview",
        "Edge case testing strategy algorithm",
    ],
}

# ⏱️ 시간 변환 함수
def get_seconds(duration_str):
    if not duration_str: return 0
    try:
        parts = duration_str.split(':')
        if len(parts) == 3: # H:M:S
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: # M:S
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1: # S
            return int(parts[0])
    except:
        return 0
    return 0

# 라이브러리 패치
def _patch_ysp_httpx_proxies():
    try:
        from youtubesearchpython.core import requests as ysp_requests
    except Exception:
        return
    def _sync_post(self):
        headers = {"User-Agent": ysp_requests.userAgent}
        if self.proxy:
            with httpx.Client(proxies=self.proxy) as client:
                return client.post(self.url, headers=headers, json=self.data, timeout=self.timeout)
        return httpx.post(self.url, headers=headers, json=self.data, timeout=self.timeout)
    def _sync_get(self):
        headers = {"User-Agent": ysp_requests.userAgent}
        cookies = {"CONSENT": "YES+1"}
        if self.proxy:
            with httpx.Client(proxies=self.proxy) as client:
                return client.get(self.url, headers=headers, timeout=self.timeout, cookies=cookies)
        return httpx.get(self.url, headers=headers, timeout=self.timeout, cookies=cookies)
    ysp_requests.RequestCore.syncPostRequest = _sync_post
    ysp_requests.RequestCore.syncGetRequest = _sync_get

def collect_youtube_data():
    data_list = []
    current_id = 1
    
    # 파일명 설정 (영문 + 긴 영상)
    output_filename = "live_coding_videos_en_long.csv"

    print(f"[{DOMAIN_NAME}] 영문 데이터 수집 시작 (5분 이상만)...")
    _patch_ysp_httpx_proxies()

    for category, keywords in search_rules.items():
        print(f"\n📂 Category: {category} Collecting...")

        for keyword in keywords:
            print(f"   ㄴ Searching for: '{keyword}'...")

            try:
                # region='US' 설정 (영문 콘텐츠 타겟)
                videos_search = VideosSearch(keyword, limit=MAX_RESULTS_PER_KEYWORD, region='US')
                results = videos_search.result()["result"]

                for video in results:
                    video_url = video["link"]
                    title = video["title"]
                    duration_str = video.get("duration")
                    
                    # 1️⃣ [제목 필터링] 제외 키워드
                    is_excluded = False
                    for bad_word in EXCLUDED_KEYWORDS:
                        if bad_word in title.lower():
                            is_excluded = True
                            # print(f"      ❌ 제목 필터링: {title[:20]}...")
                            break
                    if is_excluded: continue

                    # 2️⃣ [시간 필터링] 5분(300초) 미만 제거
                    seconds = get_seconds(duration_str)
                    if seconds < MIN_DURATION_SECONDS: 
                        # print(f"      ❌ 짧은 영상 제외 ({duration_str}): {title[:20]}...")
                        continue

                    # 조건 통과: 저장
                    data_list.append({
                        "id": current_id,
                        "domain": DOMAIN_NAME,
                        "category": category,
                        "video_url": video_url,
                        "title": title,
                        "duration": duration_str
                    })
                    current_id += 1

                time.sleep(1)

            except Exception as e:
                print(f"   ⚠️ Error ({keyword}): {e}")

    columns = ["id", "domain", "category", "video_url", "title", "duration"]
    df = pd.DataFrame(data_list, columns=columns)

    df.to_csv(output_filename, index=False, encoding="utf-8-sig")

    print(f"\n✅ 수집 완료! 총 {len(df)}개의 긴 영문 영상을 '{output_filename}'에 저장했습니다.")
    print(df.head())

if __name__ == "__main__":
    collect_youtube_data()