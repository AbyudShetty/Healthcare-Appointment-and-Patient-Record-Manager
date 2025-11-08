# audit_logs/utils.py

def log_action(user=None, action="", details="", ip_address=None):
    """
    Temporary placeholder for audit logging.
    In final implementation, this will write entries to the AuditLog model.
    """
    print(f"[AUDIT_LOG] user={getattr(user, 'username', 'anonymous')} | action={action} | details={details}")
