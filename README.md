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
- ✅ **Administrative provisioning** — no public sign-up; admin uploads users via Excel
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
```

Create `api/.env` with at least:

```
DATABASE_URL=postgresql://...
PGVECTOR_CONNECTION_STRING=postgresql://...
OPENAI_API_KEY=...
SECRET_KEY=...
ADMIN_PASSWORD=<strong-password-for-admin-account>
```

On first startup, the API seeds the sole **Administrative** account:

| Field | Value |
|-------|--------|
| Email | `eng-maha@gmail.com` |
| Username | `maha` |
| Role | Administrative (`admin`) |
| Password | value of `ADMIN_PASSWORD` |

```bash
python main.py
```

### Frontend Setup:
```bash
cd frontend
npm install
npm start
```

## Usage

### Administrative (MANAMU staff)

1. Log in at `/login` with role **Administrative**, username `maha`, and your `ADMIN_PASSWORD`.
2. Open **Admin Console** (`/admin`).
3. Download the CSV template and fill columns: **Name**, **Email** (role is auto-detected from domain), optional **University ID** / **Specialization**.
   - Students: `{id}@student.kk.edu.sa`
   - Faculty: `{account}@kk.edu.sa`
   - Or provide **University ID** (student) / **Account** (faculty) without email — addresses are generated automatically.
4. Upload the Excel file (`.xlsx` / `.xls`).
5. Provisioned users log in with their **University ID / account** as username and initial password `MANAMU` + last 4 digits of their ID (e.g. `MANAMU4567`).

### Faculty & students

1. Log in with credentials provisioned by the administrator (public registration is disabled).
2. **Faculty**: upload course PDFs and manage courses.
3. **Students**: chat with the AI tutor using indexed materials.

## Security

- Password encryption using bcrypt
- JWT tokens for sessions
- User data isolation
- Endpoint protection
- Single fixed admin email (`eng-maha@gmail.com`); only one administrative account
- `POST /register` disabled — users created only via admin Excel upload

## Contributing

We welcome contributions! Please:
1. Fork the project
2. Create a feature branch
3. Send a Pull Request

## License

This project is licensed under the MIT License.