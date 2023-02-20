"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


from app.tests import TestClass, TestingSessionLocal
from app.publication.repository import PublicationRepository


class TestPublicationRepo(TestClass):
    """
    This class tests the Publication class
    """
    def create_publications_for_methods(self):
        """
        It creates two publications in the database
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            publication_repository.create_publication("1200", "2010",
                                                      "Computer Science",
                                                      "Herbarium API")
            publication_repository.create_publication("1200", "2010",
                                                      "Modern Science",
                                                      "Covid: Hoax or Truth")

    def test_create_publication(self):
        """
        > This function creates a publication with the given parameters and returns it
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            pub = publication_repository.create_publication("1200", "2010",
                                                            "Computer Science",
                                                            "Herbarium API")
            assert pub.doi == "1200"
            assert pub.journal == "Computer Science"

    def test_read_all(self):
        """
        It creates two publications, then reads them all back and asserts that there are two of them
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            all_publications = publication_repository.read_all()
            assert len(all_publications) == 2

    def test_read_publication_by_id(self):
        """
        This function creates a publication and then retrieves it by its ID
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine",
                                                            "COVID-19 Treatment")
            retrieved_pub = publication_repository.read_publication_by_id(pub.pub_id)
            assert retrieved_pub.title == "COVID-19 Treatment"

    def test_delete_publication(self):
        """
        This function tests the delete_publication function in the PublicationRepository class
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine",
                                                            "COVID-19 Treatment")
            success = publication_repository.delete_publication(pub.pub_id)
            assert success is True

    def test_read_publication_by_doi(self):
        """
        This function tests the read_publication_by_doi function in the PublicationRepository class
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            publication_repository.create_publication("1234",
                                                      "2020",
                                                      "Journal of Medicine",
                                                      "COVID-19 Treatment")
            retrieved_pub = publication_repository.read_publication_by_doi("1234")
            assert retrieved_pub.title == "COVID-19 Treatment"
