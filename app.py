import base64
import os
from datetime import datetime

import requests
import streamlit as st
from bs4 import BeautifulSoup
from groq import Groq


# --- Function to add background image ---
def add_bg_from_local(image_file):
    """Add background image to Streamlit app from a local file"""
    with open(image_file, "rb") as img:
        encoded_img = base64.b64encode(img.read()).decode()

    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{encoded_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0.9);
    }}
    
    [data-testid="stSidebar"] {{
        background-color: rgba(30, 30, 46, 0.4);
        backdrop-filter: blur(10px);
    }}
    
    /* Main content area */
    [data-testid="stMainBlockContainer"] {{
        background-color: rgba(500, 600, 800, 0.4);
        padding: 2rem;
    }}
    
    /* Chat messages styling */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px;
        padding: 1rem !important;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }}
    
    /* Input box styling */
    .stTextInput > div > div > input {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-radius: 8px;
        border: 2px solid rgba(0,0,0,0.2) !important;
        padding: 0.75rem !important;
        color: #FFFFFF !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: rgba(255, 255, 255, 0.7) !important;
    }}
    
    /* Button styling */
    .stButton > button {{
        background-color: #2E7D32;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }}
    
    .stButton > button:hover {{
        background-color: #1B5E20;
        box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
    }}
    
    /* Delete button styling */
    button[key*="del_"] {{
        background-color: #D32F2F !important;
        color: white;
    }}
    
    /* Markdown styling */
    .stMarkdown {{
        color: #333;
    }}
    
    /* Sidebar text styling */
    .stSidebar .stMarkdown {{
        color: #FFFFFF;
    }}
    
    /* Title styling */
    h1, h2, h3 {{
        color: #000000;
        text-shadow: 2px 2px 4px rgba(255,255,255,0.3);
    }}
    
    /* Info box styling */
    .stInfo {{
        background-color: rgba(13, 110, 253, 0.25) !important;
        border-left: 4px solid #0D6EFD;
        border-radius: 8px;
        padding: 1rem;
    }}
    
    .stInfo p {{
        color: #000000;
        font-weight: 500;
    }}
    
    /* Warning styling */
    .stWarning {{
        background-color: rgba(255, 193, 7, 0.1) !important;
        border-left: 4px solid #FFC107;
    }}
    
    /* Error styling */
    .stError {{
        background-color: rgba(211, 47, 47, 0.1) !important;
        border-left: 4px solid #D32F2F;
    }}
    
    /* Success styling */
    .stSuccess {{
        background-color: rgba(46, 125, 50, 0.1) !important;
        border-left: 4px solid #2E7D32;
    }}
    
    /* Spinner styling */
    .stSpinner {{
        color: #2E7D32;
    }}
    
    /* URL display in sidebar */
    .stText {{
        color: #FFFFFF;
        font-size: 0.85rem;
        word-break: break-word;
    }}
    
    /* Caption styling */
    .stCaption {{
        color: rgba(0, 0, 0, 0.8);
        text-align: center;
    }}
    
    /* Divider */
    hr {{
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    /* News card styling */
    .news-card {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }}
    
    .news-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }}
    
    .genre-button {{
        background-color: #2E7D32 !important;
        color: white !important;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        margin: 0.3rem;
        font-weight: 600;
        border: none;
    }}
    
    .genre-button:hover {{
        background-color: #1B5E20 !important;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)


# Page config
st.set_page_config(
    page_title="NEWSBOT - News Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the background image
add_bg_from_local("image.jpg")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'article_content' not in st.session_state:
    st.session_state.article_content = {}
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'selected_genre' not in st.session_state:
    st.session_state.selected_genre = None
if 'expanded_article' not in st.session_state:
    st.session_state.expanded_article = None
if 'user_location' not in st.session_state:
    st.session_state.user_location = "Texas"

# News genres and keywords
GENRES = {
    "🤖 AI & Tech": "artificial intelligence technology",
    "💼 Business": "business economy finance",
    "🏥 Health": "health medical science",
    "🌍 World": "world international news",
    "⚽ Sports": "sports athletics games",
    "🎬 Entertainment": "entertainment movies celebrity",
    "🔬 Science": "science research discovery",
    "🚀 Innovation": "innovation startup technology",
    "🏛️ Politics": "politics government election policy",
    "📍 Regional": "regional_local"
}

def fetch_news_by_genre(genre_keyword, api_key):
    """Fetch news articles using NewsAPI based on genre keyword"""
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": genre_keyword,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 10,
            "apiKey": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []

def extract_article_content(url):
    """Extract text content from a news article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:15000]
    except Exception as e:
        return f"Error extracting content: {str(e)}"

def query_groq(question, context, api_key):
    """Query Groq API with article context"""
    try:
        client = Groq(api_key=api_key)
        
        prompt = f"""You are NEWSBOT, a helpful news research assistant. Based on the following article content, answer the user's question accurately and concisely.

Article Content:
{context}

User Question: {question}

Provide a clear, informative answer based solely on the article content. If the information isn't in the article, say so."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are NEWSBOT, a helpful and accurate news research assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1024,
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error querying Groq: {str(e)}"

# Get API keys from secrets
try:
    groq_api_key = st.secrets["groq"]["api_key"]
    news_api_key = st.secrets.get("newsapi", {}).get("api_key", "")
except Exception as e:
    st.error("⚠️ API keys not found in secrets.toml")
    st.stop()

# Sidebar navigation
with st.sidebar:
    st.header("🗂️ Navigation")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("📖 Research", use_container_width=True):
            st.session_state.page = "research"
            st.rerun()
    
    st.markdown("---")
    st.subheader("📍 Your Location")
    
    location_input = st.text_input(
        "Enter your location",
        value=st.session_state.user_location,
        placeholder="e.g., India, New York, London"
    )
    
    if location_input and location_input != st.session_state.user_location:
        st.session_state.user_location = location_input
        st.success(f"✅ Location updated to {location_input}")

# HOME PAGE
if st.session_state.page == "home":
    st.markdown("<h1 style='color: black;'>🤖 NEWSBOT</h1>", unsafe_allow_html=True)
    st.markdown("<h5 style='color: black;'>Stay Updated with Latest News Across All Genres</h5>", unsafe_allow_html=True)
    if not news_api_key:
        st.warning("⚠️ NewsAPI key not configured. Please add it to secrets.toml to view trending news.")
        st.info("Get a free API key from https://newsapi.org")
    else:
        st.markdown("### 📰 Select a Genre")
        
        # Display genre buttons in columns
        cols = st.columns(3)
        for idx, (genre, keyword) in enumerate(GENRES.items()):
            with cols[idx % 3]:
                if st.button(genre, use_container_width=True, key=f"genre_{idx}"):
                    st.session_state.selected_genre = genre
                    st.session_state.genre_keyword = keyword
                    st.rerun()
        
        # Display selected genre news
        if st.session_state.selected_genre:
            st.markdown(f"### {st.session_state.selected_genre}")
            st.markdown("---")
            
            with st.spinner(f"Fetching {st.session_state.selected_genre} news..."):
                # Check if it's regional news
                if st.session_state.genre_keyword == "regional_local":
                    news_keyword = st.session_state.user_location
                    articles = fetch_news_by_genre(news_keyword, news_api_key)
                else:
                    articles = fetch_news_by_genre(st.session_state.genre_keyword, news_api_key)
            
            if articles:
                for idx, article in enumerate(articles):
                    article_key = f"article_{idx}"
                    is_expanded = st.session_state.expanded_article == article_key
                    
                    col1, col2, col3 = st.columns([2.5, 0.5, 0.5])
                    
                    with col1:
                        st.markdown(f"#### {article.get('title', 'No Title')}")
                        st.markdown(f"**Source:** {article.get('source', {}).get('name', 'Unknown')}")
                        
                        description = article.get('description', '')
                        if description:
                            if is_expanded:
                                st.markdown(f"{description}")
                            else:
                                st.markdown(f"{description[:200]}...")
                        
                        pub_date = article.get('publishedAt', '')
                        if pub_date:
                            st.caption(f"📅 {pub_date[:10]}")
                        
                        # Show additional info when expanded
                        if is_expanded:
                            st.markdown("---")
                            author = article.get('author', 'Unknown')
                            content = article.get('content', 'No content available')
                            url = article.get('url', '')
                            
                            st.markdown(f"**Author:** {author}")
                            st.markdown(f"**Full Content Preview:**")
                            st.markdown(f"{content}")
                            
                            if url:
                                st.markdown(f"**[🔗 Read Full Article]({url})**")
                    
                    with col2:
                        if st.button("📖 Load", key=f"load_{idx}", use_container_width=True):
                            article_url = article.get('url', '')
                            if article_url:
                                with st.spinner("Extracting article content..."):
                                    content = extract_article_content(article_url)
                                    if not content.startswith("Error"):
                                        st.session_state.article_content[article_url] = content
                                        st.session_state.page = "research"
                                        st.success("✅ Article loaded! Go to Research tab.")
                                        st.rerun()
                                    else:
                                        st.error(content)
                    
                    with col3:
                        if st.button("📖 Read More" if not is_expanded else "📕 Read Less", key=f"expand_{idx}", use_container_width=True):
                            if is_expanded:
                                st.session_state.expanded_article = None
                            else:
                                st.session_state.expanded_article = article_key
                            st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("No articles found for this genre.")

# RESEARCH PAGE
elif st.session_state.page == "research":
    st.markdown("<h1 style='color: black;'>🤖 NEWSBOT</h1>", unsafe_allow_html=True)
    
    st.markdown("<h6 style='color: black;'>Your News Research Assistant</h6>", unsafe_allow_html=True)

    
    # Sidebar for settings
    with st.sidebar:
        st.header("📰 Load Articles")
        
        url_input = st.text_input("Enter article URL 📎", placeholder="https://example.com/article")
        
        if st.button("Load Article", use_container_width=True):
            if url_input:
                with st.spinner("Extracting article content..."):
                    content = extract_article_content(url_input)
                    if not content.startswith("Error"):
                        st.session_state.article_content[url_input] = content
                        st.success("✅ Article loaded!")
                    else:
                        st.error(content)
            else:
                st.warning("Please enter a URL 📎")
        
        # Display loaded articles
        if st.session_state.article_content:
            st.markdown("---")
            st.subheader("📚 Loaded Articles")
            for i, url in enumerate(st.session_state.article_content.keys(), 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"{i}. {url[:30]}...")
                with col2:
                    if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                        del st.session_state.article_content[url]
                        st.rerun()
            
            st.markdown("---")
            if st.button("Clear All", use_container_width=True):
                st.session_state.article_content = {}
                st.session_state.messages = []
                st.rerun()
    
    # Main chat interface
    st.markdown("---")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("💬 Ask a question about your loaded articles..."):
        if not st.session_state.article_content:
            st.error("❌ Please load at least one article first")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    combined_context = "\n\n---\n\n".join(
                        f"Article from {url}:\n{content}" 
                        for url, content in st.session_state.article_content.items()
                    )
                    
                    response = query_groq(prompt, combined_context, groq_api_key)
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Instructions
    if not st.session_state.article_content:
        st.markdown("""
        <div style="background-color: rgba(200, 200, 200, 0.4); border-left: 9px solid #FFFFFF; border-radius: 8px; padding: 1rem;">
            <p style="color: #000000; font-size: 1.1rem;"><strong>👋 Welcome to NEWSBOT!</strong></p>
            <p style="color: #000000;"><strong>To get started:</strong></p>
            <ol style="color: #000000;">
                <li>📎 Paste article URLs in the sidebar to load them</li>
                <li>💬 Ask questions about your articles in the chat</li>
                <li>🏠 Go to Home to explore trending news by genre</li>
            </ol>
            <p style="color: #000000;">NewsBOT will analyze the content and answer your questions!</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: rgba(0,0,0,0.7); font-size: 0.9rem;'><b>Built with Streamlit & Groq Cloud | NewsBOT v2.0</b></p>", unsafe_allow_html=True)
