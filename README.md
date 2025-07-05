# 🌟 Nova — The Humanlike, Memory-Aware Chatbot

Nova is not just a chatbot — it's a personalized, emotionally intelligent conversational AI designed to mimic the way real humans interact. Inspired by the experience of texting someone on WhatsApp, Nova is powered by cutting-edge LLMs (via Groq and Gemini APIs), long-term memory through Firebase, and a UI that prioritizes realism and context.

---

## 🚀 Core Vision

Nova aims to go beyond simple question-answering. Its goals include:

- 🧠 Long-term & short-term memory of conversations
- 🕒 Context-aware replies based on timestamps ("yesterday", "last week")
- 🔁 Quoted message replies like WhatsApp
- 🧵 Topic-based memory threading (even across weeks)
- ❌ Zero-hallucination mode — always factually grounded in chat history
- 🤖 Realistic, concise or detailed responses depending on tone and topic
- 📜 Scrollable, unified conversation view (no isolated sessions)
- 🗣️ Optional voice replies using TTS

---

## 🔧 Technologies Involved

- **Frontend**: React + Vite (WhatsApp-style UI)
- **Backend**: FastAPI (Python), Firebase Firestore, Gemini + Groq LLM APIs
- **Memory/Storage**: Semantic session summaries, raw message logs, topic tagging
- **LLM Logic**: Smart chaining of Gemini + LLaMA (via Groq), with context injection
- **Extras**: Quoting engine, scroll-to-message, summarization, time-awareness

---

## ✨ Current Status

Nova is currently in the **active development phase**.  
Initial architecture decisions, backend scaffolding, and basic Firebase integration are underway.

---

## 📌 Goals for MVP

- ✅ Firebase message storage & retrieval
- ✅ Quoted message support
- ✅ Dual LLM API integration (Groq + Gemini)
- ✅ Smart backend-driven session detection & summaries
- ⏳ WhatsApp-style frontend with quoting and message metadata
- ⏳ Time-aware, memory-grounded reply engine

---

## 🤝 Contributing

This project is being developed collaboratively with version control and PR reviews in mind.  
More contribution guidelines will be added as the architecture stabilizes.

---

## 🧾 License

MIT License (to be confirmed before public release)

---

Stay tuned. Nova is just getting started. 🌠
