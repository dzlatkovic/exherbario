from app.tests import TestClass, TestingSessionLocal
from app.publication.repository import PublicationRepository


class TestPublicationRepo(TestClass):
    """
    This class tests the Publication class
    """
    def create_publications_for_methods(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            publication_repository.create_publication("1200", "2010",
                                                      "Computer Science", "Herbarium API")
            publication_repository.create_publication("1200", "2010",
                                                      "Modern Science", "Covid: Hoax or Truth")

    def test_create_publication(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            pub = publication_repository.create_publication("1200", "2010",
                                                            "Computer Science", "Herbarium API")
            assert pub.doi == "1200"
            assert pub.journal == "Computer Science"

    def test_read_all(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            all_publications = publication_repository.read_all()
            assert len(all_publications) == 2

    def test_read_publication_by_id(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine", "COVID-19 Treatment")
            retrieved_pub = publication_repository.read_publication_by_id(pub.pub_id)
            assert retrieved_pub.title == "COVID-19 Treatment"

    def test_delete_publication(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine", "COVID-19 Treatment")
            success = publication_repository.delete_publication(pub.pub_id)
            assert success == True

    def test_read_publication_by_doi(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            self.create_publications_for_methods()
            pub = publication_repository.create_publication("1234", "2020",
                                                            "Journal of Medicine", "COVID-19 Treatment")
            retrieved_pub = publication_repository.read_publication_by_doi("1234")
            assert retrieved_pub.title == "COVID-19 Treatment"
