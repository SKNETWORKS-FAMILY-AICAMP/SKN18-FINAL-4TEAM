import os
import time
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ============================================================================
# 프롬프트 전략 정의
# ============================================================================

PROMPTS = {
    "기본": """당신은 친절한 코딩 면접관입니다.
응시자의 질문에 자세하고 도움이 되는 답변을 제공하세요.""",
    
    "짧은첫문장": """당신은 친절한 코딩 면접관입니다.

**중요 규칙:**
1. 첫 문장은 반드시 5-10단어로 매우 짧게 시작하세요
2. 예: "좋은 질문이네요." / "설명드릴게요." / "함께 봐볼까요?"
3. 그 다음 필요한 설명을 이어가세요""",
    
    "단계적구조": """당신은 친절한 코딩 면접관입니다.

**답변 구조:**
1단계: 짧은 공감/인사 (5단어 이내)
2단계: 핵심 포인트 (1-2문장)
3단계: 상세 설명 (필요시만)
4단계: 격려 (1문장)

각 단계를 명확한 마침표(.)로 구분하세요.""",
    
    "초간결": """당신은 친절한 코딩 면접관입니다.

**답변 스타일:**
- 모든 문장을 짧게 끊어 말하세요
- 한 문장에 하나의 아이디어만
- 쉼표(,) 대신 마침표(.) 사용
- 전체 3-4문장으로 제한
- 첫 문장은 특히 짧게!""",
    
    "우선순위": """당신은 친절한 코딩 면접관입니다.

**답변 우선순위:**
최우선: 즉각 반응 (3-5단어만!)
중요: 가장 핵심적인 내용 1가지
선택: 추가 설명 (간단히)
마무리: 격려/제안 (짧게)

전체 답변은 가능한 한 간결하게 하세요."""
}

# ============================================================================
# 생성 방법 정의
# ============================================================================

class Method1Basic:
    """방법 1: 기본 - 전체 답변 후 TTS"""
    
    name = "기본(전체→TTS)"
    
    @staticmethod
    def generate(question, system_prompt):
        start_time = time.time()
        metrics = {
            'llm_time': 0,
            'tts_time': 0,
            'first_audio_time': 0,
            'total_time': 0,
            'audio_files': 0,
            'first_sentence': '',
            'first_sentence_length': 0
        }
        
        # LLM 생성
        llm_start = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content
        metrics['llm_time'] = time.time() - llm_start
        
        # 첫 문장 추출
        first_sent = re.split(r'[.!?]\s+', answer)[0] + '.'
        metrics['first_sentence'] = first_sent
        metrics['first_sentence_length'] = len(first_sent)
        
        # TTS 생성
        tts_start = time.time()
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=answer
        )
        metrics['tts_time'] = time.time() - tts_start
        
        metrics['first_audio_time'] = time.time() - start_time
        metrics['total_time'] = time.time() - start_time
        metrics['audio_files'] = 1
        
        return metrics, answer


class Method2Streaming:
    """방법 2: 문장 단위 스트리밍"""
    
    name = "스트리밍(문장별)"
    
    @staticmethod
    def generate(question, system_prompt):
        start_time = time.time()
        metrics = {
            'llm_time': 0,
            'tts_time': 0,
            'first_audio_time': 0,
            'total_time': 0,
            'audio_files': 0,
            'first_sentence': '',
            'first_sentence_length': 0
        }
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=300
        )
        
        sentence_buffer = ""
        full_answer = ""
        first_sentence_done = False
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_answer += content
                sentence_buffer += content
                
                # 문장 끝 감지
                if re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                    sentence = sentence_buffer.strip()
                    
                    if not first_sentence_done:
                        metrics['llm_time'] = time.time() - start_time
                        metrics['first_sentence'] = sentence
                        metrics['first_sentence_length'] = len(sentence)
                        
                        # 첫 문장 TTS
                        tts_start = time.time()
                        tts_response = client.audio.speech.create(
                            model="tts-1",
                            voice="nova",
                            input=sentence
                        )
                        tts_duration = time.time() - tts_start
                        metrics['tts_time'] += tts_duration
                        
                        metrics['first_audio_time'] = time.time() - start_time
                        first_sentence_done = True
                    else:
                        # 나머지 문장 TTS
                        tts_start = time.time()
                        tts_response = client.audio.speech.create(
                            model="tts-1",
                            voice="nova",
                            input=sentence
                        )
                        metrics['tts_time'] += time.time() - tts_start
                    
                    metrics['audio_files'] += 1
                    sentence_buffer = ""
        
        # 남은 버퍼 처리
        if sentence_buffer.strip():
            metrics['audio_files'] += 1
        
        metrics['total_time'] = time.time() - start_time
        
        return metrics, full_answer


