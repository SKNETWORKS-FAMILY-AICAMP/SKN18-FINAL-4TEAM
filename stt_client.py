"""
AI 면접관 TTS 모듈
- 최적 조합: 단계적구조 프롬프트 + 문장별 스트리밍
- 평균 첫 음성: 2.0초
- TTS: OpenAI TTS-1 (nova)
"""

import os
import re
import time
import base64
from typing import Generator, Dict
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# TTS 설정 (실험 결과 기반 최적값)
TTS_MODEL = "tts-1"  # 빠른 응답을 위해 tts-1 사용
TTS_VOICE = "nova"   # 따뜻하고 정중한 여성 목소리
TTS_SPEED = 1.0      # 정상 속도


def split_into_sentences(text: str) -> list[str]:
    """
    텍스트를 문장 단위로 분리
    
    Args:
        text: 분리할 텍스트
        
    Returns:
        문장 리스트
    """
    # 문장 종결 기호로 분리
    sentences = re.split(r'([.!?]\s+)', text)
    
    result = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sentence = (sentences[i] + sentences[i+1]).strip()
            if sentence:
                result.append(sentence)
    
    # 마지막 남은 텍스트 처리
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    
    return result


def generate_interview_audio(text: str) -> Generator[Dict, None, None]:
    """
    면접관 음성 생성 (문장별 스트리밍)
    
    실험 결과:
    - 평균 첫 음성: 2.0초
    - 최고 기록: 1.72초
    - 문장별 즉시 생성으로 자연스러운 경험 제공
    
    Args:
        text: 면접관이 말할 완성된 텍스트
        
    Yields:
        {
            'sentence_number': int,      # 문장 번호 (1부터 시작)
            'text': str,                 # 문장 텍스트
            'audio_base64': str,         # Base64 인코딩된 MP3 오디오
            'is_first': bool,            # 첫 문장 여부
            'generation_time': float     # 이 문장 생성에 걸린 시간(초)
        }
        
    Example:
        >>> text = "안녕하세요. 해시맵의 시간복잡도는 O(1)입니다."
        >>> for chunk in generate_interview_audio(text):
        >>>     print(f"문장 {chunk['sentence_number']}: {chunk['text']}")
        >>>     # chunk['audio_base64']를 프론트엔드로 전송
    """
    
    # 텍스트를 문장 단위로 분리
    sentences = split_into_sentences(text)
    
    if not sentences:
        # 빈 텍스트 처리
        return
    
    # 각 문장을 TTS로 변환하여 yield
    for index, sentence in enumerate(sentences, start=1):
        sentence_start_time = time.time()
        
        try:
            # TTS 생성
            tts_response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=TTS_VOICE,
                input=sentence,
                speed=TTS_SPEED
            )
            
            # Base64 인코딩
            audio_base64 = base64.b64encode(tts_response.content).decode('utf-8')
            
            generation_time = time.time() - sentence_start_time
            
            # 결과 yield
            yield {
                'sentence_number': index,
                'text': sentence,
                'audio_base64': audio_base64,
                'is_first': (index == 1),
                'generation_time': generation_time
            }
            
        except Exception as e:
            # 에러 발생 시에도 yield (에러 정보 포함)
            yield {
                'sentence_number': index,
                'text': sentence,
                'audio_base64': None,
                'is_first': (index == 1),
                'generation_time': 0,
                'error': str(e)
            }


# ============================================================================
# 편의 함수들
# ============================================================================

def generate_interview_audio_batch(text: str) -> Dict:
    """
    모든 문장을 한 번에 생성 (배치 모드)
    
    실시간 스트리밍이 필요 없을 때 사용
    
    Args:
        text: 면접관이 말할 완성된 텍스트
        
    Returns:
        {
            'audio_chunks': list,        # 모든 오디오 청크
            'total_chunks': int,         # 총 청크 수
            'first_audio_time': float,   # 첫 음성 생성 시간
            'total_time': float          # 전체 생성 시간
        }
    """
    start_time = time.time()
    audio_chunks = []
    first_audio_time = None
    
    for chunk in generate_interview_audio(text):
        audio_chunks.append(chunk)
        
        if chunk['is_first']:
            first_audio_time = time.time() - start_time
    
    total_time = time.time() - start_time
    
    return {
        'audio_chunks': audio_chunks,
        'total_chunks': len(audio_chunks),
        'first_audio_time': first_audio_time or 0,
        'total_time': total_time
    }


def get_audio_duration_estimate(text: str) -> float:
    """
    텍스트의 예상 오디오 재생 시간 계산
    
    실험 데이터 기반 추정:
    - 평균 처리 속도: 24.2자/초
    - 한국어 평균 발화 속도: 약 4-5자/초
    
    Args:
        text: 텍스트
        
    Returns:
        예상 재생 시간(초)
    """
    char_count = len(text)
    # 한국어 평균 발화 속도 (약 4.5자/초)
    estimated_duration = char_count / 4.5
    return estimated_duration