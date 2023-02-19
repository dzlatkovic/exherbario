import pytest

from app.publication.exceptions import PublicationNotFoundException
from app.tests import TestClass
from app.publication.services import PublicationService


class TestPublicationService(TestClass):
    """This class tests the PublicationService class"""

    def create_pubs_for_methods(self):
        """
        It creates two new publications
        """
        PublicationService.create_new_publication("1234", "2022", "Nature", "Sample Paper 1")
        PublicationService.create_new_publication("5678", "2022", "Science", "Sample Paper 2")

    def test_create_new_publication(self):
        """
        This function creates a new publication
        """
        publication = PublicationService.create_new_publication("1234", "2022", "Nature", "Sample Paper 1")
        assert publication.doi == "1234"
        assert publication.journal == "Nature"

    def test_read_all(self):
        """
        This function reads all publications
        """
        self.create_pubs_for_methods()
        publications = PublicationService.read_all()
        assert len(publications) == 2

    def test_read_publication_by_id(self):
        """
        This function reads a publication by ID
        """
        self.create_pubs_for_methods()
        publication = PublicationService.read_all()[0]
        pub_id, doi = publication.pub_id, publication.doi
        publication = PublicationService.read_publication_by_id(pub_id)
        assert publication.doi == doi

    def test_delete_publication_by_id(self):
        """
        This function deletes a publication by ID
        """
        self.create_pubs_for_methods()
        pub_id = PublicationService.read_all()[0].pub_id
        result = PublicationService.delete_publication_by_id(pub_id)
        assert result is True
        with pytest.raises(PublicationNotFoundException):
            PublicationService.read_publication_by_id(pub_id)
