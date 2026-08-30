from django.core.exceptions import PermissionDenied

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_employee_or_admin(user):
    return user.is_authenticated and user.role in ['employee', 'admin']

def is_citizen(user):
    return user.is_authenticated and user.role == 'citizen'

# هذه الدوال سنستخدمها كـ (حراس) للواجهات، 
# مثلاً إذا حاول مواطن الدخول لصفحة موظف، سيمنعه النظام.