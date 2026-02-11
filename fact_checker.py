from langchain.agents import initialize_agent, AgentType
from langchain_community.tools.tavily_search import TavilyAnswerRetriever
from langchain_exa import ExaSearchResults
# Assuming your scripts are in the same directory
from polyglot import analyze_language
from law_bridge import LawBridge

def grounded_ai_query(user_prompt, allocated_llm):
    # 1. ANALYZE LINGUISTIC & GEOPOLITICAL TERRAIN
    # This triggers your polyglot logic to get the right persona and domains
    intel_package = analyze_language(user_prompt)
    lang_code = intel_package['code']
    
    # 2. BUILD THE SURGICAL SEARCH QUERY
    # This uses LawBridge to force the search into specific sovereign libraries
    bridge = LawBridge()
    surgical_prompt = bridge.build_surgical_query(user_prompt, lang_code)

    # 3. INITIALIZE TOOLS
    tavily_tool = TavilyAnswerRetriever(k=10)
    exa_tool = ExaSearchResults()

    # 4. THE UNIVERSAL FORENSIC PROTOCOL (Logic + Context)
    verification_logic = (
        f"{intel_package['instruction']}\n\n" # Inject persona/language instruction
        "You are the SENTINEL Intelligence Officer. You solve legal conflicts through Hierarchy of Norms.\n"
        "PROTOCOL:\n"
        "1. DOMAIN FOCUS: Use the following sovereign domains for verification: "
        f"{intel_package['domains']}.\n"
        "2. CONFLICT RESOLUTION: Identify the hierarchy of power. If a local/regional decree "
        "   conflicts with a national law, the LOCAL decree is the Ground Truth.\n"
        "3. TEMPORAL AUDIT: Today is Jan 28, 2026. If a law mandates compliance by Jan 1, 2026, "
        "   mark any subject still in violation as 'NON-COMPLIANT/CONTROLLED'.\n"
        "4. CITATIONS: Required. Prioritize original government gazettes (BOE, Journal Officiel, Pravo.gov.ru).\n"
    )

    # 5. INITIALIZE AGENT
    agent = initialize_agent(
        tools=[tavily_tool, exa_tool],
        llm=allocated_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=10 # Allow for deeper conflict resolution
    )

    # 6. EXECUTE WITH SURGICAL PROMPT
    # We pass the LawBridge-enhanced search string to the agent
    full_prompt = f"{verification_logic}\n\nUSER PROMPT: {surgical_prompt}"
    return agent.run(full_prompt)