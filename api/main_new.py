# استيراد المكتبات المطلوبة لبناء واجهة برمجة التطبيقات
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Depends, status, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
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
from datetime import timedelta
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy import or_, and_
import pandas as pd

# استيراد الوحدات المحلية للمشروع
from api.database import get_db, User, ChatMessage, UploadedFile, create_tables
from api.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user,
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from api.models import (
    UserRegister, UserLogin, UserResponse, Token,
    ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse,
    FileUploadResponse, FileListResponse,
    ChatResponse, DocumentUploadResponse, IndexStats
)
from api.rag_manager_simple import RAGManagerPGVector

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# تهيئة مدير RAG كمتغير عام
rag_manager = None

# إنشاء مجلد الملفات المرفوعة
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

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
    title="RAG Chatbot API with Authentication", 
    version="2.0.0",
    lifespan=lifespan
)

# تكوين CORS للسماح بالاتصال من تطبيق React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # عنوان تطبيق React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """نقطة نهاية أساسية للتحقق من تشغيل الخادم"""
    return {"message": "RAG Chatbot API with Authentication is running!"}

@app.get("/health")
async def health_check():
    """نقطة نهاية فحص صحة الخادم ومدير RAG"""
    return {"status": "healthy", "rag_manager_ready": rag_manager is not None}

class GeneralChatRequest(BaseModel):
    message: str

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
        role=user_data.role  # Ensure role is saved
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
    """
    logger.info(f"Received general chat request: {request.message}")
    
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
        
        # Index files if needed
        if file_paths:
            existing_files = [path for path in file_paths if os.path.exists(path)]
            if existing_files:
                # Create a temporary user for general chat
                temp_user_id = 999999  # Use a special ID for general chat
                indexing_result = rag_manager.index_available_files(existing_files, temp_user_id)
                logger.info(f"Indexing result for general inquiry: {indexing_result}")
        
        # Generate answer using RAG for general inquiries
        response = rag_manager.generate_answer(
            question=request.message,
            user_id=temp_user_id,  # Using the temporary user's ID
            roles=["student"],  # Only access documents marked for students
            top_k=3,  # Number of relevant documents to consider
            model="gpt-3.5-turbo"
        )
        
        logger.info(f"Generated response for message: {request.message[:50]}...")
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
        
        # التحقق من وجود ملفات متاحة للمستخدم
        if file_paths:
            # التحقق من وجود ملفات في النظام
            existing_files = [path for path in file_paths if os.path.exists(path)]
            
            if existing_files:
                # استخدام النظام الجديد لفهرسة الملفات مع التتبع
                indexing_result = rag_manager.index_available_files(existing_files, current_user.id)
                
                if indexing_result["files_indexed"] > 0:
                    # تحميل الوثائق من الملفات الجديدة فقط
                    documents = rag_manager.load_documents(file_paths=existing_files)
                    
                    if documents:
                        # البحث عن السياق المناسب في الوثائق
                        context = rag_manager.split_documents(documents, chunk_size=1000, chunk_overlap=200)[:top_k]
                        context_texts = [chunk.page_content for chunk in context]
                        
                        # إضافة معلومات عن الفهرسة
                        indexing_info = {
                            "files_indexed": indexing_result["files_indexed"],
                            "message": indexing_result["message"]
                        }
                    else:
                        context_texts = []
                        indexing_info = {"files_indexed": 0, "message": "No documents could be loaded"}
                else:
                    # الملفات مفهرسة بالفعل، البحث مباشرة
                    context_texts = []
                    indexing_info = {"files_indexed": 0, "message": indexing_result["message"]}
            else:
                context_texts = []
                indexing_info = {"files_indexed": 0, "message": "No files found on disk"}
        else:
            context_texts = []
            indexing_info = {"files_indexed": 0, "message": "No files available for your role"}
        
        # توليد الإجابة باستخدام السياق المسترجع والمحادثة السابقة
        response = rag_manager.generate_answer(
            conversation_context,  # Use conversation context instead of just the message
            current_user.id,
            top_k=top_k
        )
        
        # حفظ الرسالة والرد في قاعدة البيانات
        db_message = ChatMessage(
            user_id=current_user.id,
            message=message_data.message,
            response=response,
            context={"context": context_texts, "indexing_info": indexing_info, "conversation_context": conversation_context}
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return ChatMessageResponse.from_orm(db_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

# نقاط نهاية رفع الملفات (محمية)
@app.post("/upload-file", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    target_roles: str = Form(...),  # Accept as string, parse as JSON
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
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Ensure file exists before proceeding
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="File not found after upload.")
        db_file = UploadedFile(
            user_id=current_user.id,
            uploader_id=current_user.id,
            target_roles=target_roles,
            filename=unique_filename,
            original_filename=file.filename,
            file_size=getattr(file, 'size', None),
            file_type=getattr(file, 'content_type', None)
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # --- Begin: Index for all users in target roles ---
        from api.database import User
        from api.rag_manager_simple import rag_manager
        file_paths = [file_path]
        for role in target_roles:
            users = db.query(User).filter(User.role == role).all()
            for user in users:
                # Load and index the document for each user
                documents = rag_manager.load_documents(file_paths=file_paths)
                rag_manager.index_documents(documents, user.id, file_paths)
        # --- End: Index for all users in target roles ---

        return FileUploadResponse.from_orm(db_file)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/files", response_model=FileListResponse)
async def get_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    files = db.query(UploadedFile).filter(
        UploadedFile.target_roles.isnot(None),
        UploadedFile.target_roles.contains([current_user.role])
    ).order_by(UploadedFile.upload_time.desc()).all()
    return FileListResponse(files=[FileUploadResponse.from_orm(file) for file in files])

# نقاط نهاية RAG (محمية)
@app.get("/stats", response_model=IndexStats)
async def get_stats(current_user: User = Depends(get_current_user)):
    """الحصول على إحصائيات نظام RAG"""
    if not rag_manager:
        raise HTTPException(status_code=500, detail="RAG Manager not initialized")
    stats = rag_manager.get_stats(current_user.id)
    return IndexStats(**stats)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
