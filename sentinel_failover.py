import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Initialize environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_KEY")

class SentinelFailover:
    def __init__(self):
        self.client = None
        # UPDATED MODEL POOL FOR 2026: 
        # Using current aliases to avoid 404 errors as older 1.5 versions retire.
        self.model_pool = [
            'gemini-3-flash-preview',  # Most advanced intelligence/speed
            'gemini-2.5-flash',        # High-stability stable tier
            'gemini-2.5-flash-lite'    # Maximum speed / Lowest cost
        ]
        
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                st.error(f"Failover Init Error: {e}")

    def execute_backup(self, prompt, system_instruction, history):
        if not self.client:
            return "🚨 **FAILOVER CRITICAL:** GEMINI_KEY missing or client failed."

        # APPENDED LOGIC: Vibe-matching directive. 
        # MODIFICATION: Explicitly blacklisting the string "my guy" from the greeting.
        vibe_check = (
            "\n\n[SENTIMENT PROTOCOL]: Pay close attention to the user's energy and tone in the chat history. "
            "Mirror their energy level precisely. If they are in a clinical/professional zone, maintain it. "
            "If they are informal, match it. "
            "CRITICAL: Do not start responses with the phrase 'my guy' or use it as a filler. "
            "Only use informal greetings if the user has used them in the immediate preceding prompt."
        )
        
        # We append the vibe_check to your original system_instruction
        adaptive_instruction = system_instruction + vibe_check

        # Convert history format for Gemini SDK
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
            )
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        # --- FALLBACK LOOP ---
        last_error = ""
        for model_id in self.model_pool:
            try:
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=adaptive_instruction,
                        temperature=0.4
                    )
                )
                
                # If we get here, the model worked!
                audit_label = f"\n\n> 🧩 **SENTINEL ACTIVE:** Routed via `{model_id}`."
                return response.text + audit_label

            except Exception as e:
                last_error = str(e)
                # If the error is a 404 (model name changed) or 429 (quota), try the next one.
                if "429" in last_error or "404" in last_error or "503" in last_error:
                    continue 
                else:
                    break 

        return f"**TOTAL SYSTEM BLACKOUT:** All failover models exhausted. \nLast Error: `{last_error}`"

# Create the instance
sentinel_backup = SentinelFailover()