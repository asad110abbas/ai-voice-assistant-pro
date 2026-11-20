from __future__ import annotations

import os
import re
from loguru import logger
from docx import Document
import chromadb
from chromadb.utils import embedding_functions

FAQ_PATH = os.getenv("FAQ_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_faqs.docx"))
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "faq_db")
COLLECTION_NAME = "store_faqs"


def _parse_faqs(path: str) -> list[dict]:
    """Extract Q&A entries from docx.

    Each answer is authored as a quoted block that can span several
    paragraphs (bullet points are separate paragraphs within one answer,
    closed by a paragraph ending in a closing quote). Grouping by "Topic:"
    headers alone (the old approach) silently merged every paragraph
    without one into whichever topic came before it, burying most answers
    — including all installment/EMI content — inside an unrelated topic's
    entry.
    """
    doc = Document(path)
    faqs: list[dict] = []
    seen: set[str] = set()
    buf: list[str] = []

    def flush():
        if not buf:
            return
        text = " ".join(buf).strip(' "“”,')
        buf.clear()
        if len(text) <= 20:
            return
        if text.lower().startswith("topic"):
            topic, sep, content = text.partition(".")
            content = content.strip() if sep and content.strip() else text
        else:
            topic, content = "", text
        # Several answers are repeated near-verbatim (only URLs, bullet
        # symbols, or spacing/punctuation differ) — without dedup these
        # clones dominate top-N search results and crowd out genuinely
        # different answers. Key on alnum tokens only to catch them.
        key = re.sub(r"https?://\S+", "", content)
        key = re.sub(r"[^a-z0-9]+", " ", key.lower()).strip()
        if key in seen:
            return
        seen.add(key)
        faqs.append({"topic": topic, "content": content})

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        buf.append(text)
        # Some paragraphs end in a closing quote followed by a stray comma
        # or period (e.g. pasted from a JSON/array literal) — strip that
        # trailing punctuation before checking, or the block never closes
        # and swallows every paragraph up to the next real closing quote.
        trimmed_end = text.rstrip(" ,.")
        if trimmed_end.endswith('"') or trimmed_end.endswith("”"):
            flush()

    flush()
    return faqs


class FAQRetriever:
    def __init__(self):
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        client = chromadb.PersistentClient(path=DB_PATH)
        self.collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
        )

        # Index FAQs if collection is empty
        if self.collection.count() == 0:
            self._index()

        logger.info(f"FAQ RAG ready — {self.collection.count()} entries indexed")

    def _index(self):
        if not os.path.exists(FAQ_PATH):
            logger.warning(f"FAQ document not found at {FAQ_PATH}")
            return

        faqs = _parse_faqs(FAQ_PATH)
        if not faqs:
            return

        docs, ids, metas = [], [], []
        for i, faq in enumerate(faqs):
            docs.append(faq["content"])
            ids.append(f"faq_{i}")
            metas.append({"topic": faq["topic"]})

        self.collection.add(documents=docs, ids=ids, metadatas=metas)
        logger.info(f"Indexed {len(faqs)} FAQ entries")

    def retrieve(self, query: str, n_results: int = 3) -> str:
        """Return relevant FAQ context for the query, combining the top matches."""
        if not query.strip() or self.collection.count() == 0:
            return ""

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count()),
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            return ""

        entries = []
        for doc, meta in zip(docs, metas):
            topic = meta.get("topic", "") if meta else ""
            entries.append(f"{topic}: {doc}" if topic else doc)

        return "\n---\n".join(entries)


# Singleton
_retriever: FAQRetriever | None = None


def get_retriever() -> FAQRetriever:
    global _retriever
    if _retriever is None:
        _retriever = FAQRetriever()
    return _retriever
