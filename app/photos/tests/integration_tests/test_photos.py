"""Integration tests for photos routes"""

from app.tests import TestClass, client
from app.users.services import UserServices


class TestPhotosRoutes(TestClass):
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

    def test_create_new_photos(self):
        """
        It creates a new photo.
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "specimen.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        storage = response.json()
        assert storage["field_photo"] == "field.jpg"
        assert storage["specimen_photo"] == "specimen.jpg"

    def test_create_new_photos_identical(self):
        """
        It tests that the create-new-photos route returns a
        400 error if the field and specimen photos are identical.
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "field.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 400

    def test_create_new_photos_duplicate(self):
        """
        It tests that a user cannot upload the same photo twice.
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "specimen.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        second_response = client.post(url="/api/photos/create-new-photos",
                                      json={"field_photo": "field.jpg",
                                            "specimen_photo": "specimen2.jpg"},
                                      headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_get_all(self):
        """
        It creates 10 photos, then gets all of them
        """
        token = TestPhotosRoutes.setup_super_user()
        for photo in range(10):
            client.post(url="/api/photos/create-new-photos",
                        json={"field_photo": f"field{photo}.jpg",
                              "specimen_photo": f"specimen{photo}.jpg"},
                        headers={"Authorization": f"Bearer {token}"})
        response = client.get(url="/api/photos/get-all-photos")
        assert response.status_code == 200
        photos = response.json()
        assert len(photos) == 10

    def test_get_by_id(self):
        """
        This function tests the get_by_id route by creating
        a new photo and then retrieving it by its id
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "specimen.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        photos = response.json()
        photos_id = photos["photos_id"]
        second_response = client.get(url="/api/photos/get-photos-by-id",
                                     params={"photos_id": photos_id})
        assert response.status_code == 200
        retrieved_photos = second_response.json()
        assert photos_id == retrieved_photos["photos_id"]

    def test_get_by_invalid_id(self):
        """
        This function tests that the API returns a 400 status
        code when the user tries to get a photo by an invalid id
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "specimen.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        second_response = client.get(url="/api/photos/get-photos-by-id",
                                     params={"photos_id": "invalid id"})
        assert second_response.status_code == 400

    def test_delete_photos_no_auth(self):
        """
        This function tests that a user cannot delete photos without authorization
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "specimen.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        photos = response.json()
        photos_id = photos["photos_id"]
        second_response = client.delete(url="/api/photos/delete-photos",
                                        params={"photos_id": photos_id})
        assert second_response.status_code == 403

    def test_delete_photos(self):
        """
        This function tests the delete-photos route
        """
        token = TestPhotosRoutes.setup_super_user()
        response = client.post(url="/api/photos/create-new-photos",
                               json={"field_photo": "field.jpg",
                                     "specimen_photo": "specimen.jpg"},
                               headers={"Authorization": f"Bearer {token}"})
        photos = response.json()
        photos_id = photos["photos_id"]
        second_response = client.delete(url="/api/photos/delete-photos",
                                        params={"photos_id": photos_id},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_delete_photos_invalid_id(self):
        """
        This function tests that the API endpoint `/api/photos/delete-photos`
        returns a 400 status code when the `photos_id` is invalid
        """
        token = TestPhotosRoutes.setup_super_user()
        client.post(url="/api/photos/create-new-photos",
                    json={"field_photo": "field.jpg",
                          "specimen_photo": "specimen.jpg"},
                    headers={"Authorization": f"Bearer {token}"})
        second_response = client.delete(url="/api/photos/delete-photos",
                                        params={"photos_id": "invalid id"},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400
