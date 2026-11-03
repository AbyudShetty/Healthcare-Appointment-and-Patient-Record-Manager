-- Run with psql as the audit table owner or a database administrator AFTER
-- migrations, passing -v app_role=<role>. The application role must not own
-- the table, inherit a privileged role, or be a superuser. Keep migration and
-- retention administration under a separate role.
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE audit_logs_auditlog FROM :"app_role";
GRANT SELECT, INSERT ON TABLE audit_logs_auditlog TO :"app_role";
GRANT USAGE, SELECT ON SEQUENCE audit_logs_auditlog_id_seq TO :"app_role";
