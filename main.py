import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from gtts import gTTS
from io import BytesIO
from PIL import Image
import google.generativeai as genai
import datetime
import json
import time
import random

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="NutriScan AI",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUN UI & CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #262730;
    }
    
    /* GLASS CARDS */
    .glass-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        color: white;
    }
    
    /* FEATURE CARDS (HOME) */
    .feature-box {
        background: #1e1e1e;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #333;
        transition: transform 0.3s;
    }
    .feature-box:hover {
        transform: scale(1.05);
        border-color: #00E676;
    }
    
    /* FUN METRICS */
    div[data-testid="stMetricValue"] {
        background: -webkit-linear-gradient(45deg, #FFEB3B, #00E676);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* BUTTONS */
    .stButton>button {
        background: linear-gradient(90deg, #FF512F 0%, #DD2476 100%);
        color: white;
        border-radius: 12px;
        border: none;
        height: 50px;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(221, 36, 118, 0.4); }
    
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
defaults = {
    'page': 'Home',
    'food_log': [],
    'scan_data': None,
    'api_key': '',
    'active_model': None,
    'daily_goal': 2000,
    'bmi': 0.0,
    'chat_history': [],
    'user_diet': 'Balanced',
    'water_ml': 0,
    'recipe_result': None # Added to keep recipes persistent
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# --- 4. SMART CONNECTION LOGIC (UPDATED FOR V3 & V2.5) ---
def connect_to_best_model(key):
    try:
        genai.configure(api_key=key)
        
        # Priority List: Tries Gemini 3 first, then 2.5, then 2.0, then 1.5
        candidates = [
            "gemini-3.0-pro",
            "gemini-3.0-flash",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash", 
            "gemini-2.0-flash-exp", 
            "gemini-1.5-pro", 
            "gemini-1.5-flash"
        ]
        
        # Get list of what this key can actually access from Google
        # We strip the 'models/' prefix to match our list
        available_models = [m.name.replace("models/", "") for m in genai.list_models()]
        
        # Find best match
        selected = None
        for c in candidates:
            # Check if the candidate string exists inside any of the available model names
            if any(c in m for m in available_models):
                selected = c
                break
        
        # Fallback if list_models fails but key is valid
        if not selected: selected = "gemini-1.5-flash"
        
        # Final Verification Test
        model = genai.GenerativeModel(selected)
        model.generate_content("test")
        return selected
    except Exception as e:
        # If specific selection fails, try generic 1.5 as last resort
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            model.generate_content("test")
            return "gemini-1.5-flash"
        except:
            return None

# --- 5. CORE LOGIC ---
def analyze_image(image):
    try:
        if not st.session_state['active_model']: return {"error": "Link Key First 🔑"}
        genai.configure(api_key=st.session_state['api_key'])
        model = genai.GenerativeModel(st.session_state['active_model'])
        prompt = """
        Analyze this food. Return raw JSON ONLY.
        Keys: "name", "cals" (int), "carbs" (float), "prot" (float), "fat" (float), 
        "desc" (fun summary), "benefits" (emoji bullet points), "harm" (emoji bullet points).
        """
        response = model.generate_content([prompt, image])
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e: return {"error": str(e)}

def get_recipes(food, diet):
    try:
        # CRITICAL FIX: Re-authenticate inside the function to prevent "Napping" error
        genai.configure(api_key=st.session_state['api_key']) 
        model = genai.GenerativeModel(st.session_state['active_model'])
        
        response = model.generate_content(f"Suggest 3 yummy {diet} recipes using {food} as the main ingredient. Use emojis and keep it short.")
        return response.text
    except Exception as e: 
        return f"Chef is napping 😴"

def chat_ai(query, context):
    try:
        genai.configure(api_key=st.session_state['api_key'])
        model = genai.GenerativeModel(st.session_state['active_model'])
        return model.generate_content(f"Context: {context}. User: {query}").text
    except: return "Connection error."

# --- 6. NAVIGATION & SIDEBAR ---
with st.sidebar:
    st.markdown("## 🥑 NutriScan AI")
    
    # NAVIGATION MENU
    st.write("---")
    st.markdown("### 🧭 Menu")
    page = st.radio("Go to:", ["🏠 Home & Health", "📸 Scan & Eat", "📊 My Diary"], label_visibility="collapsed")
    st.session_state['page'] = page
    st.write("---")

    # 1. CONNECT
    if not st.session_state['active_model']:
        with st.expander("🔑 Connect AI", expanded=True):
            key = st.text_input("API Key", type="password")
            if st.button("Link Key"):
                model = connect_to_best_model(key)
                if model:
                    st.session_state['api_key'] = key
                    st.session_state['active_model'] = model
                    st.success(f"Linked: {model} 🎉")
                    time.sleep(1); st.rerun()
                else: st.error("Invalid Key ❌")
    else:
        st.success(f"🟢 {st.session_state['active_model']}")

    # 2. PROFILE
    with st.expander("👤 Edit Profile", expanded=False):
        age = st.number_input("Age", 10, 100, 25)
        gender = st.radio("Gender", ["Male 👨", "Female 👩"], horizontal=True)
        w = st.number_input("Weight (kg)", 30, 150, 70)
        h = st.number_input("Height (cm)", 100, 250, 175)
        act = st.selectbox("Activity", ["Lazy 🛋️", "Active 🏃", "Athlete 🏋️"])
        st.session_state['user_diet'] = st.selectbox("Diet", ["Balanced ⚖️", "Keto 🥩", "Vegan 🥗"])
        
        if st.button("Save Stats"):
            bmi = w / ((h/100)**2)
            st.session_state['bmi'] = bmi
            base = (10*w) + (6.25*h) - (5*age) + (5 if "Male" in gender else -161)
            mult = 1.2 if "Lazy" in act else 1.55 if "Active" in act else 1.75
            st.session_state['daily_goal'] = int(base * mult)
            st.success("Updated! 🚀")

    # 3. HYDRATION
    st.write("### 💧 Hydration")
    w_col1, w_col2 = st.columns(2)
    if w_col1.button("🥤 Cup\n(250ml)"):
        st.session_state['water_ml'] += 250
    if w_col2.button("🍼 Bottle\n(500ml)"):
        st.session_state['water_ml'] += 500
        
    w_target = 3000
    w_curr = st.session_state['water_ml']
    st.progress(min(w_curr / w_target, 1.0))
    st.caption(f"**{w_curr}ml** / {w_target}ml Goal")

    # 4. CHATBOT
    st.write("---")
    st.markdown("### 💬 AI Buddy")
    if uq := st.chat_input("Ask me..."):
        if st.session_state['active_model']:
            st.session_state['chat_history'].append({"role":"user", "text":uq})
            ctx = st.session_state['scan_data']['name'] if st.session_state['scan_data'] else "General"
            reply = chat_ai(uq, ctx)
            st.session_state['chat_history'].append({"role":"ai", "text":reply})
            st.rerun()

    for msg in st.session_state['chat_history'][-2:]:
        with st.chat_message(msg['role']): st.write(msg['text'])

# --- 7. MAIN PAGES ---

# --- PAGE: HOME & FEATURES ---
if "Home" in st.session_state['page']:
    st.markdown("<h1 style='text-align: center; color: #00E676;'>🥗 Welcome to NutriScan AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #bbb;'>Your Fun, Smart, and Healthy Food Companion! 🚀</p>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("### ✨ What can I do?")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-box">
            <h1>📸</h1>
            <h3>AI Vision</h3>
            <p>I can see your food! Just snap a pic and I'll tell you calories, macros, and nutrients.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-box">
            <h1>👨‍🍳</h1>
            <h3>Smart Chef</h3>
            <p>Got ingredients? I'll cook up yummy recipes based on your diet (Keto, Vegan, etc.).</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-box">
            <h1>⚖️</h1>
            <h3>Health & Burn</h3>
            <p>I analyze good vs bad ingredients and tell you how much to run/walk to burn it off!</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown("""
        <div class="feature-box">
            <h1>📊</h1>
            <h3>Daily Diary</h3>
            <p>Track your meals and see your progress bars fill up!</p>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown("""
        <div class="feature-box">
            <h1>💬</h1>
            <h3>AI Chatbot</h3>
            <p>Ask me anything about nutrition, digestion, or diet tips.</p>
        </div>
        """, unsafe_allow_html=True)
    with c6:
        st.markdown("""
        <div class="feature-box">
            <h1>💧</h1>
            <h3>Hydration</h3>
            <p>Don't forget to drink water! Track your glasses in the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    st.info("💡 **Tip of the Day:** Drinking water before meals can help you feel fuller and aid weight loss!")
    
# --- PAGE: SCANNER ---
elif "Scan" in st.session_state['page']:
    # COLUMN 1: INPUT + CHEF (LEFT SIDE)
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.markdown("### 📸 Input")
        src = st.radio("Source", ["Upload 📁", "Camera 📷"], horizontal=True, label_visibility="collapsed")
        img_file = st.file_uploader("File", type=['jpg','png']) if "Upload" in src else st.camera_input("Snap")
        
        if img_file:
            img = Image.open(img_file)
            st.image(img, use_container_width=True)
            if st.button("🔍 IDENTIFY FOOD"):
                if not st.session_state['active_model']: st.error("Link Key in Sidebar!")
                else:
                    with st.spinner("AI is thinking... 🧠"):
                        res = analyze_image(img)
                        if "error" in res: st.error(res['error'])
                        else: 
                            st.session_state['scan_data'] = res
                            st.session_state['recipe_result'] = None # Reset recipe on new scan
                            st.rerun()
                            
        # --- AI CHEF (MOVED TO LEFT, BELOW IMAGE) ---
        if st.session_state['scan_data']:
            st.write("---")
            st.markdown("### 👨‍🍳 AI Chef")
            st.caption(f"Based on **{st.session_state['user_diet']}** diet")
            
            if st.button("✨ Generate Recipes"):
                with st.spinner("Cooking up ideas..."):
                    st.session_state['recipe_result'] = get_recipes(st.session_state['scan_data']['name'], st.session_state['user_diet'])
            
            if st.session_state['recipe_result']:
                st.info(st.session_state['recipe_result'])

    # COLUMN 2: NUTRITION RESULTS (RIGHT SIDE)
    with c2:
        if st.session_state['scan_data']:
            d = st.session_state['scan_data']
            
            # Header
            st.markdown(f"""
            <div class="glass-card">
                <h1 style="color:#00E676; margin:0;">{d['name']}</h1>
                <p>{d['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            tts = gTTS(f"{d['name']}. {d['desc']}")
            fp = BytesIO(); tts.write_to_fp(fp); fp.seek(0)
            st.audio(fp, format='audio/mp3')
            
            # Benefits
            with st.expander("ℹ️ Nutritional Details", expanded=True):
                k1, k2 = st.columns(2)
                k1.success(f"**Benefits:**\n{d['benefits']}")
                k2.error(f"**Risks:**\n{d['harm']}")
            
            # Calculator
            st.markdown("### 🧮 Calculator")
            u1, u2 = st.columns([1, 2])
            unit = u1.radio("Unit", ["g", "kg"])
            qty = u2.slider("Amount", 0, 1000, 100 if unit=="g" else 1)
            
            factor = qty/100 if unit=="g" else qty*10
            rcals = int(d['cals'] * factor)
            
            # Burn Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Energy 🔥", f"{rcals}")
            m2.metric("Walk 🚶", f"{int(rcals/4)}m")
            m3.metric("Run 🏃", f"{int(rcals/11)}m")
            m4.metric("Bike 🚴", f"{int(rcals/9)}m")
            
            # Chart
            fig = go.Figure(data=[go.Pie(
                labels=['Carbs', 'Protein', 'Fat'],
                values=[d['carbs'], d['prot'], d['fat']],
                hole=0.6,
                marker_colors=['#FFABAB', '#85E3FF', '#B9FBC0']
            )])
            fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            # Log
            meal = st.selectbox("Meal", ["Breakfast 🍳", "Lunch 🥗", "Dinner 🍗", "Snack 🍎"])
            if st.button("➕ Add to Diary"):
                st.session_state['food_log'].append({
                    "name": d['name'], "cals": rcals, 
                    "carbs": int(d['carbs']*factor), "prot": int(d['prot']*factor), "fat": int(d['fat']*factor),
                    "meal": meal, "time": datetime.datetime.now().strftime("%H:%M")
                })
                st.balloons()
                st.success("Logged! 📝")

# --- PAGE: DIARY ---
elif "Diary" in st.session_state['page']:
    st.subheader("📊 Your Daily Progress")
    if st.session_state['food_log']:
        df = pd.DataFrame(st.session_state['food_log'])
        total = df['cals'].sum()
        
        st.metric("Total Calories", f"{total}", f"Target: {st.session_state['daily_goal']}")
        st.progress(min(total/st.session_state['daily_goal'], 1.0))
        
        # Breakdown
        b1, b2, b3 = st.columns(3)
        b1.metric("Carbs", f"{df['carbs'].sum()}g")
        b2.metric("Protein", f"{df['prot'].sum()}g")
        b3.metric("Fat", f"{df['fat'].sum()}g")
        
        st.dataframe(df, use_container_width=True)
        if st.button("Clear History"): st.session_state['food_log'] = []; st.rerun()
    else: st.info("Empty! Eat something yummy 😋")