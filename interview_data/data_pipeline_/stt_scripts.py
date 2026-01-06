import pandas as pd
import os
import whisper
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

# 1. 설정
INPUT_FILE = "live_coding_videos_en_long_refined.csv"
OUTPUT_FILE = "stt_verified_videos_with_scripts.csv"
MODEL_SIZE = "base" 

# 2. 검증 키워드
VALIDATION_KEYWORDS = {
    "REQUIREMENT_CHECK": ["clarify", "question", "assumption", "constraint", "input", "output", "scope", "ambigu", "ask", "requirement", "edge case"],
    "LOGIC_DESIGN": ["approach", "solution", "brute force", "optimiz", "complexity", "trade-off", "structure", "algorithm", "design", "plan", "hash", "map"],
    "THINK_ALOUD": ["think", "loud", "explain", "process", "saying", "communicat", "silence", "thought", "talk", "hear", "listen"],
    "CRISIS_MGMT": ["stuck", "hint", "help", "prob", "issue", "mistake", "error", "bug", "fix", "wrong", "panic", "debug"],
    "CODE_VERIFICATION": ["test", "case", "check", "dry run", "walk through", "example", "verify", "validate", "trace", "run", "correct"]
}

# 3. Whisper 모델 로드
print(f"🤖 Whisper AI 모델({MODEL_SIZE}) 로딩 중...")
model = whisper.load_model(MODEL_SIZE)

# 4. Helper 함수들
def get_video_id(url):
    try:
        if "youtu.be" in url: return url.split("/")[-1]
        if "youtube.com" in url: return parse_qs(urlparse(url).query)["v"][0]
    except: return None

def download_audio(video_url, output_filename="temp_audio"):
    """유튜브 영상을 오디오(mp3)로 다운로드"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return f"{output_filename}.mp3"
    except Exception as e:
        print(f"   ⚠️ 다운로드 실패: {e}")
        return None

def get_transcript_hybrid(video_url, video_id):
    """1순위: 유튜브 자막, 2순위: Whisper STT"""
    
    # [1단계] 유튜브 자막 시도
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text, "YouTube_Caption"
    except:
        pass 

    # [2단계] Whisper STT 시도
    print("   👉 자막 없음. Whisper AI로 변환 시작...", end="", flush=True)
    audio_path = download_audio(video_url, f"temp_{video_id}")
    
    if audio_path and os.path.exists(audio_path):
        try:
            result = model.transcribe(audio_path)
            text = result["text"]
            os.remove(audio_path)
            return text, "Whisper_AI"
        except Exception as e:
            print(f" 변환 에러: {e}")
            if os.path.exists(audio_path): os.remove(audio_path)
            return None, "Error"
    
    return None, "Download_Failed"

# 5. 메인 실행
if __name__ == "__main__":
    if not os.path.exists(INPUT_FILE):
        print(f"❌ '{INPUT_FILE}' 파일이 없습니다.")
        exit()

    df = pd.read_csv(INPUT_FILE)
    print(f"🔄 총 {len(df)}개 영상 검증 시작 (Hybrid Mode)...")

    verified_rows = []

    for index, row in df.iterrows():
        video_url = row['video_url']
        video_id = get_video_id(video_url)
        category = row['category']
        title = row['title']

        if not video_id: continue

        print(f"\n[{index+1}/{len(df)}] 검증 중: {title[:30]}...")
        
        transcript, source = get_transcript_hybrid(video_url, video_id)
        
        if transcript:
            keywords = VALIDATION_KEYWORDS.get(category, [])
            score = 0
            transcript_lower = transcript.lower()
            
            for kw in keywords:
                score += transcript_lower.count(kw)
            
            # 🎯 통과 기준: 점수 3점 이상
            if score >= 3:
                print(f"   ✅ 통과! (출처: {source}, 점수: {score})")
                
                row['transcript_source'] = source
                row['relevance_score'] = score
                
                # ✅ [핵심 수정] 자막 전체 내용을 컬럼에 저장
                row['transcript'] = transcript 
                
                verified_rows.append(row)
            else:
                print(f"   ❌ 탈락 (주제 불일치, 점수: {score})")
        else:
            print("   ⚠️ 텍스트 추출 불가 (건너뜀)")

    # 결과 저장
    result_df = pd.DataFrame(verified_rows)
    result_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    print(f"\n🎉 모든 작업 완료!")
    print(f"   - 입력: {len(df)}개")
    print(f"   - 검증 통과: {len(result_df)}개")
    print(f"   - 저장됨: {OUTPUT_FILE}")