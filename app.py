import streamlit as st
import google.generativeai as genai
from dataclasses import dataclass, field
from typing import List, Dict
import os

# --- JÁTÉK ADATBÁZIS (Alapértelmezett, ha nincs net/AI) ---
DEFAULT_STORIES = [
    {
        "title": "A törött gyufa",
        "riddle": "Egy ember fekszik holtan a mezőn, kezében egy törött gyufaszállal. Nincs más nyom. Mi történt?",
        "solution": "Hőlégballonnal utaztak, de zuhanni kezdtek. Sorsot húztak, ki ugorjon ki. Ő húzta a rövidebbet."
    }
]

# --- KÖZÖS JÁTÉK MOTOR (Shared State) ---
@dataclass
class GameState:
    current_story: Dict = field(default_factory=lambda: DEFAULT_STORIES[0])
    chat_history: List[Dict] = field(default_factory=list)
    players: List[str] = field(default_factory=list)

@st.cache_resource
def get_game_state():
    return GameState()

state = get_game_state()

# --- GOOGLE GEMINI AI GENERÁLÓ ---
def generate_mystery_gemini(api_key):
    """Ingyenes Google Gemini hívás"""
    try:
        genai.configure(api_key=api_key)
        # A Flash modell gyors és ingyenes
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Találj ki egy új, kreatív 'Fekete Történetet' (Black Stories) magyarul.
        Legyen morbid, trükkös, de logikus.
        
        A válaszod formátuma SZIGORÚAN a következő legyen (a ||| jelekkel elválasztva):
        CÍM ||| REJTÉLY (amit a játékosok látnak, legyen rövid és talányos) ||| MEGOLDÁS (a teljes sztori)
        
        Példa a kimenetre:
        A szauna ||| Egy hulla van a szaunában és egy tócsa víz. ||| Jégcsappal szúrták le, ami elolvadt.
        """

        response = model.generate_content(prompt)
        text = response.text
        
        # Feldaraboljuk a választ a ||| jelek mentén
        parts = text.split("|||")
        
        if len(parts) >= 3:
            return {
                "title": parts[0].strip(),
                "riddle": parts[1].strip(),
                "solution": parts[2].strip()
            }
        else:
            return None
    except Exception as e:
        st.error(f"Hiba a Gemini AI hívásakor: {e}")
        return None

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Fekete Történetek (Ingyen AI)", layout="centered")

# --- OLDALSÁV ---
st.sidebar.title("Beállítások")
my_name = st.sidebar.text_input("Játékos neve", value="Játékos 1")
role = st.sidebar.radio("Válassz szerepet:", ["Játékos", "Mesélő"])

# API KULCS MEZŐ
api_key = st.sidebar.text_input("Google API Kulcs (Ingyenes)", type="password", help="Szerezd be a aistudio.google.com oldalon")

if st.sidebar.button("Frissítés 🔄"):
    st.rerun()

# --- FŐ KÉPERNYŐ ---
st.title("🕵️ Fekete Történetek + Gemini AI")

# 1. MESÉLŐ NÉZET
if role == "Mesélő":
    st.markdown("---")
    st.subheader("📖 Mesélő Pult")
    
    st.info(f"Aktuális történet: **{state.current_story['title']}**")
    
    # --- AI GENERÁTOR GOMB ---
    with st.expander("✨ Új történet generálása (Ingyen)"):
        if not api_key:
            st.warning("Másold be a Google API kulcsot a bal oldali sávba!")
            st.markdown("[Kattints ide a kulcs beszerzéséhez (Google AI Studio)](https://aistudio.google.com/app/apikey)")
        else:
            if st.button("Generálj egy új rejtélyt!"):
                with st.spinner("A Gemini AI épp egy gyilkosságot tervez..."):
                    new_story = generate_mystery_gemini(api_key)
                    if new_story:
                        state.current_story = new_story
                        state.chat_history = [] # Chat törlése
                        st.success("Új történet sikeresen betöltve!")
                        st.rerun()
                    else:
                        st.error("Az AI válasza nem volt megfelelő formátumú. Próbáld újra!")

    st.markdown("---")
    # Megoldás megjelenítése
    st.write(f"**Rejtély (Játékosok látják):** {state.current_story['riddle']}")
    st.error(f"**MEGOLDÁS (Csak te látod):** {state.current_story['solution']}")
    
    # Válasz gombok kezelése
    if state.chat_history:
        last_msg = state.chat_history[-1]
        if last_msg['type'] == 'question':
            st.write(f"❓ **{last_msg['sender']}**: {last_msg['message']}")
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ IGEN"):
                state.chat_history.append({"sender": "Mesélő", "message": "IGEN", "type": "answer"})
                st.rerun()
            if c2.button("❌ NEM"):
                state.chat_history.append({"sender": "Mesélő", "message": "NEM", "type": "answer"})
                st.rerun()
            if c3.button("⚠️ NEM RELEVÁNS"):
                state.chat_history.append({"sender": "Mesélő", "message": "Nem releváns", "type": "answer"})
                st.rerun()

# 2. JÁTÉKOS NÉZET
else:
    st.markdown("---")
    st.subheader(f"Cím: {state.current_story['title']}")
    st.info(f"**A REJTÉLY:** {state.current_story['riddle']}")
    
    with st.form("q_form", clear_on_submit=True):
        q = st.text_input("Kérdésed (eldöntendő):")
        if st.form_submit_button("Küldés") and q:
            state.chat_history.append({"sender": my_name, "message": q, "type": "question"})
            st.rerun()

# --- CHAT ---
st.markdown("---")
st.write("### Napló")
for chat in state.chat_history:
    icon = "❓" if chat['type'] == 'question' else "📢"
    
    # Formázás: Mesélő válaszai színesben
    if chat['type'] == 'answer':
        if chat['message'] == "IGEN":
            st.success(f"{icon} **Mesélő:** IGEN")
        elif chat['message'] == "NEM":
            st.error(f"{icon} **Mesélő:** NEM")
        else:
            st.warning(f"{icon} **Mesélő:** NEM RELEVÁNS")
    else:
        st.write(f"{icon} **{chat['sender']}**: {chat['message']}")
