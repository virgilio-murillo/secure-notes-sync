"""Cognito SRP + TOTP auth with refresh token caching."""
import boto3
from pycognito.aws_srp import AWSSRP
from nsync import config


def _cognito_client(region: str):
    return boto3.client("cognito-idp", region_name=region)


def _identity_client(region: str):
    return boto3.client("cognito-identity", region_name=region)


def authenticate(cfg: dict, totp_code: str | None = None) -> dict:
    """Authenticate and return temporary AWS credentials.

    Tries refresh token first (silent). Falls back to SRP + TOTP.
    On untrusted devices, refresh token expires after 1 hour.
    Returns dict with AccessKeyId, SecretKey, SessionToken.
    """
    import time

    # On untrusted devices, enforce 1-hour session window
    if not cfg.get("trusted") and cfg.get("auth_timestamp"):
        elapsed = time.time() - cfg["auth_timestamp"]
        if elapsed > 3600:
            cfg["refresh_token"] = ""
            config.save(cfg)

    # Try refresh token first (no TOTP needed)
    if cfg.get("refresh_token"):
        try:
            return _refresh_auth(cfg)
        except Exception:
            pass  # refresh token expired/revoked, fall through to full auth

    # Full SRP + TOTP auth
    if totp_code is None:
        totp_code = input("TOTP code: ").strip()

    tokens = _srp_auth(cfg, totp_code)

    # Cache refresh token + timestamp
    cfg["refresh_token"] = tokens["refresh_token"]
    cfg["auth_timestamp"] = time.time()
    config.save(cfg)

    return _get_credentials(cfg, tokens["id_token"])


def _srp_auth(cfg: dict, totp_code: str) -> dict:
    """Full SRP auth flow with TOTP MFA. Returns token dict."""
    client = _cognito_client(cfg["region"])
    srp = AWSSRP(
        username=cfg["username"],
        password=cfg["device_password"],
        pool_id=cfg["user_pool_id"],
        client_id=cfg["client_id"],
        client=client,
    )
    # Initiate SRP
    auth_params = srp.get_auth_params()
    resp = client.initiate_auth(
        AuthFlow="USER_SRP_AUTH",
        AuthParameters=auth_params,
        ClientId=cfg["client_id"],
    )
    # Respond to PASSWORD_VERIFIER
    challenge_resp = srp.process_challenge(resp["ChallengeParameters"], {"USERNAME": cfg["username"]})
    resp = client.respond_to_auth_challenge(
        ClientId=cfg["client_id"],
        ChallengeName="PASSWORD_VERIFIER",
        ChallengeResponses=challenge_resp,
    )
    # Respond to SOFTWARE_TOKEN_MFA
    if resp.get("ChallengeName") == "SOFTWARE_TOKEN_MFA":
        resp = client.respond_to_auth_challenge(
            ClientId=cfg["client_id"],
            ChallengeName="SOFTWARE_TOKEN_MFA",
            Session=resp["Session"],
            ChallengeResponses={
                "USERNAME": cfg["username"],
                "SOFTWARE_TOKEN_MFA_CODE": totp_code,
            },
        )

    result = resp["AuthenticationResult"]
    return {
        "id_token": result["IdToken"],
        "access_token": result["AccessToken"],
        "refresh_token": result["RefreshToken"],
    }


def _refresh_auth(cfg: dict) -> dict:
    """Silent refresh using cached refresh token."""
    client = _cognito_client(cfg["region"])
    resp = client.initiate_auth(
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={
            "REFRESH_TOKEN": cfg["refresh_token"],
        },
        ClientId=cfg["client_id"],
    )
    id_token = resp["AuthenticationResult"]["IdToken"]
    # Update refresh token if a new one was issued
    if "RefreshToken" in resp["AuthenticationResult"]:
        cfg["refresh_token"] = resp["AuthenticationResult"]["RefreshToken"]
        config.save(cfg)
    return _get_credentials(cfg, id_token)


def _get_credentials(cfg: dict, id_token: str) -> dict:
    """Exchange Cognito ID token for temporary AWS credentials."""
    client = _identity_client(cfg["region"])
    provider = f"cognito-idp.{cfg['region']}.amazonaws.com/{cfg['user_pool_id']}"

    identity = client.get_id(
        IdentityPoolId=cfg["identity_pool_id"],
        Logins={provider: id_token},
    )
    creds = client.get_credentials_for_identity(
        IdentityId=identity["IdentityId"],
        Logins={provider: id_token},
    )
    c = creds["Credentials"]
    return {
        "AccessKeyId": c["AccessKeyId"],
        "SecretKey": c["SecretKey"],
        "SessionToken": c["SessionToken"],
    }
