"""
Scheduler service for automated data synchronization.
Handles daily sync of St. Louis 311 data and cleanup tasks.
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
from .api_client import APIClient
from .data_processor import DataProcessor
from models import db, ServiceRequest, ServiceRequestUpdate

logger = logging.getLogger(__name__)

class DataScheduler:
    """
    Automated scheduler for St. Louis 311 data synchronization.
    Runs daily sync operations and maintenance tasks.
    """
    
    def __init__(self, app):
        self.app = app
        self.api_client = APIClient()
        self.data_processor = DataProcessor()
        self.is_running = False
        self.scheduler_thread = None
        
        # Configuration
        self.daily_sync_time = "02:00"  # 2 AM daily sync
        self.cleanup_time = "03:00"     # 3 AM cleanup tasks
        self.max_retry_attempts = 3
        self.retry_delay = 300  # 5 minutes between retries
    
    def start_scheduler(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule daily tasks
        schedule.every().day.at(self.daily_sync_time).do(self.daily_sync_job)
        schedule.every().day.at(self.cleanup_time).do(self.cleanup_job)
        
        # Schedule hourly health checks
        schedule.every().hour.do(self.health_check_job)
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Scheduler started - Daily sync at {self.daily_sync_time}, Cleanup at {self.cleanup_time}")
    
    def stop_scheduler(self):
        """Stop the background scheduler."""
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Background thread to run scheduled tasks."""
        while self.is_running:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    
    def daily_sync_job(self):
        """Daily job to sync yesterday's service requests."""
        with self.app.app_context():
            try:
                logger.info("Starting daily sync job for yesterday's data")
                
                # Calculate yesterday's date range
                yesterday = datetime.now() - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                result = self._sync_data_with_retry(start_date, end_date)
                
                if result['status'] == 'success':
                    logger.info(f"Daily sync completed: {result['requests_added']} added, {result['requests_updated']} updated")
                    
                    # Log sync statistics
                    self._log_sync_stats(result, 'daily_sync')
                else:
                    logger.error(f"Daily sync failed: {result['message']}")
                    
            except Exception as e:
                logger.error(f"Daily sync job failed: {e}", exc_info=True)
    
    def cleanup_job(self):
        """Daily cleanup job for old logs and temporary data."""
        with self.app.app_context():
            try:
                logger.info("Starting daily cleanup job")
                
                # Clean up old sync logs (older than 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                
                # This is a placeholder - implement based on your logging needs
                cleanup_count = 0
                
                logger.info(f"Cleanup completed: {cleanup_count} old records removed")
                
            except Exception as e:
                logger.error(f"Cleanup job failed: {e}", exc_info=True)
    
    def health_check_job(self):
        """Hourly health check of the API connection."""
        try:
            result = self.api_client.test_connection()
            if result['status'] != 'success':
                logger.warning(f"API health check failed: {result['message']}")
            else:
                logger.debug(f"API health check passed ({result['response_time']:.2f}s)")
                
        except Exception as e:
            logger.error(f"Health check job failed: {e}")
    
    def sync_yesterday_now(self):
        """Manual trigger to sync yesterday's data immediately."""
        with self.app.app_context():
            try:
                yesterday = datetime.now() - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                return self._sync_data_with_retry(start_date, end_date)
                
            except Exception as e:
                logger.error(f"Manual yesterday sync failed: {e}")
                return {
                    'status': 'error',
                    'message': f'Manual sync failed: {e}'
                }
    
    def sync_date_range(self, start_date, end_date):
        """Sync a specific date range."""
        with self.app.app_context():
            return self._sync_data_with_retry(start_date, end_date)
    
    def _sync_data_with_retry(self, start_date, end_date):
        """Sync data with retry logic."""
        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                logger.info(f"Sync attempt {attempt} for {start_date.date()} to {end_date.date()}")
                
                # Fetch data from API
                raw_requests = self.api_client.fetch_service_requests(
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not raw_requests:
                    return {
                        'status': 'success',
                        'message': 'No new data found',
                        'requests_added': 0,
                        'requests_updated': 0
                    }
                
                # Process and validate data
                processed_requests = self.data_processor.process_and_validate_data(raw_requests)
                
                # Update database
                result = self._update_database(processed_requests)
                
                return result
                
            except Exception as e:
                logger.warning(f"Sync attempt {attempt} failed: {e}")
                if attempt < self.max_retry_attempts:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All sync attempts failed for {start_date.date()}")
                    return {
                        'status': 'error',
                        'message': f'Sync failed after {self.max_retry_attempts} attempts: {e}'
                    }
    
    def _update_database(self, processed_requests):
        """Update database with processed requests."""
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
                    # Update existing record only if data has changed
                    if self._has_data_changed(existing, request_data):
                        existing.update_from_dict(request_data)
                        requests_updated += 1
                        
                        # Create update record
                        update = ServiceRequestUpdate(
                            request_id=existing.id,
                            new_status=request_data.get('status'),
                            update_message=f"Updated via daily sync",
                            update_date=datetime.now(),
                            updated_by="system"
                        )
                        db.session.add(update)
                else:
                    # Create new record
                    service_request = ServiceRequest()
                    service_request.update_from_dict(request_data)
                    service_request.source = 'api'  # Mark as API source
                    
                    db.session.add(service_request)
                    requests_added += 1
                
            except Exception as e:
                logger.error(f"Error processing request {request_data.get('request_id', 'unknown')}: {e}")
                continue
        
        try:
            db.session.commit()
            return {
                'status': 'success',
                'message': 'Database update completed',
                'requests_added': requests_added,
                'requests_updated': requests_updated
            }
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database commit failed: {e}")
            return {
                'status': 'error',
                'message': f'Database update failed: {e}'
            }
    
    def _has_data_changed(self, existing_request, new_data):
        """Check if the request data has meaningful changes."""
        # Check key fields for changes (submit_to is the database field for agency_responsible)
        key_fields = ['status', 'description', 'prob_address', 'submit_to']
        
        for field in key_fields:
            existing_value = getattr(existing_request, field, None)
            new_value = new_data.get(field)
            
            if existing_value != new_value:
                return True
        
        return False
    
    def _log_sync_stats(self, result, sync_type):
        """Log sync statistics for monitoring."""
        stats = {
            'sync_type': sync_type,
            'timestamp': datetime.now().isoformat(),
            'status': result['status'],
            'requests_added': result.get('requests_added', 0),
            'requests_updated': result.get('requests_updated', 0),
            'message': result.get('message', '')
        }
        
        logger.info(f"Sync Stats: {stats}")
        
        # You could also store these stats in a dedicated table for monitoring
        # or send to a monitoring service
    
    def get_scheduler_status(self):
        """Get current scheduler status."""
        return {
            'is_running': self.is_running,
            'daily_sync_time': self.daily_sync_time,
            'cleanup_time': self.cleanup_time,
            'next_sync': schedule.next_run(),
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
