"""Create an administrator from the operator's shell."""

from argparse import ArgumentParser
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.users.schemas import UserSchemaIn
from app.users.services import UserServices


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("name")
    parser.add_argument("surname")
    args = parser.parse_args()
    password = getpass("Administrator password: ")
    if not password or password != getpass("Confirm password: "):
        parser.error("Enter matching, non-empty passwords.")
    try:
        user = UserSchemaIn(**vars(args), password=password)
        UserServices.create_super_user(user.name, user.surname, user.email, user.password)
    except ValidationError:
        parser.error("Enter a valid email address.")
    except IntegrityError:
        parser.error("An account already uses that email address.")
    print(f"Administrator created for {user.email}.")


if __name__ == "__main__":
    main()
