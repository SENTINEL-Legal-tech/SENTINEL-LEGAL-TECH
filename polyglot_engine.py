from langdetect import detect
import logging

# --- CULTURAL & LINGUISTIC MAPPING ---
LANGUAGE_CONFIG = {
    'ru': {"name": "Russian", "greeting": "Братан", "persona": "Forensic Analyst (Analitik)"},
    'fr': {"name": "French", "greeting": "Mon pote", "persona": "Architecte Stratégique"},
    'es': {"name": "Spanish", "greeting": "Compadre", "persona": "Arquitecto Estratégico"},
    'zh': {"name": "Chinese", "greeting": "兄弟 (Xiōngdì)", "persona": "战略架构师 (Zhànlüè jiàgòushī)"},
    'de': {"name": "German", "greeting": "Alter", "persona": "Strategischer Architekt"},
    'it': {"name": "Italian", "greeting": "Frà", "persona": "Architetto Strategico"},
    'pt': {"name": "Portuguese", "greeting": "Parceiro", "persona": "Arquiteto Estratégico"},
    'ja': {"name": "Japanese", "greeting": "相棒 (Aibō)", "persona": "戦略アーキテクト"},
    'ko': {"name": "Korean", "greeting": "형씨 (Hyeong-ssi)", "persona": "전략 설계자"},
    'he': {"name": "Hebrew", "greeting": "Ach sheli", "persona": "Adrichal Estrategi"},
    'nl': {"name": "Dutch", "greeting": "Maat", "persona": "Strategisch Architect"}
}

# --- GEOPOLITICAL DOMAIN MAPPING ---
# This ensures that when a language is detected, we prioritize localized legal sources.
DOMAIN_MAP = {
    'ru': "consultant.ru, garant.ru, sudact.ru",
    'fr': "legifrance.gouv.fr, courdecassation.fr",
    'es': "boe.es, vlex.es, derechocomparado.ad",
    'de': "gesetze-im-internet.de, bundesverfassungsgericht.de",
    'it': "normattiva.it, gazzettaufficiale.it",
    'nl': "overheid.nl, rechtspraak.nl",
    'zh': "court.gov.cn, npc.gov.cn"
}

def analyze_language(text):
    """
    Detects language and returns a package of cultural metadata 
    to inject into the SENTINEL system prompt.
    """
    try:
        # Detect the primary language of the input
        lang_code = detect(text).split('-')[0] # Normalize (e.g., 'zh-cn' -> 'zh')
        
        config = LANGUAGE_CONFIG.get(lang_code, {
            "name": "English", 
            "greeting": "My guy", 
            "persona": "Strategic Intelligence Architect"
        })
        
        # Pull the specialized legal domains for that region
        local_domains = DOMAIN_MAP.get(lang_code, "justia.com, law.cornell.edu")
        
        return {
            "code": lang_code,
            "name": config["name"],
            "domains": local_domains,
            "instruction": f"STRICT: Speak only in {config['name']}. Use the greeting '{config['greeting']}' and maintain the persona of a {config['persona']}. Mirror the cultural nuances of a 'Real One' in {config['name']}."
        }
    except Exception as e:
        logging.error(f"Detection failed: {e}")
        return {
            "code": "en",
            "name": "English",
            "domains": "justia.com, law.cornell.edu",
            "instruction": "Speak in English. Maintain your standard persona."
        }