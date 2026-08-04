"""
Knowledge Builder — Xây dựng kho tri thức cho AI Chatbot
Thu thập, chia nhỏ, và index toàn bộ tài liệu dự án vào ChromaDB
"""

import os
import re
import glob
import time
import hashlib
import json
import threading
from pathlib import Path

import chromadb
from chromadb.config import Settings

from config import Config


class KnowledgeBuilder:
    """
    Thu thập toàn bộ kiến thức từ dự án và lưu vào ChromaDB.

    Nguồn kiến thức:
    - bao_cao_do_an.md (Báo cáo đồ án ~64KB)
    - db/schema.sql (Cấu trúc CSDL)
    - README.md (Tổng quan dự án)
    - Tất cả file Python (routes, services, core) — trích docstrings + comments
    - config.py (Cấu hình hệ thống)
    """

    CHUNK_SIZE = 800  # Ký tự mỗi chunk
    CHUNK_OVERLAP = 200  # Ký tự overlap giữa các chunk
    COLLECTION_NAME = "mtuface_knowledge"

    # Các file/thư mục cần index
    KNOWLEDGE_SOURCES = {
        "docs": [
            "README.md",
            "docs/bao_cao_do_an.md",
            "docs/ccc.md",
            "docs/huong_dan_su_dung.md",
            "docs/faq.md",
            "docs/api_documentation.md",
            "docs/PROJECT_STRUCTURE.md",
            "docs/HUONG_DAN_CAI_DAT.md",
            "docs/implementation_plan.md",
            "docs/offline_architecture_tasks.md",
        ],
        "database": [
            "db/schema.sql",
            "db/seed.sql",
        ],
        "config": [
            "config.py",
            ".env.example",
        ],
        "code_dirs": [
            "routes",
            "services",
            "core",
            "utils",
            "scripts",
        ],
    }

    def __init__(self):
        self._base_dir = Config.BASE_DIR
        self._chroma_dir = os.path.join(Config.MODELS_DIR, "chroma_db")
        self._status_file = os.path.join(Config.MODELS_DIR, "knowledge_status.json")
        self._lock = threading.Lock()
        self._progress = {"status": "idle", "progress": 0.0, "message": ""}

        # Khởi tạo ChromaDB
        os.makedirs(self._chroma_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=self._chroma_dir, settings=Settings(anonymized_telemetry=False)
        )
        self._collection = None

    def _get_collection(self):
        """Lấy và cache collection để tránh load lại model AI nhiều lần"""
        if self._collection is None:
            self._collection = self._client.get_collection(self.COLLECTION_NAME)
        return self._collection

    # ─── PUBLIC INTERFACE ────────────────────────────────────────────────

    def build(self):
        """Xây dựng kho tri thức từ toàn bộ dự án (chạy background)"""
        thread = threading.Thread(target=self._build_worker, daemon=True)
        thread.start()
        return {"status": "started", "message": "Đang xây dựng kho tri thức AI..."}

    def get_progress(self):
        """Lấy tiến độ hiện tại"""
        with self._lock:
            return dict(self._progress)

    def search(self, query: str, n_results: int = 5) -> list:
        """
        Tìm kiếm các đoạn kiến thức liên quan đến câu hỏi.
        Returns list of {text, source, category, distance}
        """
        try:
            collection = self._get_collection()
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            chunks = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    dist = results["distances"][0][i] if results["distances"] else 0
                    chunks.append(
                        {
                            "text": doc,
                            "source": meta.get("source", "unknown"),
                            "category": meta.get("category", "unknown"),
                            "distance": float(dist),
                        }
                    )
            return chunks
        except Exception as e:
            print(f"[KnowledgeBuilder] Search error: {e}")
            return []

    def get_status(self) -> dict:
        """Lấy trạng thái kho tri thức"""
        try:
            collection = self._get_collection()
            count = collection.count()
            status_data = self._load_status()
            return {
                "ready": count > 0,
                "total_chunks": count,
                "last_built": status_data.get("last_built", None),
                "sources": status_data.get("sources", []),
            }
        except Exception:
            return {
                "ready": False,
                "total_chunks": 0,
                "last_built": None,
                "sources": [],
            }

    # ─── WORKER THREAD ───────────────────────────────────────────────────

    def _build_worker(self):
        """Worker thread xây dựng kho tri thức"""
        try:
            self._update_progress("building", 0.0, "Đang khởi tạo...")

            # Xóa collection cũ và tạo mới
            try:
                self._client.delete_collection(self.COLLECTION_NAME)
            except Exception:
                pass

            collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )

            all_chunks = []
            sources_info = []

            # ── Bước 1: Thu thập tài liệu (40%) ──
            self._update_progress("building", 0.05, "Đang đọc tài liệu dự án...")

            # Docs
            for fname in self.KNOWLEDGE_SOURCES["docs"]:
                fpath = os.path.join(self._base_dir, fname)
                if os.path.exists(fpath):
                    chunks = self._process_markdown(fpath, fname)
                    all_chunks.extend(chunks)
                    sources_info.append({"file": fname, "chunks": len(chunks)})
                    self._update_progress(
                        "building", 0.1, f"Đã đọc: {fname} ({len(chunks)} đoạn)"
                    )

            # Database schema
            for fname in self.KNOWLEDGE_SOURCES["database"]:
                fpath = os.path.join(self._base_dir, fname)
                if os.path.exists(fpath):
                    chunks = self._process_sql(fpath, fname)
                    all_chunks.extend(chunks)
                    sources_info.append({"file": fname, "chunks": len(chunks)})
                    self._update_progress("building", 0.15, f"Đã đọc: {fname}")

            # Config
            for fname in self.KNOWLEDGE_SOURCES["config"]:
                fpath = os.path.join(self._base_dir, fname)
                if os.path.exists(fpath):
                    chunks = self._process_code(fpath, fname, "config")
                    all_chunks.extend(chunks)
                    sources_info.append({"file": fname, "chunks": len(chunks)})

            self._update_progress("building", 0.2, "Đang đọc mã nguồn Python...")

            # Python code
            total_dirs = len(self.KNOWLEDGE_SOURCES["code_dirs"])
            for i, code_dir in enumerate(self.KNOWLEDGE_SOURCES["code_dirs"]):
                dir_path = os.path.join(self._base_dir, code_dir)
                if os.path.isdir(dir_path):
                    py_files = glob.glob(os.path.join(dir_path, "*.py"))
                    for py_file in py_files:
                        fname_rel = os.path.relpath(py_file, self._base_dir)
                        chunks = self._process_code(py_file, fname_rel, code_dir)
                        all_chunks.extend(chunks)
                        sources_info.append({"file": fname_rel, "chunks": len(chunks)})

                progress = 0.2 + (0.2 * (i + 1) / total_dirs)
                self._update_progress("building", progress, f"Đã quét: {code_dir}/")

            # ── Bước 2: Index vào ChromaDB (60%) ──
            self._update_progress(
                "building", 0.4, f"Đang index {len(all_chunks)} đoạn kiến thức..."
            )

            # Loại bỏ ID trùng lặp
            seen_ids = set()
            unique_chunks = []
            for c in all_chunks:
                if c["id"] not in seen_ids:
                    seen_ids.add(c["id"])
                    unique_chunks.append(c)
            all_chunks = unique_chunks

            batch_size = 50
            total = len(all_chunks)
            for start in range(0, total, batch_size):
                batch = all_chunks[start : start + batch_size]
                ids = [c["id"] for c in batch]
                docs = [c["text"] for c in batch]
                metas = [c["metadata"] for c in batch]

                collection.add(
                    ids=ids,
                    documents=docs,
                    metadatas=metas,
                )

                progress = 0.4 + (0.6 * min(start + batch_size, total) / total)
                self._update_progress(
                    "building",
                    progress,
                    f"Đã index {min(start + batch_size, total)}/{total} đoạn",
                )

            # Lưu status
            self._save_status(
                {
                    "last_built": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_chunks": total,
                    "sources": sources_info,
                }
            )

            self._update_progress(
                "done",
                1.0,
                f"✅ Hoàn tất! Đã index {total} đoạn kiến thức từ {len(sources_info)} file.",
            )

        except Exception as e:
            self._update_progress("error", 0, f"❌ Lỗi: {str(e)}")
            print(f"[KnowledgeBuilder] Build error: {e}")
            import traceback

            traceback.print_exc()

    # ─── TEXT PROCESSING ─────────────────────────────────────────────────

    def _process_markdown(self, filepath: str, source_name: str) -> list:
        """Xử lý file markdown — chia theo heading sections"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Chia theo heading (##, ###)
        sections = re.split(r"\n(?=#{1,3}\s)", content)
        chunks = []

        for section in sections:
            section = section.strip()
            if not section or len(section) < 50:
                continue

            # Nếu section quá dài, chia nhỏ thêm
            sub_chunks = self._split_text(section)
            for i, chunk_text in enumerate(sub_chunks):
                chunk_id = self._make_id(source_name, chunk_text)
                # Trích heading làm title
                title_match = re.match(r"^(#{1,3})\s+(.+)", chunk_text)
                title = title_match.group(2) if title_match else source_name

                chunks.append(
                    {
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "source": source_name,
                            "category": "documentation",
                            "title": title[:200],
                            "chunk_index": i,
                        },
                    }
                )

        return chunks

    def _process_sql(self, filepath: str, source_name: str) -> list:
        """Xử lý file SQL — chia theo CREATE TABLE / INSERT"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Chia theo statement
        statements = re.split(r";\s*\n", content)
        chunks = []

        for stmt in statements:
            stmt = stmt.strip()
            if not stmt or len(stmt) < 20:
                continue

            # Thêm context header
            table_match = re.search(r"CREATE TABLE\s+`?(\w+)`?", stmt, re.IGNORECASE)
            table_name = table_match.group(1) if table_match else "SQL"

            chunk_text = f"[SQL Schema - Bảng {table_name}]\n{stmt}"
            chunk_id = self._make_id(source_name, chunk_text)

            chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": {
                        "source": source_name,
                        "category": "database",
                        "title": f"Bảng {table_name}",
                        "chunk_index": 0,
                    },
                }
            )

        return chunks

    def _process_code(self, filepath: str, source_name: str, category: str) -> list:
        """Xử lý file Python — trích xuất classes, functions, docstrings"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []

        chunks = []

        # Trích module docstring
        doc_match = re.match(r'^"""(.*?)"""', content, re.DOTALL)
        if doc_match:
            doc_text = f"[Module: {source_name}]\n{doc_match.group(1).strip()}"
            chunks.append(
                {
                    "id": self._make_id(source_name, "module_doc"),
                    "text": doc_text,
                    "metadata": {
                        "source": source_name,
                        "category": category,
                        "title": f"Module {source_name}",
                        "chunk_index": 0,
                    },
                }
            )

        # Trích class + function definitions
        # Tìm các class/function cùng docstring
        pattern = r'((?:class|def)\s+\w+[^:]*:)\s*\n\s*(?:"""(.*?)""")?'
        for match in re.finditer(pattern, content, re.DOTALL):
            sig = match.group(1).strip()
            doc = match.group(2).strip() if match.group(2) else ""
            chunk_text = (
                f"[Code: {source_name}]\n{sig}\n{doc}"
                if doc
                else f"[Code: {source_name}]\n{sig}"
            )

            if len(chunk_text) < 30:
                continue

            chunks.append(
                {
                    "id": self._make_id(source_name, sig),
                    "text": chunk_text,
                    "metadata": {
                        "source": source_name,
                        "category": category,
                        "title": sig[:200],
                        "chunk_index": 0,
                    },
                }
            )

        # Nếu file nhỏ, index toàn bộ nội dung
        if len(content) < self.CHUNK_SIZE * 2:
            full_text = f"[Toàn bộ mã nguồn: {source_name}]\n{content}"
            sub_chunks = self._split_text(full_text)
            for i, ct in enumerate(sub_chunks):
                chunks.append(
                    {
                        "id": self._make_id(source_name, f"full_{i}"),
                        "text": ct,
                        "metadata": {
                            "source": source_name,
                            "category": category,
                            "title": f"Mã nguồn {source_name}",
                            "chunk_index": i,
                        },
                    }
                )
        else:
            # Index từng phần
            sub_chunks = self._split_text(content)
            for i, ct in enumerate(sub_chunks):
                chunk_text = f"[Code: {source_name}]\n{ct}"
                chunks.append(
                    {
                        "id": self._make_id(source_name, f"part_{i}"),
                        "text": chunk_text,
                        "metadata": {
                            "source": source_name,
                            "category": category,
                            "title": f"Mã nguồn {source_name} - phần {i+1}",
                            "chunk_index": i,
                        },
                    }
                )

        return chunks

    def _split_text(self, text: str) -> list:
        """Chia text thành các chunk nhỏ với overlap"""
        if len(text) <= self.CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.CHUNK_SIZE

            # Tìm điểm cắt tự nhiên (cuối câu, cuối dòng)
            if end < len(text):
                # Ưu tiên cắt ở cuối paragraph
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + self.CHUNK_SIZE // 2:
                    end = para_break
                else:
                    # Cắt ở cuối dòng
                    line_break = text.rfind("\n", start, end)
                    if line_break > start + self.CHUNK_SIZE // 2:
                        end = line_break

            chunks.append(text[start:end].strip())
            start = end - self.CHUNK_OVERLAP

        return [c for c in chunks if c]

    # ─── UTILS ───────────────────────────────────────────────────────────

    _id_counter = 0

    def _make_id(self, source: str, content: str) -> str:
        """Tạo ID duy nhất cho mỗi chunk"""
        KnowledgeBuilder._id_counter += 1
        raw = f"{source}:{content}:{KnowledgeBuilder._id_counter}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _update_progress(self, status: str, progress: float, message: str):
        with self._lock:
            self._progress = {
                "status": status,
                "progress": round(progress, 3),
                "message": message,
            }

    def _save_status(self, data: dict):
        try:
            with open(self._status_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_status(self) -> dict:
        try:
            with open(self._status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


# ─── SINGLETON ───────────────────────────────────────────────────────────
_builder_instance = None


def get_knowledge_builder() -> KnowledgeBuilder:
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = KnowledgeBuilder()
    return _builder_instance
