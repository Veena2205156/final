import streamlit as st
import pandas as pd
import joblib

# ─── Load model and original feature list ─────────────────────────────────────
raw_features = joblib.load("features.pkl")   # list including "hypertension"
model        = joblib.load("stroke_model.pkl")

# ─── Load custom CSS (optional) ────────────────────────────────────────────────
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# ─── Session‐state init ─────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username  = ""

# ─── Authentication helpers ────────────────────────────────────────────────────
def authenticate(username, password):
    users = pd.read_csv("users.csv")
    return any((users["username"] == username) & (users["password"] == password))

def register_user(username, password):
    users = pd.read_csv("users.csv")
    if username in users["username"].values:
        return False
    users.loc[len(users)] = [username, password]
    users.to_csv("users.csv", index=False)
    return True

# ─── Risk‐level & Tips ──────────────────────────────────────────────────────────
def get_health_tips(pred):
    if pred == 2:
        return {
            "label": "🔴 High Risk",
            "tips": [
                "💉 Monitor your blood pressure regularly.",
                "🚭 Quit smoking immediately.",
                "🍽 Reduce salt and processed food intake.",
                "🏃 Walk 30 minutes daily.",
                "⚖️ Maintain healthy weight and BMI.",
                "🧘 Practice relaxation or meditation.",
                "💊 Take medications as prescribed.",
            ]
        }
    elif pred == 1:
        return {
            "label": "🟠 Medium Risk",
            "tips": [
                "🥗 Eat fruits, veggies, and whole grains.",
                "🩺 Monitor glucose and cholesterol.",
                "🚶‍♂️ Be active at least 150 minutes/week.",
                "🧂 Limit salt and sugar.",
                "😴 Get enough sleep and manage stress.",
            ]
        }
    else:
        return {
            "label": "🟢 Low Risk",
            "tips": [
                "🏋️ Continue your healthy habits.",
                "🥦 Eat a balanced diet.",
                "🩺 Annual health checkups.",
                "🚭 Avoid tobacco.",
                "💧 Stay hydrated and sleep well.",
            ]
        }

# ─── UI Layout ─────────────────────────────────────────────────────────────────
st.title("🧠 Stroke Risk Prediction")
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Navigation", menu)

# BP dropdown options
bp_options = {
    "Normal: Less than 120/80 mm Hg":           "normal",
    "Elevated: 120–129/< 80 mm Hg":             "elevated",
    "Stage 1: 130–139 or 80–89 mm Hg":           "stage1",
    "Stage 2: 140–179 or 90–119 mm Hg":          "stage2",
    "Hypertensive Crisis: ≥ 180 or ≥ 120 mm Hg": "crisis",
}

if choice == "Login":
    # ─── Login form ─────────────────────────────────────────────────────────────
    if not st.session_state.logged_in:
        st.subheader("🔐 User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.success(f"✅ Welcome {username}!")
                st.session_state.logged_in = True
                st.session_state.username  = username
            else:
                st.error("❌ Invalid username or password.")

    # ─── Prediction form ───────────────────────────────────────────────────────
    if st.session_state.logged_in:
        st.markdown("---")
        st.header("📋 Enter Your Health Details")

        with st.form("prediction_form"):
            user_input = {}

            # 1) BP category dropdown
            bp_label    = st.selectbox("Blood Pressure Category", list(bp_options.keys()))
            bp_category = bp_options[bp_label]
            st.caption(bp_label)

            # (optional) one‑hot fields if you want to inspect them
            for cat in bp_options.values():
                user_input[f"hypertension_{cat}"] = 1 if cat == bp_category else 0

            # 2) Map back to original single flag
            user_input["hypertension"] = 1 if bp_category in ["stage1","stage2","crisis"] else 0

            # 3) Other features
            for col in raw_features:
                if col == "hypertension":
                    continue
                col_label = col.replace("_", " ").capitalize()
                if col in ["age", "avg_glucose_level", "bmi"]:
                    user_input[col] = st.number_input(col_label, min_value=0.0)
                elif col == "gender":
                    gender = st.selectbox("Gender", ["Female", "Male", "Other"])
                    user_input[col] = ["Female", "Male", "Other"].index(gender)
                elif col == "ever_married":
                    user_input[col] = st.selectbox("Ever Married", ["No", "Yes"]) == "Yes"
                elif col == "work_type":
                    wt = st.selectbox("Work Type", ["Private","Self-employed","Govt_job","Children","Never_worked"])
                    user_input[col] = ["Private","Self-employed","Govt_job","Children","Never_worked"].index(wt)
                elif col == "Residence_type":
                    rt = st.selectbox("Residence Type", ["Urban","Rural"])
                    user_input[col] = ["Urban","Rural"].index(rt)
                elif col == "smoking_status":
                    sm = st.selectbox("Smoking Status", ["Never smoked","Formerly smoked","Smokes","Unknown"])
                    user_input[col] = ["Never smoked","Formerly smoked","Smokes","Unknown"].index(sm)
                elif col == "heart_disease":
                    user_input[col] = st.selectbox("Heart Disease (0: No, 1: Yes)", [0,1])
                else:
                    user_input[col] = st.selectbox(f"{col_label} (0/1)", [0,1])

            submit = st.form_submit_button("🔍 Predict Stroke Risk")

            if submit:
                # build DataFrame matching exactly raw_features
                df_input   = pd.DataFrame([user_input]).reindex(columns=raw_features, fill_value=0)
                prediction = model.predict(df_input)[0]
                result     = get_health_tips(prediction)

                st.markdown(f"### 🧾 Prediction Result: **{result['label']}**")
                st.markdown("#### 🩺 Personalized Healthcare Tips:")
                for tip in result["tips"]:
                    st.markdown(f"- {tip}")

        st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "username": ""}))

elif choice == "Sign Up":
    st.subheader("🆕 Create Account")
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Sign Up"):
        if register_user(new_user, new_pass):
            st.success("🎉 Account created successfully! You can now login.")
        else:
            st.warning("⚠️ Username already exists.")
