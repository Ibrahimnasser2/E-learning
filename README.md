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
ADMIN_PASSWORD=maha1234
```

On startup, the API seeds or syncs the sole **Administrative** account:

| Field | Value |
|-------|--------|
| Email | `eng-maha@gmail.com` |
| Username | `maha` |
| Role | Administrative (`admin`) |
| Password | `maha1234` (override with `ADMIN_PASSWORD` env) |

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

1. Log in at `/login` with username `maha` and password `maha1234`.
2. Open **Admin Console** (`/admin`).
3. Download **two separate templates** (Students + Faculty) and save as `.xlsx`:
   - **Students file:** `الرقم الجامعي`, `الاسم`, `الهاتف`
   - **Faculty file:** `الاسم`, `البريد الجامعي`, `الهاتف`
   Sample files: `test-data/students.xlsx` and `test-data/faculty.xlsx`
4. Upload each Excel file separately in Admin Console (students first, then faculty).
5. Provisioned users log in with their **University ID / account** as username and initial password `MANAMU` + last 4 digits of their ID (e.g. `MANAMU4567`).

### Faculty workflow

1. Log in with faculty credentials provisioned by the administrator.
2. Open **My Courses** and create a course (title, specialization, etc.).
3. Click **Section Roster** — upload `section-roster.xlsx` with **الرقم الجامعي** (and optional **رقم الشعبة**). Sample: `test-data/section-roster.xlsx`
4. Click **Upload Materials** — opens Chat with that course selected. Upload PDFs **for students**; materials are indexed only for students on the roster.
5. Students in that section can open **Chat**, pick the course, and use the AI tutor.

### Students

1. Log in with credentials provisioned by the administrator.
2. Open **My Courses** — only courses your instructor linked via roster appear.
3. Open **Chat**, select your course, and ask questions; answers use that course’s uploaded materials.

Public self-enrollment is disabled; access is roster-based only.

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