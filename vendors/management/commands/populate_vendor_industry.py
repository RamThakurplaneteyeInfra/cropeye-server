"""
Management command to populate industry for existing vendors and orders.
This assigns industry based on the created_by user's industry.
"""
from django.core.management.base import BaseCommand
from vendors.models import Vendor, Order
from inventory.models import Stock


class Command(BaseCommand):
    help = 'Populate industry field for existing Vendors, Orders, and Stock items based on created_by user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Populate Vendor industry
        vendors_updated = 0
        vendors_without_industry = Vendor.objects.filter(industry__isnull=True)
        
        for vendor in vendors_without_industry:
            if vendor.created_by and vendor.created_by.industry:
                if not dry_run:
                    vendor.industry = vendor.created_by.industry
                    vendor.save()
                vendors_updated += 1
                self.stdout.write(
                    f"{'Would update' if dry_run else 'Updated'} Vendor '{vendor.vendor_name}' "
                    f"with industry '{vendor.created_by.industry.name}'"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Vendor '{vendor.vendor_name}' (ID: {vendor.id}) has no created_by user "
                        f"or user has no industry - skipping"
                    )
                )
        
        # Populate Order industry
        orders_updated = 0
        orders_without_industry = Order.objects.filter(industry__isnull=True)
        
        for order in orders_without_industry:
            if order.created_by and order.created_by.industry:
                if not dry_run:
                    order.industry = order.created_by.industry
                    order.save()
                orders_updated += 1
                self.stdout.write(
                    f"{'Would update' if dry_run else 'Updated'} Order '{order.invoice_number}' "
                    f"with industry '{order.created_by.industry.name}'"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Order '{order.invoice_number}' (ID: {order.id}) has no created_by user "
                        f"or user has no industry - skipping"
                    )
                )
        
        # Populate Stock industry
        stocks_updated = 0
        stocks_without_industry = Stock.objects.filter(industry__isnull=True)
        
        for stock in stocks_without_industry:
            if stock.created_by and stock.created_by.industry:
                if not dry_run:
                    stock.industry = stock.created_by.industry
                    stock.save()
                stocks_updated += 1
                self.stdout.write(
                    f"{'Would update' if dry_run else 'Updated'} Stock '{stock.item_name}' "
                    f"with industry '{stock.created_by.industry.name}'"
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Stock '{stock.item_name}' (ID: {stock.id}) has no created_by user "
                        f"or user has no industry - skipping"
                    )
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f"Vendors {'would be updated' if dry_run else 'updated'}: {vendors_updated}")
        self.stdout.write(f"Orders {'would be updated' if dry_run else 'updated'}: {orders_updated}")
        self.stdout.write(f"Stock items {'would be updated' if dry_run else 'updated'}: {stocks_updated}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nRun without --dry-run to apply changes'))

