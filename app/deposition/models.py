from sqlalchemy import Column, DateTime, ForeignKey, ForeignKeyConstraint, Integer, JSON, LargeBinary, String, Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.mysql import MEDIUMBLOB
from sqlalchemy.orm import deferred

from app.db import Base, new_id


class Institution(Base):
    """A registered namespace for deposition accessions, tied to external registries where known."""
    __tablename__ = "institution"

    code = Column(String(40), primary_key=True)
    name = Column(String(200), nullable=False)
    index_herbariorum_code = Column(String(20), unique=True)
    ror_id = Column(String(9), unique=True)
    registered_by = Column(String(50), ForeignKey("users.user_id"))
    registered_at = Column(DateTime)


class Deposition(Base):
    __tablename__ = "deposition"
    __table_args__ = (UniqueConstraint("institution", "accession", name="uq_deposition_accession"),)

    id = Column(String(50), primary_key=True, default=new_id)
    institution = Column(String(40), nullable=False)
    accession = Column(String(50), nullable=False, default=new_id)
    owner_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    draft = Column(JSON(none_as_null=True))
    draft_revision = Column(String(50))
    latest_version = Column(Integer, nullable=False, default=0)


class DepositionVersion(Base):
    __tablename__ = "deposition_version"
    __table_args__ = (UniqueConstraint("deposition_id", "draft_revision", name="uq_deposition_published_draft"),)

    deposition_id = Column(String(50), ForeignKey("deposition.id"), primary_key=True)
    number = Column(Integer, primary_key=True, autoincrement=False)
    draft_revision = Column(String(50), nullable=False)
    published_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    published_at = Column(DateTime, nullable=False)
    snapshot = Column(JSON, nullable=False)
    snapshot_sha256 = Column(String(64), nullable=False)


class DepositionFile(Base):
    __tablename__ = "deposition_file"
    __table_args__ = (ForeignKeyConstraint(
        ["deposition_id", "version"], ["deposition_version.deposition_id", "deposition_version.number"],
    ),)

    deposition_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True, autoincrement=False)
    profile_id = Column(String(50), primary_key=True)
    content = deferred(Column(LargeBinary().with_variant(MEDIUMBLOB(), "mysql"), nullable=False))


class DepositionArticle(Base):
    __tablename__ = "deposition_article"
    __table_args__ = (ForeignKeyConstraint(
        ["deposition_id", "version"], ["deposition_version.deposition_id", "deposition_version.number"],
    ),)

    deposition_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True, autoincrement=False)
    doi = Column(String(200), primary_key=True)
    linked_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    linked_at = Column(DateTime, nullable=False)


class DepositionWithdrawal(Base):
    __tablename__ = "deposition_withdrawal"
    __table_args__ = (ForeignKeyConstraint(
        ["deposition_id", "version"], ["deposition_version.deposition_id", "deposition_version.number"],
    ),)

    deposition_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True, autoincrement=False)
    reason = Column(Text, nullable=False)
    withdrawn_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    withdrawn_at = Column(DateTime, nullable=False)


class DepositionDOI(Base):
    """A dataset DOI registered for one frozen version, e.g. by mirroring its ZIP to Zenodo."""
    __tablename__ = "deposition_doi"
    __table_args__ = (ForeignKeyConstraint(
        ["deposition_id", "version"], ["deposition_version.deposition_id", "deposition_version.number"],
    ),)

    deposition_id = Column(String(50), primary_key=True)
    version = Column(Integer, primary_key=True, autoincrement=False)
    doi = Column(String(200), nullable=False, unique=True)
    agency = Column(String(20), nullable=False)
    record_url = Column(String(500))
    registered_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    registered_at = Column(DateTime, nullable=False)
