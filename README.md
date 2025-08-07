# RAG Helpdesk - AI-Powered Customer Support System

A comprehensive AI-powered customer support system that combines Retrieval-Augmented Generation (RAG) technology with multiple interfaces including WhatsApp integration and a web-based Streamlit application. This project is specifically designed for NSE (National Stock Exchange) helpdesk operations but can be adapted for any customer support scenario.

## 🚀 Project Overview

This project provides an intelligent customer support solution that leverages historical Q&A data to provide accurate, contextual responses to customer queries. The system includes:

- **WhatsApp Bot**: Real-time customer support via WhatsApp using Twilio integration
- **Web Interface**: Streamlit-based web application for internal support staff
- **RAG Engine**: Advanced retrieval-augmented generation using LangChain and FAISS
- **Knowledge Base**: CSV-based historical Q&A data with vector embeddings

## 📁 Project Structure

```
Rag-Helpdesk-main/
├── rag-whatsapp-bot/           # WhatsApp bot implementation
│   ├── app.py                  # Flask web server for Twilio webhook
│   ├── rag_engine.py           # RAG pipeline implementation
│   ├── setup.py                # Automated setup script
│   ├── requirements.txt        # Python dependencies
│   ├── env_example.txt         # Environment variables template
│   ├── db.sqlite3              # SQLite database for chat history
│   ├── vector_store/           # FAISS vector database (auto-generated)
│   ├── logs/                   # Application logs
│   ├── data/                   # Data storage directory
│   └── README.md               # WhatsApp bot specific documentation
├── QnA.py                      # Streamlit web application
├── call.csv                    # Historical Q&A dataset (3,978 entries)
├── req.txt                     # Alternative requirements file
├── resume.tex                  # Project documentation
└── README.md                   # This file
```

## 🏗️ Architecture

```
User Query (WhatsApp/Web)
         ↓
   RAG Engine (LangChain)
         ↓
   Vector Search (FAISS)
         ↓
   Historical Q&A Context
         ↓
   LLM Response (Ollama)
         ↓
   Response Delivery
```

## 🎯 Key Features

### 🤖 WhatsApp Bot (`rag-whatsapp-bot/`)
- **Real-time messaging** via Twilio WhatsApp API
- **RAG-powered responses** using historical NSE agent data
- **Chat history tracking** with SQLite database
- **Document management** API for knowledge base updates
- **Health monitoring** and status endpoints
- **Automated setup** script for easy deployment

### 🌐 Web Interface (`QnA.py`)
- **Streamlit-based** user-friendly interface
- **Real-time Q&A** with instant responses
- **Document embedding** capabilities
- **Vector store management** with reset functionality
- **Response time tracking** for performance monitoring

### 🧠 RAG Engine (`rag_engine.py`)
- **Advanced embeddings** using HuggingFace models
- **FAISS vector database** for efficient similarity search
- **Ollama integration** for local LLM inference
- **CSV data processing** with automatic chunking
- **Context-aware responses** based on historical patterns

## 📊 Dataset

The system uses `call.csv` containing **3,978 historical Q&A interactions** from NSE helpdesk operations, including:
- Customer queries and agent responses
- File references and summaries
- Categorized support scenarios
- Real-world troubleshooting examples

## 🛠️ Installation & Setup

### Prerequisites

1. **Python 3.8+**
2. **Twilio Account** (for WhatsApp bot)
3. **Ollama** (for local LLM inference)

### Quick Setup

#### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd Rag-Helpdesk-main/rag-whatsapp-bot

# Run automated setup
python setup.py
```

#### Option 2: Manual Setup

1. **Install Python dependencies**:
   ```bash
   pip install -r rag-whatsapp-bot/requirements.txt
   ```

2. **Install Ollama**:
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull required model
   ollama pull phi4-mini:latest
   ```

