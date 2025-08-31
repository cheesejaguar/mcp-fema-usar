"""Authentication and authorization module for FEMA USAR MCP.

Provides secure authentication, role-based access control, and session management
for FEMA USAR personnel with integration to federal identity systems.
"""

import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class USARRole(Enum):
    """FEMA USAR role hierarchy."""

    TASK_FORCE_LEADER = "task_force_leader"
    DEPUTY_TF_LEADER = "deputy_tf_leader"
    SAFETY_OFFICER = "safety_officer"
    INFORMATION_OFFICER = "information_officer"
    LIAISON_OFFICER = "liaison_officer"
    OPERATIONS_CHIEF = "operations_chief"
    PLANNING_CHIEF = "planning_chief"
    LOGISTICS_CHIEF = "logistics_chief"
    FINANCE_CHIEF = "finance_chief"
    SEARCH_TEAM_MANAGER = "search_team_manager"
    RESCUE_TEAM_MANAGER = "rescue_team_manager"
    MEDICAL_TEAM_MANAGER = "medical_team_manager"
    TECHNICAL_SPECIALIST = "technical_specialist"
    TEAM_MEMBER = "team_member"
    SUPPORT_PERSONNEL = "support_personnel"
    OBSERVER = "observer"


class SecurityClearance(Enum):
    """Federal security clearance levels."""

    PUBLIC = "public"
    OFFICIAL_USE = "official_use_only"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class AuthenticationMethod(Enum):
    """Authentication methods supported."""

    PASSWORD = "password"
    PIV_CARD = "piv_card"
    CAC_CARD = "cac_card"
    BIOMETRIC = "biometric"
    TWO_FACTOR = "two_factor"


