"""Integration tests for users routes"""

from app.tests import TestClass, client
from app.users.services import UserServices


class TestStorageRoutes(TestClass):
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

    def test_create_new_storage(self):
        """
        It creates a new storage.
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage = response.json()
        assert storage["box"] == "Box1"
        assert storage["room"] == "Room1"
        assert storage["shelf"] == "Shelf1"

    def test_create_new_storage_duplicate(self):
        """
        This function tests that a user cannot create a new storage
        location with the same box name as an existing storage
        location
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        second_response = client.post(url="/api/storage/create-new-storage",
                                      json={"room": "Room2", "shelf": "Shelf2",
                                            "box": "Box1"},
                                      headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_get_storage_by_id(self):
        """
        It creates a new storage, gets the storage_id,
        and then uses that storage_id to get the storage
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage = response.json()
        storage_id = storage["storage_id"]
        second_response = client.get(url="/api/storage/get-storage-by-id",
                                     params={"storage_id": storage_id},
                                     headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_get_storage_by_invalid_id(self):
        """
        This function tests the get_storage_by_id
        by passing in an invalid storage id
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage_id = "invalid id"
        second_response = client.get(url="/api/storage/get-storage-by-id",
                                     params={"storage_id": storage_id},
                                     headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_get_all(self):
        """
        It creates 10 storages, then gets all of them
        """
        token = TestStorageRoutes.setup_super_user()
        for storage in range(10):
            client.post(url="/api/storage/create-new-storage",
                        json={"room": f"Room{storage}", "shelf": f"Shelf{storage}",
                              "box": f"Box{storage}"},
                        headers={"Authorization": f"Bearer {token}"})
        response = client.get(url="/api/storage/get-all", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        output = response.json()
        assert len(output) == 10

    def test_delete_storage_by_id(self):
        """
        It creates a new storage, then deletes it
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage = response.json()
        storage_id = storage["storage_id"]
        second_response = client.delete(url="/api/storage/delete-storage",
                                        params={"storage_id": storage_id},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_delete_storage_by_id_no_auth(self):
        """
        This function tests that a user cannot
        delete a storage if they are not authenticated
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage = response.json()
        storage_id = storage["storage_id"]
        second_response = client.delete(url="/api/storage/delete-storage",
                                        params={"storage_id": storage_id})
        assert second_response.status_code == 403

    def test_delete_storage_by_invalid_id(self):
        """
        This function tests that a user
        cannot delete a storage by an invalid id
        """
        token = TestStorageRoutes.setup_super_user()

        response = client.post(url="/api/storage/create-new-storage",
                               json={"room": "Room1", "shelf": "Shelf1",
                                     "box": "Box1"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage_id = "invalid id"
        second_response = client.delete(url="/api/storage/delete-storage",
                                        params={"storage_id": storage_id},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400
