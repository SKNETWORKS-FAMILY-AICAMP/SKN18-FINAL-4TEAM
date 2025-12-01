import os
import time
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ============================================================================
# 실험 1: 텍스트 길이별 TTS 성능 측정
# ============================================================================

def measure_tts_by_length():
    """다양한 길이의 텍스트에 대한 TTS 응답시간 측정"""
    
    print("="*80)
    print("📏 실험 1: 텍스트 길이별 TTS 응답시간")
    print("="*80)
    
    # 다양한 길이의 텍스트 준비
    test_cases = {
        "초짧음 (1문장)": "좋은 질문이네요.",
        
        "짧음 (2-3문장)": """
해시맵의 평균 시간복잡도는 O(1)입니다. 
해시 함수로 인덱스를 직접 계산하기 때문이죠.
        """.strip(),
        
        "보통 (4-5문장)": """
해시맵의 평균 시간복잡도는 O(1)입니다. 
해시 함수를 통해 키를 인덱스로 변환하여 배열에 직접 접근하기 때문입니다.
하지만 충돌이 발생하면 시간복잡도가 증가할 수 있습니다.
충돌 처리는 체이닝이나 개방 주소법을 사용합니다.
잘 설명해주셨네요!
        """.strip(),
        
        "긴 설명 (면접 힌트 수준)": """
좋은 접근입니다만, 몇 가지 개선할 점을 말씀드리겠습니다.
먼저 엣지 케이스를 고려해보세요. 배열이 비어있는 경우는 어떻게 처리하시겠어요?
또한 시간복잡도 측면에서 중첩 루프를 사용하고 계신데, 이를 해시맵을 활용해서 O(n)으로 줄일 수 있습니다.
구체적으로 말씀드리면, 첫 번째 순회에서 각 요소를 해시맵에 저장하고, 두 번째 순회에서 target에서 현재 값을 뺀 결과가 해시맵에 있는지 확인하는 방식입니다.
이렇게 하면 탐색 시간을 O(1)로 줄일 수 있어요.
한번 시도해보시겠어요?
        """.strip(),
        
        "매우 긴 설명 (문제 설명 수준)": """
지금부터 이진 탐색 트리 문제를 설명드리겠습니다.
주어진 정렬된 배열을 이용해서 높이 균형 이진 탐색 트리를 만드는 문제입니다.
여기서 높이 균형이란 모든 노드에 대해 왼쪽 서브트리와 오른쪽 서브트리의 높이 차이가 1 이하인 것을 의미합니다.
접근 방법은 다음과 같습니다.
먼저 배열의 중간 요소를 루트 노드로 선택합니다.
그런 다음 왼쪽 절반으로 왼쪽 서브트리를, 오른쪽 절반으로 오른쪽 서브트리를 재귀적으로 구성합니다.
이 방법을 사용하면 자동으로 균형 잡힌 트리가 만들어집니다.
시간복잡도는 각 요소를 한 번씩 방문하므로 O(n)이고, 공간복잡도는 재귀 스택 때문에 O(log n)입니다.
이해되셨나요? 질문 있으시면 말씀해주세요.
        """.strip()
    }
    
    results = []
    
    for category, text in test_cases.items():
        char_count = len(text)
        word_count = len(text.split())
        
        print(f"\n{'='*80}")
        print(f"📝 {category}")
        print(f"   글자 수: {char_count}자 | 단어 수: {word_count}개")
        print(f"{'='*80}")
        print(f"텍스트: {text[:100]}..." if len(text) > 100 else f"텍스트: {text}")
        print()
        
        # TTS 생성 시간 측정
        start_time = time.time()
        
        response = client.audio.speech.create(
            model="tts-1",  # 일반 모델
            voice="nova",
            input=text,
            speed=1.0
        )
        
        latency = time.time() - start_time
        
        filename = f"length_test_{category.replace(' ', '_').replace('(', '').replace(')', '')}_{int(time.time())}.mp3"
        
        with open(filename, "wb") as f:
            f.write(response.content)
        
        audio_size = len(response.content)
        
        print(f"⏱️  응답시간: {latency:.2f}초")
        print(f"📦 오디오 크기: {audio_size:,} bytes")
        print(f"📊 초당 글자 수: {char_count/latency:.1f}자/초")
        print(f"📁 파일: {filename}")
        
        results.append({
            'category': category,
            'char_count': char_count,
            'word_count': word_count,
            'latency': latency,
            'audio_size': audio_size,
            'chars_per_sec': char_count/latency
        })
        
        time.sleep(0.5)
    
    # 결과 요약
    print("\n" + "="*80)
    print("📊 텍스트 길이별 TTS 성능 요약")
    print("="*80)
    print(f"{'카테고리':<20} {'글자수':>8} {'응답시간':>10} {'초당글자수':>12}")
    print("-"*80)
    
    for r in results:
        print(f"{r['category']:<20} {r['char_count']:>8}자 {r['latency']:>8.2f}초 {r['chars_per_sec']:>10.1f}자/초")
    
    print("="*80)
    
    # 인사이트
    avg_chars_per_sec = sum(r['chars_per_sec'] for r in results) / len(results)
    print(f"\n💡 인사이트:")
    print(f"   - 평균 처리 속도: {avg_chars_per_sec:.1f}자/초")
    print(f"   - 1초 이내 응답을 위한 최대 글자수: 약 {avg_chars_per_sec:.0f}자")
    print(f"   - 3초 이내 응답을 위한 최대 글자수: 약 {avg_chars_per_sec*3:.0f}자")
    
    return results


