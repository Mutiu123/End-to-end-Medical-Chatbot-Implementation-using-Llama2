"""
Authentication Endpoints

Provides JWT-based authentication endpoints:
- User registration
- User login
- Token refresh
- User profile
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_db,
    get_request_id,
    rate_limit_dependency,
    require_authentication,
)
from app.api.schemas import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.logging import audit_logger, get_logger
from app.core.metrics import metrics
from app.core.security import SecurityUtils, TokenData


logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Create a new user account",
    dependencies=[Depends(rate_limit_dependency)],
)
async def register_user(
    user_data: UserRegisterRequest,
    request_id: str = Depends(get_request_id),
    db=Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        request_id: Request identifier
        db: Database connection

    Returns:
        Created user information

    Raises:
        ConflictError: If username or email already exists
    """
    users_collection = db["users"]

    # Check if username exists
    existing_user = await users_collection.find_one(
        {"$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]}
    )

    if existing_user:
        if existing_user.get("username") == user_data.username:
            raise ConflictError(
                message="Username already exists",
                details={"field": "username"},
            )
        raise ConflictError(
            message="Email already registered",
            details={"field": "email"},
        )

    # Hash password
    hashed_password = SecurityUtils.hash_password(user_data.password)

    # Create user document
    now = datetime.now(timezone.utc)
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "full_name": user_data.full_name,
        "is_active": True,
        "roles": ["user"],
        "created_at": now,
        "updated_at": now,
    }

    result = await users_collection.insert_one(user_doc)
    user_id = str(result.inserted_id)

    audit_logger.log_authentication(
        user_id=user_id,
        action="register",
        success=True,
        details={"username": user_data.username},
    )

    logger.info(f"User registered: {user_data.username}")

    return UserResponse(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=True,
        roles=["user"],
        created_at=now,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate user and return JWT tokens",
    dependencies=[Depends(rate_limit_dependency)],
)
async def login(
    login_data: UserLoginRequest,
    request_id: str = Depends(get_request_id),
    db=Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    Args:
        login_data: Login credentials
        request_id: Request identifier
        db: Database connection

    Returns:
        JWT access and refresh tokens

    Raises:
        AuthenticationError: If credentials are invalid
    """
    users_collection = db["users"]

    # Find user by username or email
    user = await users_collection.find_one(
        {"$or": [
            {"username": login_data.username},
            {"email": login_data.username}
        ]}
    )

    if not user:
        metrics.auth_attempts_total.labels(method="password", status="user_not_found").inc()
        audit_logger.log_authentication(
            user_id="unknown",
            action="login",
            success=False,
            details={"reason": "user_not_found", "username": login_data.username},
        )
        raise AuthenticationError(
            message="Invalid credentials",
            details={"reason": "Invalid username or password"},
        )

    # Verify password
    if not SecurityUtils.verify_password(login_data.password, user["password_hash"]):
        metrics.auth_attempts_total.labels(method="password", status="invalid_password").inc()
        audit_logger.log_authentication(
            user_id=str(user["_id"]),
            action="login",
            success=False,
            details={"reason": "invalid_password"},
        )
        raise AuthenticationError(
            message="Invalid credentials",
            details={"reason": "Invalid username or password"},
        )

    # Check if user is active
    if not user.get("is_active", True):
        metrics.auth_attempts_total.labels(method="password", status="inactive").inc()
        raise AuthenticationError(
            message="Account is disabled",
            details={"reason": "Account has been deactivated"},
        )

    # Generate tokens
    user_id = str(user["_id"])
    roles = user.get("roles", ["user"])
    token_response = SecurityUtils.create_tokens(user_id, roles)

    metrics.auth_attempts_total.labels(method="password", status="success").inc()
    metrics.active_sessions.inc()

    audit_logger.log_authentication(
        user_id=user_id,
        action="login",
        success=True,
    )

    logger.info(f"User logged in: {user['username']}")

    return token_response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Token",
    description="Refresh access token using refresh token",
    dependencies=[Depends(rate_limit_dependency)],
)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    request_id: str = Depends(get_request_id),
    db=Depends(get_db),
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        request_id: Request identifier
        db: Database connection

    Returns:
        New JWT access and refresh tokens

    Raises:
        AuthenticationError: If refresh token is invalid
    """
    token_data = SecurityUtils.verify_token(refresh_data.refresh_token)

    if token_data is None:
        metrics.token_operations_total.labels(operation="refresh", status="invalid").inc()
        raise AuthenticationError(
            message="Invalid refresh token",
            details={"reason": "Token verification failed"},
        )

    if token_data.token_type != "refresh":
        metrics.token_operations_total.labels(operation="refresh", status="wrong_type").inc()
        raise AuthenticationError(
            message="Invalid token type",
            details={"reason": "Expected refresh token"},
        )

    if SecurityUtils.is_token_expired(token_data):
        metrics.token_operations_total.labels(operation="refresh", status="expired").inc()
        raise AuthenticationError(
            message="Refresh token has expired",
            details={"reason": "Please log in again"},
        )

    # Verify user still exists and is active
    users_collection = db["users"]
    from bson import ObjectId
    user = await users_collection.find_one({"_id": ObjectId(token_data.sub)})

    if not user:
        raise AuthenticationError(message="User not found")

    if not user.get("is_active", True):
        raise AuthenticationError(message="Account is disabled")

    # Generate new tokens
    roles = user.get("roles", ["user"])
    new_tokens = SecurityUtils.create_tokens(token_data.sub, roles)

    metrics.token_operations_total.labels(operation="refresh", status="success").inc()

    audit_logger.log_authentication(
        user_id=token_data.sub,
        action="token_refresh",
        success=True,
    )

    return new_tokens


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get authenticated user's profile",
)
async def get_current_user_profile(
    token_data: TokenData = Depends(require_authentication),
    db=Depends(get_db),
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Args:
        token_data: Authenticated user's token data
        db: Database connection

    Returns:
        User profile information
    """
    users_collection = db["users"]
    from bson import ObjectId

    user = await users_collection.find_one({"_id": ObjectId(token_data.sub)})

    if not user:
        raise NotFoundError(
            message="User not found",
            resource_type="User",
            resource_id=token_data.sub,
        )

    return UserResponse(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name"),
        is_active=user.get("is_active", True),
        roles=user.get("roles", ["user"]),
        created_at=user["created_at"],
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Invalidate current session",
)
async def logout(
    token_data: TokenData = Depends(require_authentication),
) -> None:
    """
    Logout current user.

    In a production system, this would invalidate the token
    by adding it to a blacklist or removing from a whitelist.

    Args:
        token_data: Authenticated user's token data
    """
    metrics.active_sessions.dec()

    audit_logger.log_authentication(
        user_id=token_data.sub,
        action="logout",
        success=True,
    )

    logger.info(f"User logged out: {token_data.sub}")
