"""Integration tests for publication routes"""

from app.tests import TestClass, client
from app.users.services import UserServices


class TestPublicationRoutes(TestClass):
    """Test class"""

    @staticmethod
    def setup_super_user():
        """
        It creates a superuser, logs in as that user, and returns the access token
        :return: The token is being returned.
        """
        UserServices.create_super_user("John", "Smith", "john@gmail.com", "password")

        response = client.post(url="/api/users/login", json={"email": "john@gmail.com",
                                                             "password": "password"})
        token = response.json()["access_token"]
        return token

    def test_create_new_publication(self):
        """
        This function creates a new publication with the given DOI, year, journal, and title
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage = response.json()
        assert storage["doi"] == "1234"
        assert storage["journal"] == "Journal of Medicine"

    def test_create_new_publication_duplicate(self):
        """
        This function tests that a user cannot create a duplicate publication
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        second_response = client.post(url="/api/publication/create-new-publication",
                                      json={"doi": "1234",
                                            "year": "2022",
                                            "journal": "Journal of Phytochemistry",
                                            "title": "Herbarium API"},
                                      headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_get_publication_by_id(self):
        """
        This function tests the get_publication_by_id route by
        creating a new publication and then getting that publication
        by its id
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        pub = response.json()
        pub_id = pub["pub_id"]
        second_response = client.get(url="/api/publication/get-publication-by-id",
                                     params={"pub_id": pub_id})
        assert second_response.status_code == 200

    def test_get_publication_by_invalid_id(self):
        """
        This function tests the get publication by id route by
        creating a publication and then trying to get it by an
        invalid id
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        pub_id = "invalid id"
        second_response = client.get(url="/api/publication/get-publication-by-id",
                                     params={"pub_id": pub_id})
        assert second_response.status_code == 400

    def test_read_all(self):
        """
        It creates 10 publications, then reads them all
        """
        token = TestPublicationRoutes.setup_super_user()
        for pub in range(10):
            client.post(url="/api/publication/create-new-publication",
                        json={"doi": f"1234{pub}",
                              "year": "2020",
                              "journal": "Journal of Medicine",
                              "title": f"COVID-19 Treatment, part {pub}"},
                        headers={"Authorization": f"Bearer {token}"})
        response = client.get(url="/api/publication/get-all")
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 10

    def test_delete_publication(self):
        """
        This function tests the delete_publication route by
        creating a publication and then deleting it
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        pub = response.json()
        pub_id = pub["pub_id"]
        second_response = client.delete(url="/api/publication/delete-publication",
                                        params={"pub_id": pub_id},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_delete_publication_invalid_id(self):
        """
        This function tests that a publication cannot
        be deleted if the publication id is invalid
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        pub_id = "invalid id"
        second_response = client.delete(url="/api/publication/delete-publication",
                                        params={"pub_id": pub_id},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_delete_publication_invalid_id_no_auth(self):
        """
        This function tests that a user cannot delete a
        publication if they do not have the correct authorization
        """
        token = TestPublicationRoutes.setup_super_user()
        response = client.post(url="/api/publication/create-new-publication",
                               json={"doi": "1234",
                                     "year": "2020",
                                     "journal": "Journal of Medicine",
                                     "title": "COVID-19 Treatment"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        pub_id = "invalid id"
        second_response = client.delete(url="/api/publication/delete-publication",
                                        params={"pub_id": pub_id})
        assert second_response.status_code == 403
