from django.contrib.auth.decorators import user_passes_test

def role_required(roles=[]):
    def check(user):
        return user.is_authenticated and user.rol in roles
    return user_passes_test(check)