# Security policy

## Supported versions

Only the **latest** release on the `main` branch receives security updates.

## Reporting a vulnerability

**Please don't open a public GitHub issue.** Instead:

1. Use GitHub's **[private vulnerability report]** flow (Security tab → Report
   a vulnerability), or
2. Email the maintainers — replace this line with a real address before
   publishing the repo.

We aim to acknowledge reports within **2 business days** and to ship a fix
within **30 days** for confirmed high-severity issues.

When reporting, please include:

- a description of the vulnerability and its impact,
- steps to reproduce (proof-of-concept appreciated),
- the commit / version affected,
- any suggested mitigation.

## Hardening already in place

- **OWASP Top-10 (2021)** controls — see the table at the bottom of `README.md`
- **Argon2** password hashing
- **django-axes** brute-force lockout
- **CSP, HSTS, Permissions-Policy, X-Frame-Options DENY** security headers
- **CSRF** middleware on every state-changing request
- **Role-based access control** on every view, plus DRF permissions on the API
- **Per-user / per-IP rate limiting** on the importer
- **Defence in depth on self-demotion** — admins can't lower their own role
- **Pinned dependencies** in `pyproject.toml` + `uv.lock`, plus weekly
  Dependabot security PRs

## Local security tooling

- `bandit` runs in CI and locally (`make lint`)
- `ruff` enforces the `S` (security) rule set
- `mypy` strict checks help catch logic bugs early

[private vulnerability report]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability
