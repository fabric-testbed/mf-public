# FABRIC Public Metrics

Ansible-based deployment of the FABRIC Testbed metrics stack: Prometheus, Grafana, and supporting services for public, infrastructure, and research metrics.

---

## Overview

This repository contains Ansible playbooks and roles that install and configure a full observability stack on FABRIC Testbed nodes. Three distinct metric environments are supported:

| Environment | Playbook | Purpose |
|---|---|---|
| Public | `playbook_fabric_public_metrics_install.yml` | Outward-facing dashboards and metrics |
| Infrastructure | `playbook_fabric_infrastructure_metrics_install.yml` | Internal node/network monitoring |
| Research | `playbook_fabric_research_metrics_install.yml` | Experiment and research data collection |

---

## Repository Structure

```
mf-public/
├── public-metrics.ipynb               # Interactive deployment walkthrough
├── instrumentize/
│   ├── ansible/                       # Top-level playbooks
│   │   ├── playbook_fabric_public_metrics_install.yml
│   │   ├── playbook_fabric_infrastructure_metrics_install.yml
│   │   └── playbook_fabric_research_metrics_install.yml
│   └── prometheus/
│       ├── ansible/                   # Ansible roles
│       │   ├── public_metrics/        # Role: public-facing stack
│       │   └── infrastructure_metrics/# Role: internal monitoring stack
│       └── snmp_generator/            # SNMP collector configs (ISIS, PDU, PTU)
```

### Role layout (each role follows the same pattern)

```
<role>/
├── defaults/       # Default variable values
├── files/          # Static files: Flask apps, scripts, latency analyzers
├── tasks/          # Task files grouped by component
│   ├── grafana/    # Config, plugins, provisioning, users
│   ├── prometheus/ # Config, alerting rules, recording rules, targets
│   ├── nginx/      # Reverse proxy and authentication
│   ├── minio/      # S3-compatible object storage
│   ├── vouch/      # VouchProxy OIDC authentication
│   └── docker/     # Docker network and container setup
└── templates/      # Jinja2 configuration templates
```

---

## Stack Components

| Component | Role |
|---|---|
| **Prometheus** | Metrics scraping and storage |
| **Grafana** | Dashboards and visualization |
| **Nginx** | Reverse proxy and TLS termination |
| **MinIO** | S3-compatible storage for long-term metrics |
| **VouchProxy** | OIDC/OAuth2 authentication gateway |
| **SNMP Exporter** | Network device metrics (routers, PDUs, PTUs) |
| **Flask apps** | Custom metric exporters (latency analysis, auth) |
| **Docker** | Container runtime for all services |

---

## Prerequisites

- Ansible installed on the control node
- SSH access to target hosts
- An inventory file (`fabric-hosts`) with target node addresses
- An Ansible vault file containing secrets (passwords, tokens, certs)

---

## Deployment

The Jupyter notebook [`public-metrics.ipynb`](public-metrics.ipynb) provides a step-by-step interactive walkthrough. For direct CLI use:

**Dry-run (check + diff, no changes applied)**
```bash
ansible-playbook \
  -i fabric-hosts \
  --vault-password-file /path/to/vault-pass \
  --check --diff \
  instrumentize/ansible/playbook_fabric_public_metrics_install.yml
```

**Live deployment**
```bash
ansible-playbook \
  -i fabric-hosts \
  --vault-password-file /path/to/vault-pass \
  instrumentize/ansible/playbook_fabric_public_metrics_install.yml
```

Replace the playbook filename with the infrastructure or research variant as needed.

---

## Secrets Management

Sensitive values (credentials, certificates, API tokens) are stored in an Ansible vault. Never commit plaintext secrets. Encrypt new secrets with:

```bash
ansible-vault encrypt_string 'secret-value' --name 'variable_name'
```

---

## SNMP Configuration

Network device metrics are collected via the Prometheus SNMP exporter. Generator configs live in [`instrumentize/prometheus/snmp_generator/`](instrumentize/prometheus/snmp_generator/) and cover ISIS routers, PDU, and PTU devices. After editing a generator config, regenerate `snmp.yml` with the `snmp_generator` tool before redeploying.

---

## License

See [LICENSE](LICENSE).
