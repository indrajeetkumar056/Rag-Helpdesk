# WhatsApp RAG Chatbot

A WhatsApp chatbot powered by Twilio and LangChain that uses Retrieval-Augmented Generation (RAG) to provide intelligent responses based on a custom knowledge base.

## Architecture

```
User (WhatsApp)
      ⬇️
Twilio Webhook (HTTP POST)
      ⬇️
Flask Web Server
      ⬇️
Process Query via RAG System (LangChain + SQLite Vector DB)
      ⬇️
Respond back via Twilio API
```

## Features

- 🤖 **RAG-powered responses** using LangChain and FAISS vector database
- 💬 **WhatsApp integration** via Twilio
- 📚 **Custom knowledge base** with document upload capability
- 💾 **SQLite database** for chat history and document storage
- 🔍 **Semantic search** using HuggingFace embeddings
- 📊 **Chat history tracking** per user
- 🚀 **RESTful API** for management operations

## Prerequisites

1. **Twilio Account**: Sign up at [twilio.com](https://www.twilio.com)
2. **Ollama**: Install and run Ollama locally for LLM inference
3. **Python 3.8+**: Required for running the application

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rag-whatsapp-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` file with your Twilio credentials:
   ```env
   TWILIO_ACCOUNT_SID=AC24a60e345ce5d2f3e9732636da579825
   TWILIO_AUTH_TOKEN=9e28105a96b901196b5596ec24dec564
   TWILIO_PHONE_NUMBER=+14322031555
   ```

4. **Install and start Ollama**:
   ```bash
   # Install Ollama (macOS)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the required model
   ollama pull gemma:2b
   
   # Start Ollama server
   ollama serve
   ```

## Setup Twilio WhatsApp Sandbox

1. **Go to Twilio Console** → Messaging → Try it out → Send a WhatsApp message
2. **Join the sandbox** by sending the provided code to the Twilio WhatsApp number
3. **Configure webhook**:
   - Set the webhook URL to: `https://your-domain.com/webhook`
   - Method: POST

## Usage

### Starting the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Adding Documents to Knowledge Base

Via API:
```bash
curl -X POST http://localhost:5000/add-document \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Company Policy",
    "content": "Our company policy states that employees must..."
  }'
```

### Testing the Chatbot

1. Send a WhatsApp message to your Twilio number
2. The bot will process your query using RAG and respond
3. Check chat history: `GET /chat-history/<phone_number>`

## API Endpoints

### Webhook
- **POST** `/webhook` - Twilio webhook for incoming WhatsApp messages

### Management
- **GET** `/health` - Health check endpoint
- **GET** `/chat-history/<phone_number>` - Get chat history for a phone number
- **POST** `/add-document` - Add a new document to knowledge base

## Project Structure

```
rag-whatsapp-bot/
├── app.py              # Flask API for Twilio webhook
├── rag_engine.py       # RAG (LangChain-based) pipeline
├── db.sqlite3          # SQLite Database for chats and documents
├── requirements.txt    # Python dependencies
├── env_example.txt     # Environment variables template
├── README.md          # This file
└── vector_store/      # FAISS vector database (auto-generated)
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TWILIO_ACCOUNT_SID` | Your Twilio Account SID | Yes |
| `TWILIO_AUTH_TOKEN` | Your Twilio Auth Token | Yes |
| `TWILIO_PHONE_NUMBER` | Your Twilio WhatsApp number | Yes |
| `FLASK_ENV` | Flask environment (development/production) | No |
| `FLASK_DEBUG` | Enable Flask debug mode | No |

### RAG Configuration

The RAG engine uses:
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector Store**: FAISS
- **LLM**: Ollama with `gemma:2b` model
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 100 characters
- **Retrieval**: Top 3 most relevant documents

## Deployment

### Local Development
```bash
python app.py
```

### Production (using Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using ngrok for Testing
```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/

# Expose local server
ngrok http 5000

# Use the ngrok URL as your Twilio webhook
```

## Troubleshooting

### Common Issues

1. **Ollama not running**:
   ```bash
   ollama serve
   ```

2. **Model not found**:
   ```bash
   ollama pull gemma:2b
   ```

3. **Twilio webhook errors**:
   - Check webhook URL is accessible
   - Verify Twilio credentials
   - Check server logs for errors

4. **Vector store issues**:
   - Delete `vector_store/` directory to reset
   - Re-add documents via API

### Logs

The application logs to console. Check for:
- Twilio message delivery status
- RAG processing errors
- Database connection issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Twilio documentation
3. Check LangChain documentation
4. Open an issue in the repository 