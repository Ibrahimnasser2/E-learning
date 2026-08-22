# استيراد المكتبات المطلوبة لنظام RAG
import os
import hashlib
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.embeddings import Embeddings
from openai import OpenAI
from fastembed import TextEmbedding

# Groq (free) for chat — OpenAI-compatible API
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
DEFAULT_CHAT_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


class FastEmbedLC(Embeddings):
    """Lightweight free embeddings via fastembed (no torch)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts):
        return [list(vec) for vec in self._model.embed(texts)]

    def embed_query(self, text):
        return next(self._model.embed([text])).tolist()

def user_collection_name(user_id):
    """
    مجموعة فريدة لكل مستخدم.
    البادئة fe = FastEmbed (أبعاد مختلفة عن OpenAI — لا تخلط الفهارس القديمة).
    """
    return f"rag_fe_user_{user_id}"

def get_file_hash(file_path):
    """
    إنشاء hash فريد للملف للتعرف عليه
    """
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
            return hashlib.md5(file_content).hexdigest()
    except Exception:
        return None

class RAGManagerPGVector:
    """
    مدير نظام RAG باستخدام PostgreSQL مع pgvector
    Chat: Groq | Embeddings: FastEmbed (مجاني محلي خفيف)
    """

    def __init__(self, embedding_model=None, api_key=None):
        api_key = api_key or GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY must be set")

        # FastEmbed: free local embeddings, much lighter than torch/sentence-transformers
        self.embedding_model = embedding_model or FastEmbedLC(
            model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        )
        self.connection_string = os.getenv("PGVECTOR_CONNECTION_STRING") or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("PGVECTOR_CONNECTION_STRING or DATABASE_URL must be set")
        self.api_key = api_key
        self.chat_model = DEFAULT_CHAT_MODEL
        self.client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    def _get_pgvector_store(self, user_id):
        collection_name = user_collection_name(user_id)
        return PGVector(
            collection_name=collection_name,
            connection_string=self.connection_string,
            embedding_function=self.embedding_model,
        )

    def _get_indexed_files_tracking(self, user_id):
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
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
        indexed_files = self._get_indexed_files_tracking(user_id)
        files_to_index = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
            current_hash = get_file_hash(file_path)
            if not current_hash:
                continue
            if file_path not in indexed_files:
                files_to_index.append(file_path)
            elif indexed_files[file_path] != current_hash:
                files_to_index.append(file_path)
        return files_to_index

    def load_documents(self, file_paths=None, urls=None):
        file_paths = file_paths or []
        urls = urls or []
        documents = []
        for path in file_paths:
            try:
                loader = PyPDFLoader(path)
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"⚠️ Error loading file {path}: {e}")
                continue
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
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        chunks = splitter.split_documents(documents)
        print(f"✂️ Split documents into {len(chunks)} chunks.")
        return chunks

    def index_documents(self, documents, user_id, file_paths=None):
        if not documents:
            print(f"⚠️ No documents to index for user {user_id}")
            return
        chunks = self.split_documents(documents)
        pgvector_store = self._get_pgvector_store(user_id)
        pgvector_store.add_documents(chunks)
        print(f"✅ Indexed {len(chunks)} chunks in PGVector for user {user_id}.")
        if file_paths:
            for file_path in file_paths:
                file_hash = get_file_hash(file_path)
                if file_hash:
                    self._mark_file_as_indexed(user_id, file_path, file_hash)

    def index_available_files(self, file_paths, user_id):
        if not file_paths:
            print(f"⚠️ No files to index for user {user_id}")
            return {"files_indexed": 0, "message": "No files available"}
        files_to_index = self._get_files_to_index(file_paths, user_id)
        if not files_to_index:
            print(f"ℹ️ All files already indexed for user {user_id}")
            return {"files_indexed": 0, "message": "All files already indexed"}
        documents = self.load_documents(file_paths=files_to_index)
        if documents:
            self.index_documents(documents, user_id, files_to_index)
            return {
                "files_indexed": len(files_to_index),
                "message": f"Successfully indexed {len(files_to_index)} new files",
            }
        return {"files_indexed": 0, "message": "No documents could be loaded from files"}

    def query(self, query, user_id, top_k=3):
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
        results = []
        try:
            pgvector_store = self._get_pgvector_store(user_id)
            personal_results = pgvector_store.similarity_search(query, k=top_k)
            results.extend(personal_results)
        except Exception as e:
            print(f"⚠️ Error querying personal store for user {user_id}: {e}")
        if roles:
            for role in roles:
                try:
                    group_store = self._get_pgvector_store(role)
                    group_results = group_store.similarity_search(query, k=top_k)
                    results.extend(group_results)
                except Exception as e:
                    print(f"⚠️ Error querying group store for role {role}: {e}")
        seen = set()
        unique_results = []
        for r in results:
            content = getattr(r, 'page_content', str(r))
            if content not in seen:
                seen.add(content)
                unique_results.append(r)
        if unique_results and hasattr(unique_results[0], 'score'):
            unique_results.sort(key=lambda x: -x.score)
        return unique_results[:top_k]

    @staticmethod
    def _friendly_openai_error(exc):
        text = str(exc).lower()
        if "insufficient_quota" in text or "credit_balance_exhausted" in text or "no credits" in text:
            return (
                "AI API credits are exhausted. Please check your Groq/OpenAI billing, "
                "then try again."
            )
        if "429" in text or "rate limit" in text or "too many requests" in text:
            return "The AI service is busy right now. Please wait a moment and try again."
        if "invalid_api_key" in text or "authentication" in text or "401" in text:
            return "AI API key is invalid. Please update GROQ_API_KEY on the server."
        return "Sorry, unable to generate an answer at this time. Please try again later."

    def generate_from_context(self, question, context_texts, model=None, stream=False):
        """Generate from prefetched context. Yields text chunks (one chunk if not streaming)."""
        model = model or self.chat_model
        system_prompt = (
            "You are a helpful AI assistant that answers questions based on the provided "
            "context and conversation history. Be conversational and helpful. "
            "If you don't have enough information, say so clearly."
        )
        if context_texts:
            context = "\n".join(context_texts)
            user_content = f"Context from documents: {context}\n\nConversation: {question}"
        else:
            user_content = question

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            if stream:
                stream_resp = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=512,
                    stream=True,
                )
                for chunk in stream_resp:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yield delta
                return

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=512,
            )
            yield response.choices[0].message.content
        except Exception as e:
            print(f"❌ Error calling chat API: {e}")
            yield self._friendly_openai_error(e)

    def generate_answer(self, question, user_id, top_k=3, model=None, roles=None, context_texts=None):
        model = model or self.chat_model
        try:
            if context_texts is None:
                if roles:
                    retrieved_docs = self.query_multi_store(question, user_id, roles=roles, top_k=top_k)
                    context_texts = [doc.page_content for doc in retrieved_docs] if retrieved_docs else []
                else:
                    context_texts = self.query(question, user_id, top_k=top_k)

            if not context_texts:
                return (
                    "No relevant information found. Please make sure documents were uploaded "
                    "and indexed successfully for your account."
                )

            parts = list(self.generate_from_context(question, context_texts, model=model, stream=False))
            return parts[0] if parts else "Sorry, unable to generate an answer at this time."
        except Exception as e:
            print(f"❌ Error in generate_answer for user {user_id}: {e}")
            return self._friendly_openai_error(e)

    def get_stats(self, user_id):
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            collection_name = user_collection_name(user_id)
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = %s
                """,
                (collection_name,),
            )
            total_chunks = cursor.fetchone()[0]
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS indexed_files_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, file_path)
                )
            """)
            cursor.execute(
                "SELECT COUNT(*) FROM indexed_files_tracking WHERE user_id = %s",
                (user_id,),
            )
            indexed_files_count = cursor.fetchone()[0]
            conn.close()
            return {
                "total_documents": indexed_files_count,
                "total_chunks": total_chunks,
                "vector_store_available": True,
                "llm_available": True,
                "database": "PostgreSQL with pgvector",
                "llm": "Groq Llama 3.1",
            }
        except Exception as e:
            print(f"⚠️ Error getting statistics: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "vector_store_available": False,
                "llm_available": True,
                "database": "Memory backup",
                "llm": "Groq Llama 3.1",
            }

    def clear_index(self, user_id):
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            collection_name = user_collection_name(user_id)
            cursor.execute(
                """
                DELETE FROM langchain_pg_embedding e
                USING langchain_pg_collection c
                WHERE e.collection_id = c.uuid AND c.name = %s
                """,
                (collection_name,),
            )
            cursor.execute(
                "DELETE FROM indexed_files_tracking WHERE user_id = %s",
                (user_id,),
            )
            conn.commit()
            conn.close()
            print(f"🗑️ Cleared PGVector index and file tracking for user {user_id}.")
        except Exception as e:
            print(f"❌ Error clearing index: {e}")

SimpleRAGManager = RAGManagerPGVector
