"""
Comprehensive phone number fix:
1. Clean all phone numbers (remove +91, ensure 10 digits)
2. Find and fix duplicates
3. Generate unique 10-digit numbers for duplicates
"""
import psycopg2
import re
import random

DB_CONFIG = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'host': 'dev-et.cropeye.ai',
    'port': '5432'
}

def clean_phone_number(phone):
    """Clean phone number: remove +91 prefix, keep only digits, ensure 10 digits"""
    if not phone:
        return None
    
    phone_str = str(phone).strip()
    
    # Remove +91 prefix if present
    if phone_str.startswith('+91'):
        phone_str = phone_str[3:].strip()
    elif phone_str.startswith('91') and len(phone_str.replace(' ', '').replace('-', '')) > 10:
        phone_str = phone_str[2:]
    
    # Remove all non-digit characters
    phone_str = re.sub(r'\D', '', phone_str)
    
    # Take last 10 digits if longer
    if len(phone_str) > 10:
        phone_str = phone_str[-10:]
    elif len(phone_str) < 10:
        # Invalid length
        return None
    
    return phone_str

def generate_unique_10_digit_phone(cursor, existing_numbers):
    """Generate a unique 10-digit phone number (no +91, exactly 10 digits)"""
    max_attempts = 10000
    for _ in range(max_attempts):
        # Generate 10-digit number starting with 6-9 (Indian mobile prefix)
        first_digit = random.choice(['6', '7', '8', '9'])
        remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        new_number = first_digit + remaining_digits
        
        # Check if it exists
        if new_number not in existing_numbers:
            cursor.execute("""
                SELECT COUNT(*) FROM users_user 
                WHERE phone_number = %s;
            """, (new_number,))
            if cursor.fetchone()[0] == 0:
                return new_number
    
    # Fallback: timestamp-based
    import time
    timestamp = str(int(time.time() * 1000))[-9:]  # Use milliseconds for more uniqueness
    return '9' + timestamp

