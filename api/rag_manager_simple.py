# استيراد المكتبات المطلوبة لنظام RAG
import os
import hashlib
import json
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')

def user_collection_name(user_id):
    """
    إنشاء اسم مجموعة فريدة لكل مستخدم
    يضمن عزل بيانات كل مستخدم عن الآخرين
    """
    return f"rag_collection_user_{user_id}"

def get_file_hash(file_path):
    """
    إنشاء hash فريد للملف للتعرف عليه
    """
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.md5(file_content).hexdigest()
    except:
        return None

class RAGManagerPGVector:
    """
    مدير نظام RAG باستخدام PostgreSQL مع pgvector
    يتعامل مع تحميل الوثائق وفهرستها والبحث فيها وتوليد الإجابات
    """
    
    def __init__(self, embedding_model=None, api_key=api_key):
        """
        تهيئة مدير RAG
        """
        # نموذج التضمين الدلالي - تحويل النصوص إلى متجهات
        self.embedding_model = embedding_model or HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # سلسلة الاتصال بقاعدة البيانات
        self.connection_string = os.getenv("PGVECTOR_CONNECTION_STRING") or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("PGVECTOR_CONNECTION_STRING or DATABASE_URL must be set")
        self.api_key = api_key
        # عميل OpenAI لتوليد الإجابات
        self.client = OpenAI(api_key=api_key)

    def _get_pgvector_store(self, user_id):
        """
        الحصول على مخزن المتجهات لمستخدم معين
        """
        collection_name = user_collection_name(user_id)
        return PGVector(
            collection_name=collection_name,
            connection_string=self.connection_string,
            embedding_function=self.embedding_model,
        )

    def _get_indexed_files_tracking(self, user_id):
        """
        الحصول على قائمة الملفات المفهرسة للمستخدم
        """
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # إنشاء جدول لتتبع الملفات المفهرسة إذا لم يكن موجوداً
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indexed_files_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, file_path)
                );
            """)
            conn.commit()
            
            # الحصول على قائمة الملفات المفهرسة للمستخدم
            cursor.execute("""
                SELECT file_path, file_hash FROM indexed_files_tracking 
                WHERE user_id = %s
            """, (user_id,))
            
            indexed_files = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return indexed_files
        except Exception as e:
            print(f"❌ Error getting indexed files tracking: {e}")
            return {}

    def _mark_file_as_indexed(self, user_id, file_path, file_hash):
        """
        تحديد الملف كمفهرس للمستخدم
        """
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO indexed_files_tracking (user_id, file_path, file_hash)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, file_path) 
                DO UPDATE SET file_hash = EXCLUDED.file_hash, indexed_at = CURRENT_TIMESTAMP
            """, (user_id, file_path, file_hash))
            
            conn.commit()
            conn.close()
            print(f"✅ Marked file {file_path} as indexed for user {user_id}")
        except Exception as e:
            print(f"❌ Error marking file as indexed: {e}")

    def _get_files_to_index(self, file_paths, user_id):
        """
        تحديد الملفات التي تحتاج إلى فهرسة للمستخدم
        """
        indexed_files = self._get_indexed_files_tracking(user_id)
        files_to_index = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            current_hash = get_file_hash(file_path)
            if not current_hash:
                continue
                
            # التحقق من وجود الملف في قائمة المفهرس
            if file_path not in indexed_files:
                # ملف جديد لم يتم فهرسته
                files_to_index.append(file_path)
            elif indexed_files[file_path] != current_hash:
                # الملف موجود لكن تغير (hash مختلف)
                files_to_index.append(file_path)
        
        return files_to_index

    def load_documents(self, file_paths=[], urls=[]):
        """
        تحميل الوثائق من الملفات والروابط
        يدعم ملفات PDF والروابط الإلكترونية
        """
        documents = []
        # تحميل ملفات PDF
        for path in file_paths:
            try:
                loader = PyPDFLoader(path)
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"⚠️ Error loading file {path}: {e}")
                continue
        # تحميل الروابط الإلكترونية
        for url in urls:
            try:
                loader = WebBaseLoader(url)
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"⚠️ Error loading URL {url}: {e}")
                continue
        print(f"📄 Loaded {len(documents)} documents.")
        return documents

    def split_documents(self, documents, chunk_size=1000, chunk_overlap=200):
        """
        تقسيم الوثائق إلى أجزاء أصغر
        يضمن تحسين البحث الدلالي والفهرسة
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # حجم كل جزء
            chunk_overlap=chunk_overlap  # التداخل بين الأجزاء
        )
        chunks = splitter.split_documents(documents)
        print(f"✂️ Split documents into {len(chunks)} chunks.")
        return chunks

    def index_documents(self, documents, user_id, file_paths=None):
        """
        فهرسة الوثائق في مخزن المتجهات
        يحول النصوص إلى متجهات ويخزنها للبحث السريع
        """
        if not documents:
            print(f"⚠️ No documents to index for user {user_id}")
            return
            
        chunks = self.split_documents(documents)
        pgvector_store = self._get_pgvector_store(user_id)
        
        # إضافة الوثائق إلى PGVector
        pgvector_store.add_documents(chunks)
        print(f"✅ Indexed {len(chunks)} chunks in PGVector for user {user_id}.")
        
        # تحديد الملفات كمفهرسة
        if file_paths:
            for file_path in file_paths:
                file_hash = get_file_hash(file_path)
                if file_hash:
                    self._mark_file_as_indexed(user_id, file_path, file_hash)

    def index_available_files(self, file_paths, user_id):
        """
        فهرسة الملفات المتاحة للمستخدم مع تتبع الملفات المفهرسة
        """
        if not file_paths:
            print(f"⚠️ No files to index for user {user_id}")
            return {"files_indexed": 0, "message": "No files available"}
        
        # تحديد الملفات التي تحتاج إلى فهرسة
        files_to_index = self._get_files_to_index(file_paths, user_id)
        
        if not files_to_index:
            print(f"ℹ️ All files already indexed for user {user_id}")
            return {"files_indexed": 0, "message": "All files already indexed"}
        
        # تحميل وفهرسة الملفات الجديدة
        documents = self.load_documents(file_paths=files_to_index)
        
        if documents:
            self.index_documents(documents, user_id, files_to_index)
            return {
                "files_indexed": len(files_to_index),
                "message": f"Successfully indexed {len(files_to_index)} new files"
            }
        else:
            return {"files_indexed": 0, "message": "No documents could be loaded from files"}

    def query(self, query, user_id, top_k=1):
        """
        البحث في الوثائق المفهرسة
        يجد الأجزاء الأكثر تشابهاً مع الاستعلام
        """
        try:
            print(f"🔍 RAG Query: user_id={user_id}, query='{query[:50]}...', top_k={top_k}")
            pgvector_store = self._get_pgvector_store(user_id)
            results = pgvector_store.similarity_search(query, k=top_k)
            print(f"📊 RAG Query results: {len(results)} documents found")
            return [result.page_content for result in results]
        except Exception as e:
            print(f"⚠️ Error querying documents for user {user_id}: {e}")
            return []

    def query_multi_store(self, query, user_id, roles=None, top_k=3):
        """
        Query both the user's personal store and any group stores (e.g., for their roles), merging and ranking results.
        """
        results = []
        # Query personal store
        try:
            pgvector_store = self._get_pgvector_store(user_id)
            personal_results = pgvector_store.similarity_search(query, k=top_k)
            results.extend(personal_results)
        except Exception as e:
            print(f"⚠️ Error querying personal store for user {user_id}: {e}")
        # Query group stores
        if roles:
            for role in roles:
                try:
                    group_store = self._get_pgvector_store(role)
                    group_results = group_store.similarity_search(query, k=top_k)
                    results.extend(group_results)
                except Exception as e:
                    print(f"⚠️ Error querying group store for role {role}: {e}")
        # Remove duplicates and sort by similarity (if available)
        seen = set()
        unique_results = []
        for r in results:
            content = getattr(r, 'page_content', str(r))
            if content not in seen:
                seen.add(content)
                unique_results.append(r)
        # Optionally, sort by similarity score if available
        if unique_results and hasattr(unique_results[0], 'score'):
            unique_results.sort(key=lambda x: -x.score)
        return unique_results[:top_k]

    def generate_answer(self, question, user_id, top_k=3, model="gpt-3.5-turbo", roles=None):
        """
        توليد إجابة ذكية باستخدام نظام RAG
        يجمع بين البحث في الوثائق وتوليد النص
        الآن يدعم البحث في مخازن شخصية وجماعية والسياق المحادثة
        """
        try:
            # For students, search both personal and group stores
            if roles:
                retrieved_docs = self.query_multi_store(question, user_id, roles=roles, top_k=top_k)
            else:
                pgvector_store = self._get_pgvector_store(user_id)
                retrieved_docs = pgvector_store.similarity_search(question, k=top_k)
            if not retrieved_docs:
                print(f"⚠️ No relevant documents found for user {user_id}.")
                return "No relevant information found. Please make sure you have uploaded documents that are accessible to your role."
            context = "\n".join([doc.page_content for doc in retrieved_docs])
            try:
                # Enhanced system prompt for better context understanding
                system_prompt = """You are a helpful AI assistant that answers questions based on the provided context and conversation history. 
                You should:
                1. Answer questions based on the provided context
                2. If the user asks for "more details" or "in more details", provide additional information from the context
                3. If the user asks follow-up questions, use the conversation history to understand what they're referring to
                4. Be conversational and helpful
                5. If you don't have enough information, say so clearly
                
                Always respond in a helpful and informative manner."""
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context from documents: {context}\n\nConversation: {question}"}
                    ],
                    temperature=0.2,
                    max_tokens=512  # Increased for more detailed responses
                )
                answer = response.choices[0].message.content
                print(f"🤖 Generated answer: {answer}")
                return answer
            except Exception as e:
                print(f"❌ Error calling OpenAI API: {e}")
                return "Sorry, unable to generate an answer at this time."
        except Exception as e:
            print(f"❌ Error in generate_answer for user {user_id}: {e}")
            return "Sorry, there was an error processing your question. Please try again."

    def get_stats(self, user_id):
        """
        الحصول على إحصائيات نظام RAG
        يعرض معلومات عن الوثائق المفهرسة وحالة النظام
        """
        try:
            total_chunks = 0
            indexed_files_count = 0
            
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # الحصول على عدد الأجزاء المفهرسة
            collection_name = user_collection_name(user_id)
            cursor.execute(f"SELECT COUNT(*) FROM langchain_pg_embedding WHERE collection_name = '{collection_name}';")
            total_chunks = cursor.fetchone()[0]
            
            # الحصول على عدد الملفات المفهرسة
            cursor.execute("SELECT COUNT(*) FROM indexed_files_tracking WHERE user_id = %s", (user_id,))
            indexed_files_count = cursor.fetchone()[0]
            
            conn.close()
            return {
                "total_documents": indexed_files_count,
                "total_chunks": total_chunks,
                "vector_store_available": True,
                "llm_available": True,
                "database": "PostgreSQL with pgvector",
                "llm": "OpenAI GPT-3.5-turbo"
            }
        except Exception as e:
            print(f"⚠️ Error getting statistics: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "vector_store_available": False,
                "llm_available": True,
                "database": "Memory backup",
                "llm": "OpenAI GPT-3.5-turbo"
            }

    def clear_index(self, user_id):
        """
        مسح جميع الوثائق من فهرس المستخدم
        يزيل جميع البيانات المفهرسة للمستخدم المحدد
        """
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # مسح الوثائق من PGVector
            collection_name = user_collection_name(user_id)
            cursor.execute(f"DELETE FROM langchain_pg_embedding WHERE collection_name = '{collection_name}';")
            
            # مسح تتبع الملفات المفهرسة
            cursor.execute("DELETE FROM indexed_files_tracking WHERE user_id = %s", (user_id,))
            
            conn.commit()
            conn.close()
            print(f"🗑️ Cleared PGVector index and file tracking for user {user_id}.")
        except Exception as e:
            print(f"❌ Error clearing index: {e}")

# اسم بديل للتوافق مع الكود الموجود
SimpleRAGManager = RAGManagerPGVector 

rag_manager = RAGManagerPGVector() 