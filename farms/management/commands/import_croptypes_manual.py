"""
Management command to manually import CropType data.
Use this if you have the data in a specific format or want to import specific records.
"""

from django.core.management.base import BaseCommand
from farms.models import CropType
from users.models import Industry


class Command(BaseCommand):
    help = 'Manually import CropType data from a predefined list'

    def add_arguments(self, parser):
        parser.add_argument(
            '--industry-id',
            type=int,
            help='ID of the industry to assign imported crop types to'
        )
        parser.add_argument(
            '--industry-name',
            type=str,
            help='Name of the industry to assign imported crop types to'
        )

    def handle(self, *args, **options):
        industry_id = options.get('industry_id')
        industry_name = options.get('industry_name')

        # Get or create industry
        industry = self.get_industry(industry_id, industry_name)
        if not industry:
            self.stdout.write(self.style.ERROR('Failed to get or create industry'))
            return

        self.stdout.write(f'Using industry: {industry.name} (ID: {industry.id})')

        # Predefined CropType data based on your earlier example
        crop_type_data = [
            {"crop_type": "sugarcane", "plantation_type": "adsali", "planting_method": "3_bud"},
            {"crop_type": "sugarcane", "plantation_type": "suru", "planting_method": "2_bud"},
            {"crop_type": "sugarcane", "plantation_type": "ratoon", "planting_method": "1_bud"},
            {"crop_type": "sugarcane", "plantation_type": "pre-seasonal", "planting_method": "1_bud_stip_Method"},
            {"crop_type": "sugarcane", "plantation_type": "post-seasonal", "planting_method": "3_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "adsali", "planting_method": "2_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "suru", "planting_method": "2_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "suru", "planting_method": "3_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "adsali", "planting_method": "3_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "ratoon", "planting_method": "3_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "adsali", "planting_method": "other"},
            {"crop_type": "sugarcane", "plantation_type": "pre_seasonal", "planting_method": "other"},
            {"crop_type": "Sugarcane", "plantation_type": "suru", "planting_method": "1_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "suru", "planting_method": "other"},
            {"crop_type": "Sugarcane", "plantation_type": "pre-seasonal", "planting_method": "2_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "ratoon", "planting_method": "2_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "pre-seasonal", "planting_method": "3_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "pre-seasonal", "planting_method": "other"},
            {"crop_type": "Sugarcane", "plantation_type": "adsali", "planting_method": "1_bud"},
            {"crop_type": "Sugarcane", "plantation_type": "ratoon", "planting_method": "1_bud"},
        ]

        self.stdout.write(f'Found {len(crop_type_data)} CropType records to import')

        # Import the data
        imported_count = 0
        skipped_count = 0
        error_count = 0

        for data in crop_type_data:
            try:
                # Check for duplicates
                existing = CropType.objects.filter(
                    crop_type=data.get('crop_type', ''),
                    plantation_type=data.get('plantation_type', ''),
                    planting_method=data.get('planting_method', ''),
                    industry=industry
                ).first()
                
                if existing:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipped duplicate: {data.get("crop_type")} - '
                            f'{data.get("plantation_type")} - {data.get("planting_method")}'
                        )
                    )
                    continue

                # Create CropType
                crop_type = CropType.objects.create(
                    crop_type=data.get('crop_type', ''),
                    plantation_type=data.get('plantation_type', ''),
                    planting_method=data.get('planting_method', ''),
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

