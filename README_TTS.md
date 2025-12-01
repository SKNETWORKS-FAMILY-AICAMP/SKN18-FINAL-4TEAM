# AI 면접관 TTS 모듈

라이브코딩 모의면접 시스템을 위한 최적화된 TTS 모듈

## 성능

실험 결과 기반 최적 조합 적용:
- **평균 첫 음성**: 2.0초
- **최고 기록**: 1.72초
- **3초 이내 달성률**: 100%

## 설치
```bash
pip install openai python-dotenv
```

## 환경 설정

`.env` 파일 생성:
```
OPENAI_API_KEY=your_api_key_here
```

## 기본 사용법
```python
from tts_module import generate_interview_audio

# LLM이 생성한 텍스트
text = "안녕하세요. 좋은 질문이네요."

# 문장별로 음성 생성 (스트리밍)
for audio_chunk in generate_interview_audio(text):
    print(audio_chunk['text'])
    # audio_chunk['audio_base64']를 프론트엔드로 전송
```

## API

### generate_interview_audio(text: str)

문장별로 음성을 생성하는 제너레이터

**Parameters:**
- `text` (str): 면접관이 말할 완성된 텍스트

**Yields:**
```python
{
    'sentence_number': int,      # 문장 번호
    'text': str,                 # 문장 텍스트
    'audio_base64': str,         # Base64 인코딩된 MP3
    'is_first': bool,            # 첫 문장 여부
    'generation_time': float     # 생성 시간(초)
}
```

### generate_interview_audio_batch(text: str)

모든 문장을 한 번에 생성 (배치 모드)

**Returns:**
```python
{
    'audio_chunks': list,
    'total_chunks': int,
    'first_audio_time': float,
    'total_time': float
}
```

## 실험 데이터

75개 조합 테스트 결과:
- 프롬프트 전략: 5가지
- 생성 방법: 3가지
- 테스트 시나리오: 5가지

최종 선정:
- **TTS**: OpenAI TTS-1 (nova)
- **방법**: 문장별 스트리밍
- **프롬프트**: 단계적 구조 (Supervisor가 LLM에 적용)

## 파일 구조
```
tts-poc/
├── tts_module.py          # 메인 모듈
├── example_usage.py       # 사용 예시
├── README_TTS.md          # 문서
└── .env                   # 환경 변수
```

## 주의사항

- OpenAI API 키 필요
- 네트워크 연결 필요
- API 사용량 과금 발생