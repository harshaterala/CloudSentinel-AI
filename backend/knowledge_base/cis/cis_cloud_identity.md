# CIS Identity and Access Controls

Category: CIS Benchmark

- Enforce MFA for all human identities.
- Prohibit broad wildcard policies like `*:*`.
- Rotate credentials and disable stale access keys.
- Use least privilege and role-based delegation.

Risk signal mapping:
- Over-permissive IAM role => high lateral movement risk.
- Missing MFA => elevated credential abuse risk.
