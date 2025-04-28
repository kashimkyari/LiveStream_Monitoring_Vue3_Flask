#!/usr/bin/env python3
"""
postgres_drop_tables.py - Script to drop all tables from a PostgreSQL database

This script uses PostgreSQL-specific methods to safely drop all tables by:
1. Identifying all schemas and tables
2. Dropping tables using CASCADE option
3. Resetting sequences and other database objects
"""

import logging
import os
from dotenv import load_dotenv
from sqlalchemy import text
from flask import Flask
from extensions import db
from config import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('pg_drop.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def drop_all_postgres_tables():
    """Drop all tables from a PostgreSQL database using PostgreSQL specific methods."""
    load_dotenv()
    app = create_app()
    
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # Disable triggers to avoid issues during deletion
            logger.info("Disabling triggers")
            conn.execute(text("SET session_replication_role = 'replica';"))
            
            # Get the schema we're using (usually 'public')
            schema_query = text("""
                SELECT current_schema();
            """)
            schema = conn.execute(schema_query).scalar() or 'public'
            logger.info(f"Working with schema: {schema}")
            
            # Get all tables in the schema
            tables_query = text(f"""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = '{schema}'
                ORDER BY tablename;
            """)
            
            tables = [row[0] for row in conn.execute(tables_query).fetchall()]
            logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
            
            if not tables:
                logger.info("No tables found in database. Nothing to drop.")
                return
            
            # Drop all foreign key constraints first
            logger.info("Dropping all foreign key constraints...")
            drop_fk_query = text(f"""
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT conname, conrelid::regclass AS table_name FROM pg_constraint
                             WHERE contype = 'f' AND connamespace = '{schema}'::regnamespace)
                    LOOP
                        EXECUTE 'ALTER TABLE ' || r.table_name || ' DROP CONSTRAINT ' || r.conname;
                    END LOOP;
                END $$;
            """)
            conn.execute(drop_fk_query)
            logger.info("Foreign key constraints dropped")
            
            # Drop all tables (will now work since FKs are gone)
            for table in tables:
                logger.info(f"Dropping table: {table}")
                try:
                    drop_query = text(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    conn.execute(drop_query)
                    logger.info(f"Successfully dropped table: {table}")
                except Exception as e:
                    logger.error(f"Error dropping {table}: {e}")
            
            # Reset all sequences
            logger.info("Resetting sequences...")
            sequences_query = text(f"""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = '{schema}';
            """)
            
            sequences = [row[0] for row in conn.execute(sequences_query).fetchall()]
            for sequence in sequences:
                try:
                    drop_query = text(f'DROP SEQUENCE IF EXISTS "{sequence}" CASCADE;')
                    conn.execute(drop_query)
                    logger.info(f"Dropped sequence: {sequence}")
                except Exception as e:
                    logger.error(f"Error dropping sequence {sequence}: {e}")
            
            # Drop views if any remain
            logger.info("Dropping any remaining views...")
            views_query = text(f"""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = '{schema}';
            """)
            
            views = [row[0] for row in conn.execute(views_query).fetchall()]
            for view in views:
                if view.startswith('pg_') or view.startswith('information_schema'):
                    continue  # Skip system views
                try:
                    drop_query = text(f'DROP VIEW IF EXISTS "{view}" CASCADE;')
                    conn.execute(drop_query)
                    logger.info(f"Dropped view: {view}")
                except Exception as e:
                    logger.error(f"Error dropping view {view}: {e}")
            
            # Commit the transaction
            conn.commit()
            
            # Re-enable triggers
            conn.execute(text("SET session_replication_role = 'origin';"))
            
            # Final check
            tables_after = [row[0] for row in conn.execute(tables_query).fetchall()]
            if not tables_after:
                logger.info("Success! All tables have been dropped from the database.")
            else:
                logger.warning(f"Some tables could not be dropped: {', '.join(tables_after)}")
            
        except Exception as e:
            logger.error(f"Unexpected error dropping tables: {e}")
            # No need to rollback manually with connection
        finally:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting PostgreSQL table deletion process")
    drop_all_postgres_tables()
    logger.info("PostgreSQL table deletion process completed")