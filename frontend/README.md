<<<<<<< HEAD
# hamza-fe
=======
# Hamza - AI Assistant

A professional AI assistant with Retrieval-Augmented Generation (RAG) capabilities, built with React frontend and FastAPI backend.

## Features

### 🤖 AI Assistant
- **Intelligent Chat**: Powered by advanced language models
- **RAG Integration**: Answer questions from your documents
- **Context Awareness**: View sources and references
- **Customizable Settings**: Adjust temperature, output length, and more

### 📁 Document Management
- **File Upload**: Support for multiple file formats
- **Knowledge Base**: Upload PDF documents for RAG processing
- **Document Indexing**: Automatic chunking and vector storage
- **File Organization**: Easy management of uploaded files

### ⚙️ Advanced Settings
- **Temperature Control**: Adjust response creativity (0.0 - 1.0)
- **Output Length**: Choose between short, medium, or long responses
- **Top-K Results**: Control number of context chunks (1-10)
- **Context Display**: Toggle source visibility
- **Auto-scroll**: Automatic chat scrolling

### 🎨 Professional UI
- **Modern Design**: Clean, professional interface
- **Responsive Layout**: Works on desktop and mobile
- **Dark/Light Theme**: Professional color scheme
- **Smooth Animations**: Enhanced user experience
- **Sidebar Navigation**: Easy access to settings and features

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based auth
- **User Registration**: Create new accounts
- **Protected Routes**: Secure access to features
- **Session Management**: Persistent login state

## Tech Stack

### Frontend
- **React 18**: Modern React with hooks
- **React Router**: Client-side routing
- **React Hook Form**: Form validation and handling
- **React Dropzone**: File upload functionality
- **CSS3**: Custom styling with CSS variables

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Reliable database storage
- **SQLAlchemy**: Database ORM
- **JWT**: JSON Web Token authentication
- **Pydantic**: Data validation

### AI/ML
- **RAG Pipeline**: Retrieval-Augmented Generation
- **Vector Storage**: Document embedding and search
- **LLM Integration**: Language model processing
- **Document Processing**: PDF parsing and chunking

## Getting Started

### Prerequisites
- Node.js (v16 or higher)
- Python (v3.8 or higher)
- PostgreSQL database

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hamza-ai-assistant
   ```

2. **Backend Setup**
   ```bash
   cd api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb rag_db
   
   # Run database initialization
   python setup_database.py
   ```

4. **Frontend Setup**
   ```bash
   cd ../chatbot
   npm install
   ```

### Running the Application

1. **Start the Backend**
   ```bash
   cd api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend**
   ```bash
   cd chatbot
   npm start
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Usage

### First Time Setup
1. Register a new account
2. Upload documents to your knowledge base
3. Start chatting with Hamza!

### Chat Features
- **Ask Questions**: Type your questions in the chat
- **Upload Files**: Drag and drop files for processing
- **Adjust Settings**: Use the sidebar to customize AI behavior
- **View Sources**: Click "View Sources" to see document references
- **Export Chats**: Save your conversations as JSON files

### Document Management
- **Upload Documents**: Add PDF files to your knowledge base
- **Monitor Status**: Check document count and processing status
- **Clear Index**: Remove all documents from the knowledge base
- **File Organization**: View and manage uploaded files

## Configuration

### Environment Variables
Create a `.env` file in the `api` directory:

```env
DATABASE_URL=postgresql://postgres:hema1234@localhost/rag_db
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### AI Settings
Adjust the following parameters in the sidebar:
- **Temperature**: Controls response randomness (0.0 = focused, 1.0 = creative)
- **Max Output**: Response length (short/medium/long)
- **Top-K**: Number of context chunks to retrieve
- **Show Context**: Toggle source visibility

## Project Structure

```
hamza-ai-assistant/
├── api/                    # FastAPI backend
│   ├── main.py            # Main application
│   ├── models.py          # Database models
│   ├── auth.py            # Authentication utilities
│   ├── rag_manager_simple.py  # RAG implementation
│   └── requirements.txt   # Python dependencies
├── chatbot/               # React frontend
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── context/       # React context
│   │   ├── services/      # API services
│   │   └── App.js         # Main app component
│   └── package.json       # Node.js dependencies
└── backend/               # Database setup scripts
    ├── init.sql           # Database schema
    └── setup_database.py  # Setup script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review the console for error messages

---

**Hamza** - Your Professional AI Assistant 🤖
>>>>>>> db506b6 (Initial commit: React frontend application(User Authentication - Local)
