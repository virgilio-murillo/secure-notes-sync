# nsync — Secure Notes Sync

Sync encrypted notes across devices using AWS (Cognito + S3). Zero-trust: AWS never sees plaintext. TOTP-only auth.

## Architecture

- **S3**: stores a single AES-256-GCM encrypted blob (`store.enc`)
- **Cognito**: User Pool (TOTP MFA required) + Identity Pool → temporary 1hr AWS credentials
- **Client-side encryption**: all data encrypted before touching AWS
- **Pending approval**: untrusted devices submit changes; trusted device approves

## Setup

### 1. Deploy infrastructure
```bash
cd infra && npm install && npx cdk deploy
```

### 2. Create Cognito user (one-time, via AWS CLI)
```bash
aws cognito-idp admin-create-user --user-pool-id <POOL_ID> --username <USER>
aws cognito-idp admin-set-user-password --user-pool-id <POOL_ID> --username <USER> --password <DEVICE_PWD> --permanent
```

### 3. Install CLI
```bash
cd cli && pip install -e .
```

### 4. Configure
```bash
nsync setup
```

### 5. Trusted Arch laptop — source the pass wrapper
```bash
echo 'source /path/to/pass-nsync.bash' >> ~/.bashrc
```

## Commands

| Command | Description |
|---------|-------------|
| `nsync setup` | First-time config + auth |
| `nsync get <path> [-c]` | Show entry (-c: clipboard, clears after 45s) |
| `nsync add <path>` | Add entry (pending if untrusted) |
| `nsync rm <path>` | Remove entry (pending if untrusted) |
| `nsync ls` | List all entries |
| `nsync approve` | Review pending changes (trusted only) |
| `nsync rotate-key` | Rotate cloud encryption key (trusted only) |
| `nsync import-pass` | Import from pass store (trusted only) |

## Security Model

| Layer | Protection |
|-------|-----------|
| AES-256-GCM | Client-side encryption — AWS sees only opaque blob |
| Cognito TOTP | Phone required for any AWS access |
| SRP | Password never transmitted in plaintext |
| Temp credentials | 1-hour STS tokens, no long-lived keys |
| Pending approval | Untrusted changes require trusted device review |
| Stealth naming | No "password" in any resource names |
