import time
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection, transaction
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Run migrations safely with proper dependency order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=30,
            help='Maximum number of database connection retries'
        )
        parser.add_argument(
            '--retry-delay',
            type=int,
            default=2,
            help='Delay between connection retries in seconds'
        )

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        retry_delay = options['retry_delay']
        
        self.stdout.write(self.style.SUCCESS('Starting safe migration process...'))
        
        # Wait for database to be ready
        if not self._wait_for_database(max_retries, retry_delay):
            self.stdout.write(self.style.ERROR('Database connection failed after maximum retries'))
            return
            
        self.stdout.write(self.style.SUCCESS('Database connection established'))
        
        # Run migrations safely
        self._run_migrations()

    def _wait_for_database(self, max_retries, retry_delay):
        """Wait for the database to be available."""
        retry_count = 0
        while retry_count < max_retries:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return True
            except OperationalError as e:
                retry_count += 1
                self.stdout.write(
                    f'Database not ready, retrying... ({retry_count}/{max_retries})'
                )
                self.stdout.write(f'Error: {e}')
                time.sleep(retry_delay)
        return False

    def _run_migrations(self):
        """Run migrations in the correct order."""
        # Define the migration order to avoid foreign key issues
        migration_order = [
            'contenttypes',
            'auth',
            'admin', 
            'sessions',
            'sites',
            'account',
            'socialaccount',
            'authtoken',
        ]
        
        try:
            # First, run syncdb to create basic tables
            self.stdout.write('Creating database tables...')
            call_command('migrate', '--run-syncdb', verbosity=1, interactive=False)
            
            # Then run specific app migrations in order
            for app in migration_order:
                try:
                    self.stdout.write(f'Migrating {app}...')
                    call_command('migrate', app, verbosity=1, interactive=False)
                    self.stdout.write(self.style.SUCCESS(f'✓ Successfully migrated {app}'))
                except Exception as e:
                    # Some migrations might already be applied or might fail
                    # Log the warning but continue with other migrations
                    self.stdout.write(
                        self.style.WARNING(f'⚠ Migration for {app}: {str(e)}')
                    )
                    continue
            
            # Run any remaining migrations
            self.stdout.write('Running any remaining migrations...')
            call_command('migrate', verbosity=1, interactive=False)
                    
            self.stdout.write(self.style.SUCCESS('✓ All migrations completed successfully'))
            
            # Verify the migration status
            self._verify_migrations()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration failed: {e}'))
            raise

    def _verify_migrations(self):
        """Verify that all migrations have been applied."""
        try:
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            
            if plan:
                self.stdout.write(
                    self.style.WARNING(f'⚠ {len(plan)} migrations still pending')
                )
                for migration, backwards in plan:
                    self.stdout.write(f'  - {migration}')
            else:
                self.stdout.write(self.style.SUCCESS('✓ All migrations are up to date'))
                
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not verify migrations: {e}'))