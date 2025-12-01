from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import base64
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

OPTIMIZED_PROMPT = """당신은 친절한 코딩 면접관입니다.

**답변 구조:**
1단계: 짧은 공감/인사 (5단어 이내)
2단계: 핵심 포인트 (1-2문장)
3단계: 상세 설명 (필요시만)
4단계: 격려 (1문장)

각 단계를 명확한 마침표(.)로 구분하세요."""


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
async def get_html():
    return HTMLResponse(content="""<!DOCTYPE html>
<html>
<head>
    <title>AI 면접관 데모</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:disabled { background: #ccc; }
        #result {
            margin-top: 20px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 5px;
            display: none;
        }
        .sentence {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-left: 3px solid #4CAF50;
        }
        .metric {
            display: inline-block;
            margin: 10px;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 5px;
        }
        audio {
            width: 100%;
            margin: 5px 0;
        }
        #status {
            margin: 10px 0;
            padding: 10px;
            background: #fff3cd;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 AI 면접관 데모</h1>
        
        <input 
            type="text" 
            id="question" 
            placeholder="질문을 입력하세요"
            value="해시맵의 시간복잡도를 설명해주세요"
        >
        
        <button id="askBtn">질문하기</button>
        
        <div id="status" style="display:none;"></div>
        <div id="result"></div>
    </div>

    <script>
        const askBtn = document.getElementById('askBtn');
        const questionInput = document.getElementById('question');
        const statusDiv = document.getElementById('status');
        const resultDiv = document.getElementById('result');
        
        async function askQuestion() {
            const question = questionInput.value;
            
            if (!question.trim()) {
                alert('질문을 입력해주세요!');
                return;
            }
            
            console.log('질문:', question);
            
            // 초기화
            resultDiv.innerHTML = '';
            resultDiv.style.display = 'none';
            statusDiv.style.display = 'block';
            statusDiv.textContent = '면접관이 답변 준비 중...';
            askBtn.disabled = true;
            
            try {
                console.log('API 요청 시작...');
                
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                console.log('응답 상태:', response.status);
                
                if (!response.ok) {
                    throw new Error('서버 응답 에러: ' + response.status);
                }
                
                const data = await response.json();
                console.log('받은 데이터:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                statusDiv.style.display = 'none';
                resultDiv.style.display = 'block';
                
                // 메트릭 표시
                const metricsHTML = `
                    <div class="metric">첫 음성: ${data.first_audio_time.toFixed(2)}초</div>
                    <div class="metric">총 시간: ${data.total_time.toFixed(2)}초</div>
                    <div class="metric">문장 수: ${data.sentences.length}개</div>
                `;
                
                resultDiv.innerHTML = metricsHTML;
                
                // 각 문장 표시
                data.sentences.forEach((item, index) => {
                    const sentenceDiv = document.createElement('div');
                    sentenceDiv.className = 'sentence';
                    
                    const text = document.createElement('div');
                    text.innerHTML = `<strong>#${index + 1}</strong> ${item.text}`;
                    if (index === 0) {
                        text.innerHTML += ' <span style="color: green;">⭐ 첫 음성!</span>';
                    }
                    
                    const audio = document.createElement('audio');
                    audio.controls = true;
                    audio.src = 'data:audio/mp3;base64,' + item.audio;
                    
                    sentenceDiv.appendChild(text);
                    sentenceDiv.appendChild(audio);
                    resultDiv.appendChild(sentenceDiv);
                    
                    // 첫 번째 음성 자동 재생
                    if (index === 0) {
                        setTimeout(() => audio.play(), 100);
                    }
                });
                
            } catch (error) {
                statusDiv.textContent = '에러 발생: ' + error.message;
                statusDiv.style.background = '#f8d7da';
                statusDiv.style.color = '#721c24';
                console.error('Error:', error);
            } finally {
                askBtn.disabled = false;
            }
        }
        
        // 버튼 클릭 이벤트
        askBtn.addEventListener('click', askQuestion);
        
        // Enter 키 지원
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askQuestion();
            }
        });
        
        console.log('페이지 로드 완료!');
    </script>
</body>
</html>""")


@app.post("/api/ask")
async def ask_question(request: QuestionRequest):
    """간단한 질문-응답 API"""
    
    import time
    start_time = time.time()
    
    question = request.question
    print(f"\n[요청] 질문: {question}")
    
    try:
        # LLM 스트리밍
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": OPTIMIZED_PROMPT},
                {"role": "user", "content": question}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=300
        )
        
        sentences = []
        sentence_buffer = ""
        first_audio_time = None
        
        print("[LLM] 스트리밍 시작...")
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                sentence_buffer += content
                
                # 문장 끝 감지
                if re.search(r'[.!?]\s*$', sentence_buffer.strip()):
                    sentence = sentence_buffer.strip()
                    print(f"[문장 {len(sentences)+1}] {sentence}")
                    
                    # TTS 생성
                    tts_response = client.audio.speech.create(
                        model="tts-1",
                        voice="nova",
                        input=sentence
                    )
                    
                    # 첫 음성 시간 기록
                    if first_audio_time is None:
                        first_audio_time = time.time() - start_time
                        print(f"[첫 음성] {first_audio_time:.2f}초")
                    
                    # Base64 인코딩
                    audio_base64 = base64.b64encode(tts_response.content).decode('utf-8')
                    
                    sentences.append({
                        'text': sentence,
                        'audio': audio_base64
                    })
                    
                    sentence_buffer = ""
        
        # 남은 버퍼 처리
        if sentence_buffer.strip():
            sentence = sentence_buffer.strip()
            print(f"[문장 {len(sentences)+1}] {sentence}")
            
            tts_response = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=sentence
            )
            
            if first_audio_time is None:
                first_audio_time = time.time() - start_time
            
            audio_base64 = base64.b64encode(tts_response.content).decode('utf-8')
            
            sentences.append({
                'text': sentence,
                'audio': audio_base64
            })
        
        total_time = time.time() - start_time
        print(f"[완료] 총 시간: {total_time:.2f}초, 문장 수: {len(sentences)}개\n")
        
        return {
            'sentences': sentences,
            'first_audio_time': first_audio_time or 0,
            'total_time': total_time
        }
        
    except Exception as e:
        print(f"[에러] {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': str(e),
            'sentences': [],
            'first_audio_time': 0,
            'total_time': 0
        }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 AI 면접관 데모 서버 시작!")
    print("="*60)
    print("📍 브라우저에서 접속: http://localhost:8000")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")