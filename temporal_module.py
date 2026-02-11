import requests
import datetime
import os

def get_global_dynamic_context(user_ip):
    """Fetches real-time location and uses Tavily to find local legal status."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")

    try:
        # 1. Get Geo-location from IP
        geo_res = requests.get(f"http://ip-api.com/json/{user_ip}").json()
        location = f"{geo_res.get('city', 'Unknown')}, {geo_res.get('country', 'Global')}"
        
        # 2. Check for active legal holidays via Tavily (Keyless/Integrated)
        search_url = "https://api.tavily.com/search"
        search_query = f"official court holidays and closures in {location} for {date_str}"
        
        resp = requests.post(search_url, json={
            "api_key": tavily_key,
            "query": search_query,
            "search_depth": "basic"
        }).json()
        
        holiday_data = resp.get('results', [{}])[0].get('content', 'No specific holiday closures reported.')

        return f"""
        [DYNAMIC_GLOBAL_CONTEXT]
        CURRENT_SESSION_TIME: {date_str}
        USER_GEOGRAPHIC_LOCATION: {location}
        LOCAL_LEGAL_CALENDAR_STATUS: {holiday_data[:200]}
        [END_CONTEXT]
        """
    except Exception:
        return f"[DYNAMIC_CONTEXT_FALLBACK] Date: {date_str}. Location: Global (UTC)."