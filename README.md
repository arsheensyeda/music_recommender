# Moodify — AI Mood-Based Music Recommendation System

Moodify is an AI-powered mood-based music recommendation web application built using Python, Streamlit, and MySQL.

This project was developed as part of a Python Expo conducted at my college, where the goal was to build innovative real-world applications using Python and modern technologies. The system analyzes a user’s emotional state from text input and recommends songs that match their mood in real time.

The project combines affective computing, mood detection, music recommendation, analytics, and an immersive UI experience into a single personalized platform.

---

## - Features

### AI Mood Detection

* Detects user emotions from natural language text input
* Keyword-based affective computing engine
* Supports multiple moods including:

  * Happy 😊
  * Sad 💙
  * Calm 🌿
  * Energetic ⚡
  * Romantic 🌹
  * Adventurous 🏔️

### 🎵 Smart Music Recommendations

* Recommends songs based on detected mood
* Randomized recommendations for variety
* Organized mood-wise audio library
* Built-in waveform audio visualizer

### 📊 User Analytics

* Mood analytics dashboard
* Session tracking
* Most played songs tracking
* Mood of the day detection
* Personalized mood journal history

### 👤 Multi-User Support

* User profile system
* Stores individual mood history
* Personalized recommendations and analytics

### 🎨 Modern UI/UX

* Futuristic dark-themed interface
* Fully responsive Streamlit UI
* Animated waveform music player
* Dynamic mood-based colors and gradients

### 🗄️ Database Integration

* MySQL database support
* Automatic database/table initialization
* Stores:

  * User profiles
  * Mood logs
  * Song play history

---

## 🛠️ Tech Stack

### Frontend

* Streamlit
* HTML/CSS
* Custom JavaScript waveform visualizer

### Backend

* Python
* MySQL

### Libraries Used

* pandas
* mysql-connector-python
* streamlit
* base64
* random
* os

---

## 📂 Project Structure

```bash
Moodify/
│
├── songs/
│   ├── happy/
│   ├── sad/
│   ├── calm/
│   ├── energetic/
│   ├── romantic/
│   └── adventure/
│
├── app.py                 # Main Streamlit application
├── songs.csv              # Song dataset
├── requirements.txt       # Project dependencies
├── README.md              # Documentation
└── assets/                # Screenshots and visuals
```

---

## ⚙️ How It Works

1. User enters how they are feeling.
2. The mood detection engine analyzes keywords in the text.
3. The system identifies the dominant mood.
4. Songs matching that mood are selected.
5. A custom waveform audio player visualizes playback.
6. Mood history and song plays are stored in MySQL.
7. Analytics dashboards update in real time.

---

## 🧠 Mood Detection Engine

Moodify uses a keyword-based affective computing approach.

Example:

```text
Input: “I’m feeling stressed and need to focus.”
Detected Mood: Calm 🌿
```

```text
Input: “Gym time, I’m feeling pumped!”
Detected Mood: Energetic ⚡
```

The engine scans user text for emotionally relevant keywords and maps them to the most suitable mood category.

---

## 🗃️ Database Schema

The application automatically creates the following MySQL tables:

### users

Stores user profiles.

### user_logs

Stores:

* User mood input
* Detected mood
* Timestamp

### song_plays

Stores:

* Song play count
* Mood category
* Last played timestamp

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/moodify.git
cd moodify
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup MySQL Database

Create a MySQL database:

```sql
CREATE DATABASE music_ai;
```

Update your MySQL credentials inside `app.py`.

```python
host="localhost"
user="root"
password="your_password"
database="music_ai"
```

### 4. Add Songs

Create the following folder structure:

```bash
songs/
├── happy/
├── sad/
├── calm/
├── energetic/
├── romantic/
└── adventure/
```

Add `.mp3` files into each folder.

### 5. Run the Application

```bash
streamlit run app.py
```

---

## 🎓 Project Context

Moodify was created for a college Python Expo project presentation.

The project focused on combining:

* Artificial Intelligence
* Affective Computing
* Music Recommendation Systems
* UI/UX Design
* Database Integration

The aim was to build an interactive application capable of understanding user emotions and recommending suitable music experiences in real time.

---

## 🎧 Audio Credits

All songs and audio files used in this project are copyright-free and were included strictly for educational and demonstration purposes.

No copyrighted commercial music has been distributed with this project.

---

## 📸 Screenshots

Add screenshots here.

```bash
assets/homepage.png
assets/recommendations.png
assets/analytics.png
assets/journal.png
```

---

## 🔥 Key Highlights

* AI-powered mood recognition
* Personalized music recommendation engine
* Real-time analytics dashboard
* Audio waveform visualization
* Mood journaling system
* Dynamic mood-based UI theming
* MySQL-powered persistent storage

---

## 📈 Future Improvements

* Spotify API integration
* NLP-based sentiment analysis using transformers
* Machine learning recommendation engine
* Playlist generation
* Emotion detection from voice
* Facial emotion recognition
* Cloud deployment
* User authentication system
* Song liking/disliking system

---

## 📚 Learning Outcomes

This project demonstrates:

* Affective Computing
* AI-based recommendation systems
* Streamlit web app development
* Database integration with MySQL
* Frontend customization in Streamlit
* Audio visualization techniques
* User analytics systems

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👩‍💻 Author

Developed by Arsheen Syeda

---

## 🙌 Acknowledgements

* Streamlit
* MySQL
* Python Open Source Community
* Affective Computing Research
* Open-source music recommendation projects

---

## 📌 Project Reference

The README was generated based on the uploaded `app.py` project implementation. fileciteturn0file0
