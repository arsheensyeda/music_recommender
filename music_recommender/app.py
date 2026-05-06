import streamlit as st
import pandas as pd
import mysql.connector
import os
import random
import base64
from datetime import date

# ═══════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════
st.set_page_config(
    page_title="Moodify",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════
SONGS_DIR = "songs"

MOOD_FILES = {
    "happy":     [f"happy{i}.mp3"     for i in range(1, 9)],
    "sad":       [f"sad{i}.mp3"       for i in range(1, 8)],
    "calm":      [f"calm{i}.mp3"      for i in range(1, 9)],
    "energetic": [f"upbeat{i}.mp3"    for i in range(1, 9)],
    "romantic":  [f"love{i}.mp3"      for i in range(1, 10)],
    "adventure": [f"adventure{i}.mp3" for i in range(1, 7)],
}

MOOD_DISPLAY_NAMES = {
    "happy":     "Happy 😊",
    "sad":       "Sad 💙",
    "calm":      "Calm 🌿",
    "energetic": "Energetic ⚡",
    "romantic":  "Romantic 🌹",
    "adventure": "Adventurous 🏔️",
}

MOOD_COLORS = {
    "happy":     "#FFD93D",
    "sad":       "#4D96FF",
    "calm":      "#43D9A2",
    "energetic": "#FF4C4C",
    "romantic":  "#FF6EB4",
    "adventure": "#FF9A3C",
}

MOOD_GRADIENTS = {
    "happy":     "linear-gradient(135deg, #FFD93D18, #FF990010)",
    "sad":       "linear-gradient(135deg, #4D96FF18, #1a3a6010)",
    "calm":      "linear-gradient(135deg, #43D9A218, #00897B10)",
    "energetic": "linear-gradient(135deg, #FF4C4C18, #FF990010)",
    "romantic":  "linear-gradient(135deg, #FF6EB418, #c2185b10)",
    "adventure": "linear-gradient(135deg, #FF9A3C18, #e65c0010)",
}

# ═══════════════════════════════════════════════
#  DATABASE  — self-healing, no manual SQL needed
# ═══════════════════════════════════════════════
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Arsh#7819",
        database="music_ai"
    )

def init_db():
    conn   = get_connection()
    cursor = conn.cursor()

    # users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            name       VARCHAR(255) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # user_logs — create with username column from scratch
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_logs (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            username   VARCHAR(255),
            user_input TEXT,
            mood       VARCHAR(100),
            timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # If user_logs was created without username column (old version), add it
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'music_ai'
          AND TABLE_NAME   = 'user_logs'
          AND COLUMN_NAME  = 'username'
    """)
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE user_logs ADD COLUMN username VARCHAR(255) AFTER id")

    # song_plays table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS song_plays (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            song_name   VARCHAR(255),
            mood        VARCHAR(100),
            play_count  INT DEFAULT 1,
            last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY  unique_song (song_name)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def upsert_user(name):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT IGNORE INTO users (name) VALUES (%s)", (name,))
    conn.commit()
    cursor.close()
    conn.close()

def log_mood(username, user_input, mood):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_logs (username, user_input, mood) VALUES (%s, %s, %s)",
        (username, user_input, mood)
    )
    conn.commit()
    cursor.close()
    conn.close()

def log_song_play(song_name, mood):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO song_plays (song_name, mood, play_count)
        VALUES (%s, %s, 1)
        ON DUPLICATE KEY UPDATE play_count = play_count + 1, last_played = CURRENT_TIMESTAMP
    """, (song_name, mood))
    conn.commit()
    cursor.close()
    conn.close()

@st.cache_data(ttl=3)
def get_mood_analytics(username=None):
    conn   = get_connection()
    cursor = conn.cursor()
    if username:
        cursor.execute(
            "SELECT mood, COUNT(*) FROM user_logs WHERE username=%s GROUP BY mood ORDER BY COUNT(*) DESC",
            (username,)
        )
    else:
        cursor.execute("SELECT mood, COUNT(*) FROM user_logs GROUP BY mood ORDER BY COUNT(*) DESC")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@st.cache_data(ttl=3)
