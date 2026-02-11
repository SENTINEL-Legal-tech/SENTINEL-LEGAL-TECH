import os
import sys
import hashlib
import streamlit as st
import requests
import time
import re
import json
import concurrent.futures
import io
import numpy as np
from datetime import datetime
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
from langsmith import traceable

# AI & FORENSIC IMPORTS
from textblob import TextBlob
from duckduckgo_search import DDGS
from supabase.client import create_client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# CUSTOM MODULES
import polyglot_engine as pg
from law_bridge import LawBridge
import sentinel_failover
from forensics_audit import auditor
import temporal_module
import sentry

# --- START APPLICATION LOGIC ---
load_dotenv()

# Key Retrieval from .env - NO HARDCODING
GEMINI_KEY = os.getenv("GEMINI_KEY")
META_KEY = os.getenv("META_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

os.environ["LANGCHAIN_PROJECT"] = "SENTINEL-CORE-PRO"
st.set_page_config(page_title="SENTINEL | Strategic Architect", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500&display=swap');
    .stApp { background-color: #131314; color: #E3E3E3; }
    [data-testid="stSidebar"] { background-color: #1e1f20 !important; border-right: 1px solid #333; }
    html, body, [class*="st-"], .stMarkdown, p, div, span, [data-testid="stChatMessageContent"] p { 
        font-family: 'Lucida Sans', 'Lexend', sans-serif !important;
        font-size: 0.92rem; 
    }
    [data-testid="stStatusWidget"], [data-testid="stNotification"], .st-emotion-cache-16idsys p {
        visibility: hidden !important; height: 0px !important; display: none !important;
    }
    [data-testid="stChatMessageAvatarBackground"], [data-testid="stChatMessageAvatarCustom"],
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        display: none !important;
    }
    @keyframes persistent-pulse {
        0% { box-shadow: 0 0 0 0px rgba(138, 180, 248, 0.4); }
        100% { box-shadow: 0 0 0 10px rgba(138, 180, 248, 0); }
    }
    .active-indicator {
        width: 10px; height: 10px; background: #8ab4f8; border-radius: 50%;
        display: inline-block; margin-left: 10px; animation: persistent-pulse 2s infinite;
    }
    .monitor-box { background: #1e1f20; border: 1px solid #333; border-radius: 8px; padding: 12px; margin-bottom: 20px; }
    .monitor-label { font-size: 0.7rem; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .monitor-value { font-family: monospace; color: #8ab4f8; font-size: 0.9rem; }
    .model-active { color: #00ff88; font-size: 0.65rem; margin-left: 5px; }
    
    @keyframes blink { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
    
    @keyframes lang-cycle {
        0%, 8% { content: "Sentinel is initializing and ready for your command"; }
        9%, 16% { content: "Sentinel est en cours d'initialisation et prêt"; }
        17%, 24% { content: "Sentinel wird initialisiert und ist bereit"; }
        25%, 32% { content: "Sentinel se está inicializando y está listo"; }
        33%, 40% { content: "Sentinel инициализируется и готов"; }
        41%, 48% { content: "Sentinel 正在初始化并准备就绪"; }
        49%, 56% { content: "Sentinel يتم تهيئته وجאהز"; }
        57%, 64% { content: "Sentinel इनिशואलाइज़ हो रहा है और तैयार है"; }
        65%, 72% { content: "Sentinel está sendo inicializado e está pronto"; }
        73%, 80% { content: "Sentinel は初期化中で準備ができています"; }
        81%, 100% { content: "Sentinel è in fase di inizializzazione ed è pronto"; }
    }
    .init-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 100px; text-align: center; }
    .init-text-natural { font-size: 1.2rem; color: #E3E3E3; font-weight: 300; animation: blink 3s infinite; }
    .init-text-natural::after { content: ""; animation: lang-cycle 35s infinite; }
    .init-pulse { width: 40px; height: 40px; border: 2px solid #8ab4f8; border-radius: 50%; margin-bottom: 20px; animation: persistent-pulse 2s infinite; }
    
    [data-testid="stFileUploader"] { background-color: transparent; border: none; padding: 0px; }
    .forensic-hash { font-family: monospace; font-size: 0.65rem; color: #444; margin-top: 8px; border-top: 1px solid #333; padding-top: 4px; }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from user"]) [data-testid="stChatMessageContent"] {
        background-color: #2b2c2e !important; border-radius: 18px !important; padding: 10px 16px !important; margin-left: 15% !important; color: #FFFFFF !important;
    }
    div[data-testid="stChatMessage"]:has(div[aria-label="Chat message from assistant"]) [data-testid="stChatMessageContent"] {
        border-left: 1px solid #8ab4f8 !important; padding-left: 20px !important; margin-right: 5% !important; width: 85% !important;
    }
    .thinking-text { color: #8ab4f8; font-family: monospace; font-size: 0.75rem; padding-left: 20px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def generate_forensic_hash(content):
    return hashlib.sha256(str(content).encode()).hexdigest()

@st.cache_data(ttl=3600)
def search_web(query):
    if not TAVILY_KEY: return ""
    try:
        url = "https://api.tavily.com/search"
        payload = {"api_key": TAVILY_KEY, "query": f"{query} current status 2026", "search_depth": "advanced", "max_results": 6}
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            return "\n\n".join([r['content'] for r in res.json().get('results', [])])
    except: pass
    return ""

# --- MAIN LOGIC ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "direct_context" not in st.session_state: st.session_state.direct_context = "" 

@st.fragment(run_every=1)
def show_temporal_status():
    now = datetime.now()
    ts = now.strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="monitor-box">
        <div class="monitor-label">Temporal Sync</div>
        <div class="monitor-value">{ts}<span class="active-indicator"></span></div>
        <div class="monitor-label" style="margin-top:5px;">Cycle Refresh</div>
        <div class="monitor-value" style="font-size:0.7rem; color:#ff4b4b;">T-MINUS {60 - now.second}s</div>
    </div>
    """, unsafe_allow_html=True)

@traceable(run_type="llm", name="SENTINEL Analysis")
def run_query(prompt, _unused_model):
    intel_package = pg.analyze_language(prompt)
    bridge = LawBridge()
    surgical_prompt = bridge.build_surgical_query(prompt, intel_package['code'])
    
    local_context = st.session_state.direct_context 
    external_context = search_web(surgical_prompt)
    current_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    system_instruction = f"""
    SYSTEM: SENTINEL STRATEGIC ARCHITECT. 
    CURRENT DATE/TIME: {current_ts}
    USER: Mark. 
    GUIDELINE: Use RAG (Docket) and Real-Time Intel for forensic synthesis.
    DOCKET: {local_context if local_context else "No local files uploaded."}
    INTEL: {external_context if external_context else "No live search results available."}
    """

    # --- TIER 1: GOOGLE AI STUDIO PRIMARY ---
    google_targets = ["gemini-3-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash"]
    for model_id in google_targets:
        try:
            g_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_KEY}"
            g_res = requests.post(g_url, json={"contents": [{"parts": [{"text": f"{system_instruction}\n\n{surgical_prompt}"}]}]}, timeout=12)
            if g_res.status_code == 200:
                return g_res.json()['candidates'][0]['content']['parts'][0]['text']
        except: continue

    # --- TIER 2: OPENROUTER SECONDARY ---
    or_targets = ["google/gemini-3-flash", "google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]
    for or_id in or_targets:
        try:
            or_url = "https://openrouter.ai/api/v1/chat/completions"
            or_headers = {
                "Authorization": f"Bearer {META_KEY}",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "SENTINEL-STRATEGIC"
            }
            or_payload = {
                "model": or_id,
                "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": surgical_prompt}]
            }
            or_res = requests.post(or_url, headers=or_headers, json=or_payload, timeout=12)
            if or_res.status_code == 200:
                return or_res.json()['choices'][0]['message']['content']
        except: continue

    # --- TIER 3: EMERGENCY BACKUP ---
    try:
        return sentinel_failover.sentinel_backup(prompt)
    except:
        return "CRITICAL: Logic Bridge Offline. Strategic Insights Unavailable."

# --- APP RENDER ---
with st.sidebar:
    show_temporal_status()

st.title("SENTINEL")
st.caption("Strategic Intelligence Architect")
st.divider()

if not st.session_state.chat_history:
    st.markdown("""<div class="init-container"><div class="init-pulse"></div><div class="init-text-natural"></div></div>""", unsafe_allow_html=True)

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            st.markdown(f'<div class="forensic-hash">SHA-256: {generate_forensic_hash(m["content"])}</div>', unsafe_allow_html=True)

col1, col2 = st.columns([0.1, 0.9])
with col1: st.markdown("<div style='font-size: 1.2rem; padding-top: 5px;'>➕</div>", unsafe_allow_html=True)
with col2: uploaded_file = st.file_uploader("ACCESS DOCKET", type=['pdf'], label_visibility="collapsed")

if uploaded_file:
    try:
        pdf_stream = io.BytesIO(uploaded_file.getvalue())
        reader = PdfReader(pdf_stream)
        st.session_state.direct_context = "".join([p.extract_text() for p in reader.pages])
        st.success("DOCKET SYNCHRONIZED")
    except Exception as e: st.error(f"Read Error: {e}")

if prompt := st.chat_input("Engage..."):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        thinking = st.empty()
        thinking.markdown('<div class="thinking-text">Negotiating Intelligence Bridge...</div>', unsafe_allow_html=True)
        response = run_query(prompt, None)
        thinking.empty()
        st.markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})