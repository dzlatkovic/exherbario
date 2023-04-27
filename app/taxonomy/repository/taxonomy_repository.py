from sqlalchemy.orm import Session
from app.taxonomy.models import Taxonomy
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank


class TaxonomyRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_taxon(self, taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        taxon = Taxonomy(taxon_name=taxon_data.taxon_name,
                         gbif_key=taxon_data.gbif_key,
                         taxon_rank=taxon_rank,
                         parent_gbif_key=taxon_data.parent_gbif_key,
                         common_name=taxon_data.common_name,
                         authority=taxon_data.authority)
        self.db.add(taxon)
        self.db.commit()
        self.db.refresh(taxon)
        return taxon