class Method3Optimized:
    """방법 3: 최적화 - 첫 문장 초고속 + 나머지 병렬"""
    
    name = "최적화(첫문장우선)"
    
    @staticmethod
    def generate(question, system_prompt):
        start_time = time.time()
        metrics = {
            'llm_time': 0,
            'tts_time': 0,
            'first_audio_time': 0,
            'total_time': 0,
            'audio_files': 0,
            'first_sentence': '',
            'first_sentence_length': 0
        }
        
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=300
        )
        
        sentence_buffer = ""
        remaining_sentences = []
        full_answer = ""
        first_sentence_done = False
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_answer += content
                sentence_buffer += content
                
                if re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                    sentence = sentence_buffer.strip()
                    
                    if not first_sentence_done:
                        # 첫 문장은 즉시 TTS
                        metrics['llm_time'] = time.time() - start_time
                        metrics['first_sentence'] = sentence
                        metrics['first_sentence_length'] = len(sentence)
                        
                        tts_start = time.time()
                        tts_response = client.audio.speech.create(
                            model="tts-1",
                            voice="nova",
                            input=sentence,
                            speed=1.1  # 약간 빠르게
                        )
                        first_tts_time = time.time() - tts_start
                        metrics['tts_time'] = first_tts_time
                        metrics['first_audio_time'] = time.time() - start_time
                        metrics['audio_files'] = 1
                        
                        first_sentence_done = True
                    else:
                        # 나머지는 모아두기
                        remaining_sentences.append(sentence)
                    
                    sentence_buffer = ""
        
        # 남은 문장 일괄 처리
        if remaining_sentences:
            remaining_text = " ".join(remaining_sentences)
            tts_start = time.time()
            tts_response = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=remaining_text
            )
            metrics['tts_time'] += time.time() - tts_start
            metrics['audio_files'] += 1
        
        metrics['total_time'] = time.time() - start_time
        
        return metrics, full_answer


# ============================================================================
# 테스트 시나리오 정의
# ============================================================================

SCENARIOS = {
    "초단답": {
        "question": "배열의 시간복잡도는?",
        "expected_length": "짧음"
    },
    "짧은설명": {
        "question": "해시맵과 해시테이블의 차이를 간단히 설명해주세요.",
        "expected_length": "짧음"
    },
    "보통설명": {
        "question": "이진 탐색 트리의 특징과 시간복잡도를 설명해주세요.",
        "expected_length": "보통"
    },
    "긴힌트": {
        "question": "투 포인터 알고리즘을 모르겠어요. 자세한 힌트와 예시를 주세요.",
        "expected_length": "긺"
    },
    "문제설명": {
        "question": "동적 프로그래밍 문제입니다. 접근 방법부터 구현 힌트까지 자세히 설명해주세요.",
        "expected_length": "매우 긺"
    }
}

# ============================================================================
# 종합 실험 실행
# ============================================================================

