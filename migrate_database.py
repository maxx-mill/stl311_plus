"""
Database migration script to add new citizen submission fields to existing service_requests table.
This will be run inside the Docker container to safely add new columns.
"""

import psycopg2
from app import app
import os

def run_migration():
    """Add new columns to the existing service_requests table."""
    
    print("🔄 Running Database Migration for Citizen Submission Features...")
    
    # Database connection parameters
    db_params = {
        'host': 'postgres',  # Container name in Docker network
        'database': 'stl311_db',  # Database name from docker-compose.yml
        'user': 'postgres',
        'password': 'password',
        'port': 5432  # Internal port within Docker network
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # List of new columns to add
        new_columns = [
            # Source tracking
            ("source", "VARCHAR(20) DEFAULT 'api'"),
            
            # Citizen submission fields
            ("category", "VARCHAR(50)"),
            ("priority", "VARCHAR(20) DEFAULT 'normal'"),
            ("is_emergency", "BOOLEAN DEFAULT FALSE"),
            
            # Citizen contact information
            ("citizen_name", "VARCHAR(200)"),
            ("citizen_phone", "VARCHAR(20)"),
            ("citizen_email", "VARCHAR(200)"),
            ("contact_method_preference", "VARCHAR(20)"),
            
            # Staff workflow fields
            ("assigned_to", "VARCHAR(100)"),
            ("estimated_completion", "TIMESTAMP"),
            ("internal_notes", "TEXT"),
            ("citizen_updates", "TEXT"),
            
            # Validation and quality assurance
            ("is_validated", "BOOLEAN DEFAULT FALSE"),
            ("validation_notes", "TEXT"),
            ("duplicate_of", "INTEGER REFERENCES service_requests(id)"),
        ]
        
        # Check which columns already exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'service_requests' AND table_schema = 'public'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"   Found {len(existing_columns)} existing columns")
        
        # Add new columns that don't exist
        added_columns = 0
        for column_name, column_definition in new_columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE service_requests ADD COLUMN {column_name} {column_definition}"
                    cursor.execute(sql)
                    print(f"   ✅ Added column: {column_name}")
                    added_columns += 1
                except Exception as e:
                    print(f"   ⚠️ Error adding column {column_name}: {e}")
            else:
                print(f"   ⏭️ Column {column_name} already exists")
        
        # Create indexes for new columns
        indexes_to_create = [
            ("idx_service_requests_source", "source"),
            ("idx_service_requests_category", "category"),
            ("idx_service_requests_citizen_email", "citizen_email"),
        ]
        
        for index_name, column_name in indexes_to_create:
            if column_name in existing_columns or column_name in [col[0] for col in new_columns]:
                try:
                    # Check if index already exists
                    cursor.execute("""
                        SELECT indexname FROM pg_indexes 
                        WHERE tablename = 'service_requests' AND indexname = %s
                    """, (index_name,))
                    
                    if not cursor.fetchone():
                        cursor.execute(f"CREATE INDEX {index_name} ON service_requests({column_name})")
                        print(f"   ✅ Created index: {index_name}")
                    else:
                        print(f"   ⏭️ Index {index_name} already exists")
                except Exception as e:
                    print(f"   ⚠️ Error creating index {index_name}: {e}")
        
        # Commit changes
        conn.commit()
        print(f"\n🎉 Migration completed! Added {added_columns} new columns.")
        
        # Create new tables for related models
        print("\n📋 Creating related tables...")
        
        # Service Request Attachments table
        create_attachments_table = """
        CREATE TABLE IF NOT EXISTS service_request_attachments (
            id SERIAL PRIMARY KEY,
            service_request_id INTEGER NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            mime_type VARCHAR(100),
            uploaded_by VARCHAR(20) DEFAULT 'citizen',
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_public BOOLEAN DEFAULT TRUE,
            description VARCHAR(500)
        )
        """
        cursor.execute(create_attachments_table)
        print("   ✅ Created service_request_attachments table")
        
        # Service Request Updates table
        create_updates_table = """
        CREATE TABLE IF NOT EXISTS service_request_updates (
            id SERIAL PRIMARY KEY,
            service_request_id INTEGER NOT NULL REFERENCES service_requests(id) ON DELETE CASCADE,
            old_status VARCHAR(50),
            new_status VARCHAR(50) NOT NULL,
            update_message TEXT,
            internal_note TEXT,
            created_by VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_citizen_visible BOOLEAN DEFAULT TRUE
        )
        """
        cursor.execute(create_updates_table)
        print("   ✅ Created service_request_updates table")
        
        # Service Categories table
        create_categories_table = """
        CREATE TABLE IF NOT EXISTS service_categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            department VARCHAR(100),
            problem_codes TEXT,
            is_emergency_eligible BOOLEAN DEFAULT FALSE,
            estimated_response_time VARCHAR(100),
            instructions TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            sort_order INTEGER DEFAULT 0
        )
        """
        cursor.execute(create_categories_table)
        print("   ✅ Created service_categories table")
        
        # Insert default categories
        default_categories = [
            ('Street & Sidewalk Issues', 'Potholes, street repairs, sidewalk damage, street cleaning', 'Streets Division', False, '3-5 business days', 'Please provide the exact address and describe the issue clearly.'),
            ('Refuse & Recycling', 'Missed pickup, illegal dumping, dead animals, litter', 'Refuse Division', False, '1-3 business days', 'For missed pickups, please report within 24 hours of scheduled pickup.'),
            ('Traffic & Signs', 'Traffic signals, street signs, parking issues, traffic safety', 'Traffic Division', True, '1-2 business days', 'For urgent traffic safety issues, please call 911.'),
            ('Parks & Recreation', 'Park maintenance, playground issues, recreational facilities', 'Parks Division', False, '5-7 business days', 'Please specify which park and the exact location of the issue.'),
            ('Building & Property Issues', 'Code violations, vacant buildings, property maintenance', 'Building Division', False, '10-15 business days', 'Please provide the complete property address and detailed description.'),
            ('Trees & Forestry', 'Tree removal, trimming, fallen trees, tree planting requests', 'Forestry Division', True, '2-5 business days', 'For emergency tree issues blocking roads, please call 911.')
        ]
        
        # Check if categories already exist
        cursor.execute("SELECT COUNT(*) FROM service_categories")
        existing_category_count = cursor.fetchone()[0]
        
        if existing_category_count == 0:
            for i, (name, desc, dept, emergency, time, instructions) in enumerate(default_categories):
                cursor.execute("""
                    INSERT INTO service_categories (name, description, department, is_emergency_eligible, 
                                                  estimated_response_time, instructions, sort_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, desc, dept, emergency, time, instructions, i))
            print(f"   ✅ Inserted {len(default_categories)} default categories")
        else:
            print(f"   ⏭️ Found {existing_category_count} existing categories")
        
        # Final commit
        conn.commit()
        
        print("\n📊 Migration Summary:")
        print(f"- ✅ Enhanced service_requests table with {added_columns} new columns")
        print("- ✅ Created service_request_attachments table")
        print("- ✅ Created service_request_updates table") 
        print("- ✅ Created service_categories table")
        print("- ✅ Added default service categories")
        print("- ✅ Created necessary indexes")
        
        print("\n🎉 Database is now ready for citizen submissions!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    run_migration()
