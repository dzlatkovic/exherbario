"""Integration tests for field locations routes"""

from app.tests import TestClass, client
from app.users.services import UserServices


class TestFieldLocRoutes(TestClass):
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

    @staticmethod
    def create_field_loc_for_tests():
        """
        It creates a field location for testing purposes
        """
        token = TestFieldLocRoutes.setup_super_user()
        response = client.post(url="/api/field-locations/create-new-field-loc",
                               json={"country": "Serbia",
                                     "region": "Nisava",
                                     "locality": "Suva mt.",
                                     "altitude": 1400,
                                     "habitat": "wood",
                                     "gps_lat": 43.0,
                                     "gps_long": 22.1},
                               headers={"Authorization": f"Bearer {token}"})
        return response

    def test_create_new_field_loc(self):
        """
        It creates a new field location and checks that the response
        is 200 and that the country and gps_lat are correct
        """
        response = TestFieldLocRoutes.create_field_loc_for_tests()
        assert response.status_code == 200
        field_loc = response.json()
        assert field_loc["country"] == "Serbia"
        assert field_loc["gps_lat"] == 43.0

    def test_get_field_loc_by_id(self):
        """
        This function tests the get_field_loc_by_id route by creating
        a field_loc and then using the field_loc_id to get the
        field_loc
        """
        response = TestFieldLocRoutes.create_field_loc_for_tests()
        assert response.status_code == 200
        field_loc = response.json()
        field_loc_id = field_loc["field_loc_id"]
        second_response = client.get(url="/api/field-locations/get-field-loc-by-id",
                                     params={"field_loc_id": field_loc_id})
        assert second_response.status_code == 200

    def test_get_field_loc_by_invalid_id(self):
        """
        This function tests the get_field_loc_by_id route by passing in an invalid id
        """
        response = TestFieldLocRoutes.create_field_loc_for_tests()
        assert response.status_code == 200
        second_response = client.get(url="/api/field-locations/get-field-loc-by-id",
                                     params={"field_loc_id": "invalid id"})
        assert second_response.status_code == 404

    def test_get_all_field_loc(self):
        """
        This function tests the get_all_field_locations route by creating
        a field location and then getting all field locations
        """
        response = TestFieldLocRoutes.create_field_loc_for_tests()
        assert response.status_code == 200
        second_response = client.get(url="/api/field-locations/get-all-field-locations")
        assert second_response.status_code == 200
        content = second_response.json()
        assert len(content) == 1
        assert isinstance(content[0], dict)

    def test_delete_field_loc_by_invalid_id(self):
        """
        It tests if the API returns a 400 status code when the
        user tries to delete a field location by an invalid id
        """
        token = TestFieldLocRoutes.setup_super_user()
        response = client.post(url="/api/field-locations/create-new-field-loc",
                               json={"country": "Serbia",
                                     "region": "Nisava",
                                     "locality": "Suva mt.",
                                     "altitude": 1400,
                                     "habitat": "wood",
                                     "gps_lat": 43.0,
                                     "gps_long": 22.1},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        second_response = client.delete(url="/api/field-locations/delete-field-loc",
                                        params={"field_loc_id": "invalid id"},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 400

    def test_delete_field_loc_no_auth(self):
        """
        This function tests the delete-field-location
        route with an invalid field location id
        """
        response = TestFieldLocRoutes.create_field_loc_for_tests()
        assert response.status_code == 200
        second_response = client.delete(url="/api/field-locations/delete-field-loc",
                                        params={"field_loc_id": "invalid id"})
        assert second_response.status_code == 403

    def test_delete_field_loc(self):
        """
        It creates a new field location, then deletes it
        """
        token = TestFieldLocRoutes.setup_super_user()
        response = client.post(url="/api/field-locations/create-new-field-loc",
                               json={"country": "Serbia",
                                     "region": "Nisava",
                                     "locality": "Suva mt.",
                                     "altitude": 1400,
                                     "habitat": "wood",
                                     "gps_lat": 43.0,
                                     "gps_long": 22.1},
                               headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        field_loc = response.json()
        second_response = client.delete(url="/api/field-locations/delete-field-loc",
                                        params={"field_loc_id": field_loc["field_loc_id"]},
                                        headers={"Authorization": f"Bearer {token}"})
        assert second_response.status_code == 200
