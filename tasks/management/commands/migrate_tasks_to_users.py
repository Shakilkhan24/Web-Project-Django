# Create this file as: tasks/management/commands/migrate_tasks_to_users.py
# First create the directories: tasks/management/ and tasks/management/commands/

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tasks.models import Task

class Command(BaseCommand):
    help = 'Migrate existing tasks to be associated with users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-user-id',
            type=int,
            help='ID of the default user to assign tasks to',
            default=1
        )

    def handle(self, *args, **options):
        default_user_id = options['default_user_id']
        
        try:
            default_user = User.objects.get(id=default_user_id)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {default_user_id} does not exist')
            )
            return

        # Find tasks without a user assigned
        tasks_without_user = Task.objects.filter(user__isnull=True)
        count = tasks_without_user.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All tasks already have users assigned')
            )
            return

        # Update tasks to have the default user
        tasks_without_user.update(user=default_user)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully assigned {count} tasks to user: {default_user.username}'
            )
        )

        # Also try to match tasks by email if possible
        users_with_email = User.objects.exclude(email='').exclude(email__isnull=True)
        for user in users_with_email:
            matched_tasks = Task.objects.filter(owner=user.email, user=default_user)
            if matched_tasks.exists():
                count_matched = matched_tasks.count()
                matched_tasks.update(user=user)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reassigned {count_matched} tasks from default user to {user.username} based on email match'
                    )
                )