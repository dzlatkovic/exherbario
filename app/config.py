"""This module contains the Settings class."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    A class that defines the settings of the application.

    :param DATABASE_URL: The database connection used by the API and Alembic.
    :param USER_SECRET: The secret key for generating JWT tokens.
    :param ALGORITHM: The algorithm for generating JWT tokens.
    :param TOKEN_DURATION: The expiration time of the JWT token
    :param LATITUDE: The latitude value used in distance calculations.
    :param LONGITUDE: The longitude value used in distance calculations.
    :param PLANTNET_API_KEY: Private key for Pl@ntNet API.
    :param PUBLIC_BASE_URL: Public origin of this instance, e.g. https://herbar.example.edu. Published
        deposition versions record absolute identifiers under it, so it must be set before publishing.
    :param ZENODO_URL: Zenodo instance used to mirror published versions and obtain dataset DOIs.
    :param ZENODO_TOKEN: Personal access token with deposit:write and deposit:actions scopes.
    :param EXTERNAL_LOOKUPS: Comma-separated providers curators may query: gbif, crossref, ror,
        index_herbariorum, lotus. Leave empty for a fully offline instance.
    :param EXTERNAL_TIMEOUT_SECONDS: Read timeout for a provider request (the connect timeout is 5 s).
    :param EXTERNAL_CONTACT_EMAIL: Contact address sent in the User-Agent, as Crossref and ROR ask.
    :param ROR_CLIENT_ID: Optional ROR client ID for a higher rate limit.
    :param ORCID_CLIENT_ID: Public API client ID; ORCID linking is off until it and the secret are set.
    :param ORCID_CLIENT_SECRET: Public API client secret.
    :param ORCID_URL: https://orcid.org, or https://sandbox.orcid.org for testing.
    :param ORCID_SIGN_IN: Let people whose account has a linked iD sign in with ORCID.
    :param DWC_DATASET_TITLE: Title of the Darwin Core Archive dataset (GBIF shows it).
    :param DWC_DATASET_DESCRIPTION: A paragraph describing the dataset.
    :param DWC_PUBLISHER: Organization publishing the dataset, e.g. the university herbarium.
    :param DWC_CONTACT_EMAIL: Dataset contact; EXTERNAL_CONTACT_EMAIL is used when empty.
    :param DWC_LICENSE: CC0-1.0, CC-BY-4.0 or CC-BY-NC-4.0, the licences GBIF accepts.
    """
    DATABASE_URL: str = "sqlite:///./herbar.db"
    USER_SECRET: str
    ALGORITHM: str
    TOKEN_DURATION: int
    LATITUDE: float
    LONGITUDE: float
    PLANTNET_API_KEY: str
    PUBLIC_BASE_URL: str = ""
    ZENODO_URL: str = "https://zenodo.org"
    ZENODO_TOKEN: str = ""
    EXTERNAL_LOOKUPS: str = "gbif,crossref,ror,index_herbariorum,lotus"
    EXTERNAL_TIMEOUT_SECONDS: float = 15
    EXTERNAL_CONTACT_EMAIL: str = ""
    ROR_CLIENT_ID: str = ""
    ORCID_CLIENT_ID: str = ""
    ORCID_CLIENT_SECRET: str = ""
    ORCID_URL: str = "https://orcid.org"
    ORCID_SIGN_IN: bool = True
    DWC_DATASET_TITLE: str = ""
    DWC_DATASET_DESCRIPTION: str = ""
    DWC_PUBLISHER: str = ""
    DWC_CONTACT_EMAIL: str = ""
    DWC_LICENSE: str = "CC-BY-4.0"

    # Read environment variables, then ./.env. Unrelated keys in .env are ignored, as before.
    model_config = SettingsConfigDict(env_file="./.env", extra="ignore")


settings = Settings()