def get_top_songs(limit=5):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT song_name, mood, play_count FROM song_plays ORDER BY play_count DESC LIMIT %s",
        (limit,)
    )
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@st.cache_data(ttl=3)
def get_mood_journal(username, limit=20):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_input, mood, timestamp FROM user_logs
        WHERE username = %s
        ORDER BY timestamp DESC LIMIT %s
    """, (username, limit))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@st.cache_data(ttl=3)
def get_mood_of_day(username=None):
    conn   = get_connection()
    cursor = conn.cursor()
    today  = date.today().isoformat()
    if username:
        cursor.execute("""
            SELECT mood, COUNT(*) as c FROM user_logs
            WHERE DATE(timestamp)=%s AND username=%s
            GROUP BY mood ORDER BY c DESC LIMIT 1
        """, (today, username))
    else:
        cursor.execute("""
            SELECT mood, COUNT(*) as c FROM user_logs
            WHERE DATE(timestamp)=%s
            GROUP BY mood ORDER BY c DESC LIMIT 1
        """, (today,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

init_db()

# ═══════════════════════════════════════════════
#  MOOD DETECTION
# ═══════════════════════════════════════════════
def detect_mood(text):
    text = text.lower()
    keywords = {
        "happy": [
            "happy","joy","joyful","excited","great","amazing","wonderful","cheerful",
            "delighted","fantastic","good mood","celebrating","blessed","grateful",
            "laughing","smile","smiling","positive","pumped","thrilled","ecstatic",
            "elated","over the moon","stoked","good vibes","feeling good","so good",
            "content","bright","sunny","grinning","gleeful","love life"
        ],
        "sad": [
            "sad","cry","crying","depressed","depression","betrayed","low","heartbroken",
            "miss","lonely","grief","tears","upset","down","hurt","stressed","frustrated",
            "lost","empty","hopeless","devastated","miserable","broken","unhappy","gloomy",
            "melancholy","blue","defeated","exhausted","drained","numb","worthless","alone",
            "abandoned","rejected","failure","terrible","awful","horrible","bad day",
            "feeling low","not okay","not well","teary","weeping","sorrow","aching",
            "heavy heart","regret"
        ],
        "calm": [
            "calm","relaxed","chill","peaceful","quiet","meditate","breathe","serene",
            "tranquil","nervous","anxious","study","focus","reading","sleepy","tired",
            "rest","gentle","slow","soft","mellow","cosy","cozy","wind down","unwind",
            "de-stress","easy","light","still","zen","mindful","night time","morning",
            "coffee","tea","rain","cloudy","library","homework","assignment","work from home"
        ],
        "energetic": [
            "energetic","hyped","gym","workout","run","running","pump","motivated","beast",
            "grind","power","let's go","fired up","hustle","lift","lifting","cardio",
            "sprint","sweat","train","training","strong","beast mode","no pain no gain",
            "crush it","kill it","smash","high energy","lets go","go hard","push","fuel",
            "adrenaline","fast","intense","fire","hype","active","bounce","dance","party",
            "club","jumping"
        ],
        "romantic": [
            "love","romantic","crush","date","miss you","cuddle","together","valentines",
            "heart","relationship","feelings for","in love","falling for","thinking of you",
            "darling","sweetheart","affection","intimacy","warm","tender","soulmate",
            "partner","boyfriend","girlfriend","husband","wife","wedding","kiss",
            "holding hands","moonlight","roses","dinner date","butterflies","adore",
            "cherish","devoted","longing","pine","dreaming of"
        ],
        "adventure": [
            "adventure","adventurous","explore","travel","hike","hiking","journey",
            "road trip","wanderlust","discover","thrill","outdoor","brave","wild",
            "mountains","beach","camping","trek","trekking","backpack","new places",
            "trip","vacation","holiday","fly","flight","passport","spontaneous","epic",
            "bold","fearless","cliff","summit","sunrise","forest","river","sky","free",
            "roam","wander"
        ],
    }
    scores = {m: 0 for m in keywords}
    for mood, kws in keywords.items():
        for kw in kws:
            if kw in text:
                scores[mood] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "happy"

# ═══════════════════════════════════════════════
#  AUDIO HELPERS
# ═══════════════════════════════════════════════
def get_audio_b64(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_songs_for_mood(mood, count=3):
    folder    = os.path.join(SONGS_DIR, mood)
    available = [
        (f, os.path.join(folder, f))
        for f in MOOD_FILES.get(mood, [])
        if os.path.exists(os.path.join(folder, f))
    ]
    return random.sample(available, min(count, len(available))) if available else []

# ═══════════════════════════════════════════════
#  WAVEFORM
# ═══════════════════════════════════════════════
def render_waveform(audio_b64, color, song_key):
    return f"""
