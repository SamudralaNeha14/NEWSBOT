import base64
import os

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
        background: rgba(0,0,0,0);
    }}
    
    [data-testid="stSidebar"] {{
        background-color: rgba(30, 30, 46, 0.95);
        backdrop-filter: blur(10px);
    }}
    
    /* Main content area */
    [data-testid="stMainBlockContainer"] {{
        background-color: rgba(255, 255, 255, 0.02);
        padding: 2rem;
    }}
    
    /* Chat messages styling */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px;
        padding: 1rem !important;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
        color: #FFFFFF;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
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
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)


# Page config
st.set_page_config(
    page_title="NEWSBot - News Research Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ Add the background image
add_bg_from_local("image.jpg")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'article_content' not in st.session_state:
    st.session_state.article_content = {}

def extract_article_content(url):
    """Extract text content from a news article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:15000]  # Limit to 15k chars
    except Exception as e:
        return f"Error extracting content: {str(e)}"

def query_groq(question, context, api_key):
    """Query Groq API with article context"""
    try:
        client = Groq(api_key=api_key)
        
        prompt = f"""You are NEWSBot, a helpful news research assistant. Based on the following article content, answer the user's question accurately and concisely.

Article Content:
{context}

User Question: {question}

Provide a clear, informative answer based solely on the article content. If the information isn't in the article, say so."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are NEWSBot, a helpful and accurate news research assistant."
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

# UI Layout
st.title("🤖 NEWSBot")
st.subheader("Your News Research Assistant")

# Get API key from secrets
try:
    api_key = st.secrets["groq"]["api_key"]
except Exception as e:
    st.error("⚠️ Groq API key not found in secrets.toml")
    st.stop()

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
if prompt := st.chat_input("💬Ask a question about your loaded articles..."):
    if not st.session_state.article_content:
        st.error("❌ Please load at least one article first")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Combine all article contents
                combined_context = "\n\n---\n\n".join(
                    f"Article from {url}:\n{content}" 
                    for url, content in st.session_state.article_content.items()
                )
                
                response = query_groq(prompt, combined_context, api_key)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

# Instructions
if not st.session_state.article_content:
    st.markdown("""
    <div style="background-color: rgba(200, 200, 200, 0.4); border-left: 9px solid #FFFFFF; border-radius: 8px; padding: 1rem;">
        <p style="color: #000000; font-size: 1.1rem;"><strong>👋 Welcome to NewsBot!</strong></p>
        <p style="color: #000000;"><strong>To get started:</strong></p>
        <ol style="color: #000000;">
            <li>📎 Paste article URLs in the sidebar to load them</li>
            <li>💬 Ask questions about your articles in the chat</li>
        </ol>
        <p style="color: #000000;">NewsBot will analyze the content and answer your questions!</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: rgba(0,0,0,0.7); font-size: 0.9rem;'><b>Built with Streamlit & Groq Cloud | NewsBot v1.0</b></p>", unsafe_allow_html=True)