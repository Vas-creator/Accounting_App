import streamlit as st
from openai import OpenAI

def get_ai_response(user_query: str, client_context: str = "") -> str:
    """AI ကို မေးခွန်းမေးပြီး အဖြေယူတဲ့ Function"""
    try:
        # Streamlit Secrets ကနေ API Key ကို ယူမယ်
        api_key = st.secrets["OPENAI_API_KEY"]
        client = OpenAI(api_key=api_key)
        
        system_prompt = f"""
        သင်သည် မြန်မာနိုင်ငံသား စာရင်းကိုင် ကျွမ်းကျင်သူတစ်ဦး ဖြစ်သည်။
        သင်သည် ရိုးရှင်းပြီး နားလည်လွယ်သော မြန်မာစကားဖြင့် ပြန်လည်ဖြေကြားရမည်။
        အောက်ပါ ဖောက်သည်အချက်အလက်များကို အသုံးပြု၍ မေးခွန်းများကို ဖြေကြားပါ။
        
        ဖောက်သည်အချက်အလက်:
        {client_context}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ AI Error: {e}"