import streamlit as st
import pandas as pd
import joblib

# Load model and feature list
model = joblib.load("stroke_model.pkl")
features = joblib.load("features.pkl")

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

            for col in features:
                col_label = col.replace("_", " ").capitalize()

                if col in ["age", "avg_glucose_level", "bmi"]:
                    user_input[col] = st.number_input(col_label, min_value=0.0)
                elif col == "gender":
                    gender = st.selectbox("Gender", ["Female", "Male", "Other"])
                    user_input[col] = ["Female", "Male", "Other"].index(gender)
                elif col == "ever_married":
                    user_input[col] = st.selectbox("Ever Married", ["No", "Yes"]) == "Yes"
                elif col == "work_type":
                    option = st.selectbox("Work Type", ["Private", "Self-employed", "Govt_job", "Children", "Never_worked"])
                    user_input[col] = ["Private", "Self-employed", "Govt_job", "Children", "Never_worked"].index(option)
                elif col == "Residence_type":
                    res = st.selectbox("Residence Type", ["Urban", "Rural"])
                    user_input[col] = ["Urban", "Rural"].index(res)
                elif col == "smoking_status":
                    smoke = st.selectbox("Smoking Status", ["Never smoked", "Formerly smoked", "Smokes", "Unknown"])
                    user_input[col] = ["Never smoked", "Formerly smoked", "Smokes", "Unknown"].index(smoke)
                elif col in ["hypertension", "heart_disease"]:
                    user_input[col] = st.selectbox(f"{col_label} (0: No, 1: Yes)", [0, 1])
                else:
                    user_input[col] = st.selectbox(f"{col_label} (0/1)", [0, 1])

            submit = st.form_submit_button("🔍 Predict Stroke Risk")

        if submit:
            df_input = pd.DataFrame([user_input])
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
