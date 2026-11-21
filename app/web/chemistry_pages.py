"""Public study, profile and compound pages, rendered from released data only."""

from fastapi import APIRouter, Depends, Request
from fastapi import Path as RoutePath
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.repository import ChemistryRepository
from app.chemistry.services import ChemistryService
from app.chemistry.services.compounds import CompoundRegistry, compound_summary
from app.chemistry.sample_links import public_site, redetermined
from app.db import get_db

router = APIRouter(include_in_schema=False)
ROLE_LABELS = {
    "sampled_from_voucher": "Sampled from the voucher", "same_individual": "Same individual",
    "same_population": "Same population", "collected_alongside": "Collected alongside",
    "cultivated_from": "Cultivated from the voucher", "reference_for_commercial_material": "Reference for commercial material",
}
RUN_LABELS = {"column": "Column", "stationary_phase": "Stationary phase", "polarity_class": "Column polarity",
              "temperature_programme": "Temperature programme", "carrier_gas": "Carrier gas",
              "alkane_series": "Alkane reference series", "ri_type": "RI type", "mobile_phase": "Mobile phase",
              "gradient": "Gradient", "ionisation_mode": "Ionisation mode", "mass_analyser": "Mass analyser"}
PUBCHEM_IMAGES = "; img-src 'self' https://pubchem.ncbi.nlm.nih.gov"


def render(request, *args, **kwargs):
    from .routes import render as render_page  # routes imports this module
    return render_page(request, *args, **kwargs)


class NoPubChem:
    """Public pages read the local registry only."""

    def compounds(self, *_):
        return []

    def same_connectivity(self, *_):
        return []


def service(db: Session) -> ChemistryService:
    return ChemistryService(ChemistryRepository(db), CompoundRegistry(db, NoPubChem()))


def voucher_rows(db: Session, links):
    return [{"id": link.specimen_id, "role": ROLE_LABELS.get(link.role, link.role),
             "name": taxon_name or voucher.subnomen or "Unidentified specimen",
             "accession": voucher.accession or voucher.reg_no, "redetermined": redetermined(link, voucher),
             "at_link": link.name_at_link or link.taxon_name_at_link}
            for link, voucher, taxon_name in links]


@router.get("/studies/{study_id}")
def study_page(request: Request, study_id: str, db: Session = Depends(get_db)):
    try:
        study, profiles, links = service(db).get_public_study(study_id[:50])
    except ChemistryError:
        return render(request, "study.html", status=404, study=None)
    rows = [{"profile": profile, "preparation": preparation, "sample": sample,
             "vouchers": voucher_rows(db, links[sample.id])} for profile, preparation, sample in profiles]
    return render(request, "study.html", study=study, rows=rows)


@router.get("/profiles/{profile_id}")
def profile_page(request: Request, profile_id: str, db: Session = Depends(get_db)):
    try:
        record, links, measurements, corrections = service(db).get_public_profile(profile_id[:50])
    except ChemistryError:
        return render(request, "profile.html", status=404, profile=None)
    profile, preparation, sample = record
    sample_links = links[sample.id]
    study = ChemistryRepository(db).get_study(sample.study_id)
    return render(request, "profile.html", profile=profile, preparation=preparation, sample=sample, study=study,
                  vouchers=voucher_rows(db, sample_links), site=public_site(sample, sample_links),
                  # Elution order when retention times exist, as in a GC results table.
                  measurements=sorted(measurements, key=lambda item: (item[0].rt_min is None, item[0].rt_min or 0,
                                                                      item[0].feature.casefold())),
                  corrections=corrections, run_labels=RUN_LABELS,
                  has=lambda name: any(getattr(row, name) is not None for row, _ in measurements))


@router.get("/compounds/{cid}")
def compound_page(request: Request, cid: int = RoutePath(gt=0, lt=2 ** 31), db: Session = Depends(get_db)):
    compound = ChemistryRepository(db).get_compound(cid)
    if compound is None:
        return render(request, "compound.html", status=404, compound=None)
    return render(request, "compound.html", compound=compound_summary(compound), synonyms=compound.synonyms[:12],
                  headers={"Content-Security-Policy": "default-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
                                                      "form-action 'self'" + PUBCHEM_IMAGES})


