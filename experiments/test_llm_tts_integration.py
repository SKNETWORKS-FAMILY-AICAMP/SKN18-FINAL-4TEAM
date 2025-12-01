import os
import time
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 공통 시스템 프롬프트
SYSTEM_PROMPT = """당신은 따뜻하고 정중한 코딩 면접관입니다.
- 친절하지만 전문적인 톤으로 답변하세요
- 기술 용어를 정확하게 사용하세요
- 응시자를 격려하면서 피드백하세요
- 2-3문장으로 간결하게 답변하세요"""

# 테스트 질문
TEST_QUESTION = "해시맵의 시간복잡도와 충돌 처리 방법에 대해 설명해주세요."

class PerformanceMetrics:
    """성능 측정 헬퍼"""
    
    def __init__(self, method_name):
        self.method_name = method_name
        self.llm_time = 0
        self.tts_time = 0
        self.total_time = 0
        self.first_audio_time = 0  # 첫 음성까지 걸린 시간
        self.audio_files = []
        
    def print_results(self):
        print(f"\n{'='*70}")
        print(f"📊 [{self.method_name}] 성능 결과")
        print(f"{'='*70}")
        print(f"  LLM 응답 시간:        {self.llm_time:.2f}초")
        print(f"  TTS 생성 시간:        {self.tts_time:.2f}초")
        print(f"  총 소요 시간:         {self.total_time:.2f}초")
        if self.first_audio_time > 0:
            print(f"  첫 음성까지 시간:     {self.first_audio_time:.2f}초 ⭐")
        print(f"  생성된 음성 파일 수:  {len(self.audio_files)}개")
        print(f"{'='*70}\n")


# ============================================================================
# 방법 1: 기본 방식 (전체 답변 → TTS)
# ============================================================================

def method1_basic(question, voice="nova"):
    """방법 1: 기본 - LLM 전체 답변 후 TTS"""
    
    metrics = PerformanceMetrics("방법 1: 기본")
    
    print(f"\n{'='*70}")
    print(f"방법 1: 기본 방식 테스트")
    print(f"{'='*70}")
    print(f"질문: {question}\n")
    
    total_start = time.time()
    
    # 1. LLM 답변 생성
    print("🤖 LLM 답변 생성 중...")
    llm_start = time.time()
    
    llm_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=300
    )
    
    answer_text = llm_response.choices[0].message.content
    metrics.llm_time = time.time() - llm_start
    
    print(f"✅ LLM 완료 ({metrics.llm_time:.2f}초)")
    print(f"\n면접관: {answer_text}\n")
    
    # 2. TTS 변환
    print("🔊 음성 생성 중...")
    tts_start = time.time()
    
    tts_response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=answer_text,
        speed=1.0
    )
    
    metrics.tts_time = time.time() - tts_start
    
    filename = f"method1_basic_{int(time.time())}.mp3"
    tts_response.stream_to_file(filename)
    metrics.audio_files.append(filename)
    
    print(f"✅ TTS 완료 ({metrics.tts_time:.2f}초)")
    print(f"📁 저장: {filename}")
    
    metrics.total_time = time.time() - total_start
    metrics.first_audio_time = metrics.total_time
    
    metrics.print_results()
    return metrics


# ============================================================================
# 방법 2: 문장 단위 스트리밍
# ============================================================================

def split_sentences(text):
    """텍스트를 문장으로 분리"""
    sentences = re.split(r'([.!?]\s+)', text)
    result = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sentence = (sentences[i] + sentences[i+1]).strip()
            if sentence:
                result.append(sentence)
    # 마지막 문장 처리
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    return result

def method2_sentence_streaming(question, voice="nova"):
    """방법 2: 문장 단위 스트리밍 - LLM 스트림 + 문장별 즉시 TTS"""
    
    metrics = PerformanceMetrics("방법 2: 문장 스트리밍")
    
    print(f"\n{'='*70}")
    print(f"방법 2: 문장 단위 스트리밍 테스트")
    print(f"{'='*70}")
    print(f"질문: {question}\n")
    
    total_start = time.time()
    
    # LLM 스트리밍
    print("🤖 LLM 스트리밍 시작...\n")
    llm_start = time.time()
    
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        stream=True,
        temperature=0.7,
        max_tokens=300
    )
    
    full_response = ""
    sentence_buffer = ""
    sentence_count = 0
    first_audio_generated = False
    
    print("면접관: ", end="", flush=True)
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            
            full_response += content
            sentence_buffer += content
            
            # 문장 끝 감지
            if re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                sentence = sentence_buffer.strip()
                
                if not first_audio_generated:
                    metrics.llm_time = time.time() - llm_start
                
                # 즉시 TTS 생성
                tts_start = time.time()
                
                tts_response = client.audio.speech.create(
                    model="tts-1",  # 속도를 위해 tts-1
                    voice=voice,
                    input=sentence,
                    speed=1.0
                )
                
                tts_duration = time.time() - tts_start
                metrics.tts_time += tts_duration
                
                sentence_count += 1
                filename = f"method2_sentence_{sentence_count}_{int(time.time())}.mp3"
                tts_response.stream_to_file(filename)
                metrics.audio_files.append(filename)
                
                if not first_audio_generated:
                    metrics.first_audio_time = time.time() - total_start
                    first_audio_generated = True
                    print(f"\n\n⚡ 첫 음성 생성! ({metrics.first_audio_time:.2f}초)")
                
                print(f"\n  → 문장 {sentence_count} 음성 생성 완료 ({tts_duration:.2f}초): {filename}")
                print("면접관: ", end="", flush=True)
                
                sentence_buffer = ""
    
    # 남은 버퍼 처리
    if sentence_buffer.strip():
        tts_start = time.time()
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=sentence_buffer.strip(),
            speed=1.0
        )
        tts_duration = time.time() - tts_start
        metrics.tts_time += tts_duration
        
        sentence_count += 1
        filename = f"method2_sentence_{sentence_count}_{int(time.time())}.mp3"
        tts_response.stream_to_file(filename)
        metrics.audio_files.append(filename)
        print(f"\n  → 문장 {sentence_count} 음성 생성 완료 ({tts_duration:.2f}초): {filename}")
    
    print("\n")
    metrics.total_time = time.time() - total_start
    
    metrics.print_results()
    return metrics


