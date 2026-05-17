# Privacy Policy

**Project:** CMP9134 — Robot Management System (Ground Control Station)  
**Last updated:** May 2026

---

## 1. Overview

This privacy policy describes how the Ground Control Station (GCS) application collects, stores, and manages personal data. The GCS is a prototype system developed for academic purposes. Users should be aware that certain data privacy mechanisms that would be expected in a production deployment are not yet implemented, and these are documented explicitly in this policy.

---

## 2. What Data Is Collected

The GCS collects and stores the following personal data:

- **Username** — provided at registration and used to identify the user across all system interactions.
- **Command history** — a record of every movement command issued, including the target coordinates (x, y) submitted to the `/api/move` endpoint.
- **Timestamps** — the date and time at which each command was issued.
- **Command outcomes** — the result of each command, recorded as either `success` or an error message describing the failure. Error messages may contain system-level information such as HTTP status codes returned by the robot API.

This data is stored in the `mission_logs` table of the application database.

---

## 3. Why Data Is Collected

Data is collected for the following purposes:

- **Safety auditing** — the mission log functions as an audit trail, enabling reconstruction of the sequence of commands issued in the event of an incident or unexpected robot behaviour.
- **Accountability** — associating commands with a named user ensures that all robot control actions are attributable to a specific authenticated individual, supporting the role-based access control model.
- **System diagnostics** — recording command outcomes, including failures, supports debugging and monitoring of the system's interaction with the robot API.

No data is collected for commercial, advertising, or profiling purposes.

---

## 4. How Long Data Is Retained

**Prototype deployment:** Because the application database is stored within the container's filesystem, all data — including user accounts and mission logs — is permanently erased when the container is stopped or recreated. In practice, no data persists beyond an active session in a standard prototype deployment.

**Production deployment:** In a production environment with persistent storage, mission logs would accumulate indefinitely under the current implementation, as no automated retention policy has been configured. This is a known limitation. A production deployment should enforce a defined retention period, for example automatically expiring log entries older than 90 days, in accordance with the GDPR principle of data minimisation.

---

## 5. Who Can Access Collected Data

Mission logs are currently accessible to any authenticated user via the `GET /api/logs` endpoint, regardless of their assigned role.

**This is a known limitation.** In a production system, access to audit logs containing personal data should be restricted to users with an administrator role. This change has been identified as a required improvement prior to any production deployment.

---

## 6. Requesting Deletion of Your Data

Under the General Data Protection Regulation (GDPR), users have the right to request deletion of their personal data (the right to erasure).

**No automated deletion mechanism is currently implemented.** This is a known limitation of the prototype system. In the interim, deletion requests should be directed to the system administrator, who can manually remove records from the database.

This mechanism should be implemented programmatically before any production deployment.

---

## 7. Known Limitations Summary

The following data privacy gaps are acknowledged and documented for transparency:

| Limitation | Status |
|---|---|
| Users not notified that actions are logged | Known limitation — no in-app notification exists |
| Audit logs accessible to all authenticated users | Known limitation — should be admin-only |
| No automated data retention policy | Known limitation — logs accumulate indefinitely in production |
| No programmatic right-to-erasure mechanism | Known limitation — manual deletion only |
| Error messages in outcome field may contain system data | Under review |

---

## 8. Contact

This application is operated for academic purposes under the CMP9134 module. For data-related queries, contact the system administrator responsible for the deployment.
