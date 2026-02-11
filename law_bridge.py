# law_bridge.py - The Sentinel Sovereign Legal Engine

class LawBridge:
    def __init__(self):
        # Jurisdictional "Powerhouse" Repositories (All Areas of Law)
        self.MASTER_LIBRARIES = {
            "USA": "site:law.cornell.edu OR site:courtlistener.com OR site:scholar.google.com",
            "UK": "site:legislation.gov.uk OR site:caselaw.nationalarchives.gov.uk OR site:bailii.org",
            "CANADA": "site:canlii.org", # Multilingual (EN/FR)
            "EU": "site:eur-lex.europa.eu", # Multilingual (FR/DE/ES/IT/NL/PT)
            "AUSTRALIA": "site:austlii.edu.au OR site:hcourt.gov.au"
        }

        # Language-Specific Sovereign Libraries
        self.SOVEREIGN_LIBRARIES = {
            "ru": "site:pravo.gov.ru OR site:court.gov.by OR site:etalonline.by",
            "fr": "site:legifrance.gouv.fr OR site:justice.gc.ca",
            "es": "site:boe.es OR site:scjn.gob.mx OR site:pjn.gov.ar",
            "zh": "site:court.gov.cn OR site:npc.gov.cn",
            "de": "site:gesetze-im-internet.de OR site:ris.bka.gv.at",
            "it": "site:normattiva.it OR site:cortecostituzionale.it"
        }

    def build_surgical_query(self, prompt, lang_code):
        """Builds a real-time retrieval string targeting global law libraries."""
        p_lower = prompt.lower()
        
        # 1. Start with the Base Prompt
        final_query = prompt
        
        # 2. Detect Master Jurisdictions (USA, UK, Canada, AU, EU)
        target_filters = []
        if any(w in p_lower for w in ["usa", "us ", "america", "supreme court"]):
            target_filters.append(self.MASTER_LIBRARIES["USA"])
        if any(w in p_lower for w in ["uk ", "united kingdom", "london", "high court"]):
            target_filters.append(self.MASTER_LIBRARIES["UK"])
        if "canada" in p_lower:
            target_filters.append(self.MASTER_LIBRARIES["CANADA"])
        if any(w in p_lower for w in ["eu ", "european union", "brussels", "euro"]):
            target_filters.append(self.MASTER_LIBRARIES["EU"])
        if any(w in p_lower for w in ["australia", "au court", "sydney"]):
            target_filters.append(self.MASTER_LIBRARIES["AUSTRALIA"])

        # 3. Apply Language-Specific Filters (Only if no Master is detected or for cross-ref)
        if not target_filters:
            if lang_code in self.SOVEREIGN_LIBRARIES:
                target_filters.append(self.SOVEREIGN_LIBRARIES[lang_code])

        # 4. Construct Final Search Dork
        if target_filters:
            # Join filters with OR and wrap in parentheses
            combined_sites = " OR ".join(target_filters)
            final_query = f"({combined_sites}) {prompt}"
        
        return final_query