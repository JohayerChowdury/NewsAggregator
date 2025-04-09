from supabase import create_client, Client


class SupabaseAuthService:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_client: Client = create_client(supabase_url, supabase_key)

    def sign_in(self, email: str, password: str) -> dict:
        """
        Sign in a user with email and password.
        """
        response = self.supabase_client.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )
        return response

    def sign_up(self, email: str, password: str) -> dict:
        """
        Sign up a new user with email and password.
        """
        response = self.supabase_client.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )
        return response

    def sign_out(self) -> dict:
        """
        Sign out the current user.
        """
        response = self.supabase_client.auth.sign_out()
        return response
