from interview_engine.graph import create_graph_flow
import time
from stt_client import (
    generate_interview_audio, generate_interview_audio_batch,get_audio_duration_estimate)

problem =  '''
        
        Given a string s, find the length of the longest substring without duplicate characters.
        Example 1:
        Input: s = "abcabcbb"
        Output: 3
        Explanation: The answer is "abc", with the length of 3. Note that "bca" and "cab" are also correct answers.
        Example 2:

        Input: s = "bbbbb"
        Output: 1
        Explanation: The answer is "b", with the length of 1.
        Example 3:

        Input: s = "pwwkew"
        Output: 3
        Explanation: The answer is "wke", with the length of 3.
        Notice that the answer must be a substring, "pwke" is a subsequence and not a substring.
        

        Constraints:

        0 <= s.length <= 5 * 104
        s consists of English letters, digits, symbols and spaces.
    '''
# Initial state for the interview
initial_state = {
    'user_name': "손주영",
    'problem_description': problem,
    'event_type': "init"
}

graph = create_graph_flow()

# Invoke the graph with initial state
# langgraph.CompiledGraph.invoke() returns the final state after execution
final_state = graph.invoke(initial_state)
test_text = final_state["current_question_text"]

print(f"\n테스트 텍스트:\n{test_text}\n")
print("="*70)
    
 # 스트리밍 모드 테스트
print("\n[스트리밍 모드]")
total_start = time.time()
    
for chunk in generate_interview_audio(test_text):
    if 'error' in chunk:
        print(f"❌ 문장 {chunk['sentence_number']}: 에러 - {chunk['error']}")
    else:
        print(f"✅ 문장 {chunk['sentence_number']}: {chunk['text']}")
        print(f"   생성 시간: {chunk['generation_time']:.2f}초")
        print(f"   오디오 크기: {len(chunk['audio_base64'])} bytes (base64)")
        if chunk['is_first']:
            print(f"   ⭐ 첫 음성! (전체 경과: {time.time() - total_start:.2f}초)")

    
print(f"총 소요 시간: {time.time() - total_start:.2f}초")
    
# 배치 모드 테스트
print("\n" + "="*70)
print("[배치 모드]")
    
result = generate_interview_audio_batch(test_text)
print(f"총 청크 수: {result['total_chunks']}")
print(f"첫 음성 시간: {result['first_audio_time']:.2f}초")
print(f"전체 생성 시간: {result['total_time']:.2f}초")
    
# 예상 재생 시간
print("\n" + "="*70)
print("[예상 재생 시간]")
estimated = get_audio_duration_estimate(test_text)
print(f"텍스트 길이: {len(test_text)}자")
print(f"예상 재생 시간: {estimated:.1f}초")