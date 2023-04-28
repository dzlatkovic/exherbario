from sqlalchemy.orm import Session
from app.taxonomy.models import Taxonomy
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank


class TaxonomyRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_taxon(self, taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        try:
            taxon = Taxonomy(taxon_name=taxon_data.taxon_name,
                             gbif_key=taxon_data.gbif_key,
                             taxon_rank=taxon_rank,
                             parent_taxon_key=taxon_data.parent_taxon_key,
                             common_name=taxon_data.common_name,
                             authority=taxon_data.authority)
            self.db.add(taxon)
            self.db.commit()
            self.db.refresh(taxon)
            return taxon
        except Exception as error:
            raise error

    def read_taxon_by_gbif_key(self, gbif_key: str):
        return self.db.query(Taxonomy).filter(Taxonomy.gbif_key
                                              == gbif_key).first()

    def read_taxon_by_taxon_id(self, taxon_id: str):
        return self.db.query(Taxonomy).filter(Taxonomy.taxon_id
                                              == taxon_id).first()
