# استيراد المكتبات المطلوبة لنظام RAG
import os
import re
import hashlib
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')

# OpenAI text-embedding-3-small uses 1536 dims.
# FastEmbed experiment left Neon tables at 384 dims — must reset those tables.
OPENAI_EMBEDDING_DIMS = 1536

def user_collection_name(user_id):
    """
    إنشاء اسم مجموعة فريدة لكل مستخدم (OpenAI 1536-d embeddings)
    """
    return f"rag_oai1536_user_{user_id}"

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
    يتعامل مع تحميل الوثائق وفهرستها والبحث فيها وتوليد الإجابات
    """

    def __init__(self, embedding_model=None, api_key=api_key):
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        self.embedding_model = embedding_model or OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )
        self.connection_string = os.getenv("PGVECTOR_CONNECTION_STRING") or os.getenv("DATABASE_URL")
        if not self.connection_string:
            raise ValueError("PGVECTOR_CONNECTION_STRING or DATABASE_URL must be set")
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.ensure_embedding_schema()

    def ensure_embedding_schema(self):
        """
        Drop/recreate vector tables only when stored vectors are the wrong size
        (e.g. FastEmbed 384-d vs OpenAI 1536-d).

        LangChain often creates the column as unbounded `vector` (not vector(1536)).
        That is OK — do NOT wipe on that alone, or every restart deletes the index.
        """
        try:
            import psycopg2
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")

            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = 'langchain_pg_embedding'
                )
            """)
            table_exists = cursor.fetchone()[0]
            needs_reset = False

            if table_exists:
                cursor.execute("""
                    SELECT format_type(a.atttypid, a.atttypmod)
                    FROM pg_attribute a
                    JOIN pg_class c ON a.attrelid = c.oid
                    JOIN pg_namespace n ON c.relnamespace = n.oid
                    WHERE c.relname = 'langchain_pg_embedding'
                      AND a.attname = 'embedding'
                      AND a.attnum > 0
                      AND NOT a.attisdropped
                      AND n.nspname = current_schema()
                """)
                row = cursor.fetchone()
                type_name = (row[0] if row else "") or ""

                # Prefer actual stored vector length over column declaration.
                stored_dims = None
                try:
                    cursor.execute(
                        """
                        SELECT vector_dims(embedding)
                        FROM langchain_pg_embedding
                        WHERE embedding IS NOT NULL
                        LIMIT 1
                        """
                    )
                    dim_row = cursor.fetchone()
                    if dim_row and dim_row[0] is not None:
                        stored_dims = int(dim_row[0])
                except Exception as e:
                    print(f"⚠️ Could not read vector_dims: {e}")

                if stored_dims is not None and stored_dims != OPENAI_EMBEDDING_DIMS:
                    print(
                        f"⚠️ Stored embeddings are {stored_dims}-d, "
                        f"expected {OPENAI_EMBEDDING_DIMS}. Resetting vector tables."
                    )
                    needs_reset = True
                elif stored_dims is None and type_name.startswith("vector("):
                    # Declared fixed size that is not OpenAI's size, and no rows yet
                    if f"vector({OPENAI_EMBEDDING_DIMS})" not in type_name:
                        print(
                            f"⚠️ Embedding column type is '{type_name}', "
                            f"expected vector({OPENAI_EMBEDDING_DIMS}). Resetting vector tables."
                        )
                        needs_reset = True
                else:
                    # Unbounded `vector` or matching dims — keep existing data
                    print(
                        f"ℹ️ Embedding schema OK "
                        f"(column={type_name!r}, stored_dims={stored_dims})"
                    )

            if needs_reset:
                cursor.execute("DROP TABLE IF EXISTS langchain_pg_embedding CASCADE")
                cursor.execute("DROP TABLE IF EXISTS langchain_pg_collection CASCADE")
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
                cursor.execute("DELETE FROM indexed_files_tracking")
                conn.commit()
                print(
                    "✅ Cleared incompatible vector tables. "
                    "Please re-upload PDFs so they can be indexed with OpenAI embeddings."
                )
            else:
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ ensure_embedding_schema warning: {e}")

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

    def query(self, query, user_id, top_k=5, allowed_sources=None):
        """
        البحث في الوثائق المفهرسة
        allowed_sources: optional set/list of file paths — chunks from other sources are excluded
        """
        try:
            clean_query = (query or "").replace('"', "").replace("'", "").strip()
            print(f"🔍 RAG Query: user_id={user_id}, query='{clean_query[:120]}...', top_k={top_k}")
            print(f"📚 Collection: {user_collection_name(user_id)}")
            pgvector_store = self._get_pgvector_store(user_id)

            results = []
            try:
                scored = pgvector_store.similarity_search_with_relevance_scores(clean_query, k=top_k * 3 if allowed_sources else top_k)
                for doc, score in scored:
                    if allowed_sources and not self._source_allowed(doc, allowed_sources):
                        continue
                    try:
                        print(f"   ↪ score={float(score):.4f} preview={doc.page_content[:80]!r}")
                    except Exception:
                        print(f"   ↪ score={score} preview={doc.page_content[:80]!r}")
                    if doc and doc.page_content:
                        results.append(doc.page_content)
                    if len(results) >= top_k:
                        break
            except Exception as e:
                print(f"⚠️ scored search failed, falling back: {e}")
                docs = pgvector_store.similarity_search(clean_query, k=top_k * 3 if allowed_sources else top_k)
                for d in docs:
                    if allowed_sources and not self._source_allowed(d, allowed_sources):
                        continue
                    if d and d.page_content:
                        results.append(d.page_content)
                    if len(results) >= top_k:
                        break

            if not results:
                results = self._vector_sql_fallback(clean_query, user_id, top_k=top_k, allowed_sources=allowed_sources)
            if not results:
                results = self._keyword_fallback(clean_query, user_id, top_k=top_k, allowed_sources=allowed_sources)

            print(f"📊 RAG Query results: {len(results)} documents found")
            return results
        except Exception as e:
            print(f"⚠️ Error querying documents for user {user_id}: {e}")
            return []

    def _source_allowed(self, doc, allowed_sources):
        if not allowed_sources:
            return True
        source = (doc.metadata or {}).get("source") or ""
        src_norm = os.path.normpath(source).lower()
        src_base = os.path.basename(src_norm)
        for allowed in allowed_sources:
            a_norm = os.path.normpath(allowed).lower()
            if src_norm == a_norm or src_base == os.path.basename(a_norm):
                return True
        return False

    def query_with_variants(self, queries, user_id, top_k=8, allowed_sources=None):
        """Run several retrieval queries and merge unique chunks (order preserved)."""
        seen = set()
        merged = []
        variants = []
        for q in queries or []:
            q = (q or "").strip()
            if q and q not in variants:
                variants.append(q)
        if not variants:
            return []
        per_query_k = max(top_k, 6)
        for q in variants[:4]:
            for chunk in self.query(q, user_id, top_k=per_query_k, allowed_sources=allowed_sources) or []:
                if chunk not in seen:
                    seen.add(chunk)
                    merged.append(chunk)
                if len(merged) >= top_k * 2:
                    break
            if len(merged) >= top_k * 2:
                break
        return merged[: max(top_k, 10)]

    def _metadata_source_allowed(self, metadata, allowed_sources):
        if not allowed_sources:
            return True
        if not metadata:
            return False
        if isinstance(metadata, str):
            import json
            try:
                metadata = json.loads(metadata)
            except Exception:
                return False
        source = metadata.get("source") or ""
        src_norm = os.path.normpath(source).lower()
        src_base = os.path.basename(src_norm)
        for allowed in allowed_sources:
            a_norm = os.path.normpath(allowed).lower()
            if src_norm == a_norm or src_base == os.path.basename(a_norm):
                return True
        return False

    def _filter_doc_rows(self, rows, allowed_sources, top_k):
        if not allowed_sources:
            return [r[0] for r in rows[:top_k] if r and r[0]]
        filtered = []
        for row in rows:
            if len(row) >= 2:
                doc_text, meta = row[0], row[1]
                if self._metadata_source_allowed(meta, allowed_sources):
                    filtered.append(doc_text)
            elif row[0]:
                filtered.append(row[0])
            if len(filtered) >= top_k:
                break
        return filtered

    def _vector_sql_fallback(self, query, user_id, top_k=5, allowed_sources=None):
        """Raw pgvector cosine distance when LangChain search returns nothing."""
        try:
            import psycopg2
            collection_name = user_collection_name(user_id)
            embedding = self.embedding_model.embed_query(query)
            vector_literal = "[" + ",".join(str(float(x)) for x in embedding) + "]"
            fetch_k = top_k * 5 if allowed_sources else top_k
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.document, e.cmetadata
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = %s
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
                """,
                (collection_name, vector_literal, fetch_k),
            )
            rows = cursor.fetchall()
            results = self._filter_doc_rows(rows, allowed_sources, top_k)
            if results:
                print(f"🧮 SQL vector fallback found {len(results)} docs for user {user_id}")
            conn.close()
            return results
        except Exception as e:
            print(f"⚠️ SQL vector fallback failed: {e}")
            return []

    def _keyword_fallback(self, query, user_id, top_k=5, allowed_sources=None):
        """If vector search returns nothing, try simple keyword match in stored docs."""
        try:
            import psycopg2
            terms = [t for t in re.findall(r"[A-Za-z0-9\u0600-\u06FF]+", query or "") if len(t) >= 2][:10]
            if not terms:
                return []
            collection_name = user_collection_name(user_id)
            fetch_k = top_k * 5 if allowed_sources else top_k
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            like_clauses = " OR ".join(["e.document ILIKE %s" for _ in terms])
            params = [collection_name] + [f"%{t}%" for t in terms]
            cursor.execute(
                f"""
                SELECT e.document, e.cmetadata
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = %s AND ({like_clauses})
                LIMIT %s
                """,
                params + [fetch_k],
            )
            rows = cursor.fetchall()
            results = self._filter_doc_rows(rows, allowed_sources, top_k)
            conn.close()
            if results:
                print(f"🔎 Keyword fallback found {len(results)} docs for user {user_id}")
            return results
        except Exception as e:
            print(f"⚠️ Keyword fallback failed: {e}")
            return []

    def query_multi_store(self, query, user_id, roles=None, top_k=5):
        # Documents are indexed per user id at upload time — search that store only.
        # (Role-named collections are not used for indexing.)
        _ = roles
        return self.query(query, user_id, top_k=top_k)

    @staticmethod
    def _friendly_openai_error(exc):
        text = str(exc).lower()
        if "insufficient_quota" in text or "credit_balance_exhausted" in text or "no credits" in text:
            return (
                "OpenAI API credits are exhausted. Please add billing credits, "
                "then try again. Your documents remain indexed."
            )
        if "429" in text or "rate limit" in text or "too many requests" in text:
            return "The AI service is busy right now. Please wait a moment and try again."
        return "Sorry, unable to generate an answer at this time. Please try again later."

    def generate_from_context(self, question, context_texts, model="gpt-3.5-turbo", stream=False):
        """Generate from prefetched context. Yields text chunks (one chunk if not streaming)."""
        if not context_texts:
            msg = (
                "I could not find relevant content in your indexed documents for this question. "
                "Make sure the PDF was uploaded and indexed for your account, then try asking "
                "with words that appear in the slides (for example a slide title)."
            )
            yield msg
            return

        system_prompt = (
            "You are a document assistant. Answer using the DOCUMENT CONTEXT below. "
            "Use the conversation history to understand follow-ups like 'tell me more', "
            "'give me more skills', or 'what about X'. "
            "When asked for more detail, extract ALL related facts from the context — "
            "do not only repeat what was already said if more appears in the documents. "
            "If a short name/acronym (e.g. MSN) appears in the context, explain it from that context. "
            "Only say information is missing when it truly is not in the context."
        )
        context = "\n\n---\n\n".join(context_texts)
        user_content = (
            f"DOCUMENT CONTEXT:\n{context}\n\n"
            f"USER QUESTION / CONVERSATION:\n{question}\n\n"
            "Answer thoroughly using the document context. For follow-ups, add new details from the context."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            if stream:
                stream_resp = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=700,
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
                temperature=0.1,
                max_tokens=700,
            )
            yield response.choices[0].message.content
        except Exception as e:
            print(f"❌ Error calling OpenAI API: {e}")
            yield self._friendly_openai_error(e)

    def generate_answer(self, question, user_id, top_k=3, model="gpt-3.5-turbo", roles=None, context_texts=None):
        try:
            if context_texts is None:
                context_texts = self.query_multi_store(
                    question, user_id, roles=roles, top_k=top_k
                ) or []

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
                "llm": "OpenAI GPT-3.5-turbo",
            }
        except Exception as e:
            print(f"⚠️ Error getting statistics: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "vector_store_available": False,
                "llm_available": True,
                "database": "Memory backup",
                "llm": "OpenAI GPT-3.5-turbo",
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