3. **Configure environment**:
   ```bash
   cp rag-whatsapp-bot/env_example.txt rag-whatsapp-bot/.env
   # Edit .env with your Twilio credentials
   ```

## 🚀 Usage

### WhatsApp Bot

1. **Start the server**:
   ```bash
   cd rag-whatsapp-bot
   python app.py
   ```

2. **Configure Twilio webhook**:
   - Set webhook URL to: `https://your-domain.com/webhook`
   - Method: POST

3. **Test the bot**:
   - Send WhatsApp message to your Twilio number
   - Bot will respond using RAG-powered knowledge

### Web Interface

1. **Launch Streamlit app**:
   ```bash
   streamlit run QnA.py
   ```

2. **Use the interface**:
   - Click "Embed Documents" to load CSV data
   - Enter questions in the text input
   - Get instant AI-powered responses

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TWILIO_ACCOUNT_SID` | Twilio Account SID | Yes (WhatsApp bot) |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token | Yes (WhatsApp bot) |
| `TWILIO_PHONE_NUMBER` | Twilio WhatsApp number | Yes (WhatsApp bot) |
| `FLASK_ENV` | Flask environment | No |
| `FLASK_DEBUG` | Flask debug mode | No |
| `OLLAMA_BASE_URL` | Ollama server URL | No |

### RAG Configuration

- **Embeddings Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: FAISS with local persistence
- **LLM**: Ollama with `phi4-mini:latest` model
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 100 characters
- **Retrieval**: Top 3 most relevant documents

## 📡 API Endpoints

### WhatsApp Bot Endpoints

- **POST** `/webhook` - Twilio webhook for incoming messages
- **GET** `/health` - Health check endpoint
- **GET** `/chat-history/<phone_number>` - Get chat history
- **POST** `/add-document` - Add document to knowledge base
- **POST** `/reload-csv` - Reload CSV data
- **GET** `/csv-status` - Check CSV processing status

## 🗄️ Database Schema

### Chats Table
```sql
CREATE TABLE chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_phone TEXT NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT
);
```

### Documents Table
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Deployment

### Local Development
```bash
# WhatsApp Bot
cd rag-whatsapp-bot
python app.py

# Web Interface
streamlit run QnA.py
```

### Production Deployment

#### Using Gunicorn (WhatsApp Bot)
```bash
cd rag-whatsapp-bot
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Using ngrok for Testing
```bash
# Expose local server
ngrok http 5000

# Use ngrok URL as Twilio webhook
```

## 🔍 Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ```

2. **Model not found**:
   ```bash
   ollama pull phi4-mini:latest
   ```

3. **Vector store issues**:
   ```bash
   # Reset vector store
   rm -rf rag-whatsapp-bot/vector_store/
   ```

4. **Twilio webhook errors**:
   - Verify webhook URL accessibility
   - Check Twilio credentials
   - Review server logs

### Logs and Monitoring

- Application logs are written to console
- Check for Twilio message delivery status
- Monitor RAG processing performance
- Review database connection issues

## 📈 Performance

- **Response Time**: Typically 2-5 seconds
- **Accuracy**: High accuracy based on historical patterns
- **Scalability**: Supports multiple concurrent users
- **Memory Usage**: Optimized with FAISS vector store

## 🔒 Security

- **Environment variables** for sensitive credentials
- **Input validation** on all endpoints
- **SQL injection protection** with parameterized queries
- **Rate limiting** recommended for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Review Twilio documentation
3. Check LangChain documentation
4. Open an issue in the repository

## 🙏 Acknowledgments

- **Twilio** for WhatsApp API integration
- **LangChain** for RAG framework
- **HuggingFace** for embeddings models
- **Ollama** for local LLM inference
- **FAISS** for vector similarity search

## 📞 Contact

For project-specific questions or support, please open an issue in the repository.

---

**Note**: This project is designed for educational and demonstration purposes. For production use, ensure proper security measures and compliance with relevant regulations.
