"""
TTS 모듈 사용 예시 (Supervisor Agent 통합용)
"""

from tts_module import generate_interview_audio

# ============================================================================
# 예시 1: 기본 사용법 (스트리밍)
# ============================================================================

def example_basic():
    """기본 사용 예시"""
    
    # Supervisor가 LLM으로 생성한 답변
    llm_response = """좋은 질문이네요. 
    해시맵의 시간복잡도는 평균적으로 O(1)입니다. 
    충돌 처리는 체이닝이나 개방 주소법을 사용합니다."""
    
    print("면접관 답변 음성 생성 중...\n")
    
    # TTS 생성 (문장별로 즉시 yield)
    for audio_chunk in generate_interview_audio(llm_response):
        
        # 에러 체크
        if 'error' in audio_chunk:
            print(f"❌ 에러 발생: {audio_chunk['error']}")
            continue
        
        # 각 문장의 오디오를 프론트엔드로 전송
        print(f"✅ 문장 {audio_chunk['sentence_number']}: {audio_chunk['text']}")
        
        # 실제로는 여기서 WebSocket/HTTP로 전송
        # send_to_frontend(audio_chunk)
        
        # 첫 음성 알림
        if audio_chunk['is_first']:
            print(f"   ⚡ 첫 음성 생성 완료! ({audio_chunk['generation_time']:.2f}초)")


# ============================================================================
# 예시 2: FastAPI 통합
# ============================================================================

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

@app.post("/interview/speak")
async def interview_speak(text: str):
    """
    면접관 음성 생성 API (Server-Sent Events)
    """
    
    async def event_generator():
        for chunk in generate_interview_audio(text):
            # SSE 형식으로 전송
            data = json.dumps(chunk)
            yield f"data: {data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ============================================================================
# 예시 3: WebSocket 통합
# ============================================================================

from fastapi import WebSocket

@app.websocket("/ws/interview")
async def websocket_interview(websocket: WebSocket):
    """
    WebSocket을 통한 실시간 음성 스트리밍
    """
    await websocket.accept()
    
    try:
        while True:
            # 클라이언트로부터 텍스트 수신
            data = await websocket.receive_json()
            text = data.get('text', '')
            
            # TTS 생성 및 전송
            for chunk in generate_interview_audio(text):
                await websocket.send_json(chunk)
                
    except Exception as e:
        print(f"WebSocket 에러: {e}")
    finally:
        await websocket.close()


# ============================================================================
# 예시 4: 배치 처리
# ============================================================================

from tts_module import generate_interview_audio_batch

def example_batch():
    """배치 모드 사용 (모든 문장 한 번에 생성)"""
    
    text = "안녕하세요. 면접을 시작하겠습니다."
    
    # 모든 문장을 한 번에 생성
    result = generate_interview_audio_batch(text)
    
    print(f"총 {result['total_chunks']}개 문장 생성 완료")
    print(f"첫 음성: {result['first_audio_time']:.2f}초")
    
    # 모든 청크에 접근
    for chunk in result['audio_chunks']:
        print(f"- {chunk['text']}")


if __name__ == "__main__":
    print("="*70)
    print("TTS 모듈 사용 예시")
    print("="*70)
    
    example_basic()