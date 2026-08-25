# Hamza API Service - Intelligent Chatbot

## Project Overview

This project is an intelligent chatbot application that uses RAG (Retrieval-Augmented Generation) technology to provide accurate and useful answers based on uploaded documents. The project consists of:

### Main Components:
- **Backend Server**: Built using FastAPI and Python
- **Frontend**: Built using React.js
- **Database**: PostgreSQL with pgvector for semantic search
- **RAG System**: Combines document search and intelligent text generation

### Key Features:
- ✅ Secure authentication system using JWT
- ✅ File upload and management (PDF)
- ✅ Document indexing for semantic search
- ✅ Intelligent chat with AI bot
- ✅ Modern and user-friendly interface
- ✅ Chat history storage
- ✅ Detailed system statistics

### Technologies Used:
- **Backend**: FastAPI, SQLAlchemy, LangChain, OpenAI
- **Frontend**: React, Axios, React Router
- **Database**: PostgreSQL, pgvector
- **AI**: OpenAI GPT-3.5-turbo, Sentence Transformers

## Project Structure

```
v5/
├── api/                    # Backend Server (FastAPI)
│   ├── main.py            # Main server file
│   ├── models.py          # Data models
│   ├── database.py        # Database settings
│   ├── auth.py            # Authentication system
│   ├── rag_manager_simple.py  # RAG system manager
│   └── requirements.txt   # Python requirements
├── frontend/              # Frontend (React)
│   ├── src/
│   │   ├── App.js         # Main component
│   │   ├── context/       # Authentication context
│   │   ├── services/      # API services
│   │   └── pages/         # Application pages
│   └── package.json       # Node.js requirements
└── backend/               # Database scripts
    ├── init.sql           # Database initialization script
    └── setup_database_windows.py  # Windows setup script
```

## Running Requirements

### Prerequisites:
1. Python 3.8+
2. Node.js 16+
3. PostgreSQL 12+ with pgvector extension
4. OpenAI API key

### Database Setup:
```bash
# Run database setup script
cd backend
python setup_database_windows.py
```

### Backend Server Setup:
```bash
cd api
pip install -r requirements.txt
python main.py
```

### Frontend Setup:
```bash
cd frontend
npm install
npm start
```

## Usage

1. **Registration**: Create a new account or log in
2. **Upload Documents**: Upload PDF files for indexing
3. **Chat**: Start a conversation with the AI bot
4. **Management**: Review chat history and uploaded files

## Security

- Password encryption using bcrypt
- JWT tokens for sessions
- User data isolation
- Endpoint protection

## Contributing

We welcome contributions! Please:
1. Fork the project
2. Create a feature branch
3. Send a Pull Request

## License

This project is licensed under the MIT License.