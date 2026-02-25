from django.contrib.admin import AdminSite
from django.contrib import admin
from django.apps import apps

class SecureAdminSite(AdminSite):
    site_header = "Secure Admin"
    site_title = "Secure Admin Panel"
    index_title = "Dashboard"

    def has_permission(self, request):
        """
        Allow only active staff users.
        Works with custom user model.
        """
        user = request.user
        return user.is_active and user.is_staff

    def get_app_list(self, request, app_label=None):
        """
        Filter sidebar apps & models based on permissions.
        Respects:
        - Superuser
        - Group permissions
        - Direct user permissions
        - Custom user model
        """
        try:
            app_list = super().get_app_list(request, app_label)
        except TypeError:
            # Backward compatible with Django versions without app_label arg.
            app_list = super().get_app_list(request)

        user = request.user
        if user.is_superuser:
            return app_list

        filtered_apps = []

        for app in app_list:
            filtered_models = []
            for model in app["models"]:
                perms = model.get("perms", {})

                # Check if user has any permission for this model
                if any(
                    getattr(user, f"has_{perm}_perm", None)() if hasattr(user, f"has_{perm}_perm") else perms.get(perm)
                    for perm in ["add", "change", "delete", "view"]
                ):
                    filtered_models.append(model)

            if filtered_models:
                app["models"] = filtered_models
                filtered_apps.append(app)

        return filtered_apps


secure_admin_site = SecureAdminSite(name="secure_admin")