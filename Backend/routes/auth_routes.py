# routes/auth_routes.py
from flask import Blueprint, request, jsonify, session, make_response, url_for, current_app
from extensions import db
from models import User, PasswordReset
from utils import login_required
from utils.enhanced_email import email_service, send_welcome_email, send_password_reset_email
import re
import secrets
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:8080")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

# --------------------------------------------------------------------
# Authentication Endpoints
# --------------------------------------------------------------------

@auth_bp.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json()
    username_or_email = data.get("username")
    password = data.get("password")
    
    if not username_or_email or not password:
        return jsonify({"message": "Username/email and password are required"}), 400
    
    try:
        user = None
        # Check if input is email format
        if '@' in username_or_email:
            try:
                # Try to query by email
                user = User.query.filter_by(email=username_or_email).first()
            except Exception as e:
                # If email column doesn't exist, log error but continue with username check
                current_app.logger.warning(f"Email query failed, trying username: {str(e)}")
        
        # If not found by email, try username
        if not user:
            user = User.query.filter_by(username=username_or_email).first()
        
        if user and check_password_hash(user.password, password):
            # Set session to permanent (30 days by default) or customizable
            session.permanent = True
            session["user_id"] = user.id
            session["user_role"] = user.role
            
            # Update last login timestamp
            user.last_active = datetime.datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "message": "Login successful", 
                "role": user.role,
                "username": user.username
            })
        
        # Use generic error message for security
        return jsonify({"message": "Invalid credentials"}), 401
    
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({"message": "An error occurred during login"}), 500

@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@auth_bp.route("/api/session", methods=["GET"])
def check_session():
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        if user is None:
            return jsonify({"logged_in": False}), 401
        
        # Update last active timestamp
        user.last_active = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "logged_in": True, 
            "user": user.serialize(),
            "role": user.role
        })
    return jsonify({"logged_in": False}), 401

# --------------------------------------------------------------------
# Registration and Account Management Endpoints
# --------------------------------------------------------------------

@auth_bp.route("/api/check-username", methods=["POST", "OPTIONS"])
def check_username():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json()
    username = data.get("username")
    
    if not username:
        return jsonify({"available": False, "message": "Username is required"}), 400
    
    # Validate username format
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({
            "available": False, 
            "message": "Username must be 3-20 characters and contain only letters, numbers, and underscores"
        }), 400
    
    # Check if username exists
    exists = User.query.filter_by(username=username).first() is not None
    
    return jsonify({"available": not exists})

@auth_bp.route("/api/check-email", methods=["POST", "OPTIONS"])
def check_email():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json()
    email = data.get("email")
    
    if not email:
        return jsonify({"available": False, "message": "Email is required"}), 400
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"available": False, "message": "Invalid email format"}), 400
    
    # Check if email exists
    exists = User.query.filter_by(email=email).first() is not None
    
    return jsonify({"available": not exists})