class USARUser(BaseModel):
    """FEMA USAR user model."""

    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    usar_role: USARRole = Field(..., description="USAR role")
    security_clearance: SecurityClearance = Field(
        ..., description="Security clearance level"
    )
    task_force_id: str | None = Field(None, description="Task force assignment")
    agency: str = Field(..., description="Employing agency")
    badge_number: str | None = Field(None, description="Badge/ID number")
    piv_card_id: str | None = Field(None, description="PIV card identifier")
    phone: str | None = Field(None, description="Phone number")
    emergency_contact: dict[str, str] | None = Field(
        None, description="Emergency contact"
    )
    certifications: list[str] = Field(
        default_factory=list, description="Certifications held"
    )
    last_training: datetime | None = Field(None, description="Last training date")
    active: bool = Field(True, description="Account active status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_login: datetime | None = Field(None, description="Last login timestamp")
    failed_attempts: int = Field(0, description="Failed login attempts")
    locked_until: datetime | None = Field(None, description="Account locked until")

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()


class AuthToken(BaseModel):
    """Authentication token model."""

    token_id: str = Field(..., description="Unique token identifier")
    user_id: str = Field(..., description="Associated user ID")
    token_type: str = Field(..., description="Token type (access/refresh)")
    expires_at: datetime = Field(..., description="Token expiration")
    permissions: list[str] = Field(
        default_factory=list, description="Token permissions"
    )
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    revoked: bool = Field(False, description="Token revoked status")


class SecurityConfig:
    """Security configuration settings."""

    def __init__(self):
        self.JWT_SECRET_KEY = self._get_secret_key()
        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days
        self.PASSWORD_RESET_EXPIRE_MINUTES = 15
        self.MAX_LOGIN_ATTEMPTS = 3
        self.ACCOUNT_LOCKOUT_MINUTES = 30
        self.ENCRYPTION_KEY = self._get_encryption_key()
        self.SESSION_TIMEOUT_MINUTES = 120  # 2 hours
        self.REQUIRE_2FA = True
        self.MINIMUM_PASSWORD_LENGTH = 12
        self.PASSWORD_COMPLEXITY_REQUIRED = True

    def _get_secret_key(self) -> str:
        """Get or generate JWT secret key."""
        import os

        secret = os.getenv("JWT_SECRET")
        if not secret:
            secret = secrets.token_urlsafe(32)
            logger.warning(
                "Using generated JWT secret key - set JWT_SECRET environment variable"
            )
        return secret

    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        import os

        key = os.getenv("ENCRYPTION_KEY")
        if key:
            return key.encode()
        else:
            key = Fernet.generate_key()
            logger.warning(
                "Using generated encryption key - set ENCRYPTION_KEY environment variable"
            )
            return key


class PasswordManager:
    """Secure password management."""

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a password securely.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Stored password hash

        Returns:
            True if password matches
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> dict[str, Any]:
        """Validate password strength requirements.

        Args:
            password: Password to validate

        Returns:
            Validation result with details
        """
        validation = {"valid": True, "score": 0, "issues": []}

        # Length requirement
        if len(password) < 12:
            validation["valid"] = False
            validation["issues"].append("Password must be at least 12 characters long")
        else:
            validation["score"] += 1

        # Character diversity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not has_upper:
            validation["valid"] = False
            validation["issues"].append("Password must contain uppercase letters")
        else:
            validation["score"] += 1

        if not has_lower:
            validation["valid"] = False
            validation["issues"].append("Password must contain lowercase letters")
        else:
            validation["score"] += 1

        if not has_digit:
            validation["valid"] = False
            validation["issues"].append("Password must contain numbers")
        else:
            validation["score"] += 1

        if not has_special:
            validation["valid"] = False
            validation["issues"].append("Password must contain special characters")
        else:
            validation["score"] += 1

        # Common password checks
        common_patterns = ["password", "123456", "qwerty", "admin", "usar", "fema"]
        if any(pattern in password.lower() for pattern in common_patterns):
            validation["valid"] = False
            validation["issues"].append("Password contains common patterns")
            validation["score"] -= 2

        return validation


class JWTManager:
    """JWT token management."""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.encryption = Fernet(config.ENCRYPTION_KEY)

    def create_access_token(self, user: USARUser, permissions: list[str] = None) -> str:
        """Create JWT access token.

        Args:
            user: User object
            permissions: Additional permissions

        Returns:
            JWT access token
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.usar_role.value,
            "clearance": user.security_clearance.value,
            "task_force": user.task_force_id,
            "permissions": permissions or [],
            "iat": now,
            "exp": expire,
            "type": "access",
        }

        token = jwt.encode(
            payload, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM
        )
        return token

    def create_refresh_token(self, user: USARUser) -> str:
        """Create JWT refresh token.

        Args:
            user: User object

        Returns:
            JWT refresh token
        """
        now = datetime.now(UTC)
        expire = now + timedelta(days=self.config.REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {"sub": user.user_id, "iat": now, "exp": expire, "type": "refresh"}

        token = jwt.encode(
            payload, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM
        )
        return token

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.config.JWT_SECRET_KEY,
                algorithms=[self.config.JWT_ALGORITHM],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token")

    def refresh_access_token(self, refresh_token: str, user: USARUser) -> str:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token
            user: User object

        Returns:
            New access token
        """
        payload = self.verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise jwt.InvalidTokenError("Invalid refresh token")

        if payload.get("sub") != user.user_id:
            raise jwt.InvalidTokenError("Token user mismatch")

        return self.create_access_token(user)


class TwoFactorAuth:
    """Two-factor authentication management."""

    def __init__(self):
        self.totp_issuer = "FEMA-USAR-MCP"

    def generate_secret(self, user: USARUser) -> str:
        """Generate TOTP secret for user.

        Args:
            user: User object

        Returns:
            Base32 encoded secret
        """
        import pyotp

        secret = pyotp.random_base32()
        return secret

    def generate_qr_code_url(self, user: USARUser, secret: str) -> str:
        """Generate QR code URL for TOTP setup.

        Args:
            user: User object
            secret: TOTP secret

        Returns:
            QR code provisioning URL
        """
        import pyotp

        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user.email, issuer_name=self.totp_issuer)

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token.

        Args:
            secret: User's TOTP secret
            token: TOTP token to verify

        Returns:
            True if token is valid
        """
        import pyotp

        totp = pyotp.TOTP(secret)
        return totp.verify(token)


class SecurityAuditLogger:
    """Security event audit logging."""

    def __init__(self):
        self.logger = logging.getLogger("security.audit")

    def log_login_attempt(
        self,
        username: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        method: AuthenticationMethod,
    ):
        """Log login attempt.

        Args:
            username: Username attempted
            success: Whether login succeeded
            ip_address: Client IP address
            user_agent: Client user agent
            method: Authentication method used
        """
        event = {
            "event_type": "login_attempt",
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "auth_method": method.value,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Login attempt: {json.dumps(event)}")

    def log_permission_denied(
        self, user_id: str, resource: str, action: str, ip_address: str
    ):
        """Log access denied event.

        Args:
            user_id: User identifier
            resource: Resource accessed
            action: Action attempted
            ip_address: Client IP address
        """
        event = {
            "event_type": "access_denied",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.logger.warning(f"Access denied: {json.dumps(event)}")

    def log_privilege_escalation(
        self, user_id: str, from_role: str, to_role: str, authorized_by: str
    ):
        """Log privilege escalation event.

        Args:
            user_id: User identifier
            from_role: Previous role
            to_role: New role
            authorized_by: Who authorized the change
        """
        event = {
            "event_type": "privilege_escalation",
            "user_id": user_id,
            "from_role": from_role,
            "to_role": to_role,
            "authorized_by": authorized_by,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.logger.warning(f"Privilege escalation: {json.dumps(event)}")


class RoleBasedAccessControl:
    """Role-based access control system."""

    def __init__(self):
        self.permissions = self._initialize_permissions()

    def _initialize_permissions(self) -> dict[USARRole, list[str]]:
        """Initialize role-based permissions matrix.

        Returns:
            Role permissions mapping
        """
        return {
            USARRole.TASK_FORCE_LEADER: [
                "command:*",
                "operations:*",
                "planning:*",
                "logistics:*",
                "search:*",
                "rescue:*",
                "medical:*",
                "technical:*",
                "personnel:manage",
                "resources:manage",
                "reports:create",
                "communications:manage",
                "safety:override",
            ],
            USARRole.DEPUTY_TF_LEADER: [
                "command:read",
                "operations:manage",
                "planning:manage",
                "logistics:manage",
                "search:*",
                "rescue:*",
                "medical:*",
                "personnel:manage",
                "resources:manage",
                "reports:create",
            ],
            USARRole.SAFETY_OFFICER: [
                "safety:*",
                "personnel:read",
                "operations:read",
                "hazmat:*",
                "environmental:*",
                "reports:create",
                "communications:read",
                "emergency:declare",
            ],
            USARRole.OPERATIONS_CHIEF: [
                "operations:*",
                "search:*",
                "rescue:*",
                "medical:manage",
                "personnel:manage",
                "resources:manage",
                "tactical:*",
                "communications:manage",
            ],
            USARRole.PLANNING_CHIEF: [
                "planning:*",
                "reports:*",
                "documentation:*",
                "intelligence:*",
                "maps:*",
                "weather:read",
                "resources:read",
                "personnel:read",
            ],
            USARRole.LOGISTICS_CHIEF: [
                "logistics:*",
                "supplies:*",
                "equipment:*",
                "maintenance:*",
                "facilities:*",
                "transportation:*",
                "communications:manage",
            ],
            USARRole.SEARCH_TEAM_MANAGER: [
                "search:*",
                "personnel:read",
                "equipment:read",
                "maps:read",
                "communications:read",
                "reports:create",
            ],
            USARRole.RESCUE_TEAM_MANAGER: [
                "rescue:*",
                "personnel:read",
                "equipment:read",
                "structural:read",
                "communications:read",
                "reports:create",
            ],
            USARRole.MEDICAL_TEAM_MANAGER: [
                "medical:*",
                "triage:*",
                "supplies:medical",
                "personnel:read",
                "communications:read",
                "reports:create",
            ],
            USARRole.TECHNICAL_SPECIALIST: [
                "technical:*",
                "structural:*",
                "hazmat:read",
                "communications:technical",
                "reports:create",
            ],
            USARRole.TEAM_MEMBER: [
                "operations:read",
                "personnel:read",
                "equipment:read",
                "communications:read",
                "safety:read",
            ],
            USARRole.SUPPORT_PERSONNEL: [
                "logistics:read",
                "supplies:read",
                "facilities:read",
                "communications:read",
            ],
            USARRole.OBSERVER: ["read:*"],
        }

    def check_permission(self, role: USARRole, permission: str) -> bool:
        """Check if role has specific permission.

        Args:
            role: User role
            permission: Permission to check

        Returns:
            True if permission granted
        """
        user_permissions = self.permissions.get(role, [])

        # Check exact permission match
        if permission in user_permissions:
            return True

        # Check wildcard permissions
        for perm in user_permissions:
            if perm.endswith("*"):
                prefix = perm[:-1]
                if permission.startswith(prefix):
                    return True

        return False

    def get_user_permissions(self, role: USARRole) -> list[str]:
        """Get all permissions for role.

        Args:
            role: User role

        Returns:
            List of permissions
        """
        return self.permissions.get(role, [])


class USARAuthenticationManager:
    """Main authentication manager for FEMA USAR MCP."""

    def __init__(self):
        self.config = SecurityConfig()
        self.password_mgr = PasswordManager()
        self.jwt_mgr = JWTManager(self.config)
        self.two_factor = TwoFactorAuth()
        self.audit_logger = SecurityAuditLogger()
        self.rbac = RoleBasedAccessControl()
        self._user_store: dict[str, USARUser] = {}
        self._sessions: dict[str, dict[str, Any]] = {}

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        usar_role: USARRole,
        security_clearance: SecurityClearance,
        task_force_id: str | None = None,
        agency: str = "FEMA",
    ) -> USARUser:
        """Register new USAR user.

        Args:
            username: Unique username
            email: Email address
            password: Password
            full_name: Full name
            usar_role: USAR role
            security_clearance: Security clearance level
            task_force_id: Task force assignment
            agency: Employing agency

        Returns:
            Created user object
        """
        # Validate password strength
        password_validation = self.password_mgr.validate_password_strength(password)
        if not password_validation["valid"]:
            raise ValueError(
                f"Password validation failed: {', '.join(password_validation['issues'])}"
            )

        # Hash password
        hashed_password = self.password_mgr.hash_password(password)

        # Create user
        user = USARUser(
            user_id=self._generate_user_id(),
            username=username,
            email=email,
            full_name=full_name,
            usar_role=usar_role,
            security_clearance=security_clearance,
            task_force_id=task_force_id,
            agency=agency,
        )

        # Store user (in production, this would be a database)
        self._user_store[username] = user

        logger.info(f"Registered new USAR user: {username} ({usar_role.value})")
        return user

    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
    ) -> USARUser | None:
        """Authenticate user credentials.

        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            User object if authentication successful, None otherwise
        """
        user = self._user_store.get(username)

        if not user or not user.active:
            self.audit_logger.log_login_attempt(
                username, False, ip_address, user_agent, AuthenticationMethod.PASSWORD
            )
            return None

        # Check account lockout
        if user.locked_until and datetime.now(UTC) < user.locked_until:
            self.audit_logger.log_login_attempt(
                username, False, ip_address, user_agent, AuthenticationMethod.PASSWORD
            )
            return None

        # Verify password (simplified - would check against stored hash)
        if not self._verify_stored_password(username, password):
            user.failed_attempts += 1
            if user.failed_attempts >= self.config.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(UTC) + timedelta(
                    minutes=self.config.ACCOUNT_LOCKOUT_MINUTES
                )

            self.audit_logger.log_login_attempt(
                username, False, ip_address, user_agent, AuthenticationMethod.PASSWORD
            )
            return None

        # Reset failed attempts on successful login
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(UTC)

        self.audit_logger.log_login_attempt(
            username, True, ip_address, user_agent, AuthenticationMethod.PASSWORD
        )

        return user

    def _generate_user_id(self) -> str:
        """Generate unique user ID."""
        return f"usr_{secrets.token_urlsafe(8)}"

    def _verify_stored_password(self, username: str, password: str) -> bool:
        """Verify password against stored hash (simplified implementation)."""
        # In production, this would verify against stored password hash
        return True  # Simplified for demo

    def create_session(self, user: USARUser) -> dict[str, str]:
        """Create user session with tokens.

        Args:
            user: Authenticated user

        Returns:
            Session tokens
        """
        permissions = self.rbac.get_user_permissions(user.usar_role)
        access_token = self.jwt_mgr.create_access_token(user, permissions)
        refresh_token = self.jwt_mgr.create_refresh_token(user)

        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = {
            "user_id": user.user_id,
            "created_at": datetime.now(UTC),
            "last_activity": datetime.now(UTC),
            "permissions": permissions,
        }

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": session_id,
            "token_type": "bearer",
            "expires_in": self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
