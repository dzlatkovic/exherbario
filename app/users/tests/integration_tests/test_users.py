"""Integration tests for users routes"""


from app.tests import TestClass, client
from app.users.services import UserServices


class TestUserRoutes(TestClass):
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

    def test_create_super_user(self):
        """
        We create a superuser, then use the token to create another superuser
        """
        token = self.setup_super_user()

        response = client.post(url="/api/users/add-new-super-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "michael@gmail.com"
        assert user["is_superuser"] is True

    def test_create_user(self):
        """
        We create a superuser, get a token, and then use that token to create a new user
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == "michael@gmail.com"
        assert user["is_superuser"] is False

    def test_create_user_no_auth(self):
        """
        It tests that a user cannot create a new user without authentication
        """
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"})
        assert response.status_code == 403

    def test_create_duplicate_user(self):
        """
        We create a user with the email michael@gmail.com, then we try to
        create another user with the same email
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        second_response = client.post(url="/api/users/add-new-user",
                                      json={"name": "Mike", "surname": "Scotch",
                                            "email": "michael@gmail.com", "password": "password"},
                                      headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_get_user_by_id(self):
        """
        We create a superuser, then we create a new user, then we get the user by id
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user = response.json()
        user_id = user["user_id"]
        second_response = client.get(url="/api/users/id",
                                     params={"user_id": user_id},
                                     headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_get_user_by_invalid_id(self):
        """
        The above function tests the get_user_by_id function in the
        users.py file. It tests the function by passing in an
        invalid id.
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        second_response = client.get(url="/api/users/id",
                                     params={"user_id": "invalid id"},
                                     headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_get_all_users(self):
        """
        We create a superuser, then we create 10 users, then we get
        all users and assert that the number of users is 11
        """
        token = self.setup_super_user()
        for user in range(10):
            client.post(url="/api/users/add-new-user",
                        json={
                            "name": f"Michael{user}",
                            "surname": "Scott",
                            "email": f"michael{user}@gmail.com",
                            "password": f"password{user}"
                        },
                        headers={"Authorization": f"Bearer {token}"})
        response = client.get(url="/api/users/get-all-users")
        assert response.status_code == 200
        output = response.json()
        assert len(output) == 11

    def test_login(self):
        """
        It creates a superuser, then logs in with the credentials of the superuser
        """
        UserServices.create_super_user("John", "Smith", "john@gmail.com", "password")

        response = client.post(url="/api/users/login", json={"email": "john@gmail.com",
                                                             "password": "password"})
        assert response.status_code == 200

    def test_fail_login(self):
        """
        This function tests that a user cannot log in with an incorrect email
        """
        UserServices.create_super_user("John", "Smith", "john@gmail.com", "password")

        response = client.post(url="/api/users/login", json={"email": "johnatan@gmail.com",
                                                             "password": "password"})
        assert response.status_code == 400

    def test_delete_user_invalid_id(self):
        """
        It tests the delete_user function with an invalid id.
        """
        self.setup_super_user()
        response = client.delete(url="/api/users/delete-user",
                                 params={"user_id": "invalid id"})
        assert response.status_code == 403

    def test_delete_user(self):
        """
        We create a user, then delete that user
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user = response.json()
        user_id = user["user_id"]
        second_response = client.delete(url="/api/users/delete-user",
                                        params={"user_id": user_id},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_update_user(self):
        """
        It creates a new user, then deactivates that user.
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user = response.json()
        user_id = user["user_id"]
        second_response = client.put(url="/api/users/update/is_active",
                                     params={"user_id": user_id, "is_active": False},
                                     headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200

    def test_update_invalid_user(self):
        """
        The above function tests the update_invalid_user function in the users.py file.
        """
        token = self.setup_super_user()
        response = client.post(url="/api/users/add-new-user",
                               json={"name": "Michael", "surname": "Scott",
                                     "email": "michael@gmail.com", "password": "password"},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        user_id = "invalid id"
        second_response = client.put(url="/api/users/update/is_active",
                                     params={"user_id": user_id, "is_active": False},
                                     headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400
