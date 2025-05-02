import streamlit as st
import pandas as pd
import joblib

# Load model and original feature list
raw_features = joblib.load("features.pkl")  # original feature names, including 'hypertension'
# Replace the single 'hypertension' feature with five one-hot BP category features
bp_cat_features = [
    "hypertension_normal",
    "hypertension_elevated",
    "hypertension_stage1",
    "hypertension_stage2",
    "hypertension_crisis",
]
# Build new features list for model input
features = [f for f in raw_features if f != "hypertension"] + bp_cat_features

# Load model
model = joblib.load("stroke_model.pkl")

# Load CSS (if you have one)
try:
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ------------------ Authentication ------------------ #
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

# ------------------ Risk Level & Tips ------------------ #
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

# ------------------ UI ------------------ #
st.title("🧠 Stroke Risk Prediction")

menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Navigation", menu)

# Common BP category labels and ranges
labels = {
    "normal": "✅ Normal Blood Pressure",
    "elevated": "🟡 Elevated Blood Pressure",
    "stage1": "🟠 Stage 1 Hypertension",
    "stage2": "🔴 Stage 2 Hypertension",
    "crisis": "⚠️ Hypertensive Crisis"
}
range_labels = {
    "normal":  "Less than 120/80 mm Hg",
    "elevated": "120–129 systolic and < 80 diastolic mm Hg",
    "stage1":  "130–139 systolic or 80–89 diastolic mm Hg",
    "stage2":  "140–179 systolic or 90–119 diastolic mm Hg",
    "crisis":  "≥ 180 systolic or ≥ 120 diastolic mm Hg"
}

# ------------- LOGIN PAGE ------------- #
if choice == "Login":
    if not st.session_state.logged_in:
        st.subheader("🔐 User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if authenticate(username, password):
                st.success(f"✅ Welcome {username}!")
                st.session_state.logged_in = True
                st.session_state.username = username
            else:
                st.error("❌ Invalid username or password.")

    # Prediction form
    if st.session_state.logged_in:
        st.markdown("---")
        st.header("📋 Enter Your Health Details")

        with st.form("prediction_form"):
            user_input = {}

            # ——— Blood Pressure Inputs & categories ———
            systolic = st.number_input(
                "Systolic Pressure (mm Hg)", min_value=50, max_value=250, value=120, step=1
            )
            diastolic = st.number_input(
                "Diastolic Pressure (mm Hg)", min_value=30, max_value=150, value=80, step=1
            )

            # Determine BP category
            if systolic < 120 and diastolic < 80:
                bp_category = "normal"
            elif 120 <= systolic <= 129 and diastolic < 80:
                bp_category = "elevated"
            elif (130 <= systolic <= 139) or (80 <= diastolic <= 89):
                bp_category = "stage1"
            elif (140 <= systolic < 180) or (90 <= diastolic < 120):
                bp_category = "stage2"
            else:
                bp_category = "crisis"

            # Show category & range
            st.info(labels[bp_category])
            st.caption(f"Range: {range_labels[bp_category]}")

            # One-hot encode BP category
            for cat in bp_cat_features:
                user_input[cat] = 1 if cat.endswith(bp_category) else 0

            # ——— Other features ———
            for col in raw_features:
                if col == "hypertension":
                    continue  # already represented by the five new keys

                col_label = col.replace("_", " ").capitalize()

                if col in ["age", "avg_glucose_level", "bmi"]:
                    user_input[col] = st.number_input(col_label, min_value=0.0)
                elif col == "gender":
                    gender = st.selectbox("Gender", ["Female", "Male", "Other"])
                    user_input[col] = ["Female", "Male", "Other"].index(gender)
                elif col == "ever_married":
                    user_input[col] = st.selectbox("Ever Married", ["No", "Yes"]) == "Yes"
                elif col == "work_type":
                    option = st.selectbox(
                        "Work Type", ["Private", "Self-employed", "Govt_job", "Children", "Never_worked"]
                    )
                    user_input[col] = ["Private", "Self-employed", "Govt_job", "Children", "Never_worked"].index(option)
                elif col == "Residence_type":
                    res = st.selectbox("Residence Type", ["Urban", "Rural"])
                    user_input[col] = ["Urban", "Rural"].index(res)
                elif col == "smoking_status":
                    smoke = st.selectbox(
                        "Smoking Status", ["Never smoked", "Formerly smoked", "Smokes", "Unknown"]
                    )
                    user_input[col] = ["Never smoked", "Formerly smoked", "Smokes", "Unknown"].index(smoke)
                elif col == "heart_disease":
                    user_input[col] = st.selectbox(f"{col_label} (0: No, 1: Yes)", [0, 1])
                else:
                    user_input[col] = st.selectbox(f"{col_label} (0/1)", [0, 1])

            submit = st.form_submit_button("🔍 Predict Stroke Risk")

        if submit:
            df_input = pd.DataFrame([user_input], columns=features)
            prediction = model.predict(df_input)[0]
            result = get_health_tips(prediction)

            st.markdown(f"### 🧾 Prediction Result: **{result['label']}**")
            st.markdown("#### 🩺 Personalized Healthcare Tips:")
            for tip in result["tips"]:
                st.markdown(f"- {tip}")

        st.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "username": ""}))

# ------------- SIGNUP PAGE ------------- #
elif choice == "Sign Up":
    st.subheader("🆕 Create Account")
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")

    if st.button("Sign Up"):
        if register_user(new_user, new_pass):
            st.success("🎉 Account created successfully! You can now login.")
        else:
            st.warning("⚠️ Username already exists.")

