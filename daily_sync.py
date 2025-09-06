"""
Daily sync management script for St. Louis 311+ data updates.
Provides command-line interface for sync operations.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from services.api_client import APIClient
from services.data_processor import DataProcessor
from models import db, ServiceRequest, ServiceRequestUpdate
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DailySyncManager:
    """Command-line manager for daily sync operations."""
    
    def __init__(self):
        self.api_client = APIClient()
        self.data_processor = DataProcessor()
    
    def sync_yesterday(self):
        """Sync yesterday's service requests."""
        with app.app_context():
            try:
                # Calculate yesterday's date range
                yesterday = datetime.now() - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                # API requires end_date to be different from start_date, so use today
                end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
                
                logger.info(f"Syncing data for {yesterday.strftime('%Y-%m-%d')}")
                
                return self._sync_date_range(start_date, end_date)
                
            except Exception as e:
                logger.error(f"Yesterday sync failed: {e}")
                return False
    
    def sync_date_range(self, start_date_str, end_date_str):
        """Sync a specific date range."""
        with app.app_context():
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                logger.info(f"Syncing data from {start_date_str} to {end_date_str}")
                
                return self._sync_date_range(start_date, end_date)
                
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")
                return False
            except Exception as e:
                logger.error(f"Date range sync failed: {e}")
                return False
    
    def sync_last_n_days(self, days):
        """Sync the last N days of data."""
        with app.app_context():
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                logger.info(f"Syncing last {days} days of data")
                
                return self._sync_date_range(start_date, end_date)
                
            except Exception as e:
                logger.error(f"Last {days} days sync failed: {e}")
                return False
    
    def _sync_date_range(self, start_date, end_date):
        """Internal method to sync a date range."""
        try:
            # Step 1: Fetch data from API
            logger.info("Fetching data from St. Louis 311 API...")
            raw_requests = self.api_client.fetch_service_requests(
                start_date=start_date,
                end_date=end_date
            )
            
            if not raw_requests:
                logger.info("No new data found")
                return True
            
            logger.info(f"Fetched {len(raw_requests)} raw requests")
            
            # Step 2: Process and validate data
            logger.info("Processing and validating data...")
            processed_requests = self.data_processor.process_and_validate_data(raw_requests)
            
            if not processed_requests:
                logger.warning("No valid requests after processing")
                return True
            
            logger.info(f"Processed {len(processed_requests)} valid requests")
            
            # Step 3: Update database
            logger.info("Updating database...")
            requests_added = 0
            requests_updated = 0
            
            for request_data in processed_requests:
                try:
                    request_id = request_data.get('request_id')
                    if not request_id:
                        continue
                    
                    # Check if request already exists
                    existing = ServiceRequest.query.filter_by(request_id=request_id).first()
                    
                    if existing:
                        # Update existing record
                        if self._should_update_request(existing, request_data):
                            existing.update_from_dict(request_data)
                            requests_updated += 1
                            
                            # Create update record
                            update = ServiceRequestUpdate(
                                request_id=existing.id,
                                new_status=request_data.get('status'),
                                update_message=f"Updated via daily sync on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                                update_date=datetime.now(),
                                updated_by="system"
                            )
                            db.session.add(update)
                            logger.debug(f"Updated request {request_id}")
                    else:
                        # Create new record
                        service_request = ServiceRequest()
                        service_request.update_from_dict(request_data)
                        service_request.source = 'api'  # Mark as API source
                        
                        db.session.add(service_request)
                        requests_added += 1
                        logger.debug(f"Added new request {request_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing request {request_data.get('request_id', 'unknown')}: {e}")
                    continue
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Sync completed successfully:")
            logger.info(f"  - Requests added: {requests_added}")
            logger.info(f"  - Requests updated: {requests_updated}")
            logger.info(f"  - Total processed: {len(processed_requests)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            db.session.rollback()
            return False
    
    def _should_update_request(self, existing_request, new_data):
        """Determine if a request should be updated."""
        # Always update if status changed
        if existing_request.status != new_data.get('status'):
            return True
        
        # Update if description changed
        if existing_request.description != new_data.get('description'):
            return True
        
        # Update if agency responsible changed (submit_to field)
        if existing_request.submit_to != new_data.get('submit_to'):
            return True
        
        # Update if closed date was added
        if not existing_request.datetime_closed and new_data.get('datetime_closed'):
            return True
        
        return False
    
    def test_api_connection(self):
        """Test the API connection."""
        logger.info("Testing API connection...")
        result = self.api_client.test_connection()
        
        if result['status'] == 'success':
            logger.info(f"✅ API connection successful (Response time: {result['response_time']:.2f}s)")
            return True
        else:
            logger.error(f"❌ API connection failed: {result['message']}")
            return False
    
    def get_sync_stats(self):
        """Get current sync statistics."""
        with app.app_context():
            try:
                total_requests = ServiceRequest.query.count()
                api_requests = ServiceRequest.query.filter_by(source='api').count()
                citizen_requests = ServiceRequest.query.filter_by(source='citizen').count()
                
                # Get latest requests
                latest_api = ServiceRequest.query.filter_by(source='api').order_by(ServiceRequest.date_requested.desc()).first()
                latest_citizen = ServiceRequest.query.filter_by(source='citizen').order_by(ServiceRequest.date_requested.desc()).first()
                
                stats = {
                    'total_requests': total_requests,
                    'api_requests': api_requests,
                    'citizen_requests': citizen_requests,
                    'latest_api_date': latest_api.date_requested.strftime('%Y-%m-%d %H:%M:%S') if latest_api else 'None',
                    'latest_citizen_date': latest_citizen.date_requested.strftime('%Y-%m-%d %H:%M:%S') if latest_citizen else 'None'
                }
                
                logger.info("📊 Current Sync Statistics:")
                for key, value in stats.items():
                    logger.info(f"  {key}: {value}")
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get sync stats: {e}")
                return None

def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(description='St. Louis 311+ Daily Sync Manager')
    
    parser.add_argument('command', choices=['yesterday', 'date-range', 'last-days', 'test', 'stats'], 
                       help='Sync command to execute')
    
    parser.add_argument('--start-date', type=str, 
                       help='Start date for date-range sync (YYYY-MM-DD)')
    
    parser.add_argument('--end-date', type=str,
                       help='End date for date-range sync (YYYY-MM-DD)')
    
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days for last-days sync (default: 7)')
    
    args = parser.parse_args()
    
    manager = DailySyncManager()
    
    if args.command == 'yesterday':
        success = manager.sync_yesterday()
        sys.exit(0 if success else 1)
        
    elif args.command == 'date-range':
        if not args.start_date or not args.end_date:
            logger.error("❌ Date range sync requires --start-date and --end-date")
            sys.exit(1)
        success = manager.sync_date_range(args.start_date, args.end_date)
        sys.exit(0 if success else 1)
        
    elif args.command == 'last-days':
        success = manager.sync_last_n_days(args.days)
        sys.exit(0 if success else 1)
        
    elif args.command == 'test':
        success = manager.test_api_connection()
        sys.exit(0 if success else 1)
        
    elif args.command == 'stats':
        stats = manager.get_sync_stats()
        sys.exit(0 if stats else 1)

if __name__ == '__main__':
    main()
