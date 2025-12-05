# tts 모듈 프론트에서 부르기

프론트에서

* **엔드포인트**: `POST http://localhost:8000/api/interview/ask/`

* **바디**:

  ```json
  {
    "question": "DFS랑 BFS 차이를 설명해주세요."
  }
  ```

* **응답**:

  ```json
  {
    "question": "...",
    "answer": "면접관 전체 답변 텍스트...",
    "sentences": [
      { "text": "첫 문장...", "audio": "<base64 mp3>" },
      { "text": "두 번째 문장...", "audio": "<base64 mp3>" }
    ],
    "first_audio_time": 1.9,
    "total_time": 3.4
  }
  ```

오디오는:

```js
const src = `data:audio/mp3;base64,${sentence.audio}`;
const audio = new Audio(src);
audio.play();
```

이렇게 재생하면 됩니다.
