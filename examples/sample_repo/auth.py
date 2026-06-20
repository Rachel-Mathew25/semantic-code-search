def authenticate_user(username, password):
    """Checks username and password."""
    return username == "admin" and password == "secret"


def logout_user():
    print("User logged out")


class AuthManager:
    def reset_password(self):
        print("Resetting password")