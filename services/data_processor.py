"""
Data processor service for St. Louis 311 Service Integration.
Handles data cleaning, validation, and enrichment of raw API data.
Adapted from the original ArcPy version for Flask/PostGIS.
"""

from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Professional data processor for St. Louis 311 service requests.
    Handles data cleaning, validation, and enrichment.
    """
    
    def __init__(self):
        # Date formats for parsing
        self.date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y']
        
        # Coordinate validation ranges (St. Louis area in EPSG:3857)
        self.coordinate_ranges = {
            'min_x': -10060000,  # West boundary in EPSG:3857
            'max_x': -10020000,  # East boundary in EPSG:3857
            'min_y': 4600000,    # South boundary in EPSG:3857
            'max_y': 4700000     # North boundary in EPSG:3857
        }
    
    def process_and_validate_data(self, raw_requests):
        """
        Clean and validate data - critical professional step.
        Real-world APIs often have inconsistent or missing data.
        """
        processed_requests = []
        validation_stats = {
            'total': len(raw_requests),
            'valid_coordinates': 0,
            'missing_coordinates': 0,
            'invalid_dates': 0,
            'processed': 0
        }
        
        # Debug: Print the first few raw requests to see the structure
        if raw_requests:
            logger.info("Sample raw API response structure:")
            sample_request = raw_requests[0]
            logger.info(f"Available fields: {list(sample_request.keys())}")
            logger.debug(f"Sample request data: {sample_request}")
            
            # Print all unique field names across all requests
            all_fields = set()
            for request in raw_requests:
                all_fields.update(request.keys())
            logger.info(f"All unique fields found in API response: {sorted(list(all_fields))}")
        
        for request in raw_requests:
            try:
                # Professional data validation
                processed_request = {}
                
                # Handle coordinate extraction (critical for GIS)
                if not self._extract_coordinates(request, processed_request, validation_stats):
                    continue
                
                # Process dates with professional error handling
                self._process_dates(request, processed_request, validation_stats)
             
                # Copy other fields with data cleaning
                self._copy_and_clean_fields(request, processed_request)
                
                processed_requests.append(processed_request)
                validation_stats['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing request {request.get('service_request_id', 'unknown')}: {e}")
                continue
        
        # Print validation statistics (professional reporting)
        logger.info(f"Data validation complete: {validation_stats}")
        return processed_requests
    
    def _extract_coordinates(self, request, processed_request, validation_stats):
        """
        Extract coordinates from known fields.
        Store SRX/SRY as Web Mercator (EPSG:3857) X/Y meters, as provided by the source data.
        """
        try:
            srx_raw = request.get('SRX')
            sry_raw = request.get('SRY')
            lat_raw = request.get('LAT')
            long_raw = request.get('LONG')

            x_coord = None
            y_coord = None

            # Use SRX/SRY directly if present
            if srx_raw is not None and sry_raw is not None:
                try:
                    logger.debug(f"Processing request {request.get('SERVICE_REQUEST_ID')}: SRX={srx_raw}, SRY={sry_raw}")
                    x_coord = float(srx_raw)
                    y_coord = float(sry_raw)
                except (ValueError, TypeError):
                    x_coord = None
                    y_coord = None

            # If SRX/SRY not valid, try LAT/LONG (treat as 3857 X/Y meters)
            if (x_coord is None or y_coord is None or x_coord == 0 or y_coord == 0) and (lat_raw is not None and long_raw is not None):
                try:
                    logger.debug(f"Processing request {request.get('SERVICE_REQUEST_ID')}: LAT={lat_raw}, LONG={long_raw}")
                    x_coord = float(lat_raw)   # X in 3857
                    y_coord = float(long_raw)  # Y in 3857
                except (ValueError, TypeError):
                    x_coord = None
                    y_coord = None

            # Validate coordinates are within St. Louis area bounds
            if (x_coord is not None and y_coord is not None and 
                x_coord != 0 and y_coord != 0 and
                self.coordinate_ranges['min_x'] <= x_coord <= self.coordinate_ranges['max_x'] and
                self.coordinate_ranges['min_y'] <= y_coord <= self.coordinate_ranges['max_y']):
                
                processed_request['srx'] = x_coord  # X in 3857
                processed_request['sry'] = y_coord  # Y in 3857
                validation_stats['valid_coordinates'] += 1
                return True
            else:
                logger.debug(f"No valid coordinates found for request {request.get('SERVICE_REQUEST_ID')}")
                validation_stats['missing_coordinates'] += 1
                return False

        except Exception as e:
            logger.error(f"Error processing coordinates for request {request.get('SERVICE_REQUEST_ID')}: {e}")
            validation_stats['missing_coordinates'] += 1
            return False
        
    def _process_dates(self, request, processed_request, validation_stats):
        """
        Process date fields with multiple format support.
        """
        # Map API date fields to our schema date fields
        date_field_mapping = {
            'REQUESTED_DATETIME': 'datetime_init',
            'UPDATED_DATETIME': 'datetime_closed',
            'EXPECTED_DATETIME': 'prj_complete_date'
        }
        
        for api_field, schema_field in date_field_mapping.items():
            date_str = request.get(api_field)
            if date_str:
                try:
                    # Handle ISO datetime format (2025-07-05T23:48:01Z)
                    if 'T' in date_str and ('Z' in date_str or '+' in date_str):
                        # Remove 'Z' and parse as UTC
                        if date_str.endswith('Z'):
                            date_str = date_str[:-1]
                        processed_request[schema_field] = datetime.fromisoformat(date_str)
                    else:
                        # Handle multiple date formats (professional requirement)
                        for fmt in self.date_formats:
                            try:
                                processed_request[schema_field] = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    logger.error(f"Error processing date field {api_field} -> {schema_field}: {e}")
                    validation_stats['invalid_dates'] += 1
    
    def _copy_and_clean_fields(self, request, processed_request):
        """
        Copy and clean fields from raw request to processed request.
        Map API field names to our schema field names.
        """
        # Map API field names to our schema field names
        field_mapping = {
            'SERVICE_NAME': 'description',
            'SERVICE_CODE': 'problem_code',
            'ZIPCODE': 'prob_zip',
            'ADDRESS': 'prob_address',
            'AGENCY_RESPONSIBLE': 'submit_to',
            'STATUS': 'status',
            'STATUS_NOTES': 'explanation',
            'SERVICE_NOTICE': 'caller_type',
            'MEDIA_URL': 'group_name'
        }
        
        # Initialize all schema fields with None/empty values
        schema_fields = [
            'caller_type', 'date_cancelled', 'date_inv_done', 'datetime_closed', 
            'datetime_init', 'description', 'explanation', 'neighborhood',
            'plain_english_name', 'prj_complete_date', 'prob_address',
            'prob_add_type', 'prob_city', 'problem_code', 'prob_zip', 'request_id',
            'status', 'submit_to', 'ward', 'group_name'
        ]
        
        for field in schema_fields:
            processed_request[field] = None
        
        # Copy and map fields from API response (excluding date fields which are handled separately)
        for api_field, schema_field in field_mapping.items():
            value = request.get(api_field)
            
            if value is not None:
                # Type enforcement for integer fields
                if schema_field in ['request_id', 'neighborhood', 'ward', 'prob_zip', 'problem_code']:
                    try:
                        value = int(value) if value else None
                    except (ValueError, TypeError):
                        value = None
                elif isinstance(value, str):
                    value = value.strip()[:255]  # Truncate for TEXT fields
                
                processed_request[schema_field] = value
        
        # Handle special cases
        # REQUESTID - use SERVICE_REQUEST_ID if available, otherwise generate from SERVICE_CODE
        request_id = request.get('SERVICE_REQUEST_ID')
        if request_id:
            try:
                processed_request['request_id'] = int(request_id)
            except (ValueError, TypeError):
                processed_request['request_id'] = None
        else:
            # Generate a request ID from service code and timestamp if needed
            service_code = request.get('SERVICE_CODE')
            if service_code:
                processed_request['request_id'] = service_code
        
        # NEIGHBORHOOD - might be in ADDRESS field or separate field
        if not processed_request['neighborhood']:
            address = request.get('ADDRESS', '')
            if address and ',' in address:
                # Try to extract neighborhood from address
                parts = address.split(',')
                if len(parts) > 1:
                    processed_request['neighborhood'] = parts[1].strip()
        
        # WARD - might be in ADDRESS field or separate field
        if not processed_request['ward']:
            address = request.get('ADDRESS', '')
            if address and 'WARD' in address.upper():
                # Try to extract ward from address
                ward_match = re.search(r'WARD\s*(\d+)', address.upper())
                if ward_match:
                    try:
                        processed_request['ward'] = int(ward_match.group(1))
                    except (ValueError, TypeError):
                        pass
        
        # PROBCITY - default to St. Louis
        if not processed_request['prob_city']:
            processed_request['prob_city'] = 'St. Louis'
        
        # PROBADDTYPE - default based on address type
        if not processed_request['prob_add_type']:
            address = request.get('ADDRESS', '')
            if address:
                if any(word in address.upper() for word in ['STREET', 'AVE', 'BLVD', 'DR']):
                    processed_request['prob_add_type'] = 'Street'
                elif any(word in address.upper() for word in ['ALLEY', 'LANE']):
                    processed_request['prob_add_type'] = 'Alley'
                else:
                    processed_request['prob_add_type'] = 'Address'
        
        # DATECANCELLED and DATEINVTDONE - not available in API, leave as None
        # PLAIN_ENGLISH_NAME_FOR_PROBLEMCODE - not available in API, leave as None
    
    def get_validation_summary(self, processed_requests):
        """
        Get a summary of data validation results.
        """
        total_requests = len(processed_requests)
        requests_with_coordinates = sum(1 for r in processed_requests if r.get('srx') and r.get('sry'))
        requests_with_dates = sum(1 for r in processed_requests if r.get('datetime_init'))
        
        return {
            'total_processed': total_requests,
            'with_coordinates': requests_with_coordinates,
            'with_dates': requests_with_dates,
            'coordinate_percentage': (requests_with_coordinates / total_requests * 100) if total_requests > 0 else 0
        } 