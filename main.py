import streamlit as st
from gtts import gTTS
import os
import time
import random
import re
from hashlib import md5

# Configuration
os.makedirs("temp_audio", exist_ok=True)
MAX_TEXT_LENGTH = 3000  # Increased character limit

VOICE_CHOICES = {
    "English (US)": "en",
    "English (UK)": "en-co.uk",
    "Spanish": "es",
    "French": "fr"
}

# Enhanced content templates with longer paragraphs
CONTENT_TEMPLATES = {
    "AI": [
        """Artificial Intelligence is revolutionizing our world. At its core, machine learning algorithms enable computers to learn from data without explicit programming. 
        Consider how Netflix uses AI to recommend shows based on your viewing history. These recommendation systems analyze billions of data points to predict your preferences. 
        Looking ahead, AI will transform healthcare through diagnostic tools, education via personalized learning, and transportation with self-driving cars. 
        What ethical considerations should we keep in mind as AI becomes more advanced?""",
        
        """The field of AI encompasses both narrow AI, designed for specific tasks, and the theoretical general AI that could perform any intellectual task. 
        Deep learning, a subset of machine learning, uses neural networks with multiple layers to process complex data patterns. 
        For instance, Google's AlphaFold has made breakthroughs in predicting protein structures, accelerating drug discovery. 
        As AI systems grow more capable, how can we ensure they align with human values and intentions?"""
    ],
    "HUMAN": [
        """Human cognition remains one of nature's most remarkable achievements. Our brains contain approximately 86 billion neurons connected by 100 trillion synapses. 
        Memory champions demonstrate extraordinary capabilities through techniques like the memory palace, memorizing hundreds of items in minutes. 
        Unlike artificial systems, human intelligence combines logic with creativity, emotional understanding, and contextual awareness. 
        What unique aspects of human intelligence do you think will remain irreplaceable by machines?""",
        
        """The story of human evolution spans millions of years, with natural selection shaping our biology and behavior. 
        Lactose tolerance in adults provides a fascinating example - a genetic adaptation that emerged alongside dairy farming. 
        Modern humans now face new evolutionary pressures from technology, medicine, and environmental changes. 
        How might human evolution progress in the next 10,000 years given our current lifestyle changes?"""
    ]
}

def clean_text(text):
    """Improved text cleaning"""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#\w+', '', text)
    text = ' '.join(text.split())  # Remove extra whitespace
    return text.strip()[:MAX_TEXT_LENGTH]

def get_content(topic):
    """Enhanced content generation with fallback"""
    primary_topic = topic.split()[0].upper()
    templates = CONTENT_TEMPLATES.get(primary_topic, [
        f"""Let's explore {topic}. This fascinating subject touches on multiple important aspects of our world. 
        The fundamental principles involve {primary_topic.lower()} and its applications across different domains. 
        Consider how this manifests in everyday life - from simple observations to complex systems. 
        What connections can you make between {primary_topic.lower()} and your own experiences?"""
    ])
    return random.choice(templates)

def generate_audio(text, lang_code):
    """Robust audio generation with caching"""
    try:
        text = clean_text(text)
        if not text or len(text) < 50:
            raise ValueError("Text too short for meaningful audio")
        
        # Create unique filename based on content
        filename = f"temp_audio/audio_{md5((text[:500]+lang_code).encode()).hexdigest()}.mp3"
        
        if not os.path.exists(filename):
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(filename)
            time.sleep(0.5)  # Brief pause between generations
            
        return filename
    except Exception as e:
        st.error(f"Audio generation issue: {str(e)}")
        return None

# Streamlit UI
st.set_page_config(
    page_title="Spotify for learning",
    page_icon="🎧",
    layout="centered"
)

st.title("🎧 Spotify for learning")
st.caption("Multi-topic podcast generator with rich content")

with st.sidebar:
    st.header("Settings")
    voice_name = st.selectbox("Language/Voice", list(VOICE_CHOICES.keys()))
    st.info("Now supporting multiple topics with enhanced content")

# Main input - changed to text_area for multiple topics
topics = st.text_area(
    "Enter topics (comma separated)",
    "Artificial Intelligence, Human Cognition, Space Exploration",
    height=100
)

if st.button("Generate Podcast Series", type="primary"):
    if not topics.strip():
        st.warning("Please enter at least one topic")
    else:
        topics_list = [t.strip() for t in topics.split(",") if t.strip()]
        progress_bar = st.progress(0)
        
        for i, topic in enumerate(topics_list):
            with st.expander(f"🎙️ Episode {i+1}: {topic}", expanded=True):
                content = get_content(topic)
                st.markdown(f"**Script:**\n\n{content}")
                
                audio_file = generate_audio(content, VOICE_CHOICES[voice_name])
                if audio_file:
                    st.audio(audio_file, format="audio/mp3")
                else:
                    st.error(f"Failed to generate audio for {topic}")
            
            progress_bar.progress((i+1)/len(topics_list))
        
        st.success(f"✅ Generated {len(topics_list)} episodes!")
        st.balloons()

# Cleanup old files (>24 hours)
if os.path.exists("temp_audio"):
    now = time.time()
    for f in os.listdir("temp_audio"):
        filepath = os.path.join("temp_audio", f)
        if now - os.path.getmtime(filepath) > 86400:  # 24 hours
            os.remove(filepath) 