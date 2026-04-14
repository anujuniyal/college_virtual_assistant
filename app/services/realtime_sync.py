"""
Real-time Database Synchronization Service
Handles real-time data synchronization between local and production databases
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from sqlalchemy import text
from app.extensions import db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RealtimeSyncService:
    """Service for real-time database synchronization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.local_db_url = os.environ.get('NEON_DATABASE_URL') or os.environ.get('DATABASE_URL')
        self.production_db_url = os.environ.get('DATABASE_URL')
        self.sync_interval = int(os.environ.get('SYNC_INTERVAL_MINUTES', 5))  # Default 5 minutes
        self.last_sync_time = None
        self.sync_enabled = os.environ.get('REALTIME_SYNC_ENABLED', 'true').lower() == 'true'
        
        # Tables to sync (exclude sensitive data)
        self.sync_tables = [
            'notifications',
            'results',
            'fee_records',
            'complaints',
            'student_registrations',
            'predefined_info',
            'faq_records',
            'chatbot_qa'
        ]
        
        # Tables that should not be synced (sensitive data)
        self.exclude_tables = [
            'admins',
            'faculty',
            'otp_verifications',
            'telegram_user_mappings'
        ]
    
    def is_sync_enabled(self) -> bool:
        """Check if real-time sync is enabled"""
        return self.sync_enabled and self.production_db_url is not None
    
    def get_table_changes(self, table_name: str, since: datetime) -> List[Dict]:
        """Get changes from a table since last sync"""
        try:
            query = text(f"""
                SELECT * FROM {table_name} 
                WHERE updated_at > :since_time OR created_at > :since_time
                ORDER BY updated_at DESC, created_at DESC
            """)
            
            result = db.session.execute(query, {
                'since_time': since
            })
            
            # Convert to list of dictionaries
            columns = result.keys()
            changes = []
            for row in result:
                changes.append(dict(zip(columns, row)))
            
            return changes
            
        except Exception as e:
            self.logger.error(f"Error getting changes from {table_name}: {str(e)}")
            return []
    
    def sync_table_to_production(self, table_name: str, changes: List[Dict]) -> bool:
        """Sync table changes to production database"""
        if not changes:
            return True
        
        try:
            # For now, we'll implement a simple API-based sync
            # In production, you might want to use database replication or webhooks
            
            # Prepare data for sync
            sync_data = {
                'table': table_name,
                'changes': changes,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'local'
            }
            
            # Send to production sync endpoint
            production_url = os.environ.get('PRODUCTION_APP_URL', '').rstrip('/')
            if not production_url:
                self.logger.warning("PRODUCTION_APP_URL not set, skipping sync")
                return False
            
            sync_endpoint = f"{production_url}/api/sync/receive"
            
            headers = {
                'Content-Type': 'application/json',
                'X-Sync-Token': os.environ.get('SYNC_TOKEN', 'default-sync-token')
            }
            
            response = requests.post(
                sync_endpoint,
                json=sync_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully synced {len(changes)} changes to {table_name}")
                return True
            else:
                self.logger.error(f"Failed to sync {table_name}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error syncing {table_name} to production: {str(e)}")
            return False
    
    def perform_full_sync(self) -> Dict[str, Any]:
        """Perform full synchronization of all tables"""
        if not self.is_sync_enabled():
            return {
                'success': False,
                'message': 'Real-time sync is disabled',
                'tables_synced': 0,
                'total_changes': 0
            }
        
        self.logger.info("Starting full database synchronization...")
        
        sync_results = {
            'success': True,
            'message': 'Synchronization completed',
            'tables_synced': 0,
            'total_changes': 0,
            'table_details': {}
        }
        
        try:
            # Get last sync time or use default (last 24 hours for first sync)
            since_time = self.last_sync_time or (datetime.utcnow() - timedelta(hours=24))
            
            for table_name in self.sync_tables:
                try:
                    # Get changes from local database
                    changes = self.get_table_changes(table_name, since_time)
                    
                    if changes:
                        # Sync to production
                        sync_success = self.sync_table_to_production(table_name, changes)
                        
                        sync_results['table_details'][table_name] = {
                            'changes_count': len(changes),
                            'sync_success': sync_success
                        }
                        
                        if sync_success:
                            sync_results['tables_synced'] += 1
                            sync_results['total_changes'] += len(changes)
                        else:
                            sync_results['success'] = False
                    else:
                        sync_results['table_details'][table_name] = {
                            'changes_count': 0,
                            'sync_success': True
                        }
                        
                except Exception as e:
                    self.logger.error(f"Error syncing table {table_name}: {str(e)}")
                    sync_results['table_details'][table_name] = {
                        'changes_count': 0,
                        'sync_success': False,
                        'error': str(e)
                    }
                    sync_results['success'] = False
            
            # Update last sync time
            self.last_sync_time = datetime.utcnow()
            
            if sync_results['success']:
                self.logger.info(f"Sync completed: {sync_results['tables_synced']} tables, {sync_results['total_changes']} changes")
            else:
                self.logger.warning("Sync completed with some errors")
            
            return sync_results
            
        except Exception as e:
            self.logger.error(f"Error during full sync: {str(e)}")
            return {
                'success': False,
                'message': f'Sync failed: {str(e)}',
                'tables_synced': 0,
                'total_changes': 0
            }
    
    def sync_single_table(self, table_name: str) -> Dict[str, Any]:
        """Sync a single table"""
        if table_name not in self.sync_tables:
            return {
                'success': False,
                'message': f'Table {table_name} is not configured for sync',
                'changes_count': 0
            }
        
        try:
            since_time = self.last_sync_time or (datetime.utcnow() - timedelta(hours=24))
            changes = self.get_table_changes(table_name, since_time)
            
            if changes:
                sync_success = self.sync_table_to_production(table_name, changes)
                
                return {
                    'success': sync_success,
                    'message': f'Synced {len(changes)} changes' if sync_success else 'Sync failed',
                    'changes_count': len(changes),
                    'table': table_name
                }
            else:
                return {
                    'success': True,
                    'message': 'No changes to sync',
                    'changes_count': 0,
                    'table': table_name
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error syncing {table_name}: {str(e)}',
                'changes_count': 0,
                'table': table_name
            }
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            'sync_enabled': self.is_sync_enabled(),
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'sync_interval_minutes': self.sync_interval,
            'configured_tables': self.sync_tables,
            'production_db_connected': bool(self.production_db_url)
        }
    
    def enable_sync(self) -> bool:
        """Enable real-time sync"""
        self.sync_enabled = True
        self.logger.info("Real-time sync enabled")
        return True
    
    def disable_sync(self) -> bool:
        """Disable real-time sync"""
        self.sync_enabled = False
        self.logger.info("Real-time sync disabled")
        return True
    
    def force_full_sync(self) -> Dict[str, Any]:
        """Force full sync from last 24 hours"""
        self.last_sync_time = datetime.utcnow() - timedelta(hours=24)
        return self.perform_full_sync()


# Global sync service instance
sync_service = RealtimeSyncService()


def get_sync_service() -> RealtimeSyncService:
    """Get the global sync service instance"""
    return sync_service


def perform_sync() -> Dict[str, Any]:
    """Perform synchronization (convenience function)"""
    return sync_service.perform_full_sync()


def sync_table(table_name: str) -> Dict[str, Any]:
    """Sync a specific table (convenience function)"""
    return sync_service.sync_single_table(table_name)


def get_sync_status() -> Dict[str, Any]:
    """Get sync status (convenience function)"""
    return sync_service.get_sync_status()
