import streamlit as st
import uuid
import os
import tempfile

from Backend.Services.stt_service import transcribe_audio
from Backend.Services.rag_service import get_context
from Backend.Services.llm_service import generate_response
from Backend.Services.tts_service import text_to_speech


st.set_page_config(
    page_title="Voice Assistant",
    page_icon="🎙️",
    layout="centered",
)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

.main .block-container {
    max-width: 680px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
}

/* ── Header ── */
.va-header {
    text-align: center;
    margin-bottom: 2.5rem;
}
.va-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0 0 4px;
}
.va-header p {
    font-size: 0.78rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.45;
    margin: 0;
}

/* ── Pipeline steps ── */
.step-row {
    display: flex;
    align-items: center;
    gap: 0;
    justify-content: center;
    margin-bottom: 2.5rem;
    flex-wrap: wrap;
    gap: 4px;
}
.step-pill {
    font-size: 0.7rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.08em;
    padding: 4px 12px;
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,0.25);
    opacity: 0.4;
    transition: all 0.3s;
}
.step-pill.active {
    opacity: 1;
    border-color: #4f8ef7;
    color: #4f8ef7;
    background: rgba(79,142,247,0.08);
}
.step-pill.done {
    opacity: 0.7;
    border-color: rgba(79,247,130,0.5);
    color: #3dd68c;
    background: rgba(79,247,130,0.06);
}
.step-arrow {
    font-size: 0.65rem;
    opacity: 0.25;
    margin: 0 2px;
}

/* ── Upload zone label ── */
.upload-label {
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    opacity: 0.5;
    margin-bottom: 0.4rem;
}

/* ── Result cards ── */
.result-card {
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1rem;
    background: rgba(255,255,255,0.02);
}
.card-label {
    font-size: 0.68rem;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    opacity: 0.4;
    margin-bottom: 0.5rem;
}
.card-text {
    font-size: 1rem;
    line-height: 1.65;
    font-weight: 400;
}

/* ── Context expander ── */
.context-block {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.7;
    opacity: 0.7;
    white-space: pre-wrap;
}

/* ── Error ── */
.va-error {
    border: 1px solid rgba(226,75,74,0.4);
    background: rgba(226,75,74,0.06);
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    font-size: 0.85rem;
    font-family: 'DM Mono', monospace;
    color: #e24b4a;
    margin-top: 1rem;
}

/* ── Spinner override ── */
.stSpinner > div {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="va-header">
    <h1>🎙️ Voice Assistant</h1>
    <p>E-commerce support · RAG + LLM + TTS</p>
</div>
""", unsafe_allow_html=True)


if "pipeline_step" not in st.session_state:
    st.session_state.pipeline_step = 0   # 0=idle 1=stt 2=rag 3=llm 4=tts 5=done
if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None
if "context" not in st.session_state:
    st.session_state.context = None

# ─────────────────────────────────────────
# PIPELINE STATUS BAR
# ─────────────────────────────────────────
def step_class(idx):
    s = st.session_state.pipeline_step
    if s == 0:
        return "step-pill"
    if idx < s:
        return "step-pill done"
    if idx == s:
        return "step-pill active"
    return "step-pill"

steps = ["STT", "RAG", "LLM", "TTS"]
pills_html = ""
for i, label in enumerate(steps, start=1):
    pills_html += f'<span class="{step_class(i)}">{label}</span>'
    if i < len(steps):
        pills_html += '<span class="step-arrow">→</span>'

st.markdown(f'<div class="step-row">{pills_html}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# AUDIO INPUT
# ─────────────────────────────────────────
st.markdown('<p class="upload-label">Upload or record your voice query</p>', unsafe_allow_html=True)

audio_input = st.audio_input("Record a voice message")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader(
        "Or upload a WAV / MP3 file",
        type=["wav", "mp3", "m4a", "ogg", "webm"],
        label_visibility="collapsed"
    )
with col2:
    run_btn = st.button("▶ Process", use_container_width=True, type="primary")

# ─────────────────────────────────────────
# DETERMINE AUDIO SOURCE
# ─────────────────────────────────────────
audio_source = audio_input or uploaded_file

# ─────────────────────────────────────────
# PROCESS PIPELINE
# ─────────────────────────────────────────
if run_btn:
    if not audio_source:
        st.markdown('<div class="va-error">⚠ Please record or upload an audio file first.</div>', unsafe_allow_html=True)
    else:
        st.session_state.error = None
        st.session_state.result = None
        st.session_state.context = None

        # Write audio to a temp file
        suffix = ".wav"
        if hasattr(audio_source, "name") and audio_source.name:
            ext = os.path.splitext(audio_source.name)[-1]
            suffix = ext if ext else ".wav"

        tmp_path = os.path.join(tempfile.gettempdir(), f"va_input_{uuid.uuid4().hex}{suffix}")
        with open(tmp_path, "wb") as f:
            f.write(audio_source.read() if hasattr(audio_source, "read") else audio_source.getvalue())

        try:
            # ── Step 1: STT ──────────────────────────
            st.session_state.pipeline_step = 1
            with st.spinner("🎤 Transcribing audio…"):
                query_text = transcribe_audio(tmp_path)

            # ── Step 2: RAG ──────────────────────────
            st.session_state.pipeline_step = 2
            with st.spinner("📚 Retrieving context…"):
                context = get_context(query_text)
                st.session_state.context = context

            # ── Step 3: LLM ──────────────────────────
            st.session_state.pipeline_step = 3
            with st.spinner("🤖 Generating response…"):
                response_text = generate_response(query_text, context)

            # ── Step 4: TTS ──────────────────────────
            st.session_state.pipeline_step = 4
            with st.spinner("🔊 Synthesising speech…"):
                audio_out_path = text_to_speech(response_text)

            st.session_state.pipeline_step = 5
            st.session_state.result = {
                "query": query_text,
                "response": response_text,
                "audio_path": audio_out_path,
            }

        except Exception as e:
            st.session_state.error = str(e)
            st.session_state.pipeline_step = 0
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        st.rerun()

# ─────────────────────────────────────────
# ERROR DISPLAY
# ─────────────────────────────────────────
if st.session_state.error:
    st.markdown(f'<div class="va-error">❌ {st.session_state.error}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    st.markdown("---")

    # You asked
    st.markdown(f"""
    <div class="result-card">
        <div class="card-label">You asked</div>
        <div class="card-text">{r['query']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Response
    st.markdown(f"""
    <div class="result-card">
        <div class="card-label">Response</div>
        <div class="card-text">{r['response']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Audio player
    st.markdown('<div class="result-card"><div class="card-label">Audio response (gTTS)</div>', unsafe_allow_html=True)
    if os.path.exists(r["audio_path"]):
        with open(r["audio_path"], "rb") as af:
            audio_bytes = af.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
    else:
        st.warning("Audio file not found.")
    st.markdown('</div>', unsafe_allow_html=True)

    # RAG context (collapsed)
    if st.session_state.context:
        with st.expander("🔍 Retrieved RAG context"):
            st.markdown(f'<div class="context-block">{st.session_state.context}</div>', unsafe_allow_html=True)