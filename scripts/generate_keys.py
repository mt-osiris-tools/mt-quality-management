import base64
import secrets


def _generate_key() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def main() -> None:
    for i in range(1, 4):
        print(f"ENCRYPTION_KEY_LEVEL_{i}={_generate_key()}")


if __name__ == "__main__":
    main()