# ============================================================================
# 실험 2: 프롬프트 최적화 (긴 답변에서도 빠른 첫 응답)
# ============================================================================

def test_prompt_strategies():
    """다양한 프롬프트 전략 비교"""
    
    print("\n\n" + "="*80)
    print("🎯 실험 2: 프롬프트 최적화 전략 비교")
    print("="*80)
    
    test_question = "이진 탐색 트리에서 특정 값을 찾는 알고리즘을 설명하고, 힌트를 주세요."
    
    strategies = {
        "기본 (최적화 없음)": {
            "system": """당신은 친절한 코딩 면접관입니다.
응시자의 질문에 자세하고 도움이 되는 답변을 제공하세요.""",
            "description": "일반적인 프롬프트"
        },
        
        "전략 1: 짧은 첫 문장 강제": {
            "system": """당신은 친절한 코딩 면접관입니다.

**중요 규칙:**
1. 첫 문장은 반드시 10단어 이내로 짧게 시작하세요
2. 예: "좋은 질문이네요." / "설명드리겠습니다." / "천천히 살펴볼까요?"
3. 그 다음 자세한 설명을 이어가세요""",
            "description": "첫 문장을 의도적으로 짧게"
        },
        
        "전략 2: 단계적 설명 구조": {
            "system": """당신은 친절한 코딩 면접관입니다.

**답변 구조:**
1. 짧은 인사/공감 (1문장)
2. 핵심 개념 요약 (1-2문장)
3. 구체적 설명 (필요시)
4. 격려/후속 제안 (1문장)

각 단계를 명확한 문장으로 구분하세요.""",
            "description": "구조화된 단계별 답변"
        },
        
        "전략 3: 대화형 스타일": {
            "system": """당신은 친절한 코딩 면접관입니다.

**답변 스타일:**
- 대화하듯 자연스럽게 답변하세요
- 짧은 문장들을 사용하세요
- 문장마다 쉼표(,)보다 마침표(.)를 선호하세요
- "~입니다.", "~해요.", "~할까요?" 형태로 끊어서 말하세요""",
            "description": "짧은 문장 중심 대화체"
        },
        
        "전략 4: 우선순위 명시": {
            "system": """당신은 친절한 코딩 면접관입니다.

**답변 우선순위:**
1순위: 즉각적인 반응/공감 표현 (매우 짧게!)
2순위: 가장 중요한 핵심 1-2가지만
3순위: 상세 설명은 필요시에만

전체 답변은 3-4문장으로 제한하세요.""",
            "description": "핵심 우선, 간결함 강조"
        }
    }
    
    results = []
    
    for strategy_name, config in strategies.items():
        print(f"\n{'='*80}")
        print(f"🧪 {strategy_name}")
        print(f"   {config['description']}")
        print(f"{'='*80}\n")
        
        total_start = time.time()
        
        # LLM 스트리밍
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": config["system"]},
                {"role": "user", "content": test_question}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=300
        )
        
        full_response = ""
        sentence_buffer = ""
        first_sentence = None
        first_sentence_time = None
        first_audio_time = None
        sentence_count = 0
        
        print("🎤 면접관: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
                sentence_buffer += content
                
                # 첫 문장 감지
                if first_sentence is None and re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                    first_sentence = sentence_buffer.strip()
                    first_sentence_time = time.time() - total_start
                    
                    # 첫 문장 TTS 생성
                    tts_start = time.time()
                    tts_response = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=first_sentence,
                        speed=1.0
                    )
                    first_tts_time = time.time() - tts_start
                    first_audio_time = time.time() - total_start
                    
                    filename = f"prompt_{strategy_name.replace(' ', '_').replace(':', '')}_{int(time.time())}.mp3"
                    with open(filename, "wb") as f:
                        f.write(tts_response.content)
                    
                    print(f"\n\n  ⚡ 첫 문장: \"{first_sentence}\"")
                    print(f"     글자 수: {len(first_sentence)}자")
                    print(f"     LLM 생성: {first_sentence_time:.2f}초")
                    print(f"     TTS 생성: {first_tts_time:.2f}초")
                    print(f"     총 시간: {first_audio_time:.2f}초 ⭐")
                    print(f"     파일: {filename}")
                    print("\n🎤 면접관: ", end="", flush=True)
                    
                    sentence_buffer = ""
                    sentence_count = 1
                
                elif re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                    sentence_count += 1
                    sentence_buffer = ""
        
        total_time = time.time() - total_start
        
        print(f"\n\n  📊 전체 문장 수: {sentence_count}개")
        print(f"  ⏱️  총 소요 시간: {total_time:.2f}초\n")
        
        results.append({
            'strategy': strategy_name,
            'first_sentence': first_sentence,
            'first_sentence_length': len(first_sentence) if first_sentence else 0,
            'first_audio_time': first_audio_time,
            'total_sentences': sentence_count,
            'total_time': total_time
        })
        
        time.sleep(1)
    
    # 결과 비교
    print("\n" + "="*80)
    print("📊 프롬프트 전략 성능 비교")
    print("="*80)
    print(f"{'전략':<30} {'첫문장길이':>12} {'첫음성시간':>12} {'총문장수':>10}")
    print("-"*80)
    
    for r in results:
        print(f"{r['strategy']:<30} {r['first_sentence_length']:>10}자 "
              f"{r['first_audio_time']:>10.2f}초 {r['total_sentences']:>8}개")
    
    print("="*80)
    
    # 최고 전략 찾기
    fastest = min(results, key=lambda x: x['first_audio_time'] if x['first_audio_time'] else 999)
    shortest_first = min(results, key=lambda x: x['first_sentence_length'] if x['first_sentence_length'] else 999)
    
    print(f"\n🏆 최고 전략:")
    print(f"   - 가장 빠른 첫 음성: {fastest['strategy']} ({fastest['first_audio_time']:.2f}초)")
    print(f"   - 가장 짧은 첫 문장: {shortest_first['strategy']} ({shortest_first['first_sentence_length']}자)")
    
    print(f"\n💡 권장 프롬프트:")
    print(f"   {fastest['strategy']}")
    
    return results