# ============================================================================
# 방법 3: 병렬 처리 (LLM 완료 후 문장별 병렬 TTS)
# ============================================================================

def method3_parallel_tts(question, voice="nova"):
    """방법 3: 병렬 처리 - LLM 완료 후 문장별로 TTS 동시 생성"""
    
    metrics = PerformanceMetrics("방법 3: 병렬 TTS")
    
    print(f"\n{'='*70}")
    print(f"방법 3: 병렬 TTS 처리 테스트")
    print(f"{'='*70}")
    print(f"질문: {question}\n")
    
    total_start = time.time()
    
    # 1. LLM 답변 생성
    print("🤖 LLM 답변 생성 중...")
    llm_start = time.time()
    
    llm_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        temperature=0.7,
        max_tokens=300
    )
    
    answer_text = llm_response.choices[0].message.content
    metrics.llm_time = time.time() - llm_start
    
    print(f"✅ LLM 완료 ({metrics.llm_time:.2f}초)")
    print(f"\n면접관: {answer_text}\n")
    
    # 2. 문장 분리
    sentences = split_sentences(answer_text)
    print(f"📝 {len(sentences)}개 문장으로 분리\n")
    
    # 3. 각 문장을 순차적으로 TTS 생성 (실제 병렬은 threading 필요)
    print("🔊 문장별 TTS 생성 중...")
    tts_start = time.time()
    
    for i, sentence in enumerate(sentences, 1):
        sentence_tts_start = time.time()
        
        tts_response = client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=sentence,
            speed=1.0
        )
        
        sentence_tts_time = time.time() - sentence_tts_start
        
        filename = f"method3_parallel_{i}_{int(time.time())}.mp3"
        tts_response.stream_to_file(filename)
        metrics.audio_files.append(filename)
        
        if i == 1:
            metrics.first_audio_time = time.time() - total_start
        
        print(f"  [{i}/{len(sentences)}] {sentence_tts_time:.2f}초 - {filename}")
        time.sleep(0.1)
    
    metrics.tts_time = time.time() - tts_start
    metrics.total_time = time.time() - total_start
    
    print()
    metrics.print_results()
    return metrics


# ============================================================================
# 전체 비교 실행
# ============================================================================

def run_all_tests():
    """3가지 방법 모두 테스트하고 비교"""
    
    print("\n" + "="*70)
    print("🎯 LLM + TTS 통합 성능 비교 테스트")
    print("="*70)
    print(f"테스트 질문: {TEST_QUESTION}")
    print(f"TTS 모델: tts-1-hd (방법1, 3), tts-1 (방법2)")
    print(f"TTS 목소리: nova")
    print("="*70)
    
    results = []
    
    # 방법 1
    input("\n[Enter를 눌러 방법 1 시작...]")
    result1 = method1_basic(TEST_QUESTION)
    results.append(result1)
    time.sleep(2)
    
    # 방법 2
    input("\n[Enter를 눌러 방법 2 시작...]")
    result2 = method2_sentence_streaming(TEST_QUESTION)
    results.append(result2)
    time.sleep(2)
    
    # 방법 3
    input("\n[Enter를 눌러 방법 3 시작...]")
    result3 = method3_parallel_tts(TEST_QUESTION)
    results.append(result3)
    
    # 최종 비교
    print("\n" + "="*70)
    print("📊 최종 성능 비교")
    print("="*70)
    print(f"{'방법':<20} {'총 시간':<12} {'첫 음성':<12} {'LLM':<10} {'TTS':<10} {'파일수':<8}")
    print("-"*70)
    
    for r in results:
        print(f"{r.method_name:<20} {r.total_time:>8.2f}초  {r.first_audio_time:>8.2f}초  "
              f"{r.llm_time:>6.2f}초  {r.tts_time:>6.2f}초  {len(r.audio_files):>4}개")
    
    print("="*70)
    
    # 추천
    fastest_total = min(results, key=lambda x: x.total_time)
    fastest_first = min(results, key=lambda x: x.first_audio_time)
    
    print("\n🏆 추천:")
    print(f"  - 가장 빠른 총 시간:       {fastest_total.method_name}")
    print(f"  - 가장 빠른 첫 음성 응답:  {fastest_first.method_name}")
    print(f"\n💡 실시간 면접에는 '{fastest_first.method_name}'을 추천합니다!")
    print("   (사용자가 가장 빨리 음성을 들을 수 있음)\n")
    
    # 생성된 파일 정리
    print("📁 생성된 파일:")
    all_files = []
    for r in results:
        all_files.extend(r.audio_files)
    
    print(f"  총 {len(all_files)}개 음성 파일 생성")
    print("  - method1_*.mp3 : 방법 1")
    print("  - method2_*.mp3 : 방법 2")
    print("  - method3_*.mp3 : 방법 3")


if __name__ == "__main__":
    run_all_tests()