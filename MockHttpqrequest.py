import requests
import json
import time
import logging
from urllib.parse import urljoin
from requests.exceptions import RequestException
from typing import Dict, Optional, Union, Any, List, Tuple

class MockHttpRequest:
    """
    A utility class to simulate HTTP requests with support for:
    - Session management
    - Token-based authentication
    - Request retries
    - Response handling
    - Cookie management
    - Various content types
    """
    
    def __init__(self, base_url: str = "", timeout: int = 30, max_retries: int = 3, 
                 verify_ssl: bool = True, user_agent: Optional[str] = None):
        """
        Initialize the HTTP request simulator
        
        Args:
            base_url: Base URL for all requests (can be overridden in individual requests)
            timeout: Default timeout in seconds
            max_retries: Maximum number of retries for failed requests
            verify_ssl: Whether to verify SSL certificates
            user_agent: Custom User-Agent header
        """
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        # Initialize session
        self.session = requests.Session()
        # Set default headers
        self.default_headers = {
            'User-Agent': user_agent or 'MockHttpRequest/1.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.default_headers)
        
        # Authentication token
        self.auth_token = None
        self.token_type = None  # 'Bearer', 'Basic', etc.
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('MockHttpRequest')
    
    def set_token(self, token: str, token_type: str = "Bearer"):
        """
        Set the authentication token
        
        Args:
            token: The authentication token
            token_type: The token type (Bearer, Basic, etc.)
        """
        self.auth_token = token
        self.token_type = token_type
        self.session.headers['Authorization'] = f"{token_type} {token}"
        self.logger.info(f"Token set: {token_type} token")
    
    def clear_token(self):
        """Remove the authentication token"""
        self.auth_token = None
        self.token_type = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        self.logger.info("Token cleared")
    
    def _build_url(self, url: str) -> str:
        """Combine base_url and endpoint if needed"""
        if url.startswith(('http://', 'https://')):
            return url
        return urljoin(self.base_url, url)
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Prepare headers for the request, combining defaults and custom headers"""
        result = {}
        result.update(self.default_headers)
        if headers:
            result.update(headers)
        return result
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: The URL to request
            **kwargs: Additional parameters for the request
        
        Returns:
            requests.Response: The HTTP response
        
        Raises:
            RequestException: If the request fails after all retries
        """
        full_url = self._build_url(url)
        
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        # Set default SSL verification if not provided
        if 'verify' not in kwargs:
            kwargs['verify'] = self.verify_ssl
            
        # Prepare headers
        headers = kwargs.get('headers', {})
        kwargs['headers'] = self._prepare_headers(headers)
        
        attempt = 0
        last_exception = None
        
        while attempt < self.max_retries:
            attempt += 1
            try:
                self.logger.info(f"Request {method} to {full_url} (Attempt {attempt}/{self.max_retries})")
                response = self.session.request(method, full_url, **kwargs)
                
                # Log response status
                self.logger.info(f"Response: {response.status_code} {response.reason}")
                
                # Raise exception for 4xx and 5xx responses
                response.raise_for_status()
                
                return response
                
            except RequestException as e:
                last_exception = e
                self.logger.warning(f"Request failed: {e}")
                
                # Don't retry client errors (4xx) except for 429 Too Many Requests
                if hasattr(e, 'response') and e.response is not None:
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        self.logger.error(f"Client error: {e.response.status_code} {e.response.reason}")
                        raise
                
                # Wait before retrying
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
        
        # All retries failed
        self.logger.error(f"All {self.max_retries} retry attempts failed")
        raise last_exception

    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Send a GET request"""
        return self._make_request('GET', url, params=params, **kwargs)
    
    def post(self, url: str, data: Optional[Any] = None, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Send a POST request"""
        return self._make_request('POST', url, data=data, json=json, **kwargs)
    
    def put(self, url: str, data: Optional[Any] = None, **kwargs) -> requests.Response:
        """Send a PUT request"""
        return self._make_request('PUT', url, data=data, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """Send a DELETE request"""
        return self._make_request('DELETE', url, **kwargs)
    
    def patch(self, url: str, data: Optional[Any] = None, **kwargs) -> requests.Response:
        """Send a PATCH request"""
        return self._make_request('PATCH', url, data=data, **kwargs)
    
    def head(self, url: str, **kwargs) -> requests.Response:
        """Send a HEAD request"""
        return self._make_request('HEAD', url, **kwargs)
    
    def options(self, url: str, **kwargs) -> requests.Response:
        """Send an OPTIONS request"""
        return self._make_request('OPTIONS', url, **kwargs)
    
    def login(self, url: str, username: str, password: str, 
              token_field: str = 'token', 
              username_field: str = 'username', 
              password_field: str = 'password',
              auth_type: str = 'json',
              token_type: str = 'Bearer') -> Dict:
        """
        Perform a login request and extract the authentication token
        
        Args:
            url: Login endpoint
            username: Username for login
            password: Password for login
            token_field: JSON field containing the token in the response
            username_field: Form field for username
            password_field: Form field for password
            auth_type: Authentication type ('json', 'form', 'basic')
            token_type: Token type for the Authorization header
            
        Returns:
            Dict: Login response data
        """
        try:
            if auth_type.lower() == 'json':
                # JSON login
                data = {username_field: username, password_field: password}
                response = self.post(url, json=data)
                
            elif auth_type.lower() == 'form':
                # Form login
                data = {username_field: username, password_field: password}
                response = self.post(url, data=data)
                
            elif auth_type.lower() == 'basic':
                # Basic authentication
                response = self.post(url, auth=(username, password))
                
            else:
                raise ValueError(f"Unsupported auth_type: {auth_type}")
            
            # Extract response data
            response_data = response.json()
            
            # Extract token using token_field or nested path (e.g., 'data.token')
            token = response_data
            if '.' in token_field:
                for key in token_field.split('.'):
                    token = token.get(key, {})
            else:
                token = response_data.get(token_field)
            
            if token:
                self.set_token(token, token_type)
                self.logger.info("Login successful")
            else:
                self.logger.warning(f"Login successful but no token found in field '{token_field}'")
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise
    
    def simulate_browser_visit(self, url: str, referer: Optional[str] = None) -> requests.Response:
        """
        Simulate a browser visit to a webpage
        
        Args:
            url: URL to visit
            referer: Referer header to use
            
        Returns:
            requests.Response: The HTTP response
        """
        # Set browser-like headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if referer:
            headers['Referer'] = referer
            
        return self.get(url, headers=headers, allow_redirects=True)
    
    def download_file(self, url: str, filename: str, chunk_size: int = 8192, **kwargs) -> str:
        """
        Download a file from the specified URL
        
        Args:
            url: URL to download from
            filename: Path to save the file
            chunk_size: Size of chunks for downloading
            **kwargs: Additional parameters for the request
            
        Returns:
            str: Path to the downloaded file
        """
        response = self.get(url, stream=True, **kwargs)
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        self.logger.info(f"Downloading file from {url} to {filename}")
        
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress for large files
                    if total_size > chunk_size * 10 and downloaded % (chunk_size * 10) == 0:
                        percent = (downloaded / total_size) * 100
                        self.logger.info(f"Download progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
        
        self.logger.info(f"Download complete: {filename}")
        return filename
    
    def parse_html(self, response_or_url: Union[str, requests.Response]):
        """
        Parse HTML using BeautifulSoup
        
        Args:
            response_or_url: URL string or Response object
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            self.logger.error("BeautifulSoup is not installed. Install it with 'pip install beautifulsoup4'")
            raise ImportError("BeautifulSoup is required for HTML parsing")
        
        # Get the response if a URL was provided
        if isinstance(response_or_url, str):
            response = self.get(response_or_url)
        else:
            response = response_or_url
        
        # Parse the HTML
        return BeautifulSoup(response.text, 'html.parser')
    
    def clear_cookies(self):
        """Clear all cookies in the session"""
        self.session.cookies.clear()
        self.logger.info("Cookies cleared")
    
    def get_cookies(self) -> Dict:
        """Get all cookies as a dictionary"""
        return {cookie.name: cookie.value for cookie in self.session.cookies}
    
    def set_proxy(self, proxy: Dict[str, str]):
        """
        Set proxy for all requests
        
        Args:
            proxy: Proxy configuration (e.g., {'http': 'http://10.10.1.10:3128', 'https': 'http://10.10.1.10:1080'})
        """
        self.session.proxies.update(proxy)
        self.logger.info(f"Proxy set: {proxy}")

    def close(self):
        """Close the session"""
        self.session.close()
        self.logger.info("Session closed")
        

# Usage example
if __name__ == "__main__":
    # Example 1: Basic GET request
    http = MockHttpRequest(base_url="https://api.example.com")
    try:
        response = http.get("/users")
        users = response.json()
        print(f"Users: {users}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Login with token
    try:
        login_data = http.login(
            url="/login",
            username="user123",
            password="password123",
            token_field="access_token"
        )
        print(f"Logged in, token: {http.auth_token}")
        
        # Make authenticated request
        profile = http.get("/me").json()
        print(f"Profile: {profile}")
    except Exception as e:
        print(f"Login error: {e}")
    
    # Example 3: Simulate browser visit
    browser = MockHttpRequest()
    try:
        response = browser.simulate_browser_visit("https://example.com")
        print(f"Page title: {browser.parse_html(response).title.text}")
        
        # Download a file
        browser.download_file("https://example.com/file.pdf", "downloaded_file.pdf")
    except Exception as e:
        print(f"Browser simulation error: {e}")
    
    # Close sessions
    http.close()
    browser.close()