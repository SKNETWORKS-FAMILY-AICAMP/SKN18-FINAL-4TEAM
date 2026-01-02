import pandas as pd
import openai
from openai import OpenAI

# 1. 설정
INPUT_FILE = "stt_verified_videos_with_scripts.csv" # transcript 컬럼이 있는 파일
OUTPUT_FILE = "final_data_with_summary.csv"         # 결과 파일
# API_KEY

client = OpenAI(api_key=API_KEY)

# 2. 요약 프롬프트 함수 (번역 + 요약 강화)
def summarize_text(transcript):
    if not transcript or len(str(transcript)) < 50:
        return "요약 불가 (내용 부족)"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                # ⚙️ [시스템 역할 부여] : 전문 통번역가이자 기술 면접관 페르소나 부여
                {
                    "role": "system", 
                    "content": "You are an expert technical interviewer and translator. Your task is to analyze English transcripts from coding interviews and summarize key insights into Korean."
                },
                # 🗣️ [사용자 명령] : 한국어로 3줄 요약 명시
                {
                    "role": "user", 
                    "content": f"""
                    다음은 영어로 된 개발자 면접/라이브 코딩 영상의 자막(Transcript)입니다.
                    이 내용을 분석하여 **'실전 면접 꿀팁'이나 '핵심 기술 조언'을 중심으로**
                    **자연스러운 한국어로 3줄 요약**해 주세요.
                    
                    (단, 단순 번역이 아니라 개발자가 이해하기 쉬운 용어로 의역해 주세요.)

                    [자막 내용]:
                    {transcript[:4000]}
                    """
                } 
            ],
            temperature=0.7 # 약간의 창의성 허용 (자연스러운 한국어 문장을 위해)
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"요약 실패: {e}"

# 3. 메인 실행
if __name__ == "__main__":
    # 파일 확인
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"❌ '{INPUT_FILE}' 파일이 없습니다. 경로를 확인해주세요.")
        exit()
        
    print(f"🔄 총 {len(df)}개 영상 요약 및 번역 시작...")

    # 요약 컬럼 초기화
    if 'summary' not in df.columns:
        df['summary'] = ""

    for index, row in df.iterrows():
        title = row.get('title', 'No Title')
        print(f"[{index+1}/{len(df)}] 진행 중: {title[:30]}...", end="")
        
        transcript = row.get('transcript', '')
        
        # 이미 요약된 내용이 있다면 건너뛰기 (중간에 끊겼을 때 이어하기 위함)
        if pd.notna(row['summary']) and row['summary'] != "":
            print(" (이미 완료됨)")
            continue

        summary = summarize_text(transcript)
        
        df.at[index, 'summary'] = summary
        print(" ✅ 완료")

    # 저장
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n🎉 작업 완료! '{OUTPUT_FILE}' 파일에 한국어 요약이 저장되었습니다.")