# ============================================================================
# 실험 3: 최적화된 전략 실전 테스트
# ============================================================================

def production_test(strategy_prompt):
    """실전 면접 시나리오 테스트"""
    
    print("\n\n" + "="*80)
    print("🎯 실험 3: 실전 면접 시나리오 테스트")
    print("="*80)
    
    scenarios = [
        {
            "type": "짧은 질문",
            "question": "배열과 링크드 리스트의 차이는?"
        },
        {
            "type": "코드 리뷰 피드백",
            "question": "제 코드를 봐주세요. for 루프를 두 번 중첩해서 사용했는데 괜찮을까요?"
        },
        {
            "type": "긴 힌트 요청",
            "question": "동적 프로그래밍 문제인데 접근 방법을 모르겠어요. 자세한 힌트 주세요."
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"📌 시나리오: {scenario['type']}")
        print(f"질문: {scenario['question']}")
        print(f"{'='*80}\n")
        
        total_start = time.time()
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": strategy_prompt},
                {"role": "user", "content": scenario['question']}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=300
        )
        
        sentence_buffer = ""
        first_audio_time = None
        
        print("🎤 면접관: ", end="", flush=True)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                sentence_buffer += content
                
                if first_audio_time is None and re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                    tts_start = time.time()
                    tts_response = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=sentence_buffer.strip()
                    )
                    
                    first_audio_time = time.time() - total_start
                    
                    print(f"\n\n  ⚡ 첫 음성: {first_audio_time:.2f}초")
                    print("🎤 면접관: ", end="", flush=True)
                    
                    sentence_buffer = ""
        
        print(f"\n\n  ⏱️  총 시간: {time.time() - total_start:.2f}초\n")
        
        input("[Enter를 눌러 다음 시나리오...]")


