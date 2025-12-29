from langchain_community.tools.tavily_search import TavilySearchResults
import os

def search_youtube_videos(keyword: str, max_results=1):
    """Tavily를 이용해 유튜브 영상 링크를 검색합니다."""
    try:
        search_tool = TavilySearchResults(
            max_results=max_results,
            include_domains=["youtube.com"]
        )
        # 쿼리 최적화
        query = f"{keyword} tutorial video"
        results = search_tool.invoke(query)
        
        candidates = []
        if not results:
            return []

        for r in results:
            candidates.append({
                "title": r.get('content', '')[:100], # 제목(또는 내용 요약)
                "url": r.get('url', ''),
                "video_id": "tavily_result" # ID 추출 로직 생략(URL만 있으면 됨)
            })
        return candidates

    except Exception as e:
        print(f"  ⚠️ 검색 에러: {e}")
        return []