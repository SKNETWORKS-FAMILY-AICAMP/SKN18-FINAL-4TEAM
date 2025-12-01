import os
import time
from openai import OpenAI
from google.cloud import texttospeech
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 클라이언트 초기화
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
google_client = texttospeech.TextToSpeechClient()

# 테스트 문장들
test_sentences = {
    "인사": "안녕하세요. 오늘 면접을 진행할 면접관입니다.",
    "기술용어": "해시맵을 사용해서 시간복잡도를 O(n)으로 줄일 수 있습니다.",
    "코드질문": "리액트의 useEffect 훅을 설명해주세요.",
    "피드백": "좋은 접근 방법이네요. 다만 엣지 케이스를 고려해보시겠어요?"
}

def test_openai_tts(text, voice, index):
    """OpenAI TTS 테스트"""
    print(f"\n  [OpenAI - {voice}]")
    start_time = time.time()
    
    response = openai_client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=text,
        speed=1.0
    )
    
    latency = time.time() - start_time
    filename = f"openai_{voice}_{index}.mp3"
    response.stream_to_file(filename)
    
    print(f"    ✓ 파일: {filename}")
    print(f"    ⏱️  응답시간: {latency:.2f}초")
    
    return latency

def test_google_tts(text, voice_name, index):
    """Google Cloud TTS 테스트"""
    print(f"\n  [Google - {voice_name}]")
    start_time = time.time()
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name=voice_name
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0.0
    )
    
    response = google_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    latency = time.time() - start_time
    filename = f"google_{voice_name}_{index}.mp3"
    
    with open(filename, "wb") as out:
        out.write(response.audio_content)
    
    print(f"    ✓ 파일: {filename}")
    print(f"    ⏱️  응답시간: {latency:.2f}초")
    
    return latency

def main():
    print("=" * 60)
    print("TTS 비교 테스트 시작")
    print("=" * 60)
    
    # 테스트할 목소리들
    openai_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    google_voices = [
        "ko-KR-Neural2-A",  # 여성 1
        "ko-KR-Neural2-B",  # 남성 1
        "ko-KR-Neural2-C",  # 남성 2
    ]
    
    results = []
    
    for idx, (category, text) in enumerate(test_sentences.items(), 1):
        print(f"\n{'='*60}")
        print(f"테스트 {idx}: [{category}]")
        print(f"문장: {text}")
        print(f"{'='*60}")
        
        # OpenAI 테스트
        for voice in openai_voices:
            latency = test_openai_tts(text, voice, idx)
            results.append({
                'service': 'OpenAI',
                'voice': voice,
                'category': category,
                'latency': latency
            })
            time.sleep(0.5)
        
        # Google 테스트
        for voice in google_voices:
            latency = test_google_tts(text, voice, idx)
            results.append({
                'service': 'Google',
                'voice': voice,
                'category': category,
                'latency': latency
            })
            time.sleep(0.5)
    
    # 결과 요약
    print("\n" + "="*60)
    print("테스트 완료. 결과 요약")
    print("="*60)
    
    # 평균 응답시간
    openai_avg = sum(r['latency'] for r in results if r['service'] == 'OpenAI') / len([r for r in results if r['service'] == 'OpenAI'])
    google_avg = sum(r['latency'] for r in results if r['service'] == 'Google') / len([r for r in results if r['service'] == 'Google'])
    
    print(f"\n평균 응답시간:")
    print(f"  OpenAI: {openai_avg:.2f}초")
    print(f"  Google: {google_avg:.2f}초")
    
    print(f"\n음성 파일 생성 완료")

if __name__ == "__main__":
    main()