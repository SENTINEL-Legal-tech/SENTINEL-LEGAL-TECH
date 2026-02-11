import os
from supabase import create_client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup Clients
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def sentinel_think(user_id, current_question):
    # 1. FETCH MEMORIES FROM SQL
    print(f"🔍 SENTINEL is accessing vault for {user_id}...")
    memories = supabase.table("chat_history") \
        .select("content") \
        .eq("user_id", user_id) \
        .limit(5) \
        .execute()
    
    # Flatten the memories into a single string
    past_context = "\n".join([f"- {m['content']}" for m in memories.data])
    
    # 2. BUILD THE PROMPT WITH HISTORY
    system_instruction = f"""
    You are SENTINEL, a world-class digital forensics AI. 
    You have access to the following past observations from this case:
    {past_context}
    
    Use these past observations to inform your current analysis.
    """

    # 3. GET AI RESPONSE
    print("🧠 SENTINEL is analyzing...")
    response = ai_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": current_question}
        ]
    )

    return response.choices[0].message.content

# --- TEST THE BRAIN ---
if __name__ == "__main__":
    question = "Based on what we found at 02:00 AM, what should I look for next in the system logs?"
    answer = sentinel_think("MAC_TEST_001", question)
    
    print("\n🕵️ SENTINEL'S ANALYSIS:")
    print(answer)