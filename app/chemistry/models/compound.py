from sqlalchemy import (JSON, Boolean, Column, DateTime, Double, ForeignKey, ForeignKeyConstraint, Index, Integer, String,
                        Text)

from app.db import Base, new_id


class Compound(Base):
    """A PubChem compound stored locally, so saved data works without PubChem."""
    __tablename__ = "compound"
    __table_args__ = (Index("ix_compound_inchikey", "inchikey"),)

    cid = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String(500), nullable=False)
    iupac_name = Column(Text)
    molecular_formula = Column(String(100))
    monoisotopic_mass = Column(Double)
    inchi = Column(Text)
    inchikey = Column(String(27))
    smiles = Column(Text)
    synonyms = Column(JSON, nullable=False)
    # From PubChem synonyms. Not checked against CAS; there may be several.
    cas_numbers = Column(JSON, nullable=False)
    retrieved_at = Column(DateTime, nullable=False)


class ChemistryStructure(Base):
    """A structure supplied by an author (SMILES or molfile) for a compound PubChem does not have, e.g. a new
    natural product. Identifiers are computed locally with RDKit; it is public once a released profile uses it."""
    __tablename__ = "chemistry_structure"

    id = Column(String(50), primary_key=True, default=new_id)
    inchikey = Column(String(27), nullable=False, unique=True)
    inchi = Column(Text, nullable=False)
    smiles = Column(Text, nullable=False)
    molecular_formula = Column(String(100), nullable=False)
    monoisotopic_mass = Column(Double, nullable=False)
    name = Column(String(500), nullable=False)
    submitted_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    submitted_at = Column(DateTime, nullable=False)


class CompoundAlias(Base):
    """An author's confirmed name-to-compound choice, reused in later imports."""
    __tablename__ = "compound_alias"

    owner_id = Column(String(50), ForeignKey("users.user_id"), primary_key=True)
    name_key = Column(String(160), primary_key=True)
    name = Column(String(160), nullable=False)
    cid = Column(Integer, ForeignKey("compound.cid"), nullable=False)
    updated_at = Column(DateTime, nullable=False)


class MeasurementCorrection(Base):
    """A logged change of a measurement's compound assignment. Values and source files are never edited."""
    __tablename__ = "chemistry_measurement_correction"
    __table_args__ = (ForeignKeyConstraint(["profile_id", "feature"],
                                           ["chemistry_measurement.profile_id", "chemistry_measurement.feature"]),)

    id = Column(String(50), primary_key=True, default=new_id)
    profile_id = Column(String(50), nullable=False)
    feature = Column(String(160), nullable=False)
    old_cid = Column(Integer)
    new_cid = Column(Integer)
    old_structure_id = Column(String(50), ForeignKey("chemistry_structure.id"))
    new_structure_id = Column(String(50), ForeignKey("chemistry_structure.id"))
    actor_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    reason = Column(String(1000), nullable=False)
    corrected_at = Column(DateTime, nullable=False)


class CompoundName(Base):
    """Normalized title and synonyms of a registered compound, for name matching."""
    __tablename__ = "compound_name"
    __table_args__ = (Index("ix_compound_name_key", "name_key"),)

    cid = Column(Integer, ForeignKey("compound.cid"), primary_key=True, autoincrement=False)
    name_key = Column(String(300), primary_key=True)
    is_title = Column(Boolean, nullable=False)
