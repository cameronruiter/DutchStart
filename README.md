# DutchStart

An AI assistant that explains Dutch systems in plain language for international students in the Netherlands.

Built for AI for Good, Week 3 hackathon — SDG 10 (Reduced Inequalities).
By Cameron Ruiter and Domile Zukaite.

## What it does

International students arriving in the Netherlands have to deal with unfamiliar
systems — registering with the gemeente, getting a BSN, understanding rental
rules, student finance, tax. The information exists, but it is often in Dutch,
written for people who already know how the system works.

DutchStart lets a student pick a topic (Government, Housing, University, or
Work & Money), type a question in plain English, and get back:

- a simple explanation
- clear next steps
- an explanation of any difficult Dutch terms
- a reminder to check an official source before making decisions

## Live app

**[Open DutchStart]([https://your-actual-url.streamlit.app](https://dutchstart.streamlit.app/))**

## Running it locally

You need Python 3.10 or newer and a Gemini API key
(free from https://aistudio.google.com/apikey).

**1. Clone the repo**

```
git clone https://github.com/cameronruiter/DutchStart.git
cd DutchStart
```

**2. Install the dependencies**

```
python -m pip install -r requirements.txt
```

**3. Add your API key**

Create a file named `.env` in the project folder containing:

```
GEMINI_API_KEY=your_key_here
```

This file is gitignored and is not in the repository, so you need to supply
your own key.

**4. Run the app**

```
python -m streamlit run python.py
```

It opens at http://localhost:8501

## How it works

A single Streamlit page collects the topic and the question, then sends both to
Gemini in one API call. The prompt sets the response format and instructs the
model to say when it is unsure, not to invent information, and to point the
user to official sources. Empty inputs and API errors are handled so the user
never sees a crash or an invented answer to a question they did not ask.

## Known limitations

The model can be wrong or out of date. Every answer tells the user to verify
important decisions with an official source, but the app does not yet check
answers against verified Dutch government sources — that is the main thing a
future version should add.
