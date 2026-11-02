# audit_logs/utils.py

def log_action(user=None, action="", details="", ip_address=None):
    from audit_logs.models import AuditLog
    return AuditLog.objects.create(user=user, action=action, details=details, ip_address=ip_address)
