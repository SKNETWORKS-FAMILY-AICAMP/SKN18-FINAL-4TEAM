import pandas as pd
import os

# 1. 파일 경로 설정 (병합된 파일이 있는 곳)
input_file = "live_coding_videos_en_long.csv"
output_file = "live_coding_videos_en_long_refined.csv"

# 2. 필터링 로직 정의
def filter_videos(df):
    # 제거할 키워드 (블랙리스트)
    BLACKLIST = [
        "arduino", "raspberry", "hardware", "install", "setup", "configure", # 하드웨어/설치
        "qualitative", "thesis", "dissertation", "research method", "nvivo", # 학술 연구
        "music", "song", "playlist", "lo-fi", "chill", "asmr", # 배경음악
        "gaming", "gameplay", "stream", "reaction", "react to", # 게임/리액션
        "vlog", "day in the life", "tour", "visit", # 브이로그
        "salary", "negotiation", "finance", "money", # 연봉 관련
        "#shorts", "shorts" # 숏츠
    ]

    # 필수 포함 키워드 (화이트리스트 - 관련성 체크용)
    WHITELIST = [
        "interview", "coding", "code", "algorithm", "structure", "system design",
        "whiteboard", "mock", "technical", "engineer", "developer", "programmer",
        "solve", "solution", "leetcode", "hackerrank", "faang", "google", "amazon", "meta",
        "python", "java", "c++", "javascript", "bug", "debug", "test", "case",
        "질문", "면접", "코딩", "알고리즘", "개발자", "해결", "전략" # 한국어 키워드 포함
    ]

    filtered_rows = []
    removed_count = 0

    print("데이터 필터링 중...", end="")
    
    for index, row in df.iterrows():
        title = str(row['title']).lower()
        
        # A. 블랙리스트 체크
        is_blacklisted = False
        for bad_word in BLACKLIST:
            if bad_word in title:
                is_blacklisted = True
                break
        if is_blacklisted:
            removed_count += 1
            continue

        # B. 화이트리스트 체크 (관련성 점수)
        relevance_score = 0
        for good_word in WHITELIST:
            if good_word in title:
                relevance_score += 1
        
        # 관련 키워드가 하나도 없으면 제거
        if relevance_score == 0:
            removed_count += 1
            continue

        # 통과된 데이터 담기
        filtered_rows.append(row)

    print(" 완료!")
    return pd.DataFrame(filtered_rows), removed_count

# 3. 메인 실행 부
if os.path.exists(input_file):
    df = pd.read_csv(input_file)
    print(f" 원본 데이터 로드 완료: {len(df)}개")
    
    clean_df, removed_cnt = filter_videos(df)
    
    # 파일 저장 (한글 깨짐 방지 utf-8-sig)
    clean_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n 정제 완료! 파일이 생성되었습니다: {output_file}")
    print(f"   - 원본 개수: {len(df)}개")
    print(f"   - 제거된 개수: {removed_cnt}개")
    print(f"   - 최종 남은 개수: {len(clean_df)}개")
    
    print("\n 최종 카테고리 분포:")
    print(clean_df['category'].value_counts())
    
else:
    print(f" '{input_file}' 파일이 없습니다. 병합된 파일을 먼저 준비해주세요.")