<style>
#wfw_{song_key}{{
    background:#0a0e18;border:1px solid #1a2235;border-radius:16px;
    padding:14px 16px 14px;box-shadow:0 4px 24px rgba(0,0,0,0.5);
}}
#wftop_{song_key}{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;}}
#wflbl_{song_key}{{
    font-family:'Courier New',monospace;font-size:8px;
    letter-spacing:.22em;text-transform:uppercase;
    color:{color}80;display:flex;align-items:center;gap:6px;
}}
#wfdot_{song_key}{{width:6px;height:6px;border-radius:50%;background:{color}30;transition:all .3s;}}
#wfdot_{song_key}.on{{background:{color};box-shadow:0 0 8px {color};animation:wp_{song_key} 1.2s ease-in-out infinite;}}
@keyframes wp_{song_key}{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(.7)}}}}
#wffrq_{song_key}{{font-family:'Courier New',monospace;font-size:8px;color:{color}40;}}
#wfcanvas_{song_key}{{width:100%;height:90px;display:block;border-radius:8px;}}
#wfcontrols_{song_key}{{display:flex;align-items:center;gap:10px;margin-top:10px;}}
#wfbtn_{song_key}{{
    width:34px;height:34px;border-radius:50%;border:1px solid {color}50;
    background:{color}15;color:{color};cursor:pointer;font-size:13px;
    display:flex;align-items:center;justify-content:center;flex-shrink:0;
    transition:all .2s;
}}
#wfbtn_{song_key}:hover{{background:{color}30;}}
#wfbar_{song_key}{{
    flex:1;height:3px;border-radius:2px;
    background:{color}20;cursor:pointer;position:relative;overflow:hidden;
}}
#wfprog_{song_key}{{height:100%;background:{color};border-radius:2px;width:0%;transition:width .1s linear;}}
#wftime_{song_key}{{font-family:'Courier New',monospace;font-size:9px;color:{color}50;flex-shrink:0;}}
</style>
<div id="wfw_{song_key}">
  <div id="wftop_{song_key}">
    <div id="wflbl_{song_key}"><span id="wfdot_{song_key}"></span><span id="wfst_{song_key}">Frequency Visualizer</span></div>
    <span id="wffrq_{song_key}">FFT · 512</span>
  </div>
  <canvas id="wfcanvas_{song_key}" width="900" height="90"></canvas>
  <div id="wfcontrols_{song_key}">
    <button id="wfbtn_{song_key}" onclick="(function(){{var a=document.getElementById('wfau_{song_key}');if(a.paused)a.play();else a.pause();}})()">▶</button>
    <div id="wfbar_{song_key}" onclick="(function(e){{var a=document.getElementById('wfau_{song_key}'),r=document.getElementById('wfbar_{song_key}').getBoundingClientRect();if(!isNaN(a.duration))a.currentTime=((e.clientX-r.left)/r.width)*a.duration;}})(event)">
      <div id="wfprog_{song_key}"></div>
    </div>
    <span id="wftime_{song_key}">0:00 / 0:00</span>
  </div>
  <audio id="wfau_{song_key}" style="display:none">
    <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
  </audio>