# ============================================================================
# 전체 실험 실행
# ============================================================================

def run_all_experiments():
    """모든 실험 순차 실행"""
    
    print("\n" + "="*80)
    print("🔬 TTS 길이 & 프롬프트 최적화 종합 실험")
    print("="*80)
    print("\n실험 구성:")
    print("  1️⃣  텍스트 길이별 TTS 응답시간 측정")
    print("  2️⃣  프롬프트 최적화 전략 비교")
    print("  3️⃣  최적 전략으로 실전 테스트")
    print("\n" + "="*80)
    
    # 실험 1
    input("\n[Enter를 눌러 실험 1 시작...]")
    length_results = measure_tts_by_length()
    
    # 실험 2
    input("\n[Enter를 눌러 실험 2 시작...]")
    prompt_results = test_prompt_strategies()
    
    # 최적 전략 선택
    best_strategy = min(prompt_results, key=lambda x: x['first_audio_time'] if x['first_audio_time'] else 999)
    
    # 실험 3
    print(f"\n💡 실험 3에서는 '{best_strategy['strategy']}' 전략을 사용합니다.")
    input("\n[Enter를 눌러 실험 3 시작...]")
    
    # 최적 프롬프트 하드코딩 (실험 2 결과 기반으로 수정 가능)
    optimized_prompt = """당신은 친절한 코딩 면접관입니다.

**중요 규칙:**
1. 첫 문장은 반드시 10단어 이내로 짧게 시작하세요
2. 예: "좋은 질문이네요." / "설명드리겠습니다." / "천천히 살펴볼까요?"
3. 그 다음 자세한 설명을 이어가세요"""
    
    production_test(optimized_prompt)
    
    # 최종 결론
    print("\n" + "="*80)
    print("🎉 실험 완료! 최종 권장사항")
    print("="*80)
    print(f"\n✅ 추천 TTS 모델: OpenAI TTS-1 (nova)")
    print(f"✅ 추천 프롬프트 전략: {best_strategy['strategy']}")
    print(f"✅ 예상 첫 음성 응답시간: {best_strategy['first_audio_time']:.2f}초")
    print(f"\n💡 긴 설명이 필요한 경우:")
    print(f"   - 첫 문장을 매우 짧게 유지 (10자 이내)")
    print(f"   - 문장 단위 스트리밍으로 즉시 TTS 생성")
    print(f"   - 사용자는 전체 답변을 기다리지 않고 바로 음성 청취 시작")
    print("\n" + "="*80)


if __name__ == "__main__":
    run_all_experiments()