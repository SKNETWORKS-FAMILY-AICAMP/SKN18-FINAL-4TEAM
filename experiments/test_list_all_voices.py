import os
from google.cloud import texttospeech_v1beta1 as texttospeech
from dotenv import load_dotenv

load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(
    os.path.dirname(__file__), 
    'google-credentials.json'
)

client = texttospeech.TextToSpeechClient()

print("=" * 80)
print("Google Cloud TTS - 모든 한국어 목소리")
print("=" * 80)

# 한국어 목소리 가져오기
request = texttospeech.ListVoicesRequest(language_code="ko-KR")
response = client.list_voices(request=request)

print(f"\n총 {len(response.voices)}개 발견\n")

# 타입별로 분류
standard = []
wavenet = []
neural2 = []
studio = []
others = []

for voice in response.voices:
    name = voice.name
    if "Standard" in name:
        standard.append(name)
    elif "Wavenet" in name:
        wavenet.append(name)
    elif "Neural2" in name:
        neural2.append(name)
    elif "Studio" in name:
        studio.append(name)
    else:
        others.append(name)

print("📢 Standard 목소리:")
for v in standard:
    print(f"  - {v}")

print("\n🎵 WaveNet 목소리:")
for v in wavenet:
    print(f"  - {v}")

print("\n🤖 Neural2 목소리:")
for v in neural2:
    print(f"  - {v}")

print("\n🎬 Studio 목소리:")
for v in studio:
    print(f"  - {v}")

print("\n⭐ 기타 목소리 (Gemini 포함?):")
for v in others:
    print(f"  - {v}")

print("\n" + "=" * 80)
print("모든 목소리 상세 정보:")
print("=" * 80)

for i, voice in enumerate(response.voices, 1):
    print(f"\n{i}. {voice.name}")
    print(f"   언어: {', '.join(voice.language_codes)}")
    print(f"   성별: {texttospeech.SsmlVoiceGender(voice.ssml_gender).name}")
    print(f"   샘플레이트: {voice.natural_sample_rate_hertz}Hz")