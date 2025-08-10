"""
Comprehensive form validation and security utilities for STL 311 Plus.
Implements industry best practices for user input validation and sanitization.
"""

import re
import bleach
import html
from datetime import datetime, timedelta
from typing import Tuple, List, Dict, Optional, Any
import logging
import hashlib
import secrets
from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import validate_email as external_validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation exception"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class FormValidator:
    """
    Comprehensive form validation system following OWASP guidelines.
    
    Key Security Principles:
    1. Input Validation: Validate all inputs on server-side
    2. Output Encoding: Sanitize all outputs
    3. Parameter Pollution: Handle duplicate parameters
    4. Rate Limiting: Prevent abuse
    5. File Upload Security: Validate file types and content
    """
    
    # Validation patterns
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone_us': r'^(\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',
        'zip_code': r'^\d{5}(-\d{4})?$',
        'street_address': r'^\d+\s+[a-zA-Z\s\-\'\.]+$',
        'request_id': r'^\d{8,15}$'
    }
    
    # Content sanitization settings
    ALLOWED_HTML_TAGS = []  # No HTML allowed in service requests
    ALLOWED_HTML_ATTRIBUTES = {}
    
    # File upload constraints
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILES_PER_REQUEST = 5
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'com', 'cmd', 'scr', 'pif', 'vbs', 'js', 'jar', 
        'php', 'py', 'pl', 'sh', 'asp', 'jsp', 'html', 'htm'
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_service_request(self, form_data: Dict[str, Any], files: List = None) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Comprehensive validation for service request submissions.
        
        Args:
            form_data: Dictionary of form fields
            files: List of uploaded files
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        self.errors = []
        self.warnings = []
        
        try:
            # Required field validation
            self._validate_required_fields(form_data)
            
            # Data type and format validation
            self._validate_contact_info(form_data)
            self._validate_location_data(form_data)
            self._validate_request_content(form_data)
            self._validate_metadata(form_data)
            
            # File upload validation
            if files:
                self._validate_file_uploads(files)
            
            # Cross-field validation
            self._validate_business_rules(form_data)
            
            return len(self.errors) == 0, self._format_errors()
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            self.errors.append(e)
            return False, self._format_errors()
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            self.errors.append(ValidationError('general', 'Validation failed due to system error'))
            return False, self._format_errors()
    
    def _validate_required_fields(self, form_data: Dict[str, Any]) -> None:
        """Validate required fields are present and non-empty"""
        required_fields = {
            'category': 'Service category',
            'prob_address': 'Street address',
            'description': 'Problem description',
            'citizen_email': 'Email address'
        }
        
        for field, display_name in required_fields.items():
            value = form_data.get(field, '').strip() if form_data.get(field) else ''
            if not value:
                self.errors.append(ValidationError(field, f'{display_name} is required'))
    
    def _validate_contact_info(self, form_data: Dict[str, Any]) -> None:
        """Validate contact information"""
        # Email validation
        email = form_data.get('citizen_email', '').strip()
        if email:
            try:
                # Use external library for comprehensive email validation
                valid = external_validate_email(email)
                # Store normalized email
                form_data['citizen_email'] = valid.email
            except EmailNotValidError as e:
                self.errors.append(ValidationError('citizen_email', f'Invalid email: {str(e)}'))
        
        # Phone validation
        phone = form_data.get('citizen_phone', '').strip()
        if phone:
            if not re.match(self.PATTERNS['phone_us'], phone):
                self.errors.append(ValidationError('citizen_phone', 'Phone number must be a valid US number'))
            else:
                # Normalize phone number
                digits = re.sub(r'[^\d]', '', phone)
                form_data['citizen_phone'] = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
        
        # Name validation
        name = form_data.get('citizen_name', '').strip()
        if name:
            if len(name) < 2:
                self.errors.append(ValidationError('citizen_name', 'Name must be at least 2 characters'))
            elif len(name) > 100:
                self.errors.append(ValidationError('citizen_name', 'Name must be less than 100 characters'))
            elif not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
                self.errors.append(ValidationError('citizen_name', 'Name contains invalid characters'))
            else:
                # Sanitize name
                form_data['citizen_name'] = html.escape(name.title())
    
    def _validate_location_data(self, form_data: Dict[str, Any]) -> None:
        """Validate location and address information"""
        # Address validation
        address = form_data.get('prob_address', '').strip()
        if address:
            if len(address) < 5:
                self.errors.append(ValidationError('prob_address', 'Address must be at least 5 characters'))
            elif len(address) > 255:
                self.errors.append(ValidationError('prob_address', 'Address is too long (max 255 characters)'))
            elif not re.match(self.PATTERNS['street_address'], address, re.IGNORECASE):
                self.warnings.append('Address format may be incomplete (should include house number)')
            
            # Sanitize address
            form_data['prob_address'] = html.escape(address.title())
        
        # ZIP code validation
        zip_code = form_data.get('prob_zip', '').strip()
        if zip_code:
            if not re.match(self.PATTERNS['zip_code'], zip_code):
                self.errors.append(ValidationError('prob_zip', 'ZIP code must be in format 12345 or 12345-6789'))
        
        # Coordinate validation
        try:
            lat = float(form_data.get('latitude', 0))
            lng = float(form_data.get('longitude', 0))
            
            # St. Louis area bounds validation
            STL_BOUNDS = {
                'lat_min': 38.4, 'lat_max': 38.8,
                'lng_min': -90.6, 'lng_max': -90.0
            }
            
            if lat == 0 or lng == 0:
                self.errors.append(ValidationError('location', 'Please select a location on the map'))
            elif not (STL_BOUNDS['lat_min'] <= lat <= STL_BOUNDS['lat_max']):
                self.errors.append(ValidationError('location', 'Location must be within St. Louis city limits'))
            elif not (STL_BOUNDS['lng_min'] <= lng <= STL_BOUNDS['lng_max']):
                self.errors.append(ValidationError('location', 'Location must be within St. Louis city limits'))
                
        except (ValueError, TypeError):
            self.errors.append(ValidationError('location', 'Invalid location coordinates'))
    
    def _validate_request_content(self, form_data: Dict[str, Any]) -> None:
        """Validate request content and descriptions"""
        # Description validation
        description = form_data.get('description', '').strip()
        if description:
            if len(description) < 10:
                self.errors.append(ValidationError('description', 'Description must be at least 10 characters'))
            elif len(description) > 2000:
                self.errors.append(ValidationError('description', 'Description is too long (max 2000 characters)'))
            
            # Content filtering
            description_clean = self._sanitize_text(description)
            if self._contains_inappropriate_content(description_clean):
                self.errors.append(ValidationError('description', 'Description contains inappropriate content'))
            
            form_data['description'] = description_clean
        
        # Category validation
        category = form_data.get('category', '').strip()
        if category:
            valid_categories = {
                'Street & Sidewalk Issues', 'Refuse & Recycling', 'Traffic & Signs',
                'Parks & Recreation', 'Building & Property Issues', 'Trees & Forestry'
            }
            if category not in valid_categories:
                self.errors.append(ValidationError('category', 'Invalid service category'))
        
        # Priority validation
        priority = form_data.get('priority', 'normal')
        valid_priorities = {'low', 'normal', 'high', 'urgent'}
        if priority not in valid_priorities:
            form_data['priority'] = 'normal'
    
    def _validate_metadata(self, form_data: Dict[str, Any]) -> None:
        """Validate metadata and preference fields"""
        # Contact method preference
        contact_method = form_data.get('contact_method_preference', 'email')
        valid_methods = {'email', 'phone', 'none'}
        if contact_method not in valid_methods:
            form_data['contact_method_preference'] = 'email'
        
        # Emergency flag validation
        is_emergency = form_data.get('is_emergency')
        if is_emergency and contact_method == 'none':
            self.warnings.append('Emergency requests should include contact information for follow-up')
    
    def _validate_file_uploads(self, files: List) -> None:
        """Comprehensive file upload validation"""
        if len(files) > self.MAX_FILES_PER_REQUEST:
            self.errors.append(ValidationError('files', f'Maximum {self.MAX_FILES_PER_REQUEST} files allowed'))
            return
        
        for i, file in enumerate(files):
            if not file or not file.filename:
                continue
                
            # File size validation
            if hasattr(file, 'content_length') and file.content_length > self.MAX_FILE_SIZE:
                self.errors.append(ValidationError('files', f'File {file.filename} is too large (max 10MB)'))
                continue
            
            # Extension validation
            filename_lower = file.filename.lower()
            extension = filename_lower.split('.')[-1] if '.' in filename_lower else ''
            
            if extension in self.DANGEROUS_EXTENSIONS:
                self.errors.append(ValidationError('files', f'File type .{extension} is not allowed'))
                continue
            
            # MIME type validation
            if hasattr(file, 'content_type') and file.content_type:
                if file.content_type not in self.ALLOWED_MIME_TYPES:
                    self.errors.append(ValidationError('files', f'File type {file.content_type} is not allowed'))
                    continue
            
            # Filename validation
            if not self._validate_filename(file.filename):
                self.errors.append(ValidationError('files', f'Invalid filename: {file.filename}'))
                continue
    
    def _validate_business_rules(self, form_data: Dict[str, Any]) -> None:
        """Validate business-specific rules and constraints"""
        category = form_data.get('category', '')
        priority = form_data.get('priority', 'normal')
        is_emergency = form_data.get('is_emergency', False)
        
        # Emergency escalation rules
        if is_emergency:
            emergency_eligible_categories = {'Traffic & Signs', 'Trees & Forestry'}
            if category not in emergency_eligible_categories:
                self.warnings.append(f'{category} requests are typically not classified as emergencies')
            
            if priority == 'low':
                self.warnings.append('Emergency requests should not have low priority')
        
        # Department-specific validations
        if category == 'Building & Property Issues':
            description = form_data.get('description', '').lower()
            if 'emergency' in description and not is_emergency:
                self.warnings.append('Building emergencies should be marked as emergency requests')
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input removing HTML and dangerous content"""
        if not text:
            return ''
        
        # Remove HTML tags
        clean_text = bleach.clean(text, tags=self.ALLOWED_HTML_TAGS, 
                                 attributes=self.ALLOWED_HTML_ATTRIBUTES, strip=True)
        
        # Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _contains_inappropriate_content(self, text: str) -> bool:
        """Basic inappropriate content detection"""
        # This would integrate with a content filtering service in production
        inappropriate_patterns = [
            r'\b(spam|advertisement|buy now|click here)\b',
            r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+)',  # Basic URL detection
        ]
        
        text_lower = text.lower()
        for pattern in inappropriate_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate uploaded filename"""
        if not filename or len(filename) > 255:
            return False
        
        # Check for directory traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for null bytes
        if '\x00' in filename:
            return False
        
        return True
    
    def _format_errors(self) -> Dict[str, List[str]]:
        """Format validation errors for API response"""
        errors_dict = {}
        for error in self.errors:
            if isinstance(error, ValidationError):
                if error.field not in errors_dict:
                    errors_dict[error.field] = []
                errors_dict[error.field].append(error.message)
        
        if self.warnings:
            errors_dict['warnings'] = [str(w) for w in self.warnings]
        
        return errors_dict

