# 🥑 NutriScan AI - Your Smart Health Companion

**NutriScan AI** is an interactive, AI-powered web application that turns your food photos into detailed nutritional insights. Built with **Streamlit** and **Google Gemini Vision Pro**, it acts as your personal nutritionist and chef combined.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Google%20Gemini%20AI-8E75B2?style=for-the-badge&logo=google&logoColor=white)

## ✨ Features

### 📸 1. AI Food Scanner
- **Instant Recognition:** Upload or snap a photo of any meal.
- **Deep Analysis:** Detects calories, macros (Carbs, Protein, Fat).
- **Good vs. Bad:** AI breaks down Health Benefits ✅ and Potential Risks ⚠️.
- **Smart Tags:** Auto-generates diet tags (e.g., High Protein, Low Carb).

### 👨‍🍳 2. Intelligent AI Chef
- **Instant Recipes:** Don't know what to cook? The AI suggests 3 unique recipes based on the food you just scanned.
- **Diet-Aware:** Recipes adjust based on your profile (Vegan, Keto, Paleo, etc.).

### 📊 3. Health & Progress Tracker
- **Interactive Dashboard:** Tracks your daily calorie intake vs. your BMR goal.
- **Hydration Tracker:** Log your water intake (Cup/Bottle) to hit your daily liters.
- **Burn-It-Off Calculator:** Tells you exactly how long you need to Walk 🚶, Run 🏃, or Bike 🚴 to burn off the food.

### 👤 4. Personalized Profile
- Calculates **BMI** and **BMR** based on Age, Gender, Height, and Activity Level.
- Sets custom daily calorie goals automatically.

---

## 🚀 How to Run Locally

1. **Clone the repository**
   ```bash
   git clone [https://github.com/your-username/nutriscan-ai.git](https://github.com/your-username/nutriscan-ai.git)
   cd nutriscan-ai

Install Dependencies
pip install -r requirements.txt

Run the App
streamlit run main.py

Connect AI
The app will open in your browser.
Open the Sidebar.
Paste your Google Gemini API Key (https://aistudio.google.com/app/api-keys).
Click Link Key and start scanning!

🛠️ Tech Stack
Frontend: Streamlit (Python)

AI Model: Google Gemini 2.5 Flash / Pro (Auto-Detects best available model)

Visualization: Plotly (Interactive Donut Charts)

Audio: gTTS (Text-to-Speech for accessibility)

📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

Disclaimer: This is an AI-powered tool for educational and lifestyle purposes. Always consult a professional for medical advice.
