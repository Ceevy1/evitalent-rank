from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from evitalent.settings import get_settings


Base = declarative_base()


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(80), unique=True, index=True, nullable=False)
    source_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    parse_status = Column(String(40), default="uploaded", nullable=False)
    raw_path = Column(String(600), nullable=False)
    redacted_path = Column(String(600), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CandidateRecord(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(80), unique=True, index=True, nullable=False)
    document_id = Column(String(80), index=True, nullable=False)
    masked_display_name = Column(String(120), nullable=False)
    extraction_json_path = Column(String(600), nullable=True)
    extraction_mode = Column(String(40), default="mock", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RankingRecord(Base):
    __tablename__ = "rankings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ranking_id = Column(String(80), unique=True, index=True, nullable=False)
    domain = Column(String(40), index=True, nullable=False)
    method_version = Column(String(80), nullable=False)
    result_json_path = Column(String(600), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditRecord(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(80), unique=True, index=True, nullable=False)
    ranking_id = Column(String(80), index=True, nullable=False)
    audit_type = Column(String(40), index=True, nullable=False)
    result_json_path = Column(String(600), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AssistantSessionRecord(Base):
    __tablename__ = "assistant_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(120), unique=True, index=True, nullable=False)
    task_id = Column(String(120), nullable=True)
    domain = Column(String(40), nullable=True)
    candidate_id = Column(String(120), nullable=True)
    scope = Column(String(60), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AssistantMessageRecord(Base):
    __tablename__ = "assistant_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(120), unique=True, index=True, nullable=False)
    session_id = Column(String(120), index=True, nullable=False)
    role = Column(String(20), nullable=False)
    content_safe = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AssistantKnowledgeChunkRecord(Base):
    __tablename__ = "assistant_knowledge_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(160), unique=True, index=True, nullable=False)
    task_id = Column(String(120), nullable=True)
    domain = Column(String(40), index=True, nullable=False)
    candidate_id = Column(String(120), index=True, nullable=True)
    chunk_type = Column(String(60), index=True, nullable=False)
    text_safe = Column(Text, nullable=False)
    source_refs_json = Column(Text, nullable=False)
    display_allowed = Column(Integer, default=1, nullable=False)
    safety_passed = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AssistantEmbeddingRecord(Base):
    __tablename__ = "assistant_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(160), unique=True, index=True, nullable=False)
    embedding_model = Column(String(120), nullable=False)
    vector_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


engine = create_engine(get_settings().resolved_database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _column_type_sql(column: Column) -> str:
    return column.type.compile(dialect=engine.dialect)


def _ensure_columns() -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                nullable = "" if column.nullable or column.default is not None else ""
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {_column_type_sql(column)} {nullable}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def get_session() -> Session:
    init_db()
    return SessionLocal()
