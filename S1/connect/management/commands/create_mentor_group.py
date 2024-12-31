from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User


class Command(BaseCommand):
    help = "Create the 'Mentor' group with access to the admin site"

    def handle(self, *args, **kwargs):
        group_name = "Mentor"

        # Define permissions for the Mentor group
        mentor_permissions = [
            "add_session",  # Can add sessions
            "change_session",  # Can change sessions
            "delete_session",  # Can delete sessions
            "view_session",  # Can view sessions
        ]

        # Add general view permissions for the admin site
        mentor_permissions.extend(
            [
                "view_user",  # Can view users (if necessary for your use case)
                "view_group",  # Can view groups (if necessary)
            ]
        )

        # Create or get the group
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            self.stdout.write(f"Group '{group_name}' created.")
        else:
            self.stdout.write(f"Group '{group_name}' already exists.")

        # Assign permissions to the group
        permissions = Permission.objects.filter(codename__in=mentor_permissions)
        group.permissions.set(permissions)

        # Set is_staff=True for all users in the Mentor group
        users = User.objects.filter(groups__name=group_name)
        users.update(is_staff=True)

        self.stdout.write(
            f"Assigned permissions to group '{group_name}': {', '.join(mentor_permissions)}"
        )
        self.stdout.write("Set is_staff=True for all Mentor group members.")
