from sqlalchemy import select
from sqlalchemy.orm import Session

from app.specimen.models import Specimen
from app.taxonomy.models import Taxonomy
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank


class TaxonomyRepository:

    def __init__(self, db: Session):
        self.db = db

    def add_taxon(self, taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        taxon = Taxonomy(**taxon_data.dict(), taxon_rank=taxon_rank)
        self.db.add(taxon)
        self.db.flush()
        self.db.refresh(taxon)
        return taxon

    def create_taxon(self, taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        taxon = self.add_taxon(taxon_data, taxon_rank)
        self.db.commit()
        self.db.refresh(taxon)
        return taxon

    def read_taxon_by_gbif_key(self, gbif_key: str):
        return self.db.query(Taxonomy).filter(Taxonomy.gbif_key
                                              == gbif_key).first()

    def read_taxon_by_taxon_id(self, taxon_id: str):
        return self.db.query(Taxonomy).filter(Taxonomy.taxon_id
                                              == taxon_id).first()

    def delete_taxon(self, taxon_id: str):
        try:
            taxon = self.read_taxon_by_taxon_id(taxon_id)
            self.db.delete(taxon)
            self.db.commit()
            return True
        except Exception as error:
            raise error

    def get_specimens_by_taxon_name(self, taxon_name: str):
        descendants = select(Taxonomy.taxon_id).where(
            Taxonomy.taxon_name == taxon_name
        ).cte(name="descendants", recursive=True)
        descendants = descendants.union(select(Taxonomy.taxon_id).join(
            descendants, Taxonomy.parent_taxon_key == descendants.c.taxon_id
        ))
        if not self.db.query(Taxonomy.taxon_id).filter_by(taxon_name=taxon_name).first():
            return None
        return self.db.query(Specimen).filter(
            Specimen.taxon_id.in_(select(descendants.c.taxon_id))
        ).order_by(Specimen.reg_no).all()
