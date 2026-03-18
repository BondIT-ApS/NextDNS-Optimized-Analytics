# Security: Upgrade PyJWT to 2.12.0

**Date:** 2026-03-18
**Alert:** Dependabot #41 — HIGH

## CVE
PyJWT accepts unknown `crit` header extensions, allowing bypass of critical header verification.

## Fix
Upgraded `PyJWT[crypto]` from `2.11.0` → `2.12.0` (first patched version).
