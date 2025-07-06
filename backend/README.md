# Nova Chatbot Backend

A high-performance, scalable backend for the Nova Chatbot, featuring advanced topic analysis and conversation management.

## ✨ Features

- **Topic Analysis**: Automatically groups related messages into topics using cosine similarity
- **Dual LLM Integration**: Combines Gemini for analysis and Groq for responses
- **Real-time Processing**: Background tasks for non-blocking operations
- **Redis Caching**: Optimized performance with intelligent cache invalidation
- **RESTful API**: Well-documented endpoints for frontend integration

## 🛠 Project Structure

```
backend/
├── app/
│   ├── firebase/        # Firebase configuration and utilities
│   ├── llm/             # LLM integrations (Gemini, Groq)
│   ├── models/          # Pydantic models
│   ├── routes/          # API routes
│   │   ├── messages.py  # Message and topic endpoints
│   │   └── summaries.py # Summary generation endpoints
│   ├── services/        # Business logic
│   │   ├── topic_service.py  # Topic analysis and management
│   │   └── firebase_service.py  # Firestore operations
│   └── utils/           # Utilities and helpers
│       ├── cache.py     # Redis caching implementation
│       └── config.py    # Application configuration
├── tests/               # Test files
├── .env.example         # Example environment variables
├── .gitignore
├── main.py              # Application entry point
├── README.md            # This file
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nova-chatbot.git
   cd nova-chatbot/backend
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API docs**
   - Open http://localhost:8000/docs in your browser

## 🔍 Topic Analysis

The backend automatically analyzes message content to group related conversations into topics using cosine similarity of TF-IDF vectors.

### How It Works

1. **Message Ingestion**:
   - New messages are stored in Firestore
   - A background task analyzes the message content
   - Messages are assigned to existing or new topics based on similarity

2. **Topic Identification**:
   - Uses TF-IDF vectorization to convert messages to numerical features
   - Applies cosine similarity to find related messages
   - Groups similar messages into topics with automatic keyword extraction

3. **Caching Layer**:
   - Redis caches topic analysis results and recent messages
   - Cache invalidation on message creation/updates
   - Configurable TTL for cache entries

### API Endpoints

- `GET /api/messages/topics/{user_id}` - Get all topics for a user
- `GET /api/messages?topic_id={topic_id}` - Get messages for a specific topic
- `POST /api/messages` - Create a new message (triggers topic analysis)

## ⚙️ Configuration

Key environment variables:

```env
# Redis Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=300  # 5 minutes
CACHE_ENABLED=true

# Topic Analysis
TOPIC_SIMILARITY_THRESHOLD=0.3
MAX_TOPIC_KEYWORDS=5
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

### Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for API endpoints
- `tests/fixtures/` - Test data and fixtures

## 📊 Monitoring & Logging

- **Structured Logging**: JSON-formatted logs for easy parsing
- **Performance Metrics**: Track API response times and cache hit rates
- **Error Tracking**: Sentry integration for production error monitoring

### Logging Configuration

Log levels can be controlled via the `LOG_LEVEL` environment variable:
- `DEBUG`: Detailed debug information
- `INFO`: General operational messages
- `WARNING`: Warnings about non-critical issues
- `ERROR`: Errors that need attention

Example log entry:
```json
{
  "timestamp": "2023-07-06T12:34:56.789Z",
  "level": "INFO",
  "message": "Topic analysis completed",
  "topic_id": "topic_user1_42",
  "duration_ms": 123.45,
  "cache_hit": true
}
```

## 🚀 Deployment

### Production Setup

1. **Environment Setup**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export $(cat .env | xargs)
   ```

2. **Run with Gunicorn** (recommended for production):
   ```bash
   gunicorn app.main:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000 \
     --timeout 120 \
     --log-level info \
     --access-logfile - \
     --error-logfile -
   ```

### 🐳 Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t nova-chatbot-backend .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name nova-backend \
     -p 8000:8000 \
     --env-file .env \
     --restart unless-stopped \
     nova-chatbot-backend
   ```

3. **Docker Compose** (recommended for development):
   ```yaml
   version: '3.8'
   
   services:
     app:
       build: .
       ports:
         - "8000:8000"
       env_file:
         - .env
       depends_on:
         - redis
     
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       volumes:
         - redis_data:/data
   
   volumes:
     redis_data:
   ```

### 🌐 Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Set up your development environment**
   ```bash
   # Fork and clone the repository
   git clone https://github.com/yourusername/nova-chatbot.git
   cd nova-chatbot/backend
   
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the code style (PEP 8, type hints)
   - Write tests for new features
   - Update documentation

4. **Run tests and linters**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black .
   isort .
   flake8
   
   # Check type hints
   mypy .
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   # Then create a PR on GitHub
   ```

### 🏷️ Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

Example:
```
feat(topic): add topic similarity threshold configuration

- Add TOPIC_SIMILARITY_THRESHOLD to settings
- Update topic service to use configurable threshold
- Add validation for threshold values

Closes #123
```

### 🔄 Code Review Process

1. Create a draft PR early for discussion
2. Ensure all tests pass
3. Update documentation if needed
4. Request reviews from maintainers
5. Address all review comments
6. Squash and merge when approved

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
│   ├── __init__.py
│   ├── main.py              # FastAPI app setup
│   ├── firebase/            # Firebase configuration
│   ├── llm/                 # LLM integrations (Gemini, Groq)
│   ├── routes/              # API routes
│   ├── services/            # Business logic
│   └── utils/               # Helpers and utilities
├── tests/                   # Test files
├── .env.example             # Example environment variables
└── requirements.txt         # Python dependencies
```

## Testing

To run tests:

```bash
pytest
```

## Deployment

For production deployment, consider using:

- Gunicorn with Uvicorn workers
- Environment variables for configuration
- Proper logging and monitoring
- Firebase security rules for database access

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Firebase](https://firebase.google.com/)
- Enhanced with [Redis](https://redis.io/)
- AI capabilities from [Google Gemini](https://ai.google.dev/) and [Groq](https://groq.com/)

## 📚 Resources

- [API Documentation](https://api.novachatbot.com/docs)
- [Development Guide](https://github.com/yourusername/nova-chatbot/wiki/Development-Guide)
- [Deployment Guide](https://github.com/yourusername/nova-chatbot/wiki/Deployment-Guide)
- [Troubleshooting](https://github.com/yourusername/nova-chatbot/wiki/Troubleshooting)
