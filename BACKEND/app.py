
import os
import asyncio
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import PyPDF2
import docx
from openpyxl import load_workbook
from collections import deque, defaultdict
import spacy
import re
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-fallback-key')
if 'SQLALCHEMY_DATABASE_URI' not in app.config or not app.config['SQLALCHEMY_DATABASE_URI']:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'app.db')}"
    )
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create database tables
with app.app_context():
    db.create_all()

# ==================== Scraper Component ====================
class MOSDACScraper:
    def __init__(self, base_url, output_dir="extracted_content", max_depth=3):
        self.base_url = base_url
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.visited_urls = set()
        self.to_visit_queue = deque()
        self.allowed_domains = [urlparse(base_url).netloc]
        self.max_depth = max_depth
        self.file_extensions = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]

    # ... [Include all your MOSDACScraper methods here] ...

# ==================== Knowledge Graph Component ==================== 
class KnowledgeGraphBuilder:
    def __init__(self, extracted_content_dir="extracted_content", output_dir="knowledge_graph"):
        self.extracted_content_dir = extracted_content_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.nlp = spacy.load("en_core_web_sm")
        self.entities = defaultdict(set)
        self.relationships = defaultdict(list)

    # ... [Include all your KnowledgeGraphBuilder methods here] ...

# ==================== Chatbot Component ====================
class MOSDACChatbot:

    def __init__(self, kg_dir="knowledge_graph"):
        self.kg_dir = kg_dir
        self.entities = defaultdict(set)
        self.relationships = defaultdict(list)
        self._load_knowledge_graph()

    def _load_knowledge_graph(self):
        # Placeholder: Load entities and relationships from files or database
        # For now, just initialize empty or with sample data if needed
        pass

    # ... [Include all your MOSDACChatbot methods here] ...

# Initialize components
chatbot = MOSDACChatbot()
scraper = MOSDACScraper("https://www.mosdac.gov.in")
kg_builder = KnowledgeGraphBuilder()

# ==================== API Routes ====================
@app.route('/api/scrape', methods=['POST'])
async def run_scraper():
    try:
        data = request.get_json()
        start_url = data.get('url', 'https://www.mosdac.gov.in')
        await scraper.scrape(start_url)
        return jsonify({"status": "success", "message": "Scraping completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/build-kg', methods=['POST'])
def build_knowledge_graph():
    try:
        kg_builder.build_graph()
        return jsonify({"status": "success", "message": "Knowledge graph built"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        response = chatbot.answer_query(data['query'])
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve Frontend

@app.route('/')
def serve_frontend():
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return "<h1>Frontend not built. Please build the frontend or add index.html to the static folder.</h1>", 200

@app.errorhandler(404)
def not_found(e):
    index_path = os.path.join(app.static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(app.static_folder, 'index.html'), 404
    else:
        return jsonify({"error": "Not found"}), 404

# Health Check
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "services": ["scraper", "knowledge-graph", "chatbot"]
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False') == 'true')