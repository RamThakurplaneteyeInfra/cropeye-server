"""
Management command to import CropType data from the previous project.
This command can:
1. Connect to the previous project's database directly (if accessible)
2. Read from a JSON export file
3. Import all CropType records and assign them to an industry
"""

import os
import json
import sys
from django.core.management.base import BaseCommand
from django.db import connections
from farms.models import CropType
from users.models import Industry


class Command(BaseCommand):
    help = 'Import CropType data from the previous cropeye-server project'

    def add_arguments(self, parser):
        parser.add_argument(
            '--previous-project-path',
            type=str,
            default=r'C:\Users\Ram.Thakur\Farme.AI\cropeye-server\cropeye-server',
            help='Path to the previous project directory'
        )
        parser.add_argument(
            '--industry-id',
            type=int,
            help='ID of the industry to assign imported crop types to (default: first industry)'
        )
        parser.add_argument(
            '--industry-name',
            type=str,
            help='Name of the industry to assign imported crop types to'
        )
        parser.add_argument(
            '--json-file',
            type=str,
            help='Path to JSON file containing CropType data (alternative to database connection)'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            help='Skip crop types that already exist (based on crop_type, plantation_type, planting_method)'
        )

    def handle(self, *args, **options):
        previous_project_path = options['previous_project_path']
        industry_id = options.get('industry_id')
        industry_name = options.get('industry_name')
        json_file = options.get('json_file')
        skip_duplicates = options.get('skip_duplicates', False)

        # Get or create industry
        industry = self.get_industry(industry_id, industry_name)
        if not industry:
            self.stdout.write(self.style.ERROR('Failed to get or create industry'))
            return

        self.stdout.write(f'Using industry: {industry.name} (ID: {industry.id})')

        # Get CropType data
        crop_type_data = []
        
        if json_file:
            crop_type_data = self.load_from_json(json_file)
        else:
            # Try to load from previous project's database
            crop_type_data = self.load_from_previous_project(previous_project_path)

        if not crop_type_data:
            self.stdout.write(self.style.WARNING('No CropType data found to import'))
            return

        self.stdout.write(f'Found {len(crop_type_data)} CropType records to import')

        # Import the data
        imported_count = 0
        skipped_count = 0
        error_count = 0

        for data in crop_type_data:
            try:
                # Handle Django dumpdata format: {"model": "farms.croptype", "pk": 1, "fields": {...}}
                if isinstance(data, dict) and 'fields' in data:
                    # Django dumpdata format
                    fields = data.get('fields', {})
                    crop_type_name = fields.get('crop_type', '')
                    plantation_type = fields.get('plantation_type', '')
                    planting_method = fields.get('planting_method', '')
                else:
                    # Simple format: {"crop_type": "...", "plantation_type": "...", "planting_method": "..."}
                    crop_type_name = data.get('crop_type', '')
                    plantation_type = data.get('plantation_type', '')
                    planting_method = data.get('planting_method', '')
                
                # Check for duplicates if skip_duplicates is True
                if skip_duplicates:
                    existing = CropType.objects.filter(
                        crop_type=crop_type_name,
                        plantation_type=plantation_type,
                        planting_method=planting_method,
                        industry=industry
                    ).first()
                    
                    if existing:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipped duplicate: {crop_type_name} - '
                                f'{plantation_type} - {planting_method}'
                            )
                        )
                        continue

                # Create CropType
                crop_type = CropType.objects.create(
                    crop_type=crop_type_name,
                    plantation_type=plantation_type,
                    planting_method=planting_method,
                    industry=industry
                )
                imported_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Imported: {crop_type.crop_type} - '
                        f'{crop_type.get_plantation_type_display() or "N/A"} - '
                        f'{crop_type.get_planting_method_display() or "N/A"}'
                    )
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error importing {data}: {str(e)}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Import Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Imported: {imported_count}'))
        self.stdout.write(self.style.WARNING(f'  Skipped: {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'  Errors: {error_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

    def get_industry(self, industry_id=None, industry_name=None):
        """Get or create industry"""
        if industry_id:
            try:
                return Industry.objects.get(id=industry_id)
            except Industry.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Industry with ID {industry_id} does not exist'))
                return None

        if industry_name:
            industry, created = Industry.objects.get_or_create(
                name=industry_name,
                defaults={'description': f'Industry for imported crop types: {industry_name}'}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created new industry: {industry.name}'))
            return industry

        # Default: get first industry or create one
        industry = Industry.objects.first()
        if not industry:
            industry = Industry.objects.create(
                name='Default Industry',
                description='Default industry for imported crop types'
            )
            self.stdout.write(self.style.SUCCESS(f'Created default industry: {industry.name}'))
        else:
            self.stdout.write(f'Using existing industry: {industry.name}')

        return industry

    def load_from_json(self, json_file_path):
        """Load CropType data from JSON file"""
        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_file_path}'))
            return []

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle Django dumpdata format: list of objects with "model" and "fields"
                if isinstance(data, list):
                    # Filter for CropType models only
                    crop_types = [
                        item for item in data 
                        if isinstance(item, dict) and 
                        item.get('model', '').lower() in ['farms.croptype', 'farms.croptypes']
                    ]
                    if crop_types:
                        self.stdout.write(f'Found {len(crop_types)} CropType records in JSON file')
                        return crop_types
                    elif len(data) == 0:
                        self.stdout.write(self.style.WARNING('JSON file is empty - no data to import'))
                        return []
                    else:
                        # Assume all items are crop types if no model field
                        self.stdout.write(f'Found {len(data)} records in JSON file (assuming CropType format)')
                        return data
                elif isinstance(data, dict) and 'croptypes' in data:
                    return data['croptypes']
                else:
                    self.stdout.write(self.style.ERROR('Invalid JSON format'))
                    return []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading JSON file: {str(e)}'))
            return []

    def load_from_previous_project(self, previous_project_path):
        """Load CropType data from previous project's database"""
        # Try to read from previous project's database
        # First, try to use Django's database connection to the previous project
        
        # Method 1: Try to use Django settings from previous project
        try:
            # Add previous project to Python path
            if previous_project_path not in sys.path:
                sys.path.insert(0, previous_project_path)

            # Try to import settings from previous project
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
            
            # This is complex - instead, let's try to connect directly to the database
            # We'll use raw SQL to query the previous project's database
            
            # For now, let's create a simple script that exports data first
            # Or we can try to read from a SQL dump or use direct database connection
            
            self.stdout.write(
                self.style.WARNING(
                    'Direct database connection not implemented. '
                    'Please use --json-file option or export data manually.'
                )
            )
            
            # Alternative: Try to read from a common database if both projects use the same DB
            # This would require knowing the database settings
            
            return []
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error connecting to previous project: {str(e)}')
            )
            return []

    def export_from_previous_project(self, previous_project_path, output_file):
        """
        Helper method to export CropType data from previous project to JSON.
        This can be run separately in the previous project.
        """
        self.stdout.write(
            self.style.WARNING(
                'To export data from previous project, run this in the previous project:\n'
                'python manage.py dumpdata farms.CropType --indent 2 > croptypes_export.json'
            )
        )

