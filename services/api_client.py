"""
API client service for St. Louis 311 Service Integration.
Handles communication with the St. Louis Open311 API.
Adapted from the original ArcPy version for Flask/PostGIS.
"""

import requests
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class APIClient:
    """
    Professional API client for St. Louis 311 service requests.
    Handles authentication, rate limiting, and data fetching.
    """
    
    def __init__(self):
        self.api_key = os.getenv("STL311_API_KEY")
        if not self.api_key:
            logger.warning("STL311_API_KEY environment variable is not set. API requests may fail.")
        
        # Updated base URL for St. Louis 311 API
        self.base_url = "https://www.stlouis-mo.gov/powernap/stlouis/api.cfm"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StLouis311-Flask/1.0',
            'Accept': 'application/json'
        })
        
        # Configuration
        self.max_pages = 10
        self.rate_limit_delay = 1.0
        self.request_timeout = 30
    
    def fetch_service_requests(self, start_date=None, end_date=None, status=None):
        """
        Fetch service requests from the St. Louis Open311 API.
        Uses the correct endpoint format from the official documentation.
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=1)
        if not end_date:
            end_date = datetime.now()
        if not status:
            status = "open"
            
        all_requests = []
        page = 1
        
        while page <= self.max_pages:
            try:
                # Build query parameters based on official documentation
                params = {
                    'api_key': self.api_key,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'page_size': 1000  # Maximum page size per documentation
                }
                
                # Add status parameter if specified
                if status:
                    params['status'] = status
                
                # Make API request using correct endpoint format
                # Format: https://www.stlouis-mo.gov/powernap/stlouis/api.cfm/requests.json
                url = f"{self.base_url}/requests.json"
                logger.info(f"Fetching page {page} from {url}")
                
                response = self.session.get(url, params=params, timeout=self.request_timeout)
                response.raise_for_status()
                
                data = response.json()
                
                # Debug: Print response structure
                logger.debug(f"API response type: {type(data)}")
                if isinstance(data, dict):
                    logger.debug(f"API response keys: {list(data.keys())}")
                
                # API returns a list directly, not a dictionary with service_requests key
                if isinstance(data, list):
                    requests_batch = data
                elif isinstance(data, dict):
                    requests_batch = data.get('service_requests', [])
                else:
                    logger.error(f"Unexpected API response format: {data}")
                    break
                
                if not requests_batch:
                    logger.info(f"No more requests found on page {page}")
                    break
                
                all_requests.extend(requests_batch)
                logger.info(f"Fetched {len(requests_batch)} requests from page {page}")
                
                # Check if we've reached the end
                if len(requests_batch) < 1000:
                    logger.info(f"Reached end of data on page {page}")
                    break
                
                page += 1
                time.sleep(self.rate_limit_delay)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed on page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error on page {page}: {e}")
                break
        
        logger.info(f"Total requests fetched: {len(all_requests)}")
        return all_requests
    
    def test_connection(self):
        """
        Test the API connection and return status.
        """
        try:
            params = {
                'api_key': self.api_key,
                'start_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'end_date': datetime.now().strftime('%Y-%m-%d'),
                'page_size': 1
            }
            
            url = f"{self.base_url}/requests.json"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'API connection successful',
                'response_time': response.elapsed.total_seconds()
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'message': f'API connection failed: {e}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {e}'
            } 