def run_comprehensive_test():
    """프롬프트 × 방법 × 시나리오 종합 테스트"""
    
    print("="*90)
    print("🔬 종합 최적화 실험: 프롬프트 전략 × 생성 방법 × 텍스트 길이")
    print("="*90)
    
    methods = [Method1Basic, Method2Streaming, Method3Optimized]
    
    print(f"\n📋 실험 설계:")
    print(f"  - 프롬프트 전략: {len(PROMPTS)}개")
    print(f"  - 생성 방법: {len(methods)}개")
    print(f"  - 테스트 시나리오: {len(SCENARIOS)}개")
    print(f"  - 총 조합: {len(PROMPTS) * len(methods) * len(SCENARIOS)}개")
    
    all_results = []
    
    for scenario_name, scenario in SCENARIOS.items():
        print(f"\n{'='*90}")
        print(f"📌 시나리오: {scenario_name} (예상 길이: {scenario['expected_length']})")
        print(f"   질문: {scenario['question']}")
        print(f"{'='*90}")
        
        scenario_results = []
        
        for prompt_name, prompt_text in PROMPTS.items():
            print(f"\n  🎯 프롬프트: {prompt_name}")
            print(f"  {'-'*86}")
            
            for method_class in methods:
                print(f"    🔧 방법: {method_class.name} ... ", end="", flush=True)
                
                try:
                    metrics, answer = method_class.generate(
                        scenario['question'],
                        prompt_text
                    )
                    
                    result = {
                        'scenario': scenario_name,
                        'prompt': prompt_name,
                        'method': method_class.name,
                        'first_sentence': metrics['first_sentence'],
                        'first_sentence_length': metrics['first_sentence_length'],
                        'first_audio_time': metrics['first_audio_time'],
                        'total_time': metrics['total_time'],
                        'llm_time': metrics['llm_time'],
                        'tts_time': metrics['tts_time'],
                        'audio_files': metrics['audio_files']
                    }
                    
                    all_results.append(result)
                    scenario_results.append(result)
                    
                    print(f"✅ 첫음성 {metrics['first_audio_time']:.2f}초 "
                          f"(첫문장 {metrics['first_sentence_length']}자)")
                    
                except Exception as e:
                    print(f"❌ 에러: {e}")
                
                time.sleep(0.5)  # API 레이트 제한
        
        # 시나리오별 최고 조합
        if scenario_results:
            best = min(scenario_results, key=lambda x: x['first_audio_time'])
            print(f"\n  🏆 이 시나리오 최고 조합:")
            print(f"     프롬프트: {best['prompt']} + 방법: {best['method']}")
            print(f"     첫 음성: {best['first_audio_time']:.2f}초")
            print(f"     첫 문장: \"{best['first_sentence']}\"")
        
        input(f"\n  [Enter를 눌러 다음 시나리오로...]")
    
    # 최종 분석
    analyze_results(all_results)