class RateLimiter:
    """
    Rate limiting for form submissions to prevent abuse.
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client  # In production, use Redis
        self.memory_cache = {}  # Simple in-memory cache for development
    
    def is_allowed(self, identifier: str, max_requests: int = 5, window_seconds: int = 300) -> Tuple[bool, int]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            identifier: IP address or user identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds (default: 5 minutes)
            
        Returns:
            Tuple of (is_allowed, time_until_reset)
        """
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)
        
        if self.redis_client:
            # Use Redis for production
            return self._check_redis_rate_limit(identifier, max_requests, window_seconds)
        else:
            # Use memory cache for development
            return self._check_memory_rate_limit(identifier, max_requests, window_start, current_time)
    
    def _check_memory_rate_limit(self, identifier: str, max_requests: int, 
                                window_start: datetime, current_time: datetime) -> Tuple[bool, int]:
        """Memory-based rate limiting for development"""
        if identifier not in self.memory_cache:
            self.memory_cache[identifier] = []
        
        # Clean old requests
        self.memory_cache[identifier] = [
            req_time for req_time in self.memory_cache[identifier] 
            if req_time > window_start
        ]
        
        request_count = len(self.memory_cache[identifier])
        
        if request_count >= max_requests:
            # Calculate time until oldest request expires
            if self.memory_cache[identifier]:
                oldest_request = min(self.memory_cache[identifier])
                time_until_reset = int((oldest_request - window_start).total_seconds())
                return False, max(0, time_until_reset)
            return False, 300  # Default 5 minutes
        
        # Add current request
        self.memory_cache[identifier].append(current_time)
        return True, 0
    
    def _check_redis_rate_limit(self, identifier: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """Redis-based rate limiting for production"""
        # Implementation would use Redis sliding window
        # This is a placeholder for production implementation
        return True, 0

# Security utilities
class SecurityUtils:
    """Additional security utilities for form processing"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token for form protection"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging/tracking without exposure"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]
    
    @staticmethod
    def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for safe logging (remove PII)"""
        sanitized = data.copy()
        
        # Remove or hash sensitive fields
        sensitive_fields = ['citizen_email', 'citizen_phone', 'citizen_name']
        for field in sensitive_fields:
            if field in sanitized:
                if sanitized[field]:
                    sanitized[field] = SecurityUtils.hash_sensitive_data(str(sanitized[field]))
                
        return sanitized
