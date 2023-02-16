"""
Module for the FieldLoc model.

This module defines the `FieldLoc` model class, which is used to represent a field location in
the application. The `FieldLoc` model is used in the database layer to store field location data
and to interact with the database.
"""

from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float

from app.db import Base


class FieldLoc(Base):
    """
    Model class for representing a field location.

    This class defines the fields and attributes of a field location,
    and provides methods for interacting with the database
    layer of the application.
    """
    __tablename__ = "field_loc"
    field_loc_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    country = Column(String(20))
    region = Column(String(20))
    locality = Column(String(40))
    altitude = Column(Integer)
    habitat = Column(String(20))
    gps_lat = Column(Float)
    gps_long = Column(Float)

    def __init__(self, country: str, region: str, locality: str, altitude: int,
                 habitat: str, gps_lat: float, gps_long: float):
        """
        Constructor method for creating a new instance of the FieldLoc class.

        This method creates a new instance of the FieldLoc class with the
        specified values for the class attributes
        :param country: The country where the specimen was found
        :param region: The region of the country where the specimen was found
        :param locality: The name of the place where the specimen was found
        :param altitude: altitude in meters
        :param habitat: the type of habitat the specimen was found in
        :param gps_lat: The latitude of the location
        :param gps_long: The longitude of the location
        """
        self.country = country
        self.region = region
        self.locality = locality
        self.altitude = altitude
        self.habitat = habitat
        self.gps_lat = gps_lat
        self.gps_long = gps_long