@auth_bp.route("/api/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    receive_updates = data.get("receiveUpdates", False)
    
    # Validate inputs
    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400
    
    # Check username format and length
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({
            "message": "Username must be 3-20 characters and contain only letters, numbers, and underscores"
        }), 400
    
    # Check email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"message": "Invalid email format"}), 400
    
    # Check password strength
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    
    if not re.search(r'[A-Z]', password):
        return jsonify({"message": "Password must contain at least one uppercase letter"}), 400
    
    if not re.search(r'[0-9]', password):
        return jsonify({"message": "Password must contain at least one number"}), 400
    
    if not re.search(r'[^A-Za-z0-9]', password):
        return jsonify({"message": "Password must contain at least one special character"}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already taken"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 400
    
    # Create new user
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        password=hashed_password,
        role="agent",  # Default role
        receive_updates=receive_updates,
        created_at=datetime.datetime.utcnow(),
        last_active=datetime.datetime.utcnow()
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the user
        session.permanent = True
        session["user_id"] = new_user.id
        session["user_role"] = new_user.role
        
        # Send welcome email using the enhanced email service
        try:
            send_welcome_email(email, username)
            current_app.logger.info(f"Welcome email sent to {email}")
        except Exception as e:
            # Log the error but don't stop the registration process
            current_app.logger.error(f"Failed to send welcome email: {str(e)}")
        
        return jsonify({
            "message": "Account created successfully",
            "user": new_user.serialize()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({"message": f"Error creating account: {str(e)}"}), 500

@auth_bp.route("/api/forgot-password", methods=["POST", "OPTIONS"])
def forgot_password():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json()
    email = data.get("email")
    
    # Validate email
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"message": "Valid email is required"}), 400
    
    # Check if email exists
    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal whether email exists for security
        return jsonify({"message": "If your email is registered, you will receive a password reset link"}), 200
    
    # Generate a secure token
    token = secrets.token_urlsafe(32)
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    
    # Store the reset token in the database
    password_reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=expiration
    )
    
    try:
        # Delete any existing reset tokens for this user
        PasswordReset.query.filter_by(user_id=user.id).delete()
        
        db.session.add(password_reset)
        db.session.commit()
        
        # Send password reset email using enhanced email service
        try:
            send_password_reset_email(email, token)
            current_app.logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            # Log error and inform user that there was an issue
            current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            db.session.rollback()  # Roll back the token creation
            return jsonify({"message": "Unable to send password reset email. Please try again later."}), 500
        
        return jsonify({
            "message": "If your email is registered, you will receive a password reset link"
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({"message": "An error occurred processing your request"}), 500


@auth_bp.route("/api/verify-reset-token", methods=["POST"])
def verify_reset_token():
    data = request.get_json()
    token = data.get("token")
    
    if not token:
        return jsonify({"valid": False, "message": "Token is required"}), 400
    
    # Find the token in the database
    reset_entry = PasswordReset.query.filter_by(token=token).first()
    
    if not reset_entry:
        return jsonify({"valid": False, "message": "Invalid or expired token"}), 400
    
    # Check if token is expired
    if reset_entry.expires_at < datetime.datetime.utcnow():
        return jsonify({"valid": False, "message": "Token has expired"}), 400
    
    return jsonify({"valid": True})

@auth_bp.route("/api/reset-password", methods=["POST", "OPTIONS"])
def reset_password():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("password")
    
    if not token or not new_password:
        return jsonify({"message": "Token and new password are required"}), 400
    
    # Validate password strength
    if len(new_password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    
    if not re.search(r'[A-Z]', new_password):
        return jsonify({"message": "Password must contain at least one uppercase letter"}), 400
    
    if not re.search(r'[0-9]', new_password):
        return jsonify({"message": "Password must contain at least one number"}), 400
    
    if not re.search(r'[^A-Za-z0-9]', new_password):
        return jsonify({"message": "Password must contain at least one special character"}), 400
    
    # Find the token in the database
    reset_entry = PasswordReset.query.filter_by(token=token).first()
    
    if not reset_entry:
        return jsonify({"message": "Invalid or expired token"}), 400
    
    # Check if token is expired
    if reset_entry.expires_at < datetime.datetime.utcnow():
        return jsonify({"message": "Token has expired"}), 400
    
    try:
        # Get user and update password
        user = db.session.get(User, reset_entry.user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        user.password = generate_password_hash(new_password)
        
        # Delete all reset tokens for this user
        PasswordReset.query.filter_by(user_id=user.id).delete()
        
        db.session.commit()
        
        # Send confirmation email using enhanced email service
        email_subject = "Your Password Has Been Reset"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ font-size: 12px; text-align: center; margin-top: 30px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Successful</h1>
                </div>
                <div class="content">
                    <h2>Hello {user.username},</h2>
                    <p>Your password has been successfully reset.</p>
                    <p>You can now log in to your account using your new password.</p>
                    <p>If you did not make this change, please contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; {2025} Live Stream Monitoring. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            # Use the email_service instance directly
            email_service.send_email(user.email, email_subject, html_content)
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset confirmation email: {str(e)}")
        
        return jsonify({
            "message": "Password has been reset successfully. You can now log in with your new password."
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password reset error: {str(e)}")
        return jsonify({"message": "An error occurred processing your request"}), 500


@auth_bp.route("/api/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")
    
    if not current_password or not new_password:
        return jsonify({"message": "Current and new passwords are required"}), 400
    
    # Get current user
    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Verify current password
    if not check_password_hash(user.password, current_password):
        return jsonify({"message": "Current password is incorrect"}), 400
    
    # Validate new password strength
    if len(new_password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    
    if not re.search(r'[A-Z]', new_password):
        return jsonify({"message": "Password must contain at least one uppercase letter"}), 400
    
    if not re.search(r'[0-9]', new_password):
        return jsonify({"message": "Password must contain at least one number"}), 400
    
    if not re.search(r'[^A-Za-z0-9]', new_password):
        return jsonify({"message": "Password must contain at least one special character"}), 400
    
    try:
        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        # Send confirmation email using enhanced email service
        email_subject = "Your Password Has Been Changed"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ font-size: 12px; text-align: center; margin-top: 30px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Change Notification</h1>
                </div>
                <div class="content">
                    <h2>Hello {user.username},</h2>
                    <p>Your password has been successfully changed.</p>
                    <p>If you did not make this change, please contact our support team immediately.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; {2025} Live Stream Monitoring. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            email_service.send_email(user.email, email_subject, html_content)
        except Exception as e:
            current_app.logger.error(f"Failed to send password change confirmation email: {str(e)}")
        
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Password change error: {str(e)}")
        return jsonify({"message": "An error occurred processing your request"}), 500

@auth_bp.route("/api/update-profile", methods=["POST"])
@login_required
def update_profile():
    data = request.get_json()
    
    # Get current user
    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Fields that can be updated
    if "name" in data:
        user.name = data["name"]
    
    if "bio" in data:
        user.bio = data["bio"]
    
    if "receive_updates" in data:
        user.receive_updates = data["receive_updates"]
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Profile updated successfully",
            "user": user.serialize()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Profile update error: {str(e)}")
        return jsonify({"message": "An error occurred updating your profile"}), 500