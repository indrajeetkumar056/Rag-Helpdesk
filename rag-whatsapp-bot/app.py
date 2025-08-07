from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
from rag_engine import RAGEngine
import sqlite3
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize RAG engine
rag_engine = RAGEngine()

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Create chats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT
        )
    ''')
    
    # Create documents table for storing knowledge base
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_chat(user_phone, message, response, session_id=None):
    """Save chat interaction to database"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chats (user_phone, message, response, session_id)
        VALUES (?, ?, ?, ?)
    ''', (user_phone, message, response, session_id))
    
    conn.commit()
    conn.close()

def send_whatsapp_message(to_number, message):
    """Send WhatsApp message using Twilio"""
    try:
        message = twilio_client.messages.create(
            from_=f'whatsapp:{TWILIO_PHONE_NUMBER}',
            body=message,
            to=f'whatsapp:{to_number}'
        )
        logger.info(f"Message sent successfully: {message.sid}")
        return True
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        return False

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages from Twilio"""
    try:
        # Get message details from Twilio
        incoming_msg = request.values.get('Body', '').strip()
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        
        logger.info(f"Received message from {from_number}: {incoming_msg}")
        
        # Generate response using RAG engine
        response = rag_engine.get_response(incoming_msg)
        
        # Save chat to database
        save_chat(from_number, incoming_msg, response)
        
        # Send response back via Twilio
        if send_whatsapp_message(from_number, response):
            # Return TwiML response for webhook
            resp = MessagingResponse()
            resp.message(response)
            return str(resp)
        else:
            # Fallback response if Twilio API fails
            resp = MessagingResponse()
            resp.message("Sorry, I'm having trouble responding right now. Please try again later.")
            return str(resp)
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        resp = MessagingResponse()
        resp.message("Sorry, something went wrong. Please try again.")
        return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/chat-history/<phone_number>', methods=['GET'])
def get_chat_history(phone_number):
    """Get chat history for a specific phone number"""
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response, timestamp 
            FROM chats 
            WHERE user_phone = ? 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''', (phone_number,))
        
        chats = cursor.fetchall()
        conn.close()
        
        chat_history = []
        for chat in chats:
            chat_history.append({
                "message": chat[0],
                "response": chat[1],
                "timestamp": chat[2]
            })
        
        return jsonify({"chats": chat_history})
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

@app.route('/add-document', methods=['POST'])
def add_document():
    """Add a new document to the knowledge base"""
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        
        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400
        
        # Add document to RAG engine
        rag_engine.add_document(title, content)
        
        # Save to database
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents (title, content)
            VALUES (?, ?)
        ''', (title, content))
        
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Document added successfully"})
        
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        return jsonify({"error": "Failed to add document"}), 500

@app.route('/reload-csv', methods=['POST'])
def reload_csv():
    """Reload CSV data from call.csv file"""
    try:
        rag_engine.reload_csv_data()
        return jsonify({"message": "CSV data reloaded successfully"})
        
    except Exception as e:
        logger.error(f"Error reloading CSV: {str(e)}")
        return jsonify({"error": "Failed to reload CSV data"}), 500

@app.route('/csv-status', methods=['GET'])
def csv_status():
    """Get status of CSV data loading"""
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Get CSV data count
        cursor.execute('SELECT COUNT(*) FROM csv_data WHERE source = "call.csv"')
        csv_count = cursor.fetchone()[0]
        
        # Get total documents count
        total_docs = rag_engine.get_document_count()
        
        # Check if call.csv exists
        csv_exists = os.path.exists('call.csv')
        
        conn.close()
        
        return jsonify({
            "csv_file_exists": csv_exists,
            "csv_records_loaded": csv_count,
            "total_documents": total_docs,
            "status": "loaded" if csv_count > 0 else "not_loaded"
        })
        
    except Exception as e:
        logger.error(f"Error getting CSV status: {str(e)}")
        return jsonify({"error": "Failed to get CSV status"}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Initialize RAG engine
    rag_engine.initialize()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000) 