"""
Cloud security knowledge base for RAG retrieval.
Contains best practices, common misconfiguration patterns, and remediation guidance.
"""

KNOWLEDGE_DOCUMENTS = [
    # --- S3 / Storage ---
    {
        "title": "S3 Public Access Risk",
        "content": (
            "Publicly accessible S3 buckets are one of the most common causes of cloud data breaches. "
            "When an S3 bucket allows public read or write access, any internet user can download or modify "
            "stored objects. This may lead to data leakage, regulatory violations (GDPR, HIPAA), and "
            "reputational damage. Remediation: Disable all public access using the S3 Block Public Access "
            "settings. Enforce bucket policies that deny any principal outside your AWS accounts. Enable "
            "server-side encryption (SSE-S3 or SSE-KMS). Enable access logging and CloudTrail data events."
        ),
        "tags": ["S3", "public_access", "data_leakage", "encryption"],
    },
    {
        "title": "Unencrypted Storage Volumes",
        "content": (
            "EBS volumes and other storage resources that lack encryption at rest expose sensitive data to "
            "insider threats and physical media theft. AWS, Azure, and GCP all provide transparent encryption "
            "options at no additional cost. Remediation: Enable default EBS encryption in the account. "
            "Encrypt existing volumes by creating encrypted snapshots and restoring them. Use KMS customer "
            "managed keys for finer access control."
        ),
        "tags": ["EBS", "encryption", "storage", "data_at_rest"],
    },
    # --- EC2 / Compute ---
    {
        "title": "Open Security Groups",
        "content": (
            "Security groups with ingress rules open to 0.0.0.0/0 on sensitive ports (SSH 22, RDP 3389, "
            "database ports) dramatically increase attack surface. Attackers continuously scan for open ports "
            "and can exploit default credentials or unpatched services. Remediation: Restrict security group "
            "rules to specific CIDR ranges. Use Systems Manager Session Manager or VPN instead of direct SSH. "
            "Enable VPC Flow Logs to monitor traffic patterns."
        ),
        "tags": ["EC2", "security_group", "network", "open_ports"],
    },
    {
        "title": "Publicly Exposed EC2 Instances",
        "content": (
            "EC2 instances with public IP addresses and unrestricted security groups are exposed to brute-force "
            "attacks, vulnerability exploitation, and unauthorised data access. Exposure duration amplifies risk "
            "because attackers have more time to discover and exploit weaknesses. Remediation: Move instances to "
            "private subnets behind a load balancer. Remove public IPs unless absolutely required. Use AWS WAF "
            "and Shield for internet-facing workloads."
        ),
        "tags": ["EC2", "public_exposure", "network", "attack_surface"],
    },
    {
        "title": "Idle and Oversized EC2 Instances",
        "content": (
            "EC2 instances consistently running below 10% CPU utilisation are considered idle and represent "
            "wasted cloud spend. Instances using less than 40% CPU at a high cost are oversized. Both scenarios "
            "contribute to cost inefficiency without improving security posture. Remediation: Right-size instances "
            "using AWS Compute Optimizer recommendations. Schedule non-production instances to stop outside "
            "business hours. Migrate steady-state workloads to Reserved Instances or Savings Plans."
        ),
        "tags": ["EC2", "cost", "idle", "right_sizing"],
    },
    # --- RDS / Database ---
    {
        "title": "Publicly Accessible RDS Instances",
        "content": (
            "RDS instances configured with public accessibility allow connections from any IP address if "
            "security group rules permit it. This exposes databases to SQL injection, credential stuffing, "
            "and data exfiltration. Remediation: Disable public accessibility in the RDS instance settings. "
            "Place RDS in private subnets. Use IAM database authentication. Enable encryption at rest and in "
            "transit. Enable automated backups and audit logging."
        ),
        "tags": ["RDS", "database", "public_access", "SQL_injection"],
    },
    {
        "title": "Unencrypted RDS Databases",
        "content": (
            "RDS databases without encryption at rest violate most compliance frameworks (SOC 2, PCI DSS, "
            "HIPAA). If storage media is compromised, plaintext data is immediately accessible. Remediation: "
            "Enable encryption when creating new RDS instances. For existing unencrypted instances, create an "
            "encrypted snapshot, then restore from it. Use AWS KMS for key management."
        ),
        "tags": ["RDS", "encryption", "compliance", "data_at_rest"],
    },
    # --- IAM ---
    {
        "title": "Overly Permissive IAM Policies",
        "content": (
            "IAM policies using wildcard (*) actions or resources grant excessive permissions that violate "
            "the principle of least privilege. A compromised identity with broad permissions can access any "
            "service and data. Remediation: Audit IAM policies using IAM Access Analyzer. Replace wildcard "
            "policies with specific action and resource ARNs. Implement permission boundaries. Enable MFA "
            "for all human users. Rotate access keys regularly."
        ),
        "tags": ["IAM", "permissions", "least_privilege", "access_control"],
    },
    {
        "title": "IAM Root Account Usage",
        "content": (
            "Using the AWS root account for daily operations is a critical risk. The root account has "
            "unrestricted access to all resources and cannot be constrained by IAM policies. Remediation: "
            "Enable MFA on the root account. Create individual IAM users with appropriate permissions. "
            "Use AWS Organizations SCPs to restrict root account actions. Monitor root account usage via CloudTrail."
        ),
        "tags": ["IAM", "root_account", "MFA", "access_control"],
    },
    # --- Lambda ---
    {
        "title": "Lambda Function Security",
        "content": (
            "Lambda functions with overly broad execution roles, publicly invokable endpoints, or embedded "
            "secrets are common attack vectors. Serverless doesn't mean security-free. Remediation: Apply least "
            "privilege execution roles. Use environment variables backed by Secrets Manager instead of hardcoded "
            "credentials. Enable function URL authentication. Set reserved concurrency limits to prevent abuse."
        ),
        "tags": ["Lambda", "serverless", "permissions", "secrets"],
    },
    # --- General ---
    {
        "title": "Cloud Configuration Severity",
        "content": (
            "Configuration severity is a composite measure of how far a resource's settings deviate from "
            "security best practices. High severity indicates multiple misconfigurations that compound risk. "
            "Remediation: Implement AWS Config rules or Azure Policy to enforce baseline configurations. "
            "Use infrastructure-as-code (Terraform, CloudFormation) to prevent configuration drift. Run "
            "periodic compliance scans with tools like AWS Security Hub or Prowler."
        ),
        "tags": ["configuration", "compliance", "drift", "best_practices"],
    },
    {
        "title": "Data Sensitivity Classification",
        "content": (
            "Resources handling highly sensitive data (PII, PHI, financial records) require stronger controls. "
            "Higher data sensitivity amplifies the impact of any security breach. Remediation: Classify data "
            "using AWS Macie or similar tools. Apply encryption, access controls, and audit logging proportional "
            "to sensitivity. Implement data loss prevention (DLP) policies."
        ),
        "tags": ["data_classification", "sensitivity", "PII", "DLP"],
    },
    {
        "title": "Exposure Duration Risk",
        "content": (
            "The longer a misconfiguration remains unresolved, the higher the probability of exploitation. "
            "Resources exposed for more than 30 days have significantly elevated risk profiles. Remediation: "
            "Implement automated detection using GuardDuty or Security Hub. Set SLAs for remediation based on "
            "severity. Use automated remediation with Lambda or Systems Manager for common issues."
        ),
        "tags": ["exposure_duration", "time_to_remediate", "SLA", "automation"],
    },
    {
        "title": "Cost Optimisation Best Practices",
        "content": (
            "Cloud cost optimisation requires continuous right-sizing, scheduling, and commitment planning. "
            "Idle resources, oversized instances, and lack of reserved capacity are the top cost drivers. "
            "Remediation: Use AWS Cost Explorer and Compute Optimizer. Implement auto-scaling. Purchase "
            "Reserved Instances or Savings Plans for predictable workloads. Terminate unused resources. "
            "Tag all resources for cost allocation."
        ),
        "tags": ["cost", "optimisation", "right_sizing", "reserved_instances"],
    },
    {
        "title": "DynamoDB Security and Cost",
        "content": (
            "DynamoDB tables without encryption, point-in-time recovery, or with over-provisioned capacity "
            "pose both security and cost risks. Remediation: Enable encryption at rest with KMS. Enable "
            "point-in-time recovery for critical tables. Switch to on-demand capacity mode for unpredictable "
            "workloads. Use auto-scaling for consistent workloads."
        ),
        "tags": ["DynamoDB", "encryption", "cost", "capacity"],
    },
    {
        "title": "EKS Cluster Security",
        "content": (
            "EKS clusters with public API endpoints, overly permissive RBAC, or unpatched node groups are "
            "vulnerable to container escapes and cluster takeover. Remediation: Make the API endpoint private. "
            "Implement network policies. Use managed node groups with automatic patching. Enable audit logging. "
            "Scan container images for vulnerabilities before deployment."
        ),
        "tags": ["EKS", "Kubernetes", "container", "RBAC"],
    },
    {
        "title": "CloudFront Distribution Security",
        "content": (
            "CloudFront distributions without HTTPS enforcement, with permissive CORS policies, or serving "
            "content from public S3 buckets can lead to data interception and content manipulation. "
            "Remediation: Enforce HTTPS with TLS 1.2+. Use Origin Access Identity (OAI) for S3 origins. "
            "Implement geo-restrictions as needed. Enable access logging."
        ),
        "tags": ["CloudFront", "CDN", "HTTPS", "TLS"],
    },
    {
        "title": "Multi-Cloud Security Governance",
        "content": (
            "Operating across AWS, Azure, and GCP increases complexity and the risk of inconsistent security "
            "policies. Remediation: Adopt a cloud security posture management (CSPM) solution. Standardize "
            "identity federation across clouds. Establish unified tagging and naming conventions. Centralize "
            "logging and monitoring."
        ),
        "tags": ["multi_cloud", "governance", "CSPM", "federation"],
    },
    # --- Azure-Specific ---
    {
        "title": "Azure VM Public Exposure",
        "content": (
            "Azure Virtual Machines with public IP addresses and Network Security Groups allowing inbound "
            "traffic from any source (0.0.0.0/0) are at high risk of brute-force attacks and exploitation. "
            "Remediation: Use Azure Bastion for secure RDP/SSH. Remove public IPs from VMs that do not need "
            "direct internet access. Restrict NSG rules to specific source IPs and ports. Enable Azure "
            "Defender for Servers for threat detection and vulnerability assessment."
        ),
        "tags": ["Azure VM", "public_exposure", "NSG", "Azure Bastion"],
    },
    {
        "title": "Azure Storage Account Security",
        "content": (
            "Azure Storage accounts with public blob access enabled or shared key authorization active pose "
            "data leakage risks similar to public S3 buckets. Remediation: Disable public blob access at the "
            "account level. Prefer Azure AD authentication over shared keys. Enable infrastructure encryption "
            "for double encryption at rest. Enable soft delete and versioning for data protection. Configure "
            "private endpoints to restrict network access."
        ),
        "tags": ["Azure Storage", "public_access", "encryption", "private_endpoints"],
    },
    {
        "title": "Azure SQL Database Security",
        "content": (
            "Azure SQL databases with firewall rules allowing all Azure services or 0.0.0.0/0 access are "
            "exposed to unauthorized connections. Remediation: Remove the 'Allow Azure services' rule. "
            "Configure private endpoints. Enable Transparent Data Encryption (TDE). Enable Advanced Threat "
            "Protection and auditing. Use Azure AD authentication instead of SQL authentication."
        ),
        "tags": ["Azure SQL", "database", "firewall", "TDE"],
    },
    {
        "title": "Azure AD and Identity Security",
        "content": (
            "Azure Active Directory tenants without conditional access policies, MFA enforcement, or with "
            "overly permissive role assignments are vulnerable to identity-based attacks. Remediation: "
            "Enable MFA for all users. Implement conditional access policies. Use Privileged Identity "
            "Management (PIM) for just-in-time role activation. Review and minimize Global Administrator "
            "assignments. Enable Identity Protection for risk-based sign-in policies."
        ),
        "tags": ["Azure AD", "identity", "MFA", "conditional_access"],
    },
    {
        "title": "Azure AKS Cluster Security",
        "content": (
            "Azure Kubernetes Service clusters with public API server endpoints, default namespaces in "
            "active use, or without Azure Policy for AKS are at risk of container-based attacks. "
            "Remediation: Enable private cluster mode. Use Azure CNI networking with network policies. "
            "Enable Azure Defender for Kubernetes. Restrict node pool access with managed identities."
        ),
        "tags": ["Azure AKS", "Kubernetes", "container", "private_cluster"],
    },
    # --- GCP-Specific ---
    {
        "title": "GCP Compute Instance Security",
        "content": (
            "GCP Compute Engine instances with external IP addresses, default service accounts, and "
            "permissive firewall rules are exposed to credential theft and lateral movement. Remediation: "
            "Use Identity-Aware Proxy (IAP) instead of external IPs for access. Create custom service "
            "accounts with least-privilege roles. Enable OS Login for SSH key management. Enable "
            "Shielded VM features for integrity verification."
        ),
        "tags": ["GCP Compute", "IAP", "service_account", "firewall"],
    },
    {
        "title": "GCP Storage Bucket Security",
        "content": (
            "GCP Cloud Storage buckets with uniform bucket-level access disabled, allUsers/allAuthenticatedUsers "
            "ACLs, or without customer-managed encryption keys are vulnerable to data exposure. Remediation: "
            "Enable uniform bucket-level access. Remove allUsers and allAuthenticatedUsers bindings. Use "
            "Customer-Managed Encryption Keys (CMEK). Enable object versioning and retention policies. "
            "Restrict access using VPC Service Controls."
        ),
        "tags": ["GCP Storage", "bucket", "ACL", "CMEK"],
    },
    {
        "title": "GKE Cluster Security",
        "content": (
            "Google Kubernetes Engine clusters with legacy ABAC enabled, public endpoints, or without "
            "Workload Identity are at risk of privilege escalation and cluster compromise. Remediation: "
            "Disable legacy ABAC and use RBAC. Enable Workload Identity for pod-level IAM. Use private "
            "clusters with authorized networks. Enable Binary Authorization for container image verification. "
            "Enable GKE Sandbox for untrusted workloads."
        ),
        "tags": ["GKE", "Kubernetes", "RBAC", "Workload Identity"],
    },
    {
        "title": "Cloud SQL (GCP) Security",
        "content": (
            "Cloud SQL instances with public IP addresses, no SSL enforcement, or with the default root "
            "password are prime targets for database attacks. Remediation: Use private IPs only with "
            "Cloud SQL Proxy. Enforce SSL connections. Disable the default root user. Enable automated "
            "backups and point-in-time recovery. Use IAM database authentication."
        ),
        "tags": ["Cloud SQL", "database", "SSL", "private_IP"],
    },
    {
        "title": "Compliance Framework Mapping",
        "content": (
            "Cloud misconfigurations map to specific compliance violations: public storage buckets violate "
            "PCI DSS Requirement 7, unencrypted data violates HIPAA §164.312(a)(2)(iv), overly permissive "
            "IAM policies violate SOC 2 CC6.1, and missing audit logs violate GDPR Article 30. Remediation: "
            "Map each finding to applicable compliance frameworks. Prioritize remediation by regulatory "
            "penalty severity. Implement continuous compliance monitoring."
        ),
        "tags": ["compliance", "PCI_DSS", "HIPAA", "SOC2", "GDPR"],
    },
]
