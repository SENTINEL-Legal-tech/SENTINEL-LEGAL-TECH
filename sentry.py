import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class SentinelSentry:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("❌ SENTRY ERROR: Credentials missing from .env")
            self.db = None
        else:
            try:
                self.db = create_client(url, key)
                print("🛡️ SENTRY: Database connection established.")
            except Exception as e:
                print(f"❌ SENTRY: Connection failed: {e}")
                self.db = None

        self.banners = {"BLACKOUT": False, "RED": False, "YELLOW": False, "GREEN": False}

    def analyze_prompt_dynamic(self, prompt, client, user_id="USER_01"):
        advisory = ""
        p_lower = prompt.lower()
        
        # --- 1. NLP CLASSIFICATION ---
        sentry_prompt = f"""
        [SECURITY OVERRIDE] Classify intent as RED, BLACKOUT, YELLOW, or CLEAR.
        - BLACKOUT: Violence, weapons, courthouse threats, killing, harm.
        - RED: Suicide, car engine in garage, pills, ending life.
        - YELLOW: Stalking, tracking, hacking, privacy breach.
        - CLEAR: Legal research, forensics, benign talk.
        User: "{prompt}"
        Response: [CATEGORY ONLY]
        """
        try:
            response = client.chat.completions.create(
                model="google/gemini-2.0-flash-lite:free",
                messages=[{"role": "system", "content": "ONE WORD ONLY: RED, BLACKOUT, YELLOW, or CLEAR."},
                          {"role": "user", "content": sentry_prompt}],
                temperature=0
            )
            classification = response.choices[0].message.content.strip().upper()

            # --- APPENDED: CATCH THE SAFETY LECTURE ---
            # If Gemini returns a paragraph instead of one word, it's a hard refusal block.
            if len(classification.split()) > 3:
                classification = "BLACKOUT"
                
        except:
            # --- APPENDED: FAIL-SAFE FOR BLOCKED API ---
            classification = "BLACKOUT" if any(word in p_lower for word in ["9mm", "kill", "weapon", "shoot", "attack"]) else "CLEAR"

        # --- 2. HARD-CODED REINFORCEMENT (If NLP Fails) ---
        # BLACKOUT KEYWORDS
        if any(word in p_lower for word in ["weapon", "gun", "kill", "shoot", "attack", "courthouse", "9mm"]):
            classification = "BLACKOUT"
        # YELLOW KEYWORDS 
        elif any(word in p_lower for word in ["track", "hack", "gps", "ex-wife", "ex-husband", "spy"]):
            classification = "YELLOW"
        # RED KEYWORDS
        elif "engine" in p_lower and ("garage" in p_lower or "running" in p_lower):
            classification = "RED"

        # --- 3. MANDATORY LOGGING & BANNERS ---
        if classification in ["RED", "BLACKOUT", "YELLOW"]:
            print(f"⚠️ SENTRY TRIGGERED: {classification}. Attempting SQL Log...")
            self._execute_sql_log(user_id, prompt, classification)

            if classification == "BLACKOUT" and not self.banners["BLACKOUT"]:
                advisory = "**CRITICAL ADVISORY: THIS SESSION IS UNDER FORENSIC REVIEW.**"
                self.banners["BLACKOUT"] = True
            elif classification == "RED" and not self.banners["RED"]:
                advisory = "**⚠️ URGENT NOTICE: Please reach out for help. Call/Text 988 (US).**"
                self.banners["RED"] = True
            elif classification == "YELLOW" and not self.banners["YELLOW"]:
                advisory = "**🟡 ADVISORY: Ethical/Privacy boundary detected. Actions are logged.**"
                self.banners["YELLOW"] = True

        return classification, advisory

    def _execute_sql_log(self, user_id, prompt, level):
        if not self.db:
            print(f"❌ SQL LOG FAILED: DB Client is None.")
            return
        try:
            payload = {"user_id": user_id, "log_level": level, "prompt_text": prompt}
            response = self.db.table("security_logs").insert(payload).execute()
            if response.data:
                print(f"✅ SQL LOG SUCCESS: {level}")
        except Exception as e:
            print(f"❌ SQL LOG ERROR: {str(e)}")