def fix_all_phone_numbers():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cursor = conn.cursor()
    
    print("=" * 70)
    print("Comprehensive Phone Number Fix")
    print("=" * 70)
    print("1. Cleaning all phone numbers (remove +91, ensure 10 digits)")
    print("2. Finding and fixing duplicates")
    print("3. Generating unique numbers where needed")
    print("=" * 70)
    
    try:
        # Step 1: Get all users with phone numbers
        cursor.execute("""
            SELECT id, username, email, first_name, last_name, phone_number
            FROM users_user
            WHERE phone_number IS NOT NULL AND phone_number != '';
        """)
        all_users = cursor.fetchall()
        
        print(f"\nTotal users with phone numbers: {len(all_users)}")
        
        # Step 2: Clean all phone numbers
        print("\nStep 1: Cleaning phone numbers...")
        cleaned_count = 0
        invalid_count = 0
        normalized_phones = {}  # normalized_phone -> list of (user_id, original_phone)
        
        for user_id, username, email, first_name, last_name, phone in all_users:
            original_phone = str(phone).strip()
            cleaned = clean_phone_number(phone)
            
            if not cleaned:
                invalid_count += 1
                print(f"  Invalid phone: User {user_id} ({username or email}) - {original_phone}")
                # Will generate new one later
                continue
            
            # Track normalized phones for duplicate detection
            if cleaned not in normalized_phones:
                normalized_phones[cleaned] = []
            normalized_phones[cleaned].append((user_id, username, email, first_name, last_name, original_phone, cleaned))
            
            # Update if cleaned is different from original
            if cleaned != original_phone:
                cursor.execute("""
                    UPDATE users_user SET phone_number = %s WHERE id = %s;
                """, (cleaned, user_id))
                cleaned_count += 1
        
        print(f"  OK: Cleaned {cleaned_count} phone numbers")
        if invalid_count > 0:
            print(f"  WARNING: {invalid_count} invalid phone numbers found (will be regenerated)")
        
        # Step 3: Find duplicates
        print("\nStep 2: Finding duplicates...")
        duplicates = {phone: users for phone, users in normalized_phones.items() if len(users) > 1}
        
        if not duplicates:
            print("  OK: No duplicates found!")
        else:
            print(f"  Found {len(duplicates)} duplicate phone numbers:")
            total_affected = 0
            for phone, users in list(duplicates.items())[:5]:
                print(f"    {phone}: {len(users)} users")
                total_affected += len(users) - 1
            if len(duplicates) > 5:
                print(f"    ... and {len(duplicates) - 5} more")
            print(f"  Total users needing new numbers: {total_affected}")
        
        # Step 4: Get all existing phone numbers
        cursor.execute("""
            SELECT phone_number FROM users_user 
            WHERE phone_number IS NOT NULL AND phone_number != '';
        """)
        existing_numbers = {row[0] for row in cursor.fetchall()}
        
        # Step 5: Fix duplicates and invalid numbers
        print("\nStep 3: Fixing duplicates and invalid numbers...")
        updates_made = 0
        
        # Fix duplicates
        for phone, users in duplicates.items():
            # Keep first user (by ID), update the rest
            sorted_users = sorted(users, key=lambda x: x[0])  # Sort by user_id
            for idx, (user_id, username, email, first_name, last_name, original_phone, cleaned_phone) in enumerate(sorted_users):
                if idx == 0:
                    # Keep original
                    user_display = username or email or f'{first_name} {last_name}'.strip() or f'ID {user_id}'
                    print(f"  Keeping: User {user_id} ({user_display}) - {cleaned_phone}")
                    continue
                
                # Generate new unique number
                new_phone = generate_unique_10_digit_phone(cursor, existing_numbers)
                existing_numbers.add(new_phone)
                
                cursor.execute("""
                    UPDATE users_user SET phone_number = %s WHERE id = %s;
                """, (new_phone, user_id))
                
                user_display = username or email or f'{first_name} {last_name}'.strip() or f'ID {user_id}'
                print(f"  Updated: User {user_id} ({user_display}) - {original_phone} -> {new_phone}")
                updates_made += 1
        
        # Fix invalid numbers
        for user_id, username, email, first_name, last_name, phone in all_users:
            cleaned = clean_phone_number(phone)
            if not cleaned:
                # Generate new number
                new_phone = generate_unique_10_digit_phone(cursor, existing_numbers)
                existing_numbers.add(new_phone)
                
                cursor.execute("""
                    UPDATE users_user SET phone_number = %s WHERE id = %s;
                """, (new_phone, user_id))
                
                user_display = username or email or f'{first_name} {last_name}'.strip() or f'ID {user_id}'
                print(f"  Generated: User {user_id} ({user_display}) - {phone} -> {new_phone}")
                updates_made += 1
        
        # Commit
        conn.commit()
        
        # Verify
        print("\n" + "=" * 70)
        print("Verification")
        print("=" * 70)
        
        cursor.execute("""
            SELECT phone_number, COUNT(*) 
            FROM users_user 
            WHERE phone_number IS NOT NULL AND phone_number != ''
            GROUP BY phone_number 
            HAVING COUNT(*) > 1;
        """)
        remaining_duplicates = cursor.fetchall()
        
        if remaining_duplicates:
            print(f"WARNING: {len(remaining_duplicates)} duplicates still exist!")
        else:
            print("OK: All phone numbers are unique!")
        
        # Check for +91 prefix
        cursor.execute("""
            SELECT COUNT(*) FROM users_user 
            WHERE phone_number LIKE '+91%';
        """)
        plus91_count = cursor.fetchone()[0]
        if plus91_count > 0:
            print(f"WARNING: {plus91_count} phone numbers still have +91 prefix!")
        else:
            print("OK: No phone numbers have +91 prefix!")
        
        # Check format
        cursor.execute("""
            SELECT COUNT(*) FROM users_user 
            WHERE phone_number IS NOT NULL 
            AND phone_number != ''
            AND LENGTH(phone_number) != 10;
        """)
        invalid_length = cursor.fetchone()[0]
        if invalid_length > 0:
            print(f"WARNING: {invalid_length} phone numbers are not 10 digits!")
        else:
            print("OK: All phone numbers are exactly 10 digits!")
        
        print(f"\nTotal updates made: {updates_made}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        cursor.close()
        conn.close()
        return False

if __name__ == '__main__':
    import sys
    if '--yes' not in sys.argv and '-y' not in sys.argv:
        print("\nThis will:")
        print("1. Clean all phone numbers (remove +91, ensure 10 digits)")
        print("2. Fix any duplicates")
        print("3. Generate unique 10-digit numbers where needed")
        try:
            response = input("\nProceed? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled.")
                sys.exit(0)
        except EOFError:
            pass
    
    success = fix_all_phone_numbers()
    if success:
        print("\nOK: Phone number fix completed successfully!")
    else:
        print("\nERROR: Phone number fix failed!")
        sys.exit(1)

