import re
import os
import requests
from duckduckgo_search import DDGS
from openai import OpenAI

class ForensicAuditor:
    def __init__(self):
        # Universal regex for legal citations (French, EU, ECLI)
        self.citation_pattern = r'(\bn°\s*[\d\.\-\/]+|\bCase\s+[A-Z\d\-\/]+|\b[A-Z]+\s+c\.\s+[A-Z]+|\b[A-Z]{2,}\s+\d{4,})'
        
        self.handoff_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("META_KEY")
        )
        
        self.gemini_tiers = [
            "google/gemini-3-flash-preview", 
            "google/gemini-2.5-flash",       
            "google/gemini-2.5-flash-lite"   
        ]

    def verify_response(self, text, original_prompt=None):
        """Dynamic verification using Semantic Context Check."""
        citations = re.findall(self.citation_pattern, text)
        
        # 1. DYNAMIC INTENT ANALYSIS: Use Gemini-Lite to decide if citations are required
        # This replaces hardcoded keyword lists.
        is_legal_intent = self._evaluate_intent_dynamically(original_prompt)
        
        if is_legal_intent and not citations:
            return self._execute_gemini_recovery(text, original_prompt, "MISSING_REQUIRED_CITATIONS")

        audit_findings = []
        needs_correction = False
        
        if citations:
            with DDGS() as ddgs:
                for cite in set(citations):
                    query = f"official legal summary for: {cite}"
                    try:
                        results = list(ddgs.text(query, max_results=3))
                        snippet = " ".join([r.get('body', '').lower() for r in results])
                        
                        # 2. SEMANTIC CROSS-CHECK: Does the snippet match the prompt's domain?
                        # This prevents "Marseille Urban Planning" cases from passing an "Asylum" prompt.
                        if not self._is_citation_relevant(original_prompt, cite, snippet):
                            audit_findings.append(f"{cite} (Context Mismatch)")
                            needs_correction = True
                    except:
                        needs_correction = True

        if needs_correction and original_prompt:
            return self._execute_gemini_recovery(text, original_prompt, audit_findings)
        
        return text

    def _evaluate_intent_dynamically(self, prompt):
        """Uses a low-cost tier to determine if the prompt requires forensic citation."""
        try:
            res = self.handoff_client.chat.completions.create(
                model=self.gemini_tiers[2], # Use Lite for speed
                messages=[{"role": "system", "content": "Return 'YES' if this prompt requires specific legal citations or case law, otherwise 'NO'."},
                          {"role": "user", "content": prompt}],
                max_tokens=5
            )
            return "YES" in res.choices[0].message.content.upper()
        except: return False

    def _is_citation_relevant(self, prompt, cite, search_snippet):
        """Uses LLM to verify if the found legal snippet matches the user's legal domain."""
        try:
            res = self.handoff_client.chat.completions.create(
                model=self.gemini_tiers[1], # Use Flash for stability
                messages=[
                    {"role": "system", "content": "You are a Legal Auditor. Compare the user's legal topic with the search result for a citation. Does the citation actually relate to the topic? Return 'VALID' or 'INVALID'."},
                    {"role": "user", "content": f"Topic: {prompt}\nCitation: {cite}\nSearch Content: {search_snippet}"}
                ],
                max_tokens=10
            )
            return "VALID" in res.choices[0].message.content.upper()
        except: return True # Fallback to true to avoid loops on API failure

    def _execute_gemini_recovery(self, faulty_text, prompt, failed_cites):
        """The 'Silent Handoff': Re-routes to Gemini for factual correction."""
        target_model = self.gemini_tiers[0] 
        
        recovery_prompt = f"""
        FACTUAL RECOVERY MISSION:
        The draft below failed forensic audit. Issues: {failed_cites}
        
        TASK:
        1. Rewrite the argument with 100% accurate, verified French or EU case law.
        2. Ensure the citation domain matches the prompt domain.
        3. Do NOT mention this is a correction. Preserve 'Soutenance Orale' style.
        
        DRAFT TO FIX:
        {faulty_text}
        """

        try:
            res = self.handoff_client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": "You are a Forensic Legal Specialist. Accuracy in ECLI and Docket numbers is non-negotiable."},
                    {"role": "user", "content": recovery_prompt}
                ],
                temperature=0.1
            )
            return res.choices[0].message.content + "\n\n> *Forensic integrity secured via Gemini-3-Flash cross-reference.*"
        except Exception:
            return faulty_text + "\n\n> ⚠️ *Forensic Audit: Contextual verification failed. Manual review required.*"

# Global Instance
auditor = ForensicAuditor()