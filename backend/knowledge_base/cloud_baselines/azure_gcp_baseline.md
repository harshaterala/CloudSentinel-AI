# Azure and GCP Security Baseline Concepts

Category: Cloud Baselines

Azure:
- Remove unnecessary public IPs, enforce NSG minimum access.
- Use Azure Policy and Defender recommendations.

GCP:
- Avoid external IP by default; prefer IAP/private access.
- Restrict permissive firewall rules and broad IAM bindings.
- Use SCC and audit logging for posture visibility.
