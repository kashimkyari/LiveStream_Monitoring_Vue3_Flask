import logging
from functools import wraps
from typing import Any, Callable, List, Optional, Union
from flask import jsonify, session

logger = logging.getLogger(__name__)

def login_required(roles: Optional[Union[str, List[str]]] = None) -> Callable:
    """
    Decorator to enforce authentication and optional role-based authorization.
    
    Args:
        roles: A single role name or list of role names permitted to access the endpoint.
               If None or empty, any authenticated user is allowed.
    """
    # Normalize roles to a list for membership checks
    if isinstance(roles, str):
        allowed_roles: List[str] = [roles]
    elif isinstance(roles, list):
        allowed_roles = roles
    else:
        allowed_roles = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            user_id = session.get("user_id")
            user_role = session.get("user_role")

            # Authentication check
            if not user_id:
                logger.warning("Unauthorized access attempt to %s", f.__name__)
                resp = jsonify({
                    "error": "Unauthorized",
                    "message": "Authentication required."
                })
                resp.status_code = 401
                return resp

            # Authorization check (if roles were specified)
            if allowed_roles and user_role not in allowed_roles:
                logger.warning(
                    "Permission denied for user %s with role %s (requires one of: %s) for %s",
                    user_id, user_role, ", ".join(allowed_roles), f.__name__
                )
                resp = jsonify({
                    "error": "Forbidden",
                    "message": "You do not have permission to perform this action."
                })
                resp.status_code = 403
                return resp

            # Passed all checks — proceed to the view function
            return f(*args, **kwargs)

        return wrapped
    return decorator