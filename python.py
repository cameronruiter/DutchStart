import streamlit as st
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

st.title("🇳🇱 DutchStart")

st.write("Helping international students understand life in the Netherlands.")

category = st.selectbox(
    "Choose a topic:",
    ["Government", "Housing", "University", "Work & Money"]
)

question = st.text_area("What do you need help with?")

if st.button("Explain"):

    # If the question box is empty
    if not question.strip():
        st.warning("Please type a question first.")

    # If the user DID type a question
    else:
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"""
You are DutchStart, an assistant for international students in the Netherlands.

The user selected this topic: {category}

Explain their question in simple, clear language.

Give your answer in this format:

SIMPLE EXPLANATION:
Explain it simply.

WHAT TO DO:
Give clear next steps if there are any.

IMPORTANT TERMS:
Explain difficult Dutch words or terms.

IMPORTANT:
If you are unsure about something, say so.
Do not invent information.
Tell the user to check an official source for important decisions.

User's question:
{question}
"""
            )

            st.write("### Answer")
            st.write(response.text)

        # If Gemini/API has a problem
        except Exception:
            st.error("Something went wrong. Please try again in a moment.")
