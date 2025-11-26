-- SQL Script to Apply Bookings Migrations
-- Run this directly on your PostgreSQL database
-- This bypasses Django's migration system

-- Migration 0002: Add industry field to bookings table
-- Check if column already exists before adding
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bookings_booking' 
        AND column_name = 'industry_id'
    ) THEN
        ALTER TABLE bookings_booking 
        ADD COLUMN industry_id INTEGER NULL;
        
        ALTER TABLE bookings_booking 
        ADD CONSTRAINT bookings_booking_industry_id_fkey 
        FOREIGN KEY (industry_id) 
        REFERENCES users_industry(id) 
        ON DELETE CASCADE;
        
        COMMENT ON COLUMN bookings_booking.industry_id IS 'Industry this booking belongs to';
    END IF;
END $$;

-- Migration 0003: Assign industry to existing bookings (if needed)
-- This migration assigns bookings to industries based on created_by user's industry
-- Update this query based on your business logic
UPDATE bookings_booking 
SET industry_id = (
    SELECT industry_id 
    FROM users_user 
    WHERE users_user.id = bookings_booking.created_by_id
)
WHERE industry_id IS NULL 
AND created_by_id IS NOT NULL;

-- Migration 0004: Rename indexes (if they exist)
-- Check and rename old indexes to new names
DO $$
BEGIN
    -- Rename index if it exists
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'bookings_boo_status_8b5b0a_idx'
    ) THEN
        ALTER INDEX bookings_boo_status_8b5b0a_idx 
        RENAME TO bookings_bo_status_233e96_idx;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'bookings_boo_bookin_0b4b5a_idx'
    ) THEN
        ALTER INDEX bookings_boo_bookin_0b4b5a_idx 
        RENAME TO bookings_bo_booking_3ec655_idx;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'bookings_boo_start_d_0b4b5a_idx'
    ) THEN
        ALTER INDEX bookings_boo_start_d_0b4b5a_idx 
        RENAME TO bookings_bo_start_d_3e8155_idx;
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'bookings_boo_end_dat_0b4b5a_idx'
    ) THEN
        ALTER INDEX bookings_boo_end_dat_0b4b5a_idx 
        RENAME TO bookings_bo_end_dat_f79cb7_idx;
    END IF;
END $$;

-- Verify migrations applied
SELECT 
    'Migrations Applied Successfully!' as status,
    EXISTS(
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bookings_booking' 
        AND column_name = 'industry_id'
    ) as industry_column_exists;

