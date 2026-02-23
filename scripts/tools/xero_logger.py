"""
Xero Logger - Logs completed tasks as Manual Journals in Xero Accounting.

This module integrates with Xero API to create financial records for completed
business operations. Each task completion is logged as a Manual Journal entry
for tracking and accounting purposes.

Features:
- Auto-fetches XERO_TENANT_ID from API connections endpoint
- Saves discovered tenant ID to .env file
- Logs Manual Journals and Invoices

Usage:
    from scripts.tools.xero_logger import XeroLogger
    
    logger = XeroLogger()
    result = logger.log_task_completion(
        task_name="Social Media Post",
        description="Posted about AI automation to Discord",
        amount=0.00,
        account_code="400"
    )
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

try:
    import requests
    XERO_AVAILABLE = True
except ImportError:
    XERO_AVAILABLE = False
    logger.warning("requests library not available. Xero logging will use mock mode.")

from scripts.config import XERO_CREDENTIALS, VAULT_PATH


class XeroLogger:
    """
    Handles logging of task completions to Xero Accounting.
    
    Creates Manual Journal entries for each completed task,
    enabling financial tracking of automated work.
    """
    
    XERO_API_BASE = "https://api.xero.com/api.xro/2.0"
    XERO_AUTH_BASE = "https://identity.xero.com"
    
    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize the Xero Logger.
        
        Args:
            tenant_id: Optional Xero tenant ID. If not provided, uses config or auto-fetches.
        """
        self.tenant_id = tenant_id or XERO_CREDENTIALS.get('tenant_id', '')
        self.client_id = XERO_CREDENTIALS.get('client_id', '')
        self.client_secret = XERO_CREDENTIALS.get('client_secret', '')
        self.access_token = None
        self.refresh_token = None
        
        # Auto-fetch tenant ID if not provided but credentials exist
        if not self.tenant_id and all([self.client_id, self.client_secret]):
            logger.info("Tenant ID not found, attempting to auto-fetch...")
            self._auto_fetch_tenant_id()
        
        self._mock_mode = not all([self.client_id, self.client_secret, self.tenant_id])
        
        if self._mock_mode:
            logger.info("Xero Logger initialized in MOCK mode (missing credentials)")
        else:
            logger.info("Xero Logger initialized with tenant: %s", self.tenant_id[:8] + "...")
    
    def _get_basic_auth(self) -> str:
        """
        Create Basic Auth header for Xero OAuth2 token request.
        
        Returns:
            Base64 encoded auth string
        """
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _auto_fetch_tenant_id(self) -> bool:
        """
        Automatically fetch tenant ID from Xero connections endpoint.
        
        Uses client credentials to get an access token, then fetches connections.
        Saves the discovered tenant ID to .env file.
        
        Returns:
            True if tenant ID was successfully fetched and saved
        """
        logger.info("Fetching tenant ID from Xero connections endpoint...")
        
        try:
            # Step 1: Get access token using client credentials flow
            token_url = f"{self.XERO_AUTH_BASE}/connect/token"
            
            headers = {
                "Authorization": self._get_basic_auth(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "openid profile email accounting.transactions"
            }
            
            token_response = requests.post(token_url, headers=headers, data=data, timeout=30)
            token_response.raise_for_status()
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("No access token received from Xero")
                return False
            
            logger.info("Access token obtained successfully")
            
            # Step 2: Fetch connections to get tenant ID
            connections_url = "https://api.xero.com/connections"
            auth_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            connections_response = requests.get(connections_url, headers=auth_headers, timeout=30)
            connections_response.raise_for_status()
            
            connections = connections_response.json()
            
            if not connections:
                logger.error("No Xero connections found")
                return False
            
            # Get the first connection's tenant ID
            self.tenant_id = connections[0].get("tenantId")
            
            if not self.tenant_id:
                logger.error("No tenant ID found in connections")
                return False
            
            logger.info("Tenant ID discovered: %s", self.tenant_id[:8] + "...")
            
            # Step 3: Save tenant ID to .env file
            self._save_tenant_to_env()
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch tenant ID: %s", str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error fetching tenant ID: %s", str(e))
            return False
    
    def _save_tenant_to_env(self) -> bool:
        """
        Save the discovered tenant ID to the .env file.
        
        Returns:
            True if successfully saved
        """
        if not self.tenant_id:
            return False
        
        # Find .env file in project root
        env_path = VAULT_PATH / ".env"
        
        if not env_path.exists():
            logger.warning(".env file not found at %s", env_path)
            return False
        
        try:
            # Read current .env content
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update or add XERO_TENANT_ID
            if "XERO_TENANT_ID=" in content:
                # Replace existing value
                import re
                content = re.sub(
                    r'XERO_TENANT_ID=.*',
                    f'XERO_TENANT_ID={self.tenant_id}',
                    content
                )
                logger.info("Updated XERO_TENANT_ID in .env file")
            else:
                # Add new line
                content += f"\nXERO_TENANT_ID={self.tenant_id}\n"
                logger.info("Added XERO_TENANT_ID to .env file")
            
            # Write back
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Tenant ID saved to .env file: %s", env_path)
            return True
            
        except Exception as e:
            logger.error("Failed to save tenant ID to .env: %s", str(e))
            return False
    
    def _get_access_token(self) -> Optional[str]:
        """
        Obtain or refresh access token for Xero API.
        
        In production, implement proper OAuth2 flow with token storage.
        For now, this returns a mock token or uses client credentials flow.
        
        Returns:
            Access token string or None if authentication fails
        """
        if self._mock_mode:
            return "mock_access_token"
        
        # Try to fetch tenant ID if not available
        if not self.tenant_id:
            self._fetch_tenant_id()
            if not self.tenant_id:
                print("\n⚠️  Xero Authorization Required")
                print("Please visit http://localhost:8080 to authorize Xero")
                print("(OAuth2 handshake needed for first-time setup)\n")
                return None
        
        # TODO: Implement proper OAuth2 flow
        # For manual journal creation, you may use a stored access token
        # or implement the full OAuth2 authorization code flow
        
        logger.warning("OAuth2 flow not implemented. Please provide access_token manually.")
        return None
    
    def _fetch_tenant_id(self) -> bool:
        """
        Fetch tenant ID from Xero connections endpoint.
        
        Uses client credentials to get an access token, then fetches connections.
        Saves the discovered tenant ID to .env file.
        
        Returns:
            True if tenant ID was successfully fetched
        """
        if not all([self.client_id, self.client_secret]):
            logger.warning("Xero client credentials not configured")
            return False
        
        logger.info("Fetching tenant ID from Xero connections endpoint...")
        
        try:
            # Step 1: Get access token using client credentials flow
            token_url = f"{self.XERO_AUTH_BASE}/connect/token"
            
            headers = {
                "Authorization": self._get_basic_auth(),
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials",
                "scope": "openid profile email accounting.transactions"
            }
            
            token_response = requests.post(token_url, headers=headers, data=data, timeout=30)
            token_response.raise_for_status()
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("No access token received from Xero")
                return False
            
            logger.info("Access token obtained successfully")
            
            # Step 2: Fetch connections to get tenant ID
            connections_url = "https://api.xero.com/connections"
            auth_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            connections_response = requests.get(connections_url, headers=auth_headers, timeout=30)
            connections_response.raise_for_status()
            
            connections = connections_response.json()
            
            if not connections:
                logger.error("No Xero connections found")
                print("\n⚠️  No Xero connections found")
                print("Please visit http://localhost:8080 to authorize Xero")
                print("(Connect your Xero organization first)\n")
                return False
            
            # Get the first connection's tenant ID
            self.tenant_id = connections[0].get("tenantId")
            
            if not self.tenant_id:
                logger.error("No tenant ID found in connections")
                return False
            
            logger.info("Tenant ID discovered: %s", self.tenant_id[:8] + "...")
            
            # Step 3: Save tenant ID to .env file
            self._save_tenant_to_env()
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch tenant ID: %s", str(e))
            print(f"\n⚠️  Failed to connect to Xero: {str(e)}")
            print("Please visit http://localhost:8080 to authorize Xero\n")
            return False
        except Exception as e:
            logger.error("Unexpected error fetching tenant ID: %s", str(e))
            return False
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an authenticated request to Xero API.
        
        Args:
            method: HTTP method (GET, POST, PUT)
            endpoint: API endpoint path
            data: Optional JSON data for request body
            
        Returns:
            Response JSON as dict or None if request fails
        """
        if self._mock_mode:
            logger.info("MOCK Xero API call: %s %s", method, endpoint)
            logger.info("MOCK Data: %s", data)
            return {"success": True, "mock": True}
        
        access_token = self._get_access_token()
        if not access_token:
            logger.error("Failed to obtain Xero access token")
            return None
        
        url = f"{self.XERO_API_BASE}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Xero-tenant-id": self.tenant_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                logger.error("Unsupported HTTP method: %s", method)
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error("Xero API request failed: %s", str(e))
            return None
        except Exception as e:
            logger.error("Unexpected error during Xero API call: %s", str(e))
            return None
    
    def log_manual_journal(
        self,
        task_name: str,
        description: str,
        amount: float = 0.00,
        account_code: str = "400",
        reference: Optional[str] = None,
        narration: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a task completion as a Manual Journal in Xero.
        
        Args:
            task_name: Name of the completed task
            description: Detailed description of the work performed
            amount: Monetary value of the task (default: 0.00 for internal tracking)
            account_code: Xero account code (default: "400" for revenue)
            reference: Optional reference number
            narration: Optional narration for the journal
            
        Returns:
            Dict with success status and journal details
        """
        timestamp = datetime.now()
        journal_date = timestamp.strftime("%Y-%m-%d")
        
        if not reference:
            reference = f"TASK-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        
        if not narration:
            narration = f"Automated Task: {task_name}"
        
        # Construct Manual Journal payload
        # Xero Manual Journals require balanced debits and credits
        journal_lines = [
            {
                "LineAmount": abs(amount),
                "AccountCode": account_code,
                "Description": description,
                "LineType": "Revenue"
            }
        ]
        
        # Add balancing line if amount is non-zero
        if amount != 0:
            # Use a suspense account for balancing (configure as needed)
            journal_lines.append({
                "LineAmount": -abs(amount),
                "AccountCode": "200",  # Suspense/Liabilities account
                "Description": f"Balancing entry for {task_name}",
                "LineType": "Liability"
            })
        
        journal_payload = {
            "ManualJournals": [
                {
                    "Narration": narration,
                    "JournalDate": journal_date,
                    "LineAmountTypes": "Exclusive",
                    "Status": "DRAFT",  # Use DRAFT for review before posting
                    "Reference": reference,
                    "JournalLines": journal_lines
                }
            ]
        }
        
        logger.info("Creating Manual Journal: %s", reference)
        logger.debug("Journal payload: %s", journal_payload)
        
        result = self._make_request("POST", "/ManualJournals", journal_payload)
        
        if result:
            journal_id = result.get("ManualJournals", [{}])[0].get("ManualJournalID", "unknown")
            logger.info("Manual Journal created successfully: %s", journal_id)
            
            return {
                "success": True,
                "journal_id": journal_id,
                "reference": reference,
                "task_name": task_name,
                "amount": amount,
                "status": "DRAFT",
                "mock": result.get("mock", False)
            }
        else:
            logger.error("Failed to create Manual Journal in Xero")
            return {
                "success": False,
                "error": "Failed to create Manual Journal",
                "reference": reference,
                "task_name": task_name
            }
    
    def log_invoice(
        self,
        task_name: str,
        description: str,
        amount: float,
        contact_name: str = "Internal Tracking",
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a task completion as an Invoice in Xero.
        
        Use this for billable client work.
        
        Args:
            task_name: Name of the completed task
            description: Description of services provided
            amount: Invoice amount (excluding tax)
            contact_name: Client/contact name
            reference: Optional invoice reference
            
        Returns:
            Dict with success status and invoice details
        """
        timestamp = datetime.now()
        invoice_date = timestamp.strftime("%Y-%m-%d")
        
        if not reference:
            reference = f"INV-{timestamp.strftime('%Y%m%d-%H%M%S')}"
        
        if self._mock_mode:
            logger.info("MOCK Invoice creation: %s for %s - $%.2f", 
                       reference, task_name, amount)
            return {
                "success": True,
                "invoice_id": "mock_invoice_id",
                "reference": reference,
                "amount": amount,
                "contact": contact_name,
                "mock": True
            }
        
        # Construct Invoice payload
        invoice_payload = {
            "Invoices": [
                {
                    "Type": "ACCREC",  # Accounts Receivable
                    "Contact": {"Name": contact_name},
                    "Date": invoice_date,
                    "Reference": reference,
                    "LineItems": [
                        {
                            "Description": f"{task_name}: {description}",
                            "Quantity": 1,
                            "UnitAmount": amount,
                            "AccountCode": "400"
                        }
                    ],
                    "Status": "DRAFT"  # Draft for review
                }
            ]
        }
        
        logger.info("Creating Invoice: %s for %s", reference, contact_name)
        
        result = self._make_request("POST", "/Invoices", invoice_payload)
        
        if result:
            invoice_id = result.get("Invoices", [{}])[0].get("InvoiceID", "unknown")
            invoice_number = result.get("Invoices", [{}])[0].get("InvoiceNumber", reference)
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "invoice_number": invoice_number,
                "reference": reference,
                "amount": amount,
                "contact": contact_name,
                "status": "DRAFT"
            }
        else:
            logger.error("Failed to create Invoice in Xero")
            return {
                "success": False,
                "error": "Failed to create Invoice",
                "reference": reference
            }
    
    def log_task_completion(
        self,
        task_name: str,
        description: str,
        amount: float = 0.00,
        log_type: str = "journal"
    ) -> Dict[str, Any]:
        """
        Unified method to log task completion.
        
        Args:
            task_name: Name of the completed task
            description: Description of work performed
            amount: Optional monetary value
            log_type: "journal" for Manual Journal, "invoice" for Invoice
            
        Returns:
            Dict with logging result
        """
        if log_type == "invoice" and amount > 0:
            return self.log_invoice(task_name, description, amount)
        else:
            return self.log_manual_journal(task_name, description, amount)


# Convenience function for quick logging
def log_task(
    task_name: str,
    description: str,
    amount: float = 0.00,
    log_type: str = "journal"
) -> Dict[str, Any]:
    """
    Quick function to log a task completion to Xero.
    
    Args:
        task_name: Name of the completed task
        description: Description of work performed
        amount: Optional monetary value
        log_type: "journal" or "invoice"
        
    Returns:
        Dict with logging result
    """
    xero_logger = XeroLogger()
    return xero_logger.log_task_completion(task_name, description, amount, log_type)


if __name__ == "__main__":
    # Test the Xero Logger
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Xero Logger...")
    xero = XeroLogger()
    
    # Test Manual Journal
    result = xero.log_manual_journal(
        task_name="Social Media Management",
        description="Posted content to Discord and Twitter/X",
        amount=25.00,
        reference="TEST-001"
    )
    print(f"Manual Journal Result: {result}")
    
    # Test Invoice
    result = xero.log_invoice(
        task_name="Content Creation",
        description="Created and published blog post",
        amount=150.00,
        contact_name="Test Client"
    )
    print(f"Invoice Result: {result}")
