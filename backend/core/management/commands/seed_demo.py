"""
Management command to seed demo data for development.

Creates:
- 1 tenant (Acme Corporation)
- 2 users (admin + analyst)
- 3 data sources (SAP, Utility, Travel)
"""
from django.core.management.base import BaseCommand
from core.models import Tenant, User
from ingestion.models import DataSource


class Command(BaseCommand):
    help = 'Seed demo tenant, users, and data sources for development'

    def handle(self, *args, **options):
        # Create tenant
        tenant, created = Tenant.objects.get_or_create(
            slug='acme',
            defaults={'name': 'Acme Corporation'},
        )
        status = 'created' if created else 'already exists'
        self.stdout.write(f'  Tenant: {tenant.name} ({status})')

        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin@breatheesg.com',
            defaults={
                'email': 'admin@breatheesg.com',
                'tenant': tenant,
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('  Admin: admin@breatheesg.com / admin123 (created)'))
        else:
            self.stdout.write(f'  Admin: admin@breatheesg.com (already exists)')

        # Create analyst user
        analyst_user, created = User.objects.get_or_create(
            username='analyst@breatheesg.com',
            defaults={
                'email': 'analyst@breatheesg.com',
                'tenant': tenant,
                'role': 'analyst',
                'is_staff': False,
            },
        )
        if created:
            analyst_user.set_password('analyst123')
            analyst_user.save()
            self.stdout.write(self.style.SUCCESS('  Analyst: analyst@breatheesg.com / analyst123 (created)'))
        else:
            self.stdout.write(f'  Analyst: analyst@breatheesg.com (already exists)')

        # Create data sources
        sources = [
            {'name': 'SAP Munich Plant', 'source_type': 'sap', 'description': 'Fuel and procurement data from SAP ME2M/MB51 exports'},
            {'name': 'ComEd Electricity Portal', 'source_type': 'utility', 'description': 'Monthly electricity billing from ComEd utility portal'},
            {'name': 'Concur Travel Reports', 'source_type': 'travel', 'description': 'Corporate travel expense reports from SAP Concur'},
        ]

        for src in sources:
            ds, created = DataSource.objects.get_or_create(
                tenant=tenant,
                name=src['name'],
                defaults={
                    'source_type': src['source_type'],
                    'description': src['description'],
                    'created_by': admin_user,
                },
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f"  Source: {src['name']} ({src['source_type']}) — {status}")

        self.stdout.write(self.style.SUCCESS('\nDone! Demo data seeded successfully!'))
