import pytest
from fastapi import HTTPException

from app.publication.exceptions import PublicationNotFoundException
from app.tests import TestClass
from app.publication.controller import PublicationController


class TestPublicationController(TestClass):
    """This class tests the PublicationController class"""
    def create_publications_for_methods(self):
        """
        It creates two new publications
        """
        PublicationController.create_new_publication("0001-01", "2010",
                                                     "Computer Science", "Herbarium API")
        PublicationController.create_new_publication("0002-02", "2011",
                                                     "Modern Science", "Covid: Hoax or Truth")

    def test_create_new_publication(self):
        """
        This function creates a new publication
        """
        pub = PublicationController.create_new_publication("0003-03", "2012",
                                                           "Medical Science", "Vaccines and You")
        assert pub.doi == "0003-03"

    def test_get_all(self):
        """
        This function retrieves all publications
        """
        self.create_publications_for_methods()
        pubs = PublicationController.get_all()
        assert len(pubs) > 0

    def test_get_publication_by_id(self):
        """
        This function retrieves a publication by ID
        """
        pub = PublicationController.create_new_publication("0004-04", "2013",
                                                           "Environmental Science",
                                                           "Climate Change and You")
        retrieved_pub = PublicationController.get_publication_by_id(pub.pub_id)
        assert pub.doi == retrieved_pub.doi

    def test_delete_publication_by_id(self):
        """
        This function deletes a publication by ID
        """
        pub = PublicationController.create_new_publication("0005-05", "2014",
                                                           "Computer Science",
                                                           "AI and the Future")
        PublicationController.delete_publication_by_id(pub.pub_id)
        with pytest.raises(HTTPException):
            PublicationController.get_publication_by_id(pub.pub_id)