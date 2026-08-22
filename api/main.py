# استيراد المكتبات المطلوبة لبناء واجهة برمجة التطبيقات
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends, status, Body, Form
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, defer
from sqlalchemy.sql import func
from typing import List, Optional
from pydantic import BaseModel
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import os
import uuid
import shutil
import tempfile
from datetime import timedelta, datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy import or_, and_
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

# Load api/.env before importing modules that require env vars
load_dotenv(Path(__file__).resolve().parent / ".env")

# Local imports (works with Root Directory=api on Render, and with uvicorn api.main:app)
try:
    from database import get_db, User, ChatMessage, UploadedFile, Course, CourseEnrollment, create_tables, SessionLocal
    from auth import (
        get_password_hash,
        verify_password,
        create_access_token,
        get_current_user,
        authenticate_user,
        ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    from models import (
        UserRegister, UserLogin, UserResponse, Token,
        ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse,
        FileUploadResponse, FileListResponse,
        ChatResponse, DocumentUploadResponse, IndexStats,
        CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
        CourseEnrollmentRequest, CourseEnrollmentResponse,
    )
    from rag_manager_simple import RAGManagerPGVector
except ImportError:
    from api.database import get_db, User, ChatMessage, UploadedFile, Course, CourseEnrollment, create_tables, SessionLocal
    from api.auth import (
        get_password_hash,
        verify_password,
        create_access_token,
        get_current_user,
        authenticate_user,
        ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    from api.models import (
        UserRegister, UserLogin, UserResponse, Token,
        ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse,
        FileUploadResponse, FileListResponse,
        ChatResponse, DocumentUploadResponse, IndexStats,
        CourseCreate, CourseUpdate, CourseResponse, CourseListResponse,
        CourseEnrollmentRequest, CourseEnrollmentResponse,
    )
    from api.rag_manager_simple import RAGManagerPGVector

# تهيئة مدير RAG كمتغير عام
rag_manager = None

# إنشاء مجلد الملفات المرفوعة
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Store conversation history for general chat (in-memory, simple approach)
general_chat_history = {}  # {session_id: [{"role": "user/assistant", "content": "..."}]}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    دالة إدارة دورة حياة التطبيق
    تقوم بتهيئة قاعدة البيانات ومدير RAG عند بدء التطبيق
    وتنظيف الموارد عند إغلاق التطبيق
    """
    # بدء التشغيل
    global rag_manager
    # إنشاء جداول قاعدة البيانات
    create_tables()
    
    try:
        rag_manager = RAGManagerPGVector()
        print("✅ RAG Manager with PGVector initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG Manager: {e}")
        rag_manager = None
    
    yield
    
    # إغلاق التطبيق
    print("Shutting down application...")

# إنشاء تطبيق FastAPI مع إعدادات دورة الحياة
app = FastAPI(
    title="Students Support API", 
    version="2.0.0",
    lifespan=lifespan
)

# تكوين CORS للسماح بالاتصال من تطبيق React / frontend المنشور
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != ["*"] else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """نقطة نهاية أساسية للتحقق من تشغيل الخادم"""
    return {"message": "Students Support API is running!"}

@app.head("/")
async def root_head():
    """Render health checks use HEAD /"""
    return {"message": "ok"}

@app.get("/health")
async def health_check():
    """نقطة نهاية فحص صحة الخادم ومدير RAG"""
    return {"status": "healthy", "rag_manager_ready": rag_manager is not None}

class GeneralChatRequest(BaseModel):
    message: str
    enable_web_search: Optional[bool] = False
    session_id: Optional[str] = None  # Optional session ID for conversation history

class GeneralChatResponse(BaseModel):
    response: str

# نقاط نهاية المصادقة
@app.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    print("hemaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:", user_data)
    print("Received user_data:", user_data)
    """
    تسجيل مستخدم جديد
    يتحقق من عدم وجود اسم المستخدم أو البريد الإلكتروني مسبقاً
    """
    # التحقق من وجود اسم المستخدم مسبقاً
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # التحقق من وجود البريد الإلكتروني مسبقاً
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # إنشاء مستخدم جديد مع تشفير كلمة المرور
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role,  # Ensure role is saved
        specialization=user_data.specialization if user_data.specialization else None
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.from_orm(db_user)

@app.post("/chat/general", response_model=GeneralChatResponse)
async def general_chat(request: GeneralChatRequest):
    """
    نقطة نهاية للدردشة العامة التي لا تتطلب تسجيل دخول
    تستخدم نظام RAG للرد على الاستفسارات العامة
    يدعم البحث على الويب عند تفعيله
    """
    logger.info(f"Received general chat request: {request.message}, web_search: {request.enable_web_search}")
    
    if not rag_manager:
        logger.error("RAG system is not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="نظام الرد الآلي غير جاهز. يرجى المحاولة مرة أخرى بعد قليل."
        )
    
    try:
        if not request.message or not request.message.strip():
            raise ValueError("الرسالة فارغة")
        
        # Get all files marked for students (public documents)
        db = next(get_db())
        
        general_files = db.query(UploadedFile).filter(
            UploadedFile.target_roles.contains(["student"])
        ).filter(UploadedFile.filename.isnot(None)).all()
        
        file_paths = [os.path.join(UPLOADS_DIR, str(f.filename)) for f in general_files if f.filename is not None]
        
        # Create a temporary user for general chat
        temp_user_id = 999999  # Use a special ID for general chat
        
        # Never index during chat — only search already-indexed docs
        context_texts = []
        try:
            retrieved_docs = rag_manager.query(request.message, temp_user_id, top_k=3)
            context_texts = retrieved_docs if retrieved_docs else []
            logger.info(f"Found {len(context_texts)} relevant documents for general inquiry")
        except Exception as e:
            logger.warning(f"Error querying documents: {e}")
            context_texts = []
        
        # Detect language of the question
        detected_language = detect_language(request.message)
        language_instruction = get_language_instruction(detected_language)
        logger.info(f"🌐 Detected language: {detected_language} for question: {request.message[:50]}...")
        
        # Get conversation history for general chat
        session_id = request.session_id or "default"
        if session_id not in general_chat_history:
            general_chat_history[session_id] = []
        
        conversation_history = general_chat_history[session_id]
        conversation_context = ""
        if conversation_history:
            # Build conversation context from history
            context_parts = []
            for msg in conversation_history[-4:]:  # Last 4 messages (2 exchanges)
                context_parts.append(f"{msg['role'].title()}: {msg['content']}")
            conversation_context = "\n".join(context_parts)
        
        # Generate initial answer using RAG
        internal_answer = None
        web_search_results = None
        used_web_search = False
        previous_web_search_results = None
        
        if context_texts:
            # Use the retrieved document context
            document_context = "\n\n".join(context_texts)
            full_context = f"{language_instruction}\n\nDocument Context:\n{document_context}\n\nUser Question: {request.message}"
            internal_answer = rag_manager.generate_answer(
                full_context,
                temp_user_id,
                top_k=3,
                context_texts=context_texts,
            )
        else:
            full_context = f"{language_instruction}\n\nUser Question: {request.message}"
            parts = list(rag_manager.generate_from_context(full_context, [], stream=False))
            internal_answer = parts[0] if parts else "No indexed documents found yet."
        
        # Check if this is a follow-up question (like "in more details", "tell me more", etc.)
        follow_up_indicators = [
            "in more detail", "in more details", "tell me more", "more information",
            "أخبرني أكثر", "المزيد من التفاصيل", "تفاصيل أكثر", "مزيد من المعلومات"
        ]
        is_follow_up = any(indicator.lower() in request.message.lower() for indicator in follow_up_indicators)
        
        # If it's a follow-up and we have previous web search results, try to reuse them
        if is_follow_up and conversation_history:
            # Look for previous web search results in conversation history
            for msg in reversed(conversation_history):
                if msg.get('web_search_results'):
                    previous_web_search_results = msg['web_search_results']
                    logger.info("📋 Reusing previous web search results for follow-up question")
                    break
        
        # Agentic AI: If web search is enabled, ALWAYS perform web search and prioritize results
        if request.enable_web_search:
            logger.info("🔍 Web search enabled, performing search...")
            try:
                # Perform web search (unless we're reusing previous results for follow-up)
                if previous_web_search_results and is_follow_up:
                    web_search_results = previous_web_search_results
                    logger.info("♻️ Reusing previous web search results")
                else:
                    search_query = request.message
                    # If it's a follow-up, enhance the search query with context
                    if is_follow_up and conversation_context:
                        # Extract the main topic from conversation history
                        search_query = f"{conversation_context.split('User:')[-1].split('Assistant:')[0].strip()} {request.message}"
                    web_search_results = perform_web_search(search_query, max_results=5)
                
                if web_search_results:
                    used_web_search = True
                    # Prioritize web search results - use them as primary source
                    web_context = "\n\n".join([f"Source: {r.get('title', 'Unknown')}\n{r.get('snippet', '')}" for r in web_search_results[:3]])
                    
                    # Create a STRONG prompt that forces use of web search results
                    # Include conversation history for context understanding
                    conversation_part = ""
                    if conversation_context:
                        conversation_part = f"\n\nPREVIOUS CONVERSATION:\n{conversation_context}\n"
                    
                    follow_up_instruction = ""
                    if is_follow_up:
                        follow_up_instruction = "\n- This is a FOLLOW-UP question asking for MORE DETAILS about the previous topic. Provide additional detailed information from the web search results."
                    
                    web_search_prompt = f"""{language_instruction}

CRITICAL INSTRUCTIONS:
- You MUST use the web search results below to answer the question
- The web search results contain the answer - DO NOT say you don't have information
- Extract the relevant information from the web search results and provide it
- Respond ONLY in the same language as the user's question{follow_up_instruction}
- If this is a follow-up question (like "in more details"), provide MORE DETAILED information from the web search results about the previous topic

WEB SEARCH RESULTS (USE THIS INFORMATION - IT CONTAINS THE ANSWER):
{web_context}{conversation_part}
USER QUESTION: {request.message}

Now provide a direct answer using the web search results above. Do NOT say you don't have information - the information is in the web search results. If this is a follow-up question, provide more detailed information."""
                    
                    # Build messages with conversation history for better context
                    messages = [
                        {"role": "system", "content": f"{language_instruction}\n\nYou are a helpful assistant. You MUST use the provided web search results to answer questions. Never say you don't have information when web search results are provided. Understand follow-up questions in context."}
                    ]
                    
                    # Add conversation history as context
                    if conversation_history:
                        for msg in conversation_history[-4:]:  # Last 4 messages
                            messages.append({"role": msg['role'], "content": msg['content']})
                    
                    # Add current question
                    messages.append({"role": "user", "content": web_search_prompt})
                    
                    # Use Groq chat client for web-search answers
                    try:
                        response_obj = rag_manager.client.chat.completions.create(
                            model=rag_manager.chat_model,
                            messages=messages,
                            temperature=0.8,
                            max_tokens=512
                        )
                        response = response_obj.choices[0].message.content
                        logger.info(f"✅ Generated answer from web search results")
                    except Exception as e:
                        logger.error(f"Error generating answer from web search: {e}")
                        response = internal_answer or rag_manager._friendly_openai_error(e)
                else:
                    # Web search failed, use internal answer
                    logger.warning("Web search returned no results, using internal answer")
                    response = internal_answer
            except Exception as e:
                logger.error(f"Error in web search: {str(e)}")
                # Fallback to internal answer if web search fails
                response = internal_answer
        else:
            # Web search not enabled, use internal answer
            response = internal_answer
        
        logger.info(f"Generated response for message: {request.message[:50]}... (web_search_used: {used_web_search})")
        
        # Update conversation history
        general_chat_history[session_id].append({"role": "user", "content": request.message})
        general_chat_history[session_id].append({
            "role": "assistant", 
            "content": response,
            "web_search_results": web_search_results if used_web_search else None
        })
        # Keep only last 10 messages to avoid memory issues
        if len(general_chat_history[session_id]) > 10:
            general_chat_history[session_id] = general_chat_history[session_id][-10:]
        
        return GeneralChatResponse(response=response)
    except ValueError as ve:
        logger.warning(f"Invalid input: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="حدث خطأ في معالجة الرسالة. التفاصيل: " + str(e)
        )

@app.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    تسجيل دخول المستخدم وإرجاع رمز JWT
    يتحقق من صحة بيانات الاعتماد وإنشاء رمز الوصول
    """
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # تحقق من تطابق الدور
    if user.role != user_credentials.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect role for this account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """الحصول على معلومات المستخدم الحالي"""
    return UserResponse.from_orm(current_user)

# نقاط نهاية المحادثة (محمية)
@app.get("/chat", response_model=ChatHistoryResponse)
async def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """الحصول على سجل محادثات المستخدم"""
    messages = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).order_by(ChatMessage.created_at).all()
    return ChatHistoryResponse(messages=[ChatMessageResponse.from_orm(msg) for msg in messages])

def detect_language(text: str) -> str:
    """
    Detect the language of the input text
    Returns 'ar' for Arabic, 'en' for English
    """
    if not text:
        return 'en'
    
    # Check for Arabic characters (Unicode range for Arabic)
    arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F' or '\u08A0' <= char <= '\u08FF' or '\uFB50' <= char <= '\uFDFF' or '\uFE70' <= char <= '\uFEFF')
    total_chars = len([c for c in text if c.isalpha()])
    
    # If more than 30% of alphabetic characters are Arabic, consider it Arabic
    if total_chars > 0 and (arabic_chars / total_chars) > 0.3:
        return 'ar'
    
    return 'en'

def get_language_instruction(language: str) -> str:
    """
    Get the language instruction for the LLM based on detected language
    """
    if language == 'ar':
        return "IMPORTANT: You MUST respond in Arabic (العربية). Use the same language as the user's question. Write your entire response in Arabic."
    else:
        return "IMPORTANT: You MUST respond in English. Use the same language as the user's question."

def extract_youtube_thumbnail(url: str) -> Optional[str]:
    """
    Extract YouTube video thumbnail URL from a YouTube video URL
    Supports various YouTube URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    """
    if not url:
        return None
    
    try:
        # Extract video ID from various YouTube URL formats
        video_id = None
        
        # Pattern 1: youtube.com/watch?v=VIDEO_ID
        match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})', url)
        if match:
            video_id = match.group(1)
        
        if video_id:
            # YouTube thumbnail URLs - maxresdefault is highest quality, fallback to hqdefault
            # Format: https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            logger.info(f"✅ Extracted YouTube thumbnail: {thumbnail_url}")
            return thumbnail_url
        else:
            logger.warning(f"⚠️ Could not extract video ID from URL: {url}")
            return None
    except Exception as e:
        logger.error(f"❌ Error extracting YouTube thumbnail: {e}")
        return None

def perform_web_search(query: str, max_results: int = 5) -> List[dict]:
    """
    Perform web search using Tavily API
    Returns a list of search results with title, snippet, and url
    """
    try:
        from tavily import TavilyClient
        
        # Get Tavily API key from environment or use default
        tavily_api_key = os.getenv('TAVILY_API_KEY')
        if not tavily_api_key:
            raise HTTPException(status_code=500, detail="TAVILY_API_KEY is not configured")
        
        logger.info(f"🔍 Performing web search with Tavily for: {query[:50]}...")
        
        # Initialize Tavily client
        tavily_client = TavilyClient(api_key=tavily_api_key)
        
        # Perform search
        search_response = tavily_client.search(
            query=query,
            max_results=max_results,
            search_depth="basic"  # Can be "basic" or "advanced"
        )
        
        results = []
        if search_response and 'results' in search_response:
            for result in search_response['results']:
                    results.append({
                    'title': result.get('title', '')[:200],
                    'snippet': result.get('content', '')[:300] if result.get('content') else result.get('snippet', '')[:300],
                    'url': result.get('url', '')
                })
        
        if results:
            logger.info(f"✅ Web search successful with Tavily: {len(results)} results found")
        else:
            logger.warning("⚠️ No search results found from Tavily")
        
        return results[:max_results]
    except ImportError:
        logger.error("❌ tavily-python library not installed. Please install it with: pip install tavily-python")
        return []
    except Exception as e:
        logger.error(f"❌ Error performing web search with Tavily: {e}")
        return []

@app.post("/chat", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إرسال رسالة والحصول على رد من روبوت المحادثة
    يستخدم نظام RAG للبحث في الوثائق وتوليد إجابة ذكية
    يدعم السياق للمحادثات المتتالية
    """
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")
    try:
        top_k = message_data.top_k or 3
        
        # Get recent chat history for context
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).order_by(ChatMessage.created_at.desc()).limit(5).all()
        
        # Build context from recent messages
        context_messages = []
        for msg in reversed(recent_messages):  # Reverse to get chronological order
            context_messages.append(f"User: {msg.message}")
            context_messages.append(f"Assistant: {msg.response}")
        
        # Add current message
        context_messages.append(f"User: {message_data.message}")
        
        # Join context
        conversation_context = "\n".join(context_messages)
        
        # تحديد الملفات المسموح بها حسب الدور والتخصص
        files_query = db.query(UploadedFile)
        if current_user.role == "faculty":
            # Faculty can access both public (student) and private (faculty) documents
            allowed_files = files_query.filter(
                or_(UploadedFile.target_roles.contains(["faculty"]),
                    UploadedFile.target_roles.contains(["student"]))
            ).filter(UploadedFile.filename.isnot(None)).all()
        elif current_user.role == "student":
            # Students can only access public documents (targeted to students) matching their specialization
            student_files_query = files_query.filter(
                UploadedFile.target_roles.contains(["student"])
            ).filter(UploadedFile.filename.isnot(None))
            # Filter by specialization
            allowed_files = student_files_query.filter(
                or_(
                    UploadedFile.specialization == current_user.specialization,
                    UploadedFile.specialization.is_(None)  # Include files without specialization (for backward compatibility)
                )
            ).all()
        else:
            allowed_files = []
        
        file_paths = [os.path.join(UPLOADS_DIR, str(f.filename)) for f in allowed_files if f.filename is not None]

        # Chat never indexes — indexing happens only at upload time.
        # Search the already-indexed vectors for this user.
        context_texts = []
        indexing_info = {"files_indexed": 0, "message": "Using pre-indexed documents only"}
        try:
            print(f"🔍 Searching indexed docs for user {current_user.id}: {message_data.message[:100]}...")
            context_texts = rag_manager.query(message_data.message, current_user.id, top_k=top_k) or []
            indexing_info["documents_found"] = len(context_texts)
            print(f"📄 Found {len(context_texts)} documents")
        except Exception as e:
            print(f"❌ Error querying documents: {e}")
            context_texts = []
            indexing_info = {"files_indexed": 0, "message": f"Error querying documents: {str(e)}"}
        
        # Detect language of the question
        detected_language = detect_language(message_data.message)
        language_instruction = get_language_instruction(detected_language)
        logger.info(f"🌐 Detected language: {detected_language} for question: {message_data.message[:50]}...")
        
        # توليد الإجابة باستخدام السياق المسترجع والمحادثة السابقة
        internal_answer = None
        web_search_results = None
        used_web_search = False
        
        if context_texts:
            # Use the retrieved document context along with conversation context
            document_context = "\n\n".join(context_texts)
            full_context = f"{language_instruction}\n\nDocument Context:\n{document_context}\n\nConversation:\n{conversation_context}"
            internal_answer = rag_manager.generate_answer(
                full_context,
                current_user.id,
                top_k=top_k,
                context_texts=context_texts,
            )
        else:
            # No docs: answer from conversation only (no second vector search)
            full_context = f"{language_instruction}\n\nConversation:\n{conversation_context}"
            parts = list(rag_manager.generate_from_context(full_context, [], stream=False))
            internal_answer = parts[0] if parts else "No indexed documents found for your account yet."

        # Agentic AI: If web search is enabled, ALWAYS perform web search and prioritize results
        if message_data.enable_web_search:
            logger.info("🔍 Web search enabled, performing search...")
            try:
                # Perform web search
                search_query = message_data.message
                web_search_results = perform_web_search(search_query, max_results=5)
                
                if web_search_results:
                    used_web_search = True
                    # Prioritize web search results - use them as primary source
                    web_context = "\n\n".join([f"Source: {r.get('title', 'Unknown')}\n{r.get('snippet', '')}" for r in web_search_results[:3]])
                    
                    # Check if this is a follow-up question
                    follow_up_indicators = [
                        "in more detail", "in more details", "tell me more", "more information",
                        "أخبرني أكثر", "المزيد من التفاصيل", "تفاصيل أكثر", "مزيد من المعلومات"
                    ]
                    is_follow_up = any(indicator.lower() in message_data.message.lower() for indicator in follow_up_indicators)
                    
                    follow_up_instruction = ""
                    if is_follow_up:
                        follow_up_instruction = "\n- This is a FOLLOW-UP question asking for MORE DETAILS about the previous topic. Provide additional detailed information from the web search results."
                    
                    # Create a STRONG prompt that forces use of web search results
                    web_search_prompt = f"""{language_instruction}

CRITICAL INSTRUCTIONS:
- You MUST use the web search results below to answer the question
- The web search results contain the answer - DO NOT say you don't have information
- Extract the relevant information from the web search results and provide it
- Respond ONLY in the same language as the user's question{follow_up_instruction}
- If this is a follow-up question (like "in more details"), provide MORE DETAILED information from the web search results about the previous topic

WEB SEARCH RESULTS (USE THIS INFORMATION - IT CONTAINS THE ANSWER):
{web_context}

CONVERSATION HISTORY:
{conversation_context}

USER QUESTION: {message_data.message}

Now provide a direct answer using the web search results above. Do NOT say you don't have information - the information is in the web search results. If this is a follow-up question, provide more detailed information."""
                    
                    # Build messages with conversation history for better context
                    messages = [
                        {"role": "system", "content": f"{language_instruction}\n\nYou are a helpful assistant. You MUST use the provided web search results to answer questions. Never say you don't have information when web search results are provided. Understand follow-up questions in context."}
                    ]
                    
                    # Add conversation history as context messages
                    if conversation_context:
                        # Parse conversation context and add as messages
                        context_lines = conversation_context.split('\n')
                        for line in context_lines[-8:]:  # Last 8 lines (4 exchanges)
                            if line.startswith('User:'):
                                messages.append({"role": "user", "content": line.replace('User:', '').strip()})
                            elif line.startswith('Assistant:'):
                                messages.append({"role": "assistant", "content": line.replace('Assistant:', '').strip()})
                    
                    # Add current question
                    messages.append({"role": "user", "content": web_search_prompt})
                    
                    # Use OpenAI directly to bypass RAG query that might interfere
                    try:
                        response_obj = rag_manager.client.chat.completions.create(
                            model=rag_manager.chat_model,
                            messages=messages,
                            temperature=0.2,
                            max_tokens=512
                        )
                        response = response_obj.choices[0].message.content
                        logger.info(f"✅ Generated answer from web search results")
                    except Exception as e:
                        logger.error(f"Error generating answer from web search: {e}")
                        response = internal_answer
                else:
                    # Web search failed, use internal answer
                    logger.warning("Web search returned no results, using internal answer")
                    response = internal_answer
            except Exception as e:
                logger.error(f"Error in web search: {str(e)}")
                # Fallback to internal answer if web search fails
                response = internal_answer
        else:
            # Web search not enabled, use internal answer
            response = internal_answer
        
        # حفظ الرسالة والرد في قاعدة البيانات
        context_data = {
            "context": context_texts,
            "indexing_info": indexing_info,
            "conversation_context": conversation_context,
            "used_web_search": used_web_search,
            "web_search_results": web_search_results[:3] if web_search_results else None
        }
        
        db_message = ChatMessage(
            user_id=current_user.id,
            message=message_data.message,
            response=response,
            context=context_data
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return ChatMessageResponse.from_orm(db_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/chat/stream")
async def send_message_stream(
    message_data: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streaming chat: indexes never run here. Tokens are sent as SSE as they arrive.
    """
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")

    import json as _json

    top_k = message_data.top_k or 3
    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(5).all()

    context_messages = []
    for msg in reversed(recent_messages):
        context_messages.append(f"User: {msg.message}")
        context_messages.append(f"Assistant: {msg.response}")
    context_messages.append(f"User: {message_data.message}")
    conversation_context = "\n".join(context_messages)

    context_texts = []
    try:
        context_texts = rag_manager.query(message_data.message, current_user.id, top_k=top_k) or []
    except Exception as e:
        logger.warning(f"Stream query failed: {e}")
        context_texts = []

    detected_language = detect_language(message_data.message)
    language_instruction = get_language_instruction(detected_language)

    if context_texts:
        document_context = "\n\n".join(context_texts)
        prompt = f"{language_instruction}\n\nDocument Context:\n{document_context}\n\nConversation:\n{conversation_context}"
    else:
        prompt = f"{language_instruction}\n\nConversation:\n{conversation_context}"

    # Optional web search (non-stream gather, then stream the final answer)
    used_web_search = False
    web_search_results = None
    if message_data.enable_web_search:
        try:
            web_search_results = perform_web_search(message_data.message, max_results=5)
            if web_search_results:
                used_web_search = True
                web_context = "\n\n".join(
                    [f"Source: {r.get('title', 'Unknown')}\n{r.get('snippet', '')}" for r in web_search_results[:3]]
                )
                prompt = (
                    f"{language_instruction}\n\nUse these web results to answer:\n{web_context}\n\n"
                    f"Conversation:\n{conversation_context}\n\nQuestion: {message_data.message}"
                )
        except Exception as e:
            logger.warning(f"Web search failed in stream: {e}")

    def event_generator():
        full_answer = []
        try:
            for token in rag_manager.generate_from_context(
                prompt, context_texts if not used_web_search else [], stream=True
            ):
                full_answer.append(token)
                yield f"data: {_json.dumps({'token': token})}\n\n"
        except Exception as e:
            msg = rag_manager._friendly_openai_error(e)
            full_answer = [msg]
            yield f"data: {_json.dumps({'token': msg})}\n\n"

        answer_text = "".join(full_answer)
        context_data = {
            "context": context_texts,
            "indexing_info": {"files_indexed": 0, "message": "Using pre-indexed documents only"},
            "conversation_context": conversation_context,
            "used_web_search": used_web_search,
            "web_search_results": web_search_results[:3] if web_search_results else None,
        }
        try:
            save_db = SessionLocal()
            try:
                db_message = ChatMessage(
                    user_id=current_user.id,
                    message=message_data.message,
                    response=answer_text,
                    context=context_data,
                )
                save_db.add(db_message)
                save_db.commit()
                save_db.refresh(db_message)
                yield f"data: {_json.dumps({'done': True, 'id': db_message.id, 'created_at': db_message.created_at.isoformat(), 'context': context_data})}\n\n"
            finally:
                save_db.close()
        except Exception as e:
            logger.error(f"Failed saving streamed chat: {e}")
            yield f"data: {_json.dumps({'done': True, 'id': None, 'context': context_data})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# نقاط نهاية رفع الملفات (محمية)
@app.post("/upload-file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    target_roles: str = Form(...),  # Accept as string, parse as JSON
    specialization: str = Form(None),  # Specialization for students (optional)
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import json
    target_roles = json.loads(target_roles)
    allowed_roles = ["faculty", "student"]
    # تحقق من صلاحيات الرفع حسب الدور
    if current_user.role == "faculty":
        # Faculty can upload for students (public) or faculty (private)
        if not isinstance(target_roles, list) or not target_roles or not all(r in allowed_roles for r in target_roles):
            raise HTTPException(status_code=400, detail="Invalid target roles")
        # If uploading for students, specialization is required
        if "student" in target_roles and not specialization:
            raise HTTPException(status_code=400, detail="Specialization is required when uploading for students")
    else:
        raise HTTPException(status_code=403, detail="You do not have permission to upload files")
    if not file or not getattr(file, 'filename', None):
        raise HTTPException(status_code=400, detail="No file provided")
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No file name provided")
    file_extension = os.path.splitext(str(file.filename))[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOADS_DIR, unique_filename)
    try:
        # Read file once into memory for disk + durable DB storage
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)
        # Ensure file exists before proceeding
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="File not found after upload.")
        db_file = UploadedFile(
            user_id=current_user.id,
            uploader_id=current_user.id,
            target_roles=target_roles,
            specialization=specialization if "student" in target_roles else None,
            filename=unique_filename,
            original_filename=file.filename,
            file_size=len(file_bytes),
            file_type=getattr(file, 'content_type', None) or "application/pdf",
            file_content=file_bytes,
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # --- Begin: Index at upload time (chat will never index) ---
        global rag_manager
        if rag_manager is None:
            raise HTTPException(status_code=503, detail="RAG manager is not ready")
        file_paths = [file_path]
        print(f"📤 Uploading file for roles: {target_roles}, specialization: {specialization}")
        indexed_user_ids = set()
        documents = rag_manager.load_documents(file_paths=file_paths)
        if not documents:
            raise HTTPException(status_code=400, detail="Could not read document content for indexing")

        # Always index for the uploader (faculty)
        try:
            rag_manager.index_documents(documents, current_user.id, file_paths)
            indexed_user_ids.add(current_user.id)
            print(f"✅ Indexed for uploader {current_user.id}")
        except Exception as e:
            print(f"⚠️ Indexing failed for uploader: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Upload saved but indexing failed: {rag_manager._friendly_openai_error(e)}",
            )

        for role in target_roles:
            if role == "student" and specialization:
                users = db.query(User).filter(
                    User.role == role,
                    User.specialization == specialization,
                ).all()
                print(f"👥 Found {len(users)} students with specialization '{specialization}'")
            else:
                users = db.query(User).filter(User.role == role).all()
                print(f"👥 Found {len(users)} users with role '{role}'")
            for user in users:
                if user.id in indexed_user_ids:
                    continue
                try:
                    print(f"📚 Indexing document for user {user.id} ({user.username})")
                    rag_manager.index_documents(documents, user.id, file_paths)
                    indexed_user_ids.add(user.id)
                    print(f"✅ Indexed documents for user {user.id}")
                except Exception as e:
                    # Soft-fail per user so one failure does not break the whole upload
                    print(f"⚠️ Indexing failed for user {user.id}: {e}")
        # --- End: Index at upload time ---

        return FileUploadResponse.from_orm(db_file)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files", response_model=FileListResponse)
async def get_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files_query = db.query(UploadedFile).filter(
        UploadedFile.target_roles.isnot(None),
        UploadedFile.target_roles.contains([current_user.role])
    )
    
    # Filter by specialization for students
    if current_user.role == "student":
        files_query = files_query.filter(
            or_(
                UploadedFile.specialization == current_user.specialization,
                UploadedFile.specialization.is_(None)  # Include files without specialization (for backward compatibility)
            )
        )
    
    files = (
        files_query
        .options(defer(UploadedFile.file_content))
        .order_by(UploadedFile.upload_time.desc())
        .all()
    )
    return FileListResponse(files=[FileUploadResponse.from_orm(file) for file in files])

@app.get("/download-file/{file_id}")
async def download_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تحميل ملف مرفوع
    يمكن للطلاب والأطباء تحميل الملفات المتاحة لهم
    """
    # Get the file from database
    file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if user has access to this file
    has_access = False
    if current_user.role == "faculty":
        # Faculty can access files targeted to faculty or students
        has_access = (
            "faculty" in file_record.target_roles or 
            "student" in file_record.target_roles
        )
    elif current_user.role == "student":
        # Students can only access files targeted to students with matching specialization
        has_access = (
            "student" in file_record.target_roles and
            (file_record.specialization == current_user.specialization or 
             file_record.specialization is None)  # Include files without specialization
        )
    
    if not has_access:
        raise HTTPException(status_code=403, detail="You do not have permission to download this file")
    
    # Prefer disk; fall back to durable DB blob (needed on Render free tier)
    file_path = os.path.join(UPLOADS_DIR, file_record.filename)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=file_record.original_filename,
            media_type=file_record.file_type or 'application/octet-stream'
        )

    if file_record.file_content:
        headers = {
            "Content-Disposition": f'attachment; filename="{file_record.original_filename}"'
        }
        return Response(
            content=bytes(file_record.file_content),
            media_type=file_record.file_type or 'application/octet-stream',
            headers=headers,
        )

    raise HTTPException(
        status_code=404,
        detail=(
            "File content is missing on the server. "
            "Old uploads before durable storage are gone after Render restarts — please re-upload the PDF."
        ),
    )

# نقاط نهاية RAG (محمية)
@app.get("/stats", response_model=IndexStats)
async def get_stats(current_user: User = Depends(get_current_user)):
    """الحصول على إحصائيات نظام RAG"""
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")
    stats = rag_manager.get_stats(current_user.id)
    return IndexStats(**stats)

@app.get("/debug/user-documents")
async def debug_user_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to check user's accessible documents"""
    # Get files accessible to the user
    files_query = db.query(UploadedFile)
    if current_user.role == "faculty":
        allowed_files = files_query.filter(
            or_(UploadedFile.target_roles.contains(["faculty"]),
                UploadedFile.target_roles.contains(["student"]))
        ).filter(UploadedFile.filename.isnot(None)).all()
    elif current_user.role == "student":
        allowed_files = files_query.filter(UploadedFile.target_roles.contains(["student"])).filter(UploadedFile.filename.isnot(None)).all()
    else:
        allowed_files = []
    
    file_paths = [os.path.join(UPLOADS_DIR, str(f.filename)) for f in allowed_files if f.filename is not None]
    existing_files = [path for path in file_paths if os.path.exists(path)]
    
    # Try to query the RAG system
    try:
        test_query = rag_manager.query("test", current_user.id, top_k=3)
        rag_working = True
        rag_results = len(test_query) if test_query else 0
    except Exception as e:
        rag_working = False
        rag_results = 0
        rag_error = str(e)
    
    return {
        "user_id": current_user.id,
        "user_role": current_user.role,
        "total_files_in_db": len(allowed_files),
        "files_on_disk": len(existing_files),
        "file_paths": file_paths,
        "existing_files": existing_files,
        "rag_working": rag_working,
        "rag_results": rag_results,
        "rag_error": rag_error if not rag_working else None
    }

@app.post("/debug/reindex-user-documents")
async def debug_reindex_user_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Debug endpoint to manually reindex all documents for the current user"""
    # Get files accessible to the user
    files_query = db.query(UploadedFile)
    if current_user.role == "faculty":
        allowed_files = files_query.filter(
            or_(UploadedFile.target_roles.contains(["faculty"]),
                UploadedFile.target_roles.contains(["student"]))
        ).filter(UploadedFile.filename.isnot(None)).all()
    elif current_user.role == "student":
        allowed_files = files_query.filter(UploadedFile.target_roles.contains(["student"])).filter(UploadedFile.filename.isnot(None)).all()
    else:
        allowed_files = []
    
    file_paths = [os.path.join(UPLOADS_DIR, str(f.filename)) for f in allowed_files if f.filename is not None]
    existing_files = [path for path in file_paths if os.path.exists(path)]
    
    if not existing_files:
        return {"message": "No files found to reindex", "files_found": 0}
    
    try:
        # Clear existing index for this user
        rag_manager.clear_index(current_user.id)
        
        # Reindex all files
        documents = rag_manager.load_documents(file_paths=existing_files)
        if documents:
            rag_manager.index_documents(documents, current_user.id, existing_files)
            return {
                "message": f"Successfully reindexed {len(documents)} documents for user {current_user.id}",
                "files_processed": len(existing_files),
                "documents_loaded": len(documents)
            }
        else:
            return {"message": "No documents could be loaded from files", "files_found": len(existing_files)}
    except Exception as e:
        return {"error": f"Failed to reindex: {str(e)}"}

@app.post("/upload-document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    append: bool = Query(True, description="Add to existing index (True) or replace (False)"),
    current_user: User = Depends(get_current_user)
):
    """
    رفع وثيقة إلى نظام RAG
    يقوم بتحليل الوثيقة وإضافتها إلى فهرس البحث الدلالي
    """
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")
    if not file or not getattr(file, 'filename', None) or not isinstance(file.filename, str) or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    try:
        # حفظ الملف مؤقتاً
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        # تحميل الوثائق
        documents = rag_manager.load_documents(file_paths=[temp_file_path])
        if not append:
            rag_manager.clear_index(current_user.id)
        # فهرسة الوثائق في نظام البحث الدلالي
        rag_manager.index_documents(documents, current_user.id)
        os.unlink(temp_file_path)
        stats = rag_manager.get_stats(current_user.id)
        action = "added to" if append else "replaced"
        return DocumentUploadResponse(
            message=f"Index {action} successfully",
            documents_processed=len(documents),
            total_chunks=stats["total_chunks"],
            total_documents=stats["total_documents"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.delete("/clear-index")
async def clear_index(current_user: User = Depends(get_current_user)):
    """مسح جميع الوثائق من الفهرس"""
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")
    try:
        rag_manager.clear_index(current_user.id)
        return {"message": "Index cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing index: {str(e)}")

@app.post("/index-available-files")
async def index_available_files(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    فهرسة جميع الملفات المتاحة للمستخدم في PGVector
    مفيد للتأكد من أن جميع الملفات المرئية للمستخدم مفهرسة أيضاً
    """
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")
    
    try:
        # تحديد الملفات المسموح بها حسب الدور
        files_query = db.query(UploadedFile)
        if current_user.role == "faculty":
            # Faculty can access both public (student) and private (faculty) documents
            allowed_files = files_query.filter(
                or_(UploadedFile.target_roles.contains(["faculty"]),
                    UploadedFile.target_roles.contains(["student"]))
            ).filter(UploadedFile.filename.isnot(None)).all()
        elif current_user.role == "student":
            # Students can only access public documents (targeted to students)
            allowed_files = files_query.filter(UploadedFile.target_roles.contains(["student"])).filter(UploadedFile.filename.isnot(None)).all()
        else:
            allowed_files = []
        
        file_paths = [os.path.join(UPLOADS_DIR, str(f.filename)) for f in allowed_files if f.filename is not None]
        existing_files = [path for path in file_paths if os.path.exists(path)]
        
        if not existing_files:
            return {"message": "No files available for indexing", "files_indexed": 0}
        
        # استخدام النظام الجديد لفهرسة الملفات مع التتبع
        indexing_result = rag_manager.index_available_files(existing_files, current_user.id)
        
        return {
            "message": indexing_result["message"],
            "files_indexed": indexing_result["files_indexed"]
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error indexing files: {str(e)}")

@app.get("/tools/scrape-metadata")
async def scrape_metadata(url: str = Query(...)):
    """
    Scrape metadata (title, description, thumbnail) from a URL
    Currently optimized for YouTube
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        # Check if it's a YouTube URL
        is_youtube = "youtube.com" in url or "youtu.be" in url
        
        if is_youtube:
            # Try oEmbed first for reliable metadata
            try:
                oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                response = requests.get(oembed_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    # Get higher quality thumbnail if possible
                    thumbnail_url = data.get("thumbnail_url")
                    
                    # Try to extract video ID to get maxresdefault
                    video_id = None
                    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})', url)
                    if match:
                        video_id = match.group(1)
                        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    
                    return {
                        "title": data.get("title"),
                        "thumbnail_url": thumbnail_url,
                        "author_name": data.get("author_name"),
                        "provider_name": "YouTube"
                    }
            except Exception as e:
                logger.warning(f"oEmbed failed: {e}")
            
            # Fallback to basic extraction if oEmbed fails
            video_id = None
            match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})', url)
            if match:
                video_id = match.group(1)
                return {
                    "title": "", # Cannot reliably get title without oEmbed or heavy scraping
                    "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    "provider_name": "YouTube"
                }
        
        return {
            "title": "",
            "thumbnail_url": "",
            "provider_name": "Unknown"
        }
            
    except Exception as e:
        logger.error(f"Error scraping metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error scraping metadata: {str(e)}")

# ==================== Course Management Endpoints ====================

@app.post("/courses", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إنشاء كورس جديد (لأعضاء هيئة التدريس فقط)
    يستخرج صورة الكورس تلقائياً من رابط YouTube إذا كان الكورس خارجي
    """
    if current_user.role != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty members can create courses"
        )
    
    # Extract thumbnail from YouTube URL if course is external and URL is provided
    thumbnail_url = course_data.thumbnail_url
    if course_data.course_type == "external" and course_data.course_url and not thumbnail_url:
        thumbnail_url = extract_youtube_thumbnail(course_data.course_url)
        logger.info(f"📸 Extracted thumbnail for external course: {thumbnail_url}")
    
    db_course = Course(
        title=course_data.title,
        description=course_data.description,
        specialization=course_data.specialization,
        faculty_id=current_user.id,
        course_url=course_data.course_url,
        course_type=course_data.course_type or "internal",
        thumbnail_url=thumbnail_url
    )
    
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    
    # إضافة اسم عضو هيئة التدريس
    course_response = CourseResponse(
        id=db_course.id,
        title=db_course.title,
        description=db_course.description,
        specialization=db_course.specialization,
        faculty_id=db_course.faculty_id,
        faculty_name=current_user.username,
        created_at=db_course.created_at,
        updated_at=db_course.updated_at,
        is_active=db_course.is_active,
        course_url=db_course.course_url,
        course_type=db_course.course_type,
        thumbnail_url=db_course.thumbnail_url,
        enrollment_count=0
    )
    
    return course_response

@app.get("/courses/my-courses", response_model=CourseListResponse)
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على الكورسات الخاصة بالمستخدم:
    - لأعضاء هيئة التدريس: جميع الكورسات التي أنشأوها
    - للطلاب: الكورسات المطابقة لتخصصهم
    """
    if current_user.role == "faculty":
        # أعضاء هيئة التدريس يرون جميع كورساتهم
        courses = db.query(Course).filter(
            Course.faculty_id == current_user.id
        ).order_by(Course.created_at.desc()).all()
    elif current_user.role == "student":
        # الطلاب يرون فقط الكورسات المطابقة لتخصصهم
        if not current_user.specialization:
            courses = []
        else:
            courses = db.query(Course).filter(
                Course.specialization == current_user.specialization,
                Course.is_active == "active"
            ).order_by(Course.created_at.desc()).all()
    else:
        courses = []
    
    # إضافة معلومات إضافية لكل كورس
    course_responses = []
    for course in courses:
        enrollment_count = db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course.id
        ).count()
        
        faculty = db.query(User).filter(User.id == course.faculty_id).first()
        faculty_name = faculty.username if faculty else "Unknown"
        
        course_responses.append(CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            specialization=course.specialization,
            faculty_id=course.faculty_id,
            faculty_name=faculty_name,
            created_at=course.created_at,
            updated_at=course.updated_at,
            is_active=course.is_active,
            course_url=course.course_url,
            course_type=course.course_type,
            thumbnail_url=course.thumbnail_url,
            enrollment_count=enrollment_count
        ))
    
    return CourseListResponse(courses=course_responses, total=len(course_responses))

@app.get("/courses/my-enrollments")
async def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على الكورسات المسجل فيها الطالب
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view enrollments"
        )
    
    enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id
    ).order_by(CourseEnrollment.enrolled_at.desc()).all()
    
    enrollment_responses = []
    for enrollment in enrollments:
        course = db.query(Course).filter(Course.id == enrollment.course_id).first()
        if course:
            faculty = db.query(User).filter(User.id == course.faculty_id).first()
            enrollment_count = db.query(CourseEnrollment).filter(
                CourseEnrollment.course_id == course.id
            ).count()
            
            course_response = CourseResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                specialization=course.specialization,
                faculty_id=course.faculty_id,
                faculty_name=faculty.username if faculty else "Unknown",
                created_at=course.created_at,
                updated_at=course.updated_at,
                is_active=course.is_active,
                course_url=course.course_url,
                course_type=course.course_type,
                thumbnail_url=course.thumbnail_url,
                enrollment_count=enrollment_count
            )
            enrollment_responses.append(CourseEnrollmentResponse(
                id=enrollment.id,
                student_id=enrollment.student_id,
                course_id=enrollment.course_id,
                enrolled_at=enrollment.enrolled_at,
                progress=enrollment.progress,
                course=course_response
            ))
    
    return enrollment_responses

@app.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    الحصول على تفاصيل كورس محدد
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # التحقق من الصلاحيات
    if current_user.role == "student":
        if course.specialization != current_user.specialization:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this course"
            )
    elif current_user.role == "faculty":
        if course.faculty_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own courses"
            )
    
    enrollment_count = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course.id
    ).count()
    
    faculty = db.query(User).filter(User.id == course.faculty_id).first()
    faculty_name = faculty.username if faculty else "Unknown"
    
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        specialization=course.specialization,
        faculty_id=course.faculty_id,
        faculty_name=faculty_name,
        created_at=course.created_at,
        updated_at=course.updated_at,
        is_active=course.is_active,
        course_url=course.course_url,
        course_type=course.course_type,
        thumbnail_url=course.thumbnail_url,
        enrollment_count=enrollment_count
    )

@app.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تحديث كورس (لأعضاء هيئة التدريس فقط - مالك الكورس)
    """
    if current_user.role != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty members can update courses"
        )
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own courses"
        )
    
    # تحديث الحقول المقدمة فقط
    if course_data.title is not None:
        course.title = course_data.title
    if course_data.description is not None:
        course.description = course_data.description
    if course_data.specialization is not None:
        course.specialization = course_data.specialization
    if course_data.course_url is not None:
        course.course_url = course_data.course_url
    if course_data.is_active is not None:
        course.is_active = course_data.is_active
    if course_data.course_type is not None:
        course.course_type = course_data.course_type
    if course_data.thumbnail_url is not None:
        course.thumbnail_url = course_data.thumbnail_url
    # Auto-extract thumbnail if URL changed and course is external
    if course_data.course_url is not None and course.course_type == "external" and course_data.course_url:
        thumbnail_url = extract_youtube_thumbnail(course_data.course_url)
        if thumbnail_url:
            course.thumbnail_url = thumbnail_url
    
    course.updated_at = datetime.now()
    db.commit()
    db.refresh(course)
    
    enrollment_count = db.query(CourseEnrollment).filter(
        CourseEnrollment.course_id == course.id
    ).count()
    
    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        specialization=course.specialization,
        faculty_id=course.faculty_id,
        faculty_name=current_user.username,
        created_at=course.created_at,
        updated_at=course.updated_at,
        is_active=course.is_active,
        course_url=course.course_url,
        course_type=course.course_type,
        thumbnail_url=course.thumbnail_url,
        enrollment_count=enrollment_count
    )

@app.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    حذف كورس (لأعضاء هيئة التدريس فقط - مالك الكورس)
    """
    if current_user.role != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only faculty members can delete courses"
        )
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course.faculty_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own courses"
        )
    
    db.delete(course)
    db.commit()
    
    return {"message": "Course deleted successfully"}

@app.post("/courses/{course_id}/enroll", response_model=CourseEnrollmentResponse)
async def enroll_in_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تسجيل الطالب في كورس
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in courses"
        )
    
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # التحقق من التخصص
    if course.specialization != current_user.specialization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course is not available for your specialization"
        )
    
    # التحقق من عدم التسجيل مسبقاً
    existing_enrollment = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == current_user.id,
        CourseEnrollment.course_id == course_id
    ).first()
    
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this course"
        )
    
    enrollment = CourseEnrollment(
        student_id=current_user.id,
        course_id=course_id,
        progress=0
    )
    
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    
    return CourseEnrollmentResponse(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        enrolled_at=enrollment.enrolled_at,
        progress=enrollment.progress
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
