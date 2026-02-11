import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Use your normal Anon Key
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def test_recall_feature():
    # Since security is off, we can just make up a name
    DEV_USER = "MAC_TEST_001"
    
    print(f"🚀 Testing Recall for: {DEV_USER}")
    try:
        # 1. Save a Memory
        print("✍️ Saving a forensic observation...")
        supabase.table("chat_history").insert({
            "user_id": DEV_USER,
            "role": "user",
            "content": "Observation: The encrypted volume was mounted at 02:00 AM."
        }).execute()

        # 2. Recall: Ask the cloud for EVERYTHING for this user
        print("🔍 Searching Cloud Memory...")
        response = supabase.table("chat_history") \
            .select("content") \
            .eq("user_id", DEV_USER) \
            .execute()

        print("\n📜 SENTINEL's Recovered Memories:")
        for row in response.data:
            print(f"- {row['content']}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_recall_feature()
