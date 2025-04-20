import streamlit as st
import requests
import json
import os
from textblob import TextBlob
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# ========= Config =========
API_KEY = 'd24fe91f36dd4947b546b8d96e228ba6'
PREF_FILE = "preferences.json"
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# ========= Sentiment Analyzer =========
def analyze_sentiment(text):
    if not text.strip():
        return "Neutral"
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

# ========= Fetch News Function =========
def fetch_news(topics, language, sort_by, date_from, date_to):
    articles = []
    for topic in topics:
        params = {
            'q': topic,
            'apiKey': API_KEY,
            'language': language,
            'sortBy': sort_by,
            'from': date_from,
            'to': date_to,
            'pageSize': 10
        }
        try:
            res = requests.get(NEWS_API_URL, params=params)
            data = res.json()
            if data.get('articles'):
                for article in data['articles']:
                    articles.append({
                        'title': article.get('title', 'No Title'),
                        'description': article.get('description', 'No Description'),
                        'url': article.get('url', '#'),
                        'sentiment': analyze_sentiment(article.get('description', ''))
                    })
        except Exception as e:
            st.error(f"Error fetching news: {e}")
    return articles

# ========= Preferences Handling =========
def save_preferences(topics):
    data = {"history": []}
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r") as f:
            data = json.load(f)

    for topic in topics:
        if topic not in data["history"]:
            data["history"].append(topic)

    with open(PREF_FILE, "w") as f:
        json.dump(data, f)

def load_preferences():
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r") as f:
            return json.load(f).get("history", [])
    return []

def clear_preferences():
    if os.path.exists(PREF_FILE):
        os.remove(PREF_FILE)

# ========= Sentiment Chart =========
def show_sentiment_chart(articles):
    sentiments = [a['sentiment'] for a in articles]
    df = pd.DataFrame(sentiments, columns=["Sentiment"])
    sentiment_counts = df.value_counts().reset_index(name='Count')
    st.subheader("🧠 Sentiment Summary")
    st.bar_chart(sentiment_counts.set_index("Sentiment"))

# ========= Streamlit App =========
def main():
    st.set_page_config(page_title="📰 Smart News Feed", layout="wide")
    st.title("📰 Dynamic News Feed Personalizer")

    st.markdown("Enter your interests or topics below:")

    # ====== Sidebar Filters ======
    with st.sidebar:
        st.header("🛠 Filters")
        sort_by = st.selectbox("Sort articles by", ["publishedAt", "relevancy", "popularity"])
        language = st.selectbox("Language", ["en", "hi", "fr", "es", "de"])
        days = st.slider("How many days back?", 1, 30, 7)
        date_to = datetime.today().strftime('%Y-%m-%d')
        date_from = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')

        if st.button("🗑️ Clear History"):
            clear_preferences()
            st.success("History cleared!")

    # ====== Previous Preferences Display ======
    prev_topics = load_preferences()
    if prev_topics:
        st.subheader("🔁 Your Recent Interests")
        cols = st.columns(min(5, len(prev_topics)))
        for i, topic in enumerate(prev_topics):
            if cols[i % len(cols)].button(topic):
                st.session_state["user_input"] = topic

    # ====== Topic Input ======
    default_input = st.session_state.get("user_input", "technology, sports")
    user_input = st.text_input("Topics (comma-separated):", default_input)

    # ====== Search Button ======
    if st.button("🔍 Get Personalized News"):
        topics = [t.strip() for t in user_input.split(',') if t.strip()]
        if not topics:
            st.warning("Please enter at least one topic.")
            return
        save_preferences(topics)

        with st.spinner("🔄 Fetching your news..."):
            articles = fetch_news(topics, language, sort_by, date_from, date_to)

        if not articles:
            st.error("No articles found for these topics.")
        else:
            st.success(f"✅ Found {len(articles)} articles.")
            show_sentiment_chart(articles)

            for article in articles:
                st.subheader(article['title'])
                st.write(article['description'])
                st.markdown(f"[Read More →]({article['url']})", unsafe_allow_html=True)
                st.markdown(f"**Sentiment:** `{article['sentiment']}`")
                st.markdown("---")

if __name__ == "__main__":
    main()
