# 🎙️ Voice RAG Assistant — Streamlit

**Author:** Kirti Gowda

A voice-driven e-commerce support assistant using:

- **Whisper** (STT) → **ChromaDB + SentenceTransformers** (RAG) → **Gemini 2.5 Flash** (LLM) → **gTTS** (TTS)

---

## 📁 Project Structure

```
project_root/
│
├── streamlit.py                    ← Streamlit frontend (run this)
│
├── Backend/
│   ├── Services/
│   │   ├── stt_service.py          ← Whisper transcription
│   │   ├── rag_service.py          ← ChromaDB retrieval
│   │   ├── llm_service.py          ← Gemini response generation
│   │   └── tts_service.py          ← gTTS speech synthesis
│   │
│   ├── Rag_Pipeline/
│   │   ├── embed.py                ← Load orders.json + policies.json
│   │   ├── index.py                ← Build & search ChromaDB index
│   │   └── chroma_db/              ← Vector database storage
│   │
│   ├── controllers/
│   │   └── query_controllers.py
│   │
│   ├── routes/
│   │   └── query.py
│   │
│   ├── data/
│   │   ├── orders.json
│   │   └── policies.json
│   │
│   ├── main.py                     ← (Optional FastAPI backend)
│   └── live_test.py
│
├── requirements.txt
├── .env                            ← GEMINI_API_KEY=your_key_here
└── README.md
```

---

## ⚙️ Setup

### 1. Create a Virtual Environment (Recommended)

```bash
python -m venv voiceenv
source voiceenv/bin/activate   # macOS/Linux
voiceenv\Scripts\activate      # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Add Your Gemini API Key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Build the ChromaDB Index *(Run once)*

```bash
python -m Backend.Rag_Pipeline.index
```

### 5. Run the Streamlit App

```bash
streamlit run streamlit.py
```

---

## 🚀 How It Works

1. Record your voice query or upload an audio file
2. Click **▶ Process**
3. The pipeline executes:
   - 🎤 **STT** — Whisper converts speech → text
   - 📚 **RAG** — ChromaDB retrieves relevant documents
   - 🤖 **LLM** — Gemini generates a response
   - 🔊 **TTS** — gTTS converts the response → audio
4. Results are displayed along with an auto-playing audio response

---

## 🧠 Architecture

Streamlit directly calls backend services:

```
UI (Streamlit)
      ↓
STT → RAG → LLM → TTS
      ↓
Response + Audio Output
```

---

## ⚠️ Notes

- Ensure `__init__.py` exists inside:
  ```
  Backend/
  Backend/Services/
  ```
  *(Required for imports to work)*

- `tts_service.py` saves audio in the temp directory (`tempfile.gettempdir()`)

- **Whisper model options:**
  | Model | Speed | Accuracy |
  |-------|-------|----------|
  | `base` | Fast | Lower |
  | `small` | Medium | Better |
  | `medium` | Slower | Best |

- `main.py` (FastAPI) is optional — not required for the Streamlit version

---

## 🔥 Future Improvements

- [ ] Replace gTTS with **ElevenLabs** for more realistic voice output
- [ ] Add **chat history + memory** support
- [ ] Convert backend into **FastAPI** for production use
- [ ] Deploy on **Render / AWS / HuggingFace Spaces**