def analyze_results(results):
    """결과 종합 분석"""
    
    print("\n" + "="*90)
    print("📊 종합 분석 결과")
    print("="*90)
    
    # 1. 전체 최고 조합
    print("\n1️⃣  전체 최고 성능 조합 (첫 음성 기준)")
    print("-"*90)
    
    best_overall = min(results, key=lambda x: x['first_audio_time'])
    print(f"🏆 시나리오: {best_overall['scenario']}")
    print(f"   프롬프트: {best_overall['prompt']}")
    print(f"   방법: {best_overall['method']}")
    print(f"   첫 음성 시간: {best_overall['first_audio_time']:.2f}초 ⭐")
    print(f"   첫 문장 길이: {best_overall['first_sentence_length']}자")
    print(f"   첫 문장: \"{best_overall['first_sentence']}\"")
    
    # 2. 프롬프트별 평균 성능
    print("\n2️⃣  프롬프트 전략별 평균 성능")
    print("-"*90)
    
    from collections import defaultdict
    prompt_stats = defaultdict(list)
    
    for r in results:
        prompt_stats[r['prompt']].append(r['first_audio_time'])
    
    prompt_avgs = [(p, sum(times)/len(times)) for p, times in prompt_stats.items()]
    prompt_avgs.sort(key=lambda x: x[1])
    
    for i, (prompt, avg_time) in enumerate(prompt_avgs, 1):
        print(f"{i}. {prompt:<20} 평균 {avg_time:.2f}초")
    
    # 3. 생성 방법별 평균 성능
    print("\n3️⃣  생성 방법별 평균 성능")
    print("-"*90)
    
    method_stats = defaultdict(list)
    
    for r in results:
        method_stats[r['method']].append(r['first_audio_time'])
    
    method_avgs = [(m, sum(times)/len(times)) for m, times in method_stats.items()]
    method_avgs.sort(key=lambda x: x[1])
    
    for i, (method, avg_time) in enumerate(method_avgs, 1):
        print(f"{i}. {method:<25} 평균 {avg_time:.2f}초")
    
    # 4. 시나리오별 최적 조합
    print("\n4️⃣  시나리오별 최적 조합")
    print("-"*90)
    
    scenario_best = {}
    for scenario in SCENARIOS.keys():
        scenario_results = [r for r in results if r['scenario'] == scenario]
        if scenario_results:
            best = min(scenario_results, key=lambda x: x['first_audio_time'])
            scenario_best[scenario] = best
    
    for scenario, best in scenario_best.items():
        print(f"\n📌 {scenario}:")
        print(f"   최적: {best['prompt']} + {best['method']}")
        print(f"   성능: {best['first_audio_time']:.2f}초")
    
    # 5. 최종 권장사항
    print("\n" + "="*90)
    print("💡 최종 권장사항")
    print("="*90)
    
    # 가장 일관되게 좋은 조합 찾기
    combination_scores = defaultdict(list)
    
    for r in results:
        key = f"{r['prompt']}+{r['method']}"
        combination_scores[key].append(r['first_audio_time'])
    
    # 평균과 최대값 모두 고려 (일관성)
    combination_quality = []
    for combo, times in combination_scores.items():
        avg = sum(times) / len(times)
        max_time = max(times)
        # 점수 = 평균 + (최대값-평균)*0.3 (일관성 페널티)
        score = avg + (max_time - avg) * 0.3
        combination_quality.append((combo, avg, max_time, score))
    
    combination_quality.sort(key=lambda x: x[3])
    
    best_combo = combination_quality[0]
    prompt, method = best_combo[0].split('+')
    
    print(f"\n🎯 프로덕션 추천 조합:")
    print(f"   프롬프트: {prompt}")
    print(f"   방법: {method}")
    print(f"   평균 첫 음성: {best_combo[1]:.2f}초")
    print(f"   최악의 경우: {best_combo[2]:.2f}초")
    print(f"\n이유:")
    print(f"   - 다양한 시나리오에서 일관되게 우수한 성능")
    print(f"   - 짧은 답변과 긴 답변 모두 빠른 첫 응답")
    print(f"   - 안정적이고 예측 가능한 성능")
    
    # 6. 상세 데이터 테이블
    print("\n" + "="*90)
    print("📋 전체 결과 상세 (첫 음성 시간 기준 정렬)")
    print("="*90)
    
    results.sort(key=lambda x: x['first_audio_time'])
    
    print(f"{'순위':<4} {'시나리오':<12} {'프롬프트':<15} {'방법':<20} "
          f"{'첫음성':>8} {'첫문장':>6} {'총시간':>8}")
    print("-"*90)
    
    for i, r in enumerate(results[:15], 1):  # 상위 15개만
        print(f"{i:<4} {r['scenario']:<12} {r['prompt']:<15} {r['method']:<20} "
              f"{r['first_audio_time']:>6.2f}초 {r['first_sentence_length']:>5}자 "
              f"{r['total_time']:>6.2f}초")
    
    print("\n💾 전체 결과를 CSV로 저장하시겠습니까?")
    save = input("   (y/n): ").lower()
    
    if save == 'y':
        save_results_to_csv(results)


def save_results_to_csv(results):
    """결과를 CSV로 저장"""
    import csv
    
    filename = f"tts_optimization_results_{int(time.time())}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✅ 저장 완료: {filename}")


if __name__ == "__main__":
    print("\n⚠️  이 실험은 약 10-15분 소요됩니다.")
    print("   (5개 프롬프트 × 3개 방법 × 5개 시나리오 = 75개 조합)\n")
    
    confirm = input("시작하시겠습니까? (y/n): ")
    
    if confirm.lower() == 'y':
        run_comprehensive_test()
    else:
        print("실험이 취소되었습니다.")