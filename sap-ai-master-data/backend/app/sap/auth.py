"""
SAP Business One Service Layer Authentication Manager.
Manages B1SESSION cookie, ROUTEID, and automatic session renewal without leaking credentials.
Provides transparent connection diagnostics and prevents indefinite hangs when SAP is unreachable.
"""
from typing import Any, Dict, Optional, Tuple
import time
import httpx
from app.config import settings
from app.utils.logging import logger

class SAPAuthManager:
    def __init__(self):
        self._session_cookies: Dict[str, str] = {}
        self._is_authenticated: bool = False
        self._session_timeout_minutes: int = 30
        self._last_auth_time: float = 0.0
        self._last_error: Optional[str] = None
        self._last_error_code: Optional[str] = None
        self._last_latency_ms: Optional[float] = None

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated and "B1SESSION" in self._session_cookies

    def get_cookies(self) -> Dict[str, str]:
        return dict(self._session_cookies)

    async def login(
        self,
        client: httpx.AsyncClient,
        custom_timeout: Optional[float] = None,
        override_creds: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Authenticate against SAP Service Layer:
        POST {SAP_SERVICE_LAYER_URL}/Login
        Payload: { "CompanyDB": "...", "UserName": "...", "Password": "..." }
        Returns (success: bool, message: str, diagnostics: dict).
        """
        url = (override_creds.get("service_layer_url") if override_creds else None) or settings.sap_service_layer_url
        company_db = (override_creds.get("company_db") if override_creds else None) or settings.sap_company_db
        username = (override_creds.get("username") if override_creds else None) or settings.sap_username
        password = (override_creds.get("password") if override_creds else None) or settings.sap_password

        # Validate configuration presence
        is_configured = (
            bool(url)
            and "YOUR_SAP_SERVER" not in url
            and bool(company_db)
            and bool(username)
            and bool(password)
            and password != "YOUR_SAP_PASSWORD"
        )

        if not is_configured:
            msg = "SAP Service Layer credentials not configured (placeholder values detected)."
            self._last_error = msg
            self._last_error_code = "UNCONFIGURED"
            return False, msg, {
                "status": "UNCONFIGURED",
                "error_code": "UNCONFIGURED",
                "latency_ms": 0,
                "url": url or "Not configured"
            }

        login_url = f"{url.rstrip('/')}/Login"
        payload = {
            "CompanyDB": company_db,
            "UserName": username,
            "Password": password
        }

        req_headers: Dict[str, str] = {}
        if "103.89.45.237" in url and ":50000" in url:
            req_headers["Host"] = "CINNTRA-DEMO:50000"

        login_timeout = custom_timeout or min(settings.sap_timeout_seconds, 15.0)
        t_start = time.time()

        for attempt in range(1, 3):
            try:
                logger.info(f"Probing SAP Service Layer login at {url} (CompanyDB: {company_db}, attempt {attempt}) with timeout {login_timeout}s")
                response = await client.post(
                    login_url,
                    json=payload,
                    headers=req_headers,
                    timeout=login_timeout
                )
                latency_ms = round((time.time() - t_start) * 1000, 1)
                self._last_latency_ms = latency_ms

                if response.status_code == 200:
                    self._session_cookies = dict(response.cookies)
                    self._is_authenticated = True
                    self._last_auth_time = time.time()
                    self._last_error = None
                    self._last_error_code = None
                    data = response.json() if response.content else {}
                    self._session_timeout_minutes = data.get("SessionTimeout", 30)
                    logger.info(f"SAP Service Layer authenticated successfully in {latency_ms}ms")
                    return True, "SAP authentication successful.", {
                        "status": "CONNECTED",
                        "http_status": 200,
                        "latency_ms": latency_ms,
                        "session_timeout_min": self._session_timeout_minutes
                    }
                else:
                    self._is_authenticated = False
                    err_msg = f"SAP Login rejected by server with HTTP {response.status_code}"
                    sap_detail = ""
                    try:
                        err_json = response.json()
                        if "error" in err_json:
                            sap_detail = err_json["error"].get("message", {}).get("value", "")
                            if sap_detail:
                                err_msg += f": {sap_detail}"
                    except Exception:
                        pass
                    self._last_error = err_msg
                    self._last_error_code = "AUTH_FAILED" if response.status_code == 401 else f"HTTP_{response.status_code}"
                    logger.warning(f"SAP Login error: {err_msg}")
                    return False, err_msg, {
                        "status": "AUTH_FAILED" if response.status_code == 401 else "SERVER_ERROR",
                        "http_status": response.status_code,
                        "latency_ms": latency_ms,
                        "error_code": self._last_error_code,
                        "detail": sap_detail
                    }
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                if attempt == 1:
                    logger.warning(f"SAP login attempt 1 timed out or dropped ({exc}), retrying...")
                    continue
                latency_ms = round((time.time() - t_start) * 1000, 1)
                self._is_authenticated = False
                msg = f"SAP Service Layer connection failed after retries: {str(exc)}"
                self._last_error = msg
                self._last_error_code = "TIMEOUT" if isinstance(exc, httpx.TimeoutException) else "CONNECT_ERROR"
                logger.warning(f"SAP login error: {msg}")
                return False, msg, {
                    "status": "TIMEOUT" if isinstance(exc, httpx.TimeoutException) else "DISCONNECTED",
                    "error_code": self._last_error_code,
                    "latency_ms": latency_ms,
                    "url": url
                }
            except Exception as e:
                latency_ms = round((time.time() - t_start) * 1000, 1)
                self._is_authenticated = False
                msg = f"Unexpected error connecting to SAP: {str(e)}"
                self._last_error = msg
                self._last_error_code = "ERROR"
                logger.error(msg)
                return False, msg, {
                    "status": "DISCONNECTED",
                    "error_code": "ERROR",
                    "latency_ms": latency_ms,
                    "detail": str(e)
                }

        return False, "Failed to authenticate with SAP Service Layer", {"status": "DISCONNECTED"}

    async def logout(self, client: httpx.AsyncClient) -> None:
        """Logout and invalidate current SAP session."""
        if not self._is_authenticated:
            return
        try:
            logout_url = f"{settings.sap_service_layer_url.rstrip('/')}/Logout"
            await client.post(logout_url, cookies=self._session_cookies, timeout=3.0)
        except Exception:
            pass
        finally:
            self._session_cookies.clear()
            self._is_authenticated = False
            logger.info("SAP session cleared")
