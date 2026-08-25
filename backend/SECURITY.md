# CadastraVision Security Policy & Controls (SIH 2026, PS 26012)

## Security Architecture Overview

The CadastraVision backend implements multi-layered security controls covering authentication, authorization, data protection, upload validation, rate limiting, and audit logging.

---

## 1. Authentication & Authorization
- **JWT Authentication**: OAuth2 Bearer password flow utilizing HS256 JWT tokens.
- **Password Hashing**: Passlib with bcrypt hashing algorithms.
- **Role-Based Access Control (RBAC)**: Strict role checks (`ADMIN`, `ANALYST`, `FIELD_SURVEYOR`, `VIEWER`).
- **Resource Ownership (IDOR Protection)**: Strict ownership and tenant boundary validation on all resource modifications.

---

## 2. Production Hardening Rules
- **Environment Validation**: In `production` environment (`ENVIRONMENT=production`):
  - Insecure default `SECRET_KEY` ("INSECURE_CHANGE_ME_IN_PRODUCTION") is strictly prohibited and fails system startup.
  - `DEBUG=True` mode is strictly prohibited.
- **Request Correlation**: Unique `X-Request-ID` assigned to every request for audit tracing.
- **Information Leakage Prevention**: Stack traces, database internals, and credentials are hidden behind RFC 9457 structured error responses.

---

## 3. Upload & File Security
- **Path Traversal Protection**: Filenames containing `..`, `/`, or `\\` are strictly rejected.
- **Extension Whitelisting**: Restricted to `.tif`, `.tiff`, `.geojson`, `.png`, `.jpg`, `.jpeg`.
- **Payload Limits**: Max file size cap enforced (50MB).

---

## 4. Export & Data Protection
- **CSV Formula Injection Protection**: Leading dangerous characters (`=`, `+`, `-`, `@`) in CSV export cells are automatically escaped with `'`.
- **Secret Sanitization**: Passwords, JWT tokens, API keys, and database credentials are excluded from operational logs and exports.

---

## 5. Tamper-Evident Audit Logging
- **SHA-256 Hash Chaining**: Audit events maintain cryptographic hash continuity (`prev_hash` $\rightarrow$ `entry_hash`) to detect tampering, deletion, or reordering.

---

## 6. Vulnerability Reporting
For security vulnerabilities, please contact the security team or backend maintainer (Shiva) via confidential disclosure.
