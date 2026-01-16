"""
Management command to verify industry data separation is properly implemented.
This command checks all ViewSets and models to ensure industry filtering is in place.
"""
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models
from django.contrib.auth import get_user_model
import inspect

User = get_user_model()


class Command(BaseCommand):
    help = 'Verify that industry data separation is properly implemented across all ViewSets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information about each ViewSet',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('INDUSTRY DATA SEPARATION VERIFICATION'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Check models with industry field
        self.check_models_with_industry()
        
        # Check ViewSets
        self.check_viewsets()
        
        # Check database data
        self.check_database_data()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('VERIFICATION COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

    def check_models_with_industry(self):
        """Check which models have industry field"""
        self.stdout.write(self.style.WARNING('\n📋 MODELS WITH INDUSTRY FIELD:'))
        self.stdout.write('-' * 80)
        
        models_with_industry = []
        models_without_industry = []
        
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if hasattr(model, 'industry'):
                    models_with_industry.append(f"{app_config.name}.{model.__name__}")
                elif model.__name__ in ['User', 'Industry']:
                    # User and Industry are special cases
                    continue
                else:
                    # Check if it should have industry field
                    if model.__name__ in ['Task', 'Booking', 'InventoryItem', 'Equipment', 'Vendor']:
                        models_without_industry.append(f"{app_config.name}.{model.__name__}")
        
        for model_name in models_with_industry:
            self.stdout.write(self.style.SUCCESS(f"  ✅ {model_name}"))
        
        if models_without_industry:
            self.stdout.write(self.style.ERROR('\n⚠️  Models that might need industry field:'))
            for model_name in models_without_industry:
                self.stdout.write(self.style.WARNING(f"  ⚠️  {model_name}"))

    def check_viewsets(self):
        """Check which ViewSets use filter_by_industry"""
        self.stdout.write(self.style.WARNING('\n🔍 VIEWSETS INDUSTRY FILTERING STATUS:'))
        self.stdout.write('-' * 80)
        
        viewsets_status = {
            'users.views.UserViewSet': self.check_viewset_file('users/views.py', 'UserViewSet'),
            'farms.views.FarmViewSet': self.check_viewset_file('farms/views.py', 'FarmViewSet'),
            'farms.views.PlotViewSet': self.check_viewset_file('farms/views.py', 'PlotViewSet'),
            'tasks.views.TaskViewSet': self.check_viewset_file('tasks/views.py', 'TaskViewSet'),
            'bookings.views.BookingViewSet': self.check_viewset_file('bookings/views.py', 'BookingViewSet'),
            'inventory.views.InventoryItemViewSet': self.check_viewset_file('inventory/views.py', 'InventoryItemViewSet'),
            'equipment.views.EquipmentViewSet': self.check_viewset_file('equipment/views.py', 'EquipmentViewSet'),
            'vendors.views.VendorViewSet': self.check_viewset_file('vendors/views.py', 'VendorViewSet'),
        }
        
        implemented = []
        missing = []
        
        for viewset_name, status in viewsets_status.items():
            if status['has_filter']:
                implemented.append((viewset_name, status))
                self.stdout.write(self.style.SUCCESS(f"  ✅ {viewset_name}"))
                if status['line_number']:
                    self.stdout.write(f"      → Uses filter_by_industry at line {status['line_number']}")
            else:
                missing.append((viewset_name, status))
                self.stdout.write(self.style.ERROR(f"  ❌ {viewset_name}"))
                self.stdout.write(self.style.WARNING(f"      → Missing industry filtering in get_queryset()"))
        
        self.stdout.write(f"\n📊 Summary: {len(implemented)} implemented, {len(missing)} missing")
        
        if missing:
            self.stdout.write(self.style.ERROR('\n⚠️  ViewSets that need industry filtering:'))
            for viewset_name, _ in missing:
                self.stdout.write(self.style.WARNING(f"  - {viewset_name}"))

    def check_viewset_file(self, file_path, class_name):
        """Check if a ViewSet file uses filter_by_industry"""
        import os
        import re
        from pathlib import Path
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        full_path = base_dir / file_path
        
        if not full_path.exists():
            return {'has_filter': False, 'line_number': None, 'has_import': False}
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        has_import = 'filter_by_industry' in content or 'get_user_industry' in content or 'get_accessible_users' in content
        
        # More robust detection: look for filter_by_industry anywhere in the class
        # or get_accessible_users (which is used for UserViewSet)
        has_filter = False
        line_number = None
        
        # Check if class exists
        class_pattern = rf'class\s+{class_name}'
        class_found = False
        class_start_line = None
        
        for i, line in enumerate(lines, 1):
            if re.search(class_pattern, line):
                class_found = True
                class_start_line = i
                break
        
        if not class_found:
            return {
                'has_filter': False,
                'line_number': None,
                'has_import': has_import
            }
        
        # Look for filter_by_industry or get_accessible_users in the class
        in_class = False
        brace_count = 0
        
        for i, line in enumerate(lines[class_start_line-1:], class_start_line):
            # Simple check: if we see another class definition at same indentation, we're out
            if in_class and line.strip().startswith('class ') and not class_name in line:
                break
            
            if f'class {class_name}' in line or f'class {class_name}(' in line:
                in_class = True
            
            if in_class:
                # Check for filter_by_industry or get_accessible_users
                if 'filter_by_industry' in line or 'get_accessible_users' in line:
                    has_filter = True
                    line_number = i
                    break
                
                # If we hit another class definition, stop
                if line.strip().startswith('class ') and class_name not in line:
                    break
        
        return {
            'has_filter': has_filter,
            'line_number': line_number,
            'has_import': has_import
        }

    def check_database_data(self):
        """Check database for industry data distribution"""
        self.stdout.write(self.style.WARNING('\n💾 DATABASE DATA CHECK:'))
        self.stdout.write('-' * 80)
        
        try:
            from users.models import Industry
            
            industries = Industry.objects.all()
            self.stdout.write(f"\n📊 Total Industries: {industries.count()}")
            
            for industry in industries:
                self.stdout.write(f"\n  🏢 {industry.name} (ID: {industry.id}):")
                
                # Count users
                users_count = User.objects.filter(industry=industry).count()
                self.stdout.write(f"     Users: {users_count}")
                
                # Count farms
                try:
                    from farms.models import Farm
                    farms_count = Farm.objects.filter(industry=industry).count()
                    self.stdout.write(f"     Farms: {farms_count}")
                except:
                    pass
                
                # Count plots
                try:
                    from farms.models import Plot
                    plots_count = Plot.objects.filter(industry=industry).count()
                    self.stdout.write(f"     Plots: {plots_count}")
                except:
                    pass
                
                # Count tasks
                try:
                    from tasks.models import Task
                    tasks_count = Task.objects.filter(industry=industry).count()
                    self.stdout.write(f"     Tasks: {tasks_count}")
                except:
                    pass
                
                # Count bookings
                try:
                    from bookings.models import Booking
                    bookings_count = Booking.objects.filter(industry=industry).count()
                    self.stdout.write(f"     Bookings: {bookings_count}")
                except:
                    pass
                
                # Count inventory items
                try:
                    from inventory.models import InventoryItem
                    inventory_count = InventoryItem.objects.filter(industry=industry).count()
                    self.stdout.write(f"     Inventory Items: {inventory_count}")
                except:
                    pass
            
            # Check for data without industry
            self.stdout.write(self.style.WARNING('\n⚠️  Data without industry assignment:'))
            
            try:
                from farms.models import Farm
                farms_no_industry = Farm.objects.filter(industry__isnull=True).count()
                if farms_no_industry > 0:
                    self.stdout.write(self.style.ERROR(f"  ❌ Farms without industry: {farms_no_industry}"))
            except:
                pass
            
            try:
                from farms.models import Plot
                plots_no_industry = Plot.objects.filter(industry__isnull=True).count()
                if plots_no_industry > 0:
                    self.stdout.write(self.style.ERROR(f"  ❌ Plots without industry: {plots_no_industry}"))
            except:
                pass
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking database: {e}"))

