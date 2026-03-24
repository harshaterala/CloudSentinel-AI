# CIS Network Exposure Baseline

Category: CIS Benchmark

- Deny inbound access from 0.0.0.0/0 unless business-critical.
- Restrict admin ports (22, 3389) to approved ranges.
- Segment workloads in private subnets when possible.
- Continuously monitor flow logs for anomalous access.

Risk signal mapping:
- Open security groups + public endpoint => critical attack surface.