</div>
<script>
(function(){{
  const cv =document.getElementById('wfcanvas_{song_key}');
  const au =document.getElementById('wfau_{song_key}');
  const dot=document.getElementById('wfdot_{song_key}');
  const stEl=document.getElementById('wfst_{song_key}');
  const btn=document.getElementById('wfbtn_{song_key}');
  const prog=document.getElementById('wfprog_{song_key}');
  const timeEl=document.getElementById('wftime_{song_key}');
  const cx=cv.getContext('2d');
  const W=cv.width,H=cv.height,MID=H/2;
  const BARS=80,GAP=2,BW=W/BARS;
  const COL='{color}';
  function rgb(h){{return[parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}}
  const [R,G,B]=rgb(COL);
  let aid,analyser,actx,setup=false,playing=false;
  const sh=new Float32Array(BARS).fill(2);

  function fmt(s){{const m=Math.floor(s/60),sec=Math.floor(s%60);return m+':'+(sec<10?'0':'')+sec;}}

  function flat(){{
    cx.clearRect(0,0,W,H);
    cx.strokeStyle=`rgba(${{R}},${{G}},${{B}},.25)`;
    cx.lineWidth=1.5;cx.setLineDash([5,7]);
    cx.beginPath();cx.moveTo(0,MID);cx.lineTo(W,MID);cx.stroke();
    cx.setLineDash([]);
    for(let i=0;i<BARS;i++){{
      cx.fillStyle=`rgba(${{R}},${{G}},${{B}},.12)`;
      cx.fillRect(i*BW+BW/2-.5,MID-4,1,8);
    }}
  }}

  function drawBars(h){{
    cx.clearRect(0,0,W,H);
    cx.strokeStyle=`rgba(${{R}},${{G}},${{B}},.07)`;
    cx.lineWidth=1;cx.setLineDash([]);
    cx.beginPath();cx.moveTo(0,MID);cx.lineTo(W,MID);cx.stroke();
    for(let i=0;i<BARS;i++){{
      const hh=Math.max(4,h[i]),half=hh/2;
      const x=i*BW+GAP/2,bw=BW-GAP;
      const inten=hh/(MID*.9);
      const al=Math.min(.98,.45+inten*.55);
      if(inten>.25){{cx.shadowColor=`rgba(${{R}},${{G}},${{B}},.95)`;cx.shadowBlur=12+inten*22;}}
      else cx.shadowBlur=0;
      const gT=cx.createLinearGradient(x,MID-half,x,MID);
      gT.addColorStop(0,`rgba(${{R}},${{G}},${{B}},${{al}})`);
      gT.addColorStop(1,`rgba(${{R}},${{G}},${{B}},.04)`);
      cx.fillStyle=gT;
      cx.beginPath();cx.roundRect(x,MID-half,bw,half,[3,3,0,0]);cx.fill();
      const gB=cx.createLinearGradient(x,MID,x,MID+half*.6);
      gB.addColorStop(0,`rgba(${{R}},${{G}},${{B}},${{al*.4}})`);
      gB.addColorStop(1,`rgba(${{R}},${{G}},${{B}},.01)`);
      cx.fillStyle=gB;
      cx.beginPath();cx.roundRect(x,MID,bw,half*.6,[0,0,3,3]);cx.fill();
      cx.shadowBlur=0;
    }}
  }}

  function initAudio(){{
    if(setup)return;setup=true;
    actx=new(window.AudioContext||window.webkitAudioContext)();
    analyser=actx.createAnalyser();
    analyser.fftSize=512;analyser.smoothingTimeConstant=.82;
    const src=actx.createMediaElementSource(au);
    src.connect(analyser);analyser.connect(actx.destination);
  }}

  function live(){{
    if(!playing)return;
    aid=requestAnimationFrame(live);
    const d=new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(d);
    const step=Math.floor(d.length/BARS);
    for(let i=0;i<BARS;i++){{
      let s=0;for(let j=0;j<step;j++)s+=d[i*step+j];
      const avg=s/step;
      const bell=1+.6*Math.exp(-Math.pow((i-BARS/2)/(BARS/4),2));
      sh[i]+=(Math.max(4,(avg/255)*MID*.95*bell)-sh[i])*.2;
    }}
    drawBars(sh);
  }}

  au.addEventListener('timeupdate',()=>{{
    if(!isNaN(au.duration)&&au.duration>0){{
      const pct=(au.currentTime/au.duration)*100;
      prog.style.width=pct+'%';
      timeEl.textContent=fmt(au.currentTime)+' / '+fmt(au.duration);
    }}
  }});

  au.addEventListener('play',()=>{{
    initAudio();
    if(actx.state==='suspended')actx.resume();
    playing=true;cancelAnimationFrame(aid);
    dot.classList.add('on');stEl.textContent='Live';btn.textContent='⏸';
    live();
  }});
  au.addEventListener('pause',()=>{{
    playing=false;cancelAnimationFrame(aid);
    dot.classList.remove('on');stEl.textContent='Paused';btn.textContent='▶';
    (function drain(){{
      let any=false;
      for(let i=0;i<BARS;i++){{sh[i]+=(2-sh[i])*.15;if(sh[i]>2.5)any=true;}}
      drawBars(sh);if(any)requestAnimationFrame(drain);else flat();
    }})();
  }});
  au.addEventListener('ended',()=>{{
    playing=false;cancelAnimationFrame(aid);
    dot.classList.remove('on');stEl.textContent='Frequency Visualizer';btn.textContent='▶';
    prog.style.width='0%';timeEl.textContent='0:00 / 0:00';
    for(let i=0;i<BARS;i++)sh[i]=2;flat();
  }});

  flat();
}})();
</script>
"""

# ═══════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,400&display=swap');

*,html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;}
.stApp{background:#080c14!important;color:#d8dae8!important;}
#MainMenu,footer,header{visibility:hidden;}
.stTextInput label{display:none!important;}
.block-container{padding:2rem 3rem!important;max-width:1200px!important;}

[data-testid="collapsedControl"]{display:none!important;}
[data-testid="stSidebarCollapseButton"]{display:none!important;}
button[kind="header"]{display:none!important;}
section[data-testid="stSidebar"]{
    min-width:290px!important;max-width:290px!important;
    transform:translateX(0)!important;
    visibility:visible!important;display:block!important;
    background:#060a12!important;
    border-right:1px solid #111827!important;
}
section[data-testid="stSidebar"] *{color:#c8cad8!important;}

.sb-section{
    font-family:'Syne',sans-serif!important;
    font-size:.82rem;font-weight:700;
    letter-spacing:.2em;text-transform:uppercase;
    color:#8892a4!important;
    margin:1.6rem 0 .8rem;padding-bottom:.5rem;
    border-bottom:1px solid #111827;
}

.hero-wrap{text-align:center;padding:2.5rem 0 1.6rem;}
.hero-logo{
    font-family:'Syne',sans-serif!important;
    font-size:3.6rem;font-weight:800;letter-spacing:-2px;
    background:linear-gradient(135deg,#fff 0%,#8892b0 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    margin:0;line-height:1;
}
.hero-dot{-webkit-text-fill-color:#FF4C4C;}
.hero-sub{
    color:#4a5568;font-size:.76rem;
    letter-spacing:.14em;text-transform:uppercase;margin-top:.6rem;
}
.greeting{
    font-family:'Syne',sans-serif!important;
    font-size:1.05rem;font-weight:700;color:#c8cad8;
    text-align:center;margin-bottom:1.6rem;
}
.input-label{
    font-family:'Syne',sans-serif!important;
    font-size:1rem;font-weight:700;
    letter-spacing:.06em;color:#b8c0d4;margin-bottom:.5rem;
}
.stTextInput>div>div>input{
    background:#0c1120!important;border:1px solid #1e2840!important;
    border-radius:14px!important;color:#e8eaf0!important;
    font-size:1rem!important;padding:1rem 1.2rem!important;
    transition:border-color .2s!important;
}
.stTextInput>div>div>input:focus{
    border-color:#FF4C4C!important;
    box-shadow:0 0 0 3px rgba(255,76,76,.12)!important;
}
.stTextInput>div>div>input::placeholder{color:#283040!important;}

.mood-card{
    border-radius:20px;padding:1.6rem 2rem;
    margin-bottom:1.8rem;border:1px solid rgba(255,255,255,.05);
}
.mood-badge{
    display:inline-flex;align-items:center;gap:.5rem;
    padding:.45rem 1.1rem;border-radius:100px;
    font-family:'Syne',sans-serif!important;
    font-weight:700;font-size:.75rem;
    letter-spacing:.12em;text-transform:uppercase;margin-bottom:.4rem;
}
.mood-card-title{
    font-family:'Syne',sans-serif!important;
    font-size:2rem;font-weight:800;margin:.3rem 0 .2rem;
}
.mood-card-sub{color:#4a5568;font-size:.86rem;}

.section-header{
    font-family:'Syne',sans-serif!important;
    font-size:1rem;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;
    color:#8892a4;margin-bottom:1rem;
    padding-bottom:.5rem;border-bottom:1px solid #0e1420;
}
.song-card{
    background:#0c1120;border:1px solid #1a2235;
    border-radius:16px;padding:1.1rem 1.4rem;margin-bottom:.8rem;
}
.song-number{
    font-family:'Syne',sans-serif!important;
    font-size:.68rem;color:#2e3a50;letter-spacing:.12em;margin-bottom:.25rem;
}
.song-name{
    font-family:'Syne',sans-serif!important;
    font-size:.98rem;font-weight:700;color:#c0c8dc;
}

.top-song-item{
    background:#0c1120;border:1px solid #1a2235;border-radius:12px;
    padding:.8rem 1rem;margin-bottom:.5rem;
    display:flex;justify-content:space-between;align-items:center;
}
.top-song-name{font-size:.85rem;font-weight:500;color:#b0b8cc;}
.top-song-count{
    font-family:'Syne',sans-serif!important;
    font-size:.72rem;font-weight:700;color:#3a4a60;
}
.motd-banner{
    border-radius:14px;padding:.9rem 1.2rem;
    margin-bottom:.8rem;border:1px solid rgba(255,255,255,.04);
}
.motd-label{
    font-family:'Syne',sans-serif!important;
    font-size:.68rem;font-weight:700;
    letter-spacing:.18em;text-transform:uppercase;color:#4a5568;margin-bottom:.12rem;
}
.motd-value{font-family:'Syne',sans-serif!important;font-size:1rem;font-weight:800;}

.journal-entry{
    background:#0c1120;border-left:3px solid transparent;
    border-radius:0 12px 12px 0;padding:.8rem 1rem;margin-bottom:.6rem;
}
.journal-time{font-size:.72rem;color:#3a4a60;margin-bottom:.2rem;}
.journal-text{font-size:.88rem;color:#8892a4;font-style:italic;}
.journal-mood{
    font-family:'Syne',sans-serif!important;
    font-size:.7rem;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;margin-top:.3rem;
}

div[data-testid="stMetric"]{
    background:#0c1120;border:1px solid #1a2235;
    border-radius:12px;padding:.7rem 1rem;
}
div[data-testid="stMetricValue"]>div{color:#c8cad8!important;font-size:1.3rem!important;}
div[data-testid="stMetricLabel"]>div{color:#4a5568!important;font-size:.72rem!important;}

.stTabs [data-baseweb="tab-list"]{
    background:#0c1120!important;border-radius:12px;
    padding:4px;gap:4px;border:1px solid #1a2235;
}
.stTabs [data-baseweb="tab"]{
    background:transparent!important;border-radius:10px!important;
    font-family:'Syne',sans-serif!important;
    font-size:.82rem!important;font-weight:700!important;
    letter-spacing:.08em!important;color:#4a5568!important;
    padding:.5rem 1.4rem!important;
}
.stTabs [aria-selected="true"]{background:#1a2235!important;color:#c8cad8!important;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.5rem!important;}

.stButton>button{
    background:#FF4C4C!important;color:white!important;
    border:none!important;border-radius:10px!important;
    font-family:'Syne',sans-serif!important;
    font-weight:700!important;font-size:.78rem!important;
    letter-spacing:.1em!important;text-transform:uppercase!important;
    padding:.5rem 1.2rem!important;transition:opacity .2s!important;
}
.stButton>button:hover{opacity:.82!important;}

::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:#080c14;}
::-webkit-scrollbar-thumb{background:#1e2840;border-radius:2px;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
#  USER PROFILE GATE
# ═══════════════════════════════════════════════
if "username" not in st.session_state:
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-logo">moodify<span class="hero-dot">.</span></div>
        <div class="hero-sub">Affective Computing-Based Music Recommendation Engine</div>
    </div>
    <div style="max-width:420px;margin:0 auto;text-align:center;padding:1.5rem 0;">
        <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#c8cad8;margin-bottom:.4rem;">
            Welcome 👋
        </div>
        <div style="color:#4a5568;font-size:.9rem;margin-bottom:1.6rem;">
            Enter your name to personalise your experience
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        name_input = st.text_input("Your name", placeholder="e.g. Arsheen", key="name_field")
        if st.button("Let's Go →"):
            if name_input.strip():
                upsert_user(name_input.strip())
                st.session_state["username"] = name_input.strip()
                st.rerun()
            else:
                st.warning("Please enter your name to continue.")
    st.stop()

USERNAME = st.session_state["username"]

# ═══════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:.6rem;padding:.8rem 0 .4rem;">
        <div style="width:34px;height:34px;border-radius:50%;background:#FF4C4C22;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'Syne',sans-serif;font-weight:800;font-size:.95rem;color:#FF4C4C;">
            {USERNAME[0].upper()}
        </div>
        <div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;color:#c8cad8;">
                {USERNAME}
            </div>
            <div style="font-size:.7rem;color:#3a4a60;">Moodify profile</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mood of the Day
    motd = get_mood_of_day(USERNAME)
    if motd:
        mc = MOOD_COLORS.get(motd, "#8892a4")
        mn = MOOD_DISPLAY_NAMES.get(motd, motd.capitalize())
        st.markdown(f"""
        <div class="motd-banner" style="background:{mc}12;border-color:{mc}30;margin-top:.8rem;">
            <div class="motd-label">☀️ Mood of the Day</div>
            <div class="motd-value" style="color:{mc};">{mn}</div>
        </div>
        """, unsafe_allow_html=True)

    # Analytics
    st.markdown('<div class="sb-section">📊 Mood Analytics</div>', unsafe_allow_html=True)
    mood_data = get_mood_analytics(USERNAME)
    if mood_data:
        df = pd.DataFrame(mood_data, columns=["Mood", "Sessions"]).set_index("Mood")
        st.bar_chart(df, color="#4D96FF")
        c1, c2 = st.columns(2)
        with c1: st.metric("Sessions", int(df["Sessions"].sum()))
        with c2: st.metric("Top Mood", df["Sessions"].idxmax().capitalize())
    else:
        st.markdown('<p style="color:#2e3a50;font-size:.83rem;">No sessions yet — describe your mood!</p>', unsafe_allow_html=True)

    # Most Played
    st.markdown('<div class="sb-section">🔥 Most Played</div>', unsafe_allow_html=True)
    top_songs = get_top_songs(5)
    if top_songs:
        for sname, smood, scount in top_songs:
            sc      = MOOD_COLORS.get(smood, "#fff")
            display = sname.replace(".mp3", "").replace("_", " ").title()
            st.markdown(f"""
            <div class="top-song-item">
                <div style="display:flex;align-items:center;gap:.5rem;">
                    <span style="width:7px;height:7px;border-radius:50%;background:{sc};
                                 display:inline-block;flex-shrink:0;box-shadow:0 0 6px {sc}80;"></span>
                    <span class="top-song-name">{display}</span>
                </div>
                <span class="top-song-count">▶ {scount}</span>
            </div>
            """, unsafe_allow_html=True)

        if st.button("▶ Play Top Song"):
            ts_name, ts_mood, _ = top_songs[0]
            ts_path = os.path.join(SONGS_DIR, ts_mood, ts_name)
            if os.path.exists(ts_path):
                st.session_state["quick_play"] = (ts_name, ts_mood, ts_path)
    else:
        st.markdown('<p style="color:#2e3a50;font-size:.83rem;">Play songs to build history.</p>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.8rem;'></div>", unsafe_allow_html=True)
    if st.button("↩ Switch User"):
        del st.session_state["username"]
        st.rerun()

# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════
st.markdown("""
<div class="hero-wrap">
    <div class="hero-logo">moodify<span class="hero-dot">.</span></div>
    <div class="hero-sub">Affective Computing-Based Music Recommendation Engine</div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="greeting">Hey, {USERNAME} 👋 — what are you feeling today?</div>', unsafe_allow_html=True)

tab_home, tab_journal = st.tabs(["🎵  Discover", "📓  Mood Journal"])

# ── DISCOVER ──────────────────────────────────
with tab_home:
    if "quick_play" in st.session_state:
        qname, qmood, qpath = st.session_state.pop("quick_play")
        qc   = MOOD_COLORS.get(qmood, "#fff")
        qb64 = get_audio_b64(qpath)
        st.markdown(
            f'<div class="section-header">▶ Quick Play — {MOOD_DISPLAY_NAMES.get(qmood, qmood)}</div>',
            unsafe_allow_html=True
        )
        st.components.v1.html(render_waveform(qb64, qc, "qp"), height=210)
        st.markdown("<hr style='border-color:#111827;margin:1.5rem 0;'>", unsafe_allow_html=True)

    st.markdown('<div class="input-label">How are you feeling right now?</div>', unsafe_allow_html=True)
    user_input = st.text_input(
        label="mood_input",
        placeholder="e.g. I'm going to the gym, feeling pumped…",
        label_visibility="collapsed"
    )

    if user_input:
        mood  = detect_mood(user_input)
        color = MOOD_COLORS[mood]
        dname = MOOD_DISPLAY_NAMES[mood]
        grad  = MOOD_GRADIENTS[mood]

        log_mood(USERNAME, user_input, mood)
        get_mood_analytics.clear()
        get_mood_of_day.clear()
        get_mood_journal.clear()

        st.markdown(f"""
        <div class="mood-card" style="background:{grad};border-left:3px solid {color};">
            <div class="mood-badge" style="background:{color}20;color:{color};">● Detected Mood</div>
            <div class="mood-card-title" style="color:{color};">{dname}</div>
            <div class="mood-card-sub">Curating tracks matched to your emotional state</div>
        </div>
        """, unsafe_allow_html=True)

        songs = get_songs_for_mood(mood, count=3)
        if songs:
            st.markdown('<div class="section-header">Recommended Tracks</div>', unsafe_allow_html=True)
            for idx, (fname, fpath) in enumerate(songs):
                dsong = fname.replace(".mp3","").replace("_"," ").title()
                ab64  = get_audio_b64(fpath)
                st.markdown(f"""
                <div class="song-card">
                    <div class="song-number">Track {idx+1:02d}</div>
                    <div class="song-name">🎵 {dsong}</div>
                </div>
                """, unsafe_allow_html=True)
                st.components.v1.html(render_waveform(ab64, color, f"{mood}_{idx}"), height=210)
                log_song_play(fname, mood)
                st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)
        else:
            st.warning("No audio files found. Check your songs folder structure.")
    else:
        st.markdown("""
        <div style="text-align:center;padding:3.5rem 0;">
            <div style="font-size:2.6rem;margin-bottom:.8rem;">🎵</div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;color:#2a3a50;font-weight:700;">
                Describe your mood to get started
            </div>
            <div style="font-size:.82rem;margin-top:.4rem;color:#1a2535;">
                Try: "I need to focus and study" · "I'm heartbroken" · "Gym time, let's go!"
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── MOOD JOURNAL ──────────────────────────────
with tab_journal:
    st.markdown('<div class="section-header">📓 Mood Journal</div>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#3a4a60;font-size:.85rem;margin-bottom:1.2rem;">'
        f'Your recent mood sessions, {USERNAME}.</p>',
        unsafe_allow_html=True
    )
    journal = get_mood_journal(USERNAME, limit=20)
    if journal:
        for ei, em, ets in journal:
            ec  = MOOD_COLORS.get(em, "#8892a4")
            en  = MOOD_DISPLAY_NAMES.get(em, em.capitalize())
            ts  = ets.strftime("%d %b %Y · %H:%M") if hasattr(ets,"strftime") else str(ets)
            st.markdown(f"""
            <div class="journal-entry" style="border-left-color:{ec};">
                <div class="journal-time">{ts}</div>
                <div class="journal-text">"{ei}"</div>
                <div class="journal-mood" style="color:{ec};">{en}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 0;">
            <div style="font-size:2rem;margin-bottom:.6rem;">📓</div>
            <div style="font-family:'Syne',sans-serif;font-size:.95rem;color:#2a3a50;font-weight:700;">
                No entries yet
            </div>
            <div style="font-size:.82rem;margin-top:.3rem;color:#1a2535;">
                Start in the Discover tab — every session is saved here
            </div>
        </div>
        """, unsafe_allow_html=True)