import sqlite3
import os
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """
    Local SQLite database index for Research Archive Matcher.
    Manages indexing and searching of research documents.
    """
    def __init__(self, db_path: str = "index.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """
        Creates the SQLite schema if it doesn't exist.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT UNIQUE NOT NULL,
                title TEXT,
                authors TEXT,
                doi TEXT,
                journal TEXT,
                year TEXT,
                abstract TEXT,
                keywords TEXT,
                document_type TEXT,
                page_count INTEGER,
                file_hash TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index on doi, file_hash, title for fast lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doi ON documents (doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hash ON documents (file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON documents (title)")

        # Page-level text storage for full-text search.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pdf_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                page_text TEXT NOT NULL,
                UNIQUE(document_id, page_number),
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS page_search
            USING fts5(
                document_id UNINDEXED,
                page_number UNINDEXED,
                file_path UNINDEXED,
                title UNINDEXED,
                page_text
            )
        """)
        
        conn.commit()
        conn.close()

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        Calculates SHA-256 hash of a file to identify exact duplicates.
        """
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha256.update(data)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def add_document(self, doc_metadata: dict) -> bool:
        """
        Inserts or replaces a document in the index database.
        """
        file_path = doc_metadata["file_path"]
        file_hash = self.calculate_file_hash(file_path)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO documents (
                    file_name, file_path, title, authors, doi, journal, year, 
                    abstract, keywords, document_type, page_count, file_hash, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    file_name = excluded.file_name,
                    title = excluded.title,
                    authors = excluded.authors,
                    doi = excluded.doi,
                    journal = excluded.journal,
                    year = excluded.year,
                    abstract = excluded.abstract,
                    keywords = excluded.keywords,
                    document_type = excluded.document_type,
                    page_count = excluded.page_count,
                    file_hash = excluded.file_hash,
                    indexed_at = excluded.indexed_at
            """, (
                doc_metadata["file_name"],
                file_path,
                doc_metadata.get("title", ""),
                doc_metadata.get("authors", ""),
                doc_metadata.get("doi", ""),
                doc_metadata.get("journal", ""),
                doc_metadata.get("year", ""),
                doc_metadata.get("abstract", ""),
                doc_metadata.get("keywords", ""),
                doc_metadata.get("document_type", ""),
                doc_metadata.get("page_count", 0),
                file_hash,
                datetime.now().isoformat()
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to index document {file_path}: {e}")
            return False
        finally:
            conn.close()

    def replace_page_texts(self, file_path: str, pages: list[dict]) -> int:
        """Replace the stored page text and FTS rows for one document."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id, file_path, title FROM documents WHERE file_path = ?",
                (file_path,),
            )
            document = cursor.fetchone()

            if document is None:
                raise ValueError(f"Document is not indexed: {file_path}")

            document_id = document["id"]
            cursor.execute(
                "DELETE FROM pdf_pages WHERE document_id = ?",
                (document_id,),
            )
            cursor.execute(
                "DELETE FROM page_search WHERE document_id = ?",
                (document_id,),
            )

            for page in pages:
                page_number = int(page["page_number"])
                text = page.get("text", "") or ""
                cursor.execute(
                    """
                    INSERT INTO pdf_pages
                        (document_id, page_number, page_text)
                    VALUES (?, ?, ?)
                    """,
                    (document_id, page_number, text),
                )
                cursor.execute(
                    """
                    INSERT INTO page_search
                        (document_id, page_number, file_path, title, page_text)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        page_number,
                        document["file_path"],
                        document["title"] or "",
                        text,
                    ),
                )

            conn.commit()
            return len(pages)
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_page_count(self, file_path: str | None = None) -> int:
        """Return the number of stored PDF pages."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if file_path is None:
            cursor.execute("SELECT COUNT(*) FROM pdf_pages")
        else:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pdf_pages
                JOIN documents ON documents.id = pdf_pages.document_id
                WHERE documents.file_path = ?
                """,
                (file_path,),
            )

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def search_pages(
        self,
        query: str,
        *,
        exact_phrase: bool = False,
        limit: int = 100,
    ) -> list[dict]:
        """Search page text using SQLite FTS5 and return snippets."""
        if not query.strip():
            return []

        search_query = query.strip()
        if exact_phrase:
            search_query = '"' + search_query.replace('"', '""') + '"'

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                page_search.document_id,
                page_search.page_number,
                page_search.file_path,
                page_search.title,
                page_search.page_text,
                snippet(page_search, 4, '[', ']', ' … ', 32) AS snippet,
                bm25(page_search) AS rank
            FROM page_search
            WHERE page_search MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (search_query, limit),
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_document_count(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_all_documents(self) -> list:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def search(self, query_str: str, field: str = "all") -> list:
        """
        Searches the index database.
        :param query_str: Search term.
        :param field: Field to search in ('all', 'title', 'authors', 'doi', 'journal', 'abstract', 'keywords').
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM documents WHERE "
        term = f"%{query_str}%"
        
        if field == "all":
            sql += """
                title LIKE ? OR 
                authors LIKE ? OR 
                doi LIKE ? OR 
                journal LIKE ? OR 
                abstract LIKE ? OR 
                keywords LIKE ?
            """
            params = (term, term, term, term, term, term)
        elif field in ["title", "authors", "doi", "journal", "abstract", "keywords", "document_type", "year"]:
            sql += f"{field} LIKE ?"
            params = (term,)
        else:
            sql += "title LIKE ?"
            params = (term,)
            
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_exact_duplicates(self) -> list:
        """
        Finds exact duplicate files based on SHA-256 hash.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        # Find hashes that appear more than once
        cursor.execute("""
            SELECT file_hash, COUNT(*) as cnt 
            FROM documents 
            WHERE file_hash IS NOT NULL AND file_hash != ''
            GROUP BY file_hash 
            HAVING cnt > 1
        """)
        dup_hashes = [row['file_hash'] for row in cursor.fetchall()]
        
        duplicates = []
        for h in dup_hashes:
            cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (h,))
            rows = [dict(row) for row in cursor.fetchall()]
            duplicates.append(rows)
            
        conn.close()
        return duplicates

    def get_potential_duplicates(self) -> list:
        """
        Finds potential duplicates based on title similarity.
        (We will perform additional fuzzy title deduplication in the reports/matchers).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        # Find identical titles (case-insensitive, ignoring spacing)
        cursor.execute("""
            SELECT LOWER(TRIM(title)) as clean_title, COUNT(*) as cnt
            FROM documents
            WHERE title IS NOT NULL AND title != ''
            GROUP BY clean_title
            HAVING cnt > 1
        """)
        dup_titles = [row['clean_title'] for row in cursor.fetchall()]
        
        duplicates = []
        for t in dup_titles:
            cursor.execute("SELECT * FROM documents WHERE LOWER(TRIM(title)) = ?", (t,))
            rows = [dict(row) for row in cursor.fetchall()]
            duplicates.append(rows)
            
        conn.close()
        return duplicates

    def remove_document(self, file_path: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM documents WHERE file_path = ?", (file_path,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to remove document {file_path}: {e}")
            return False
        finally:
            conn.close()

    def clear(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()
