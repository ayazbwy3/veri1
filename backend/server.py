from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import pandas as pd
import io
import secrets
from passlib.context import CryptContext
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import xlsxwriter
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin credentials (in production, store in database with hashed passwords)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # This should be hashed in production

# Create the main app without a prefix
app = FastAPI(title="AK Parti Niğde Gençlik Kolları | SMT Sistemi")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    platform: str  # "instagram" or "x"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    platform: str

class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    platform: str
    post_id: str
    post_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PostCreate(BaseModel):
    title: str
    platform: str
    post_id: str
    post_date: datetime

class Engagement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str
    username: str
    platform: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EngagementAnalysis(BaseModel):
    post_id: str
    post_title: str
    platform: str
    total_management: int
    total_engaged: int
    engagement_percentage: float
    engaged_users: List[str]
    not_engaged_users: List[str]

# Auth function
def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yanlış kullanıcı adı ya da şifre",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Helper functions
def normalize_username(username: str) -> str:
    """Normalize username for accurate comparison - more aggressive approach"""
    if not username or pd.isna(username):
        return ""
    
    # Convert to string and strip whitespace
    username = str(username).strip()
    
    if not username:
        return ""
        
    # Remove @ symbol and common prefixes
    username = username.replace('@', '')
    
    # Convert to lowercase for case-insensitive comparison
    username = username.lower()
    
    # Remove all whitespace, dots, underscores, and hyphens for consistent matching
    import re
    username = re.sub(r'[\s\._\-]+', '', username)
    
    # Remove any remaining special characters except alphanumeric
    username = re.sub(r'[^a-z0-9]', '', username)
    
    return username

def process_csv_excel_file(file_content: bytes, file_type: str) -> List[str]:
    """Process CSV or Excel file and return list of usernames with improved error handling"""
    try:
        # Read file based on type
        if file_type.startswith('text/csv') or 'csv' in file_type.lower():
            # Try different encodings for CSV
            for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    df = pd.read_csv(io.StringIO(file_content.decode(encoding)))
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise Exception("CSV dosyası okunamadı - encoding sorunu")
        else:  # Excel file
            df = pd.read_excel(io.BytesIO(file_content))
        
        logger.info(f"File read successfully. Shape: {df.shape}, Columns: {list(df.columns)}")
        
        # Try to find username column - check multiple possible column names
        username_column = None
        possible_columns = ['username', 'kullanici_adi', 'kullanıcı_adı', 'user', 'name', 'isim']
        
        # First try exact column name matches
        for col in possible_columns:
            if col in df.columns:
                username_column = col
                break
        
        # If no match found, use first column
        if username_column is None:
            username_column = df.columns[0]
            logger.info(f"Using first column as username: {username_column}")
        else:
            logger.info(f"Found username column: {username_column}")
        
        # Extract usernames from the identified column
        raw_usernames = df[username_column].dropna().astype(str).tolist()
        logger.info(f"Raw usernames count: {len(raw_usernames)}, Sample: {raw_usernames[:3]}")
        
        # Normalize all usernames
        normalized_usernames = []
        for username in raw_usernames:
            normalized = normalize_username(username)
            if normalized:  # Only add if normalization didn't result in empty string
                normalized_usernames.append(normalized)
                
        logger.info(f"Normalized usernames count: {len(normalized_usernames)}, Sample: {normalized_usernames[:3]}")
        
        if not normalized_usernames:
            raise Exception("Dosyada geçerli kullanıcı adı bulunamadı")
            
        return normalized_usernames
        
    except Exception as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Dosya işlenirken hata: {str(e)}")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Sosyal Medya Etkileşim Takip Sistemi API"}

@api_router.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    username = authenticate_admin(credentials)
    return {"message": "Giriş başarılı", "username": username}

# User Management Routes
@api_router.post("/users/upload", response_model=Dict[str, Any])
async def upload_users(
    platform: str = Form(...),
    file: UploadFile = File(...),
    _: str = Depends(authenticate_admin)
):
    if platform not in ["instagram", "x"]:
        raise HTTPException(status_code=400, detail="Platform instagram ya da x olmalıdır")
    
    logger.info(f"Starting user upload for platform: {platform}, file: {file.filename}")
    
    content = await file.read()
    usernames = process_csv_excel_file(content, file.content_type)
    
    logger.info(f"Processed {len(usernames)} usernames for platform {platform}")
    
    # Insert users into database
    users_to_insert = []
    for username in usernames:
        user = User(username=username, platform=platform)
        users_to_insert.append(user.dict())
    
    if users_to_insert:
        # Remove existing users for this platform first
        delete_result = await db.users.delete_many({"platform": platform})
        logger.info(f"Deleted {delete_result.deleted_count} existing users for platform {platform}")
        
        insert_result = await db.users.insert_many(users_to_insert)
        logger.info(f"Inserted {len(insert_result.inserted_ids)} new users")
    
    return {
        "success": True,
        "message": f"{len(usernames)} kullanıcı başarıyla yüklendi ({platform})",
        "count": len(usernames),
        "platform": platform,
        "sample_users": usernames[:5]  # Show first 5 as sample
    }

@api_router.post("/users/add", response_model=User)
async def add_user_manually(
    user_data: UserCreate,
    _: str = Depends(authenticate_admin)
):
    if user_data.platform not in ["instagram", "x"]:
        raise HTTPException(status_code=400, detail="Platform instagram ya da x olmalıdır")
    
    normalized_username = normalize_username(user_data.username)
    if not normalized_username:
        raise HTTPException(status_code=400, detail="Geçerli bir kullanıcı adı girilmelidir")
    
    user = User(username=normalized_username, platform=user_data.platform)
    await db.users.insert_one(user.dict())
    return user

@api_router.get("/users", response_model=List[User])
async def get_users(platform: Optional[str] = None, _: str = Depends(authenticate_admin)):
    query = {}
    if platform:
        query["platform"] = platform
    
    users = await db.users.find(query).to_list(1000)
    return [User(**user) for user in users]

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, _: str = Depends(authenticate_admin)):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return {"message": "Kullanıcı silindi"}

# Post Management Routes
@api_router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, _: str = Depends(authenticate_admin)):
    post = Post(**post_data.dict())
    await db.posts.insert_one(post.dict())
    return post

@api_router.get("/posts", response_model=List[Dict[str, Any]])
async def get_posts(_: str = Depends(authenticate_admin)):
    posts = await db.posts.find().sort("created_at", -1).to_list(100)
    
    # Add engagement data status for each post
    posts_with_status = []
    for post in posts:
        post_dict = Post(**post).dict()
        
        # Check if this post has engagement data
        engagement_count = await db.engagements.count_documents({"post_id": post["id"]})
        post_dict["has_engagement_data"] = engagement_count > 0
        post_dict["engagement_count"] = engagement_count
        
        posts_with_status.append(post_dict)
    
    return posts_with_status

@api_router.delete("/posts/{post_id}")
async def delete_post(post_id: str, _: str = Depends(authenticate_admin)):
    # First delete all engagements for this post
    await db.engagements.delete_many({"post_id": post_id})
    
    # Then delete the post
    result = await db.posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gönderi bulunamadı")
    
    return {"message": "Gönderi ve ilgili etkileşim verileri başarıyla silindi"}
@api_router.post("/engagements/upload")
async def upload_engagement(
    post_id: str = Form(...),
    file: UploadFile = File(...),
    _: str = Depends(authenticate_admin)
):
    # Check if post exists
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Gönderi bulunamadı")
    
    logger.info(f"Starting engagement upload for post: {post['title']}")
    
    content = await file.read()
    usernames = process_csv_excel_file(content, file.content_type)
    
    logger.info(f"Processed {len(usernames)} engagement usernames")
    
    # Clear existing engagements for this post
    delete_result = await db.engagements.delete_many({"post_id": post_id})
    logger.info(f"Deleted {delete_result.deleted_count} existing engagements for post")
    
    # Insert new engagements
    engagements_to_insert = []
    for username in usernames:
        if username:  # Only add if normalization didn't result in empty string
            engagement = Engagement(
                post_id=post_id,
                username=username,
                platform=post["platform"]
            )
            engagements_to_insert.append(engagement.dict())
    
    if engagements_to_insert:
        insert_result = await db.engagements.insert_many(engagements_to_insert)
        logger.info(f"Inserted {len(insert_result.inserted_ids)} new engagements")
    
    return {
        "success": True,
        "message": f"{len(engagements_to_insert)} etkileşim başarıyla yüklendi",
        "count": len(engagements_to_insert),
        "sample_users": usernames[:5]  # Show first 5 as sample
    }

@api_router.get("/engagements/analysis/{post_id}", response_model=EngagementAnalysis)
async def analyze_engagement(post_id: str, _: str = Depends(authenticate_admin)):
    # Get post
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Gönderi bulunamadı")
    
    # Get management users for this platform
    management_users = await db.users.find({"platform": post["platform"]}).to_list(1000)
    management_usernames = [user["username"] for user in management_users]
    
    # Get engagements for this post
    engagements = await db.engagements.find({"post_id": post_id}).to_list(1000)
    engaged_usernames = [eng["username"] for eng in engagements]
    
    # Detailed debug logging
    logger.info(f"=== ANALYSIS DEBUG ===")
    logger.info(f"Post: {post['title']} ({post['platform']})")
    logger.info(f"Management users count: {len(management_usernames)}")
    logger.info(f"Management users sample: {management_usernames[:5]}")
    logger.info(f"Engaged users count: {len(engaged_usernames)}")
    logger.info(f"Engaged users sample: {engaged_usernames[:5]}")
    
    # Calculate analysis with exact string matching
    total_management = len(management_usernames)
    engaged_users = []
    not_engaged_users = []
    
    # Use set for faster lookup
    engaged_set = set(engaged_usernames)
    
    for username in management_usernames:
        if username in engaged_set:
            engaged_users.append(username)
            logger.debug(f"MATCH: {username}")
        else:
            not_engaged_users.append(username)
            logger.debug(f"NO_MATCH: {username}")
    
    logger.info(f"Final results - Engaged: {len(engaged_users)}, Not Engaged: {len(not_engaged_users)}")
    
    engagement_percentage = (len(engaged_users) / total_management * 100) if total_management > 0 else 0
    
    return EngagementAnalysis(
        post_id=post_id,
        post_title=post["title"],
        platform=post["platform"],
        total_management=total_management,
        total_engaged=len(engaged_users),
        engagement_percentage=round(engagement_percentage, 2),
        engaged_users=engaged_users,
        not_engaged_users=not_engaged_users
    )

@api_router.get("/reports/weekly")
async def get_weekly_report(_: str = Depends(authenticate_admin)):
    # Get all posts from last week
    week_ago = datetime.utcnow() - timedelta(days=7)
    posts = await db.posts.find({"created_at": {"$gte": week_ago}}).to_list(100)
    
    # Get all users
    all_users = await db.users.find().to_list(1000)
    
    report_data = []
    for user in all_users:
        user_engagement_count = 0
        total_posts_for_platform = len([p for p in posts if p["platform"] == user["platform"]])
        
        for post in posts:
            if post["platform"] == user["platform"]:
                engagement = await db.engagements.find_one({
                    "post_id": post["id"], 
                    "username": user["username"]
                })
                if engagement:
                    user_engagement_count += 1
        
        engagement_rate = (user_engagement_count / total_posts_for_platform * 100) if total_posts_for_platform > 0 else 0
        
        report_data.append({
            "username": user["username"],
            "platform": user["platform"],
            "engaged_posts": user_engagement_count,
            "total_posts": total_posts_for_platform,
            "engagement_rate": round(engagement_rate, 2)
        })
    
    return {
        "period": "Son 7 gün",
        "users": report_data,
        "summary": {
            "total_users": len(all_users),
            "total_posts": len(posts),
            "active_users": len([u for u in report_data if u["engaged_posts"] > 0])
        }
    }

@api_router.get("/debug/normalization/{post_id}")
async def debug_normalization(post_id: str, _: str = Depends(authenticate_admin)):
    """Debug endpoint to check username normalization and matching"""
    
    # Get post
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Gönderi bulunamadı")
    
    # Get management users
    management_users = await db.users.find({"platform": post["platform"]}).to_list(1000)
    
    # Get engagement users
    engagements = await db.engagements.find({"post_id": post_id}).to_list(1000)
    
    # Detailed comparison
    management_usernames = [user["username"] for user in management_users]
    engagement_usernames = [eng["username"] for eng in engagements]
    
    # Find exact matches and mismatches
    matches = []
    mismatches = []
    
    engagement_set = set(engagement_usernames)
    
    for mgmt_user in management_usernames:
        if mgmt_user in engagement_set:
            matches.append(mgmt_user)
        else:
            mismatches.append(mgmt_user)
    
    # Find engagement users not in management
    mgmt_set = set(management_usernames)
    extra_engagements = [eng for eng in engagement_usernames if eng not in mgmt_set]
    
    return {
        "post_title": post["title"],
        "platform": post["platform"],
        "management_users": {
            "count": len(management_usernames),
            "sample": management_usernames[:10],
            "all": management_usernames  # Return all for debugging
        },
        "engagement_users": {
            "count": len(engagement_usernames), 
            "sample": engagement_usernames[:10],
            "all": engagement_usernames  # Return all for debugging
        },
        "analysis": {
            "matches": {
                "count": len(matches),
                "users": matches
            },
            "mismatches": {
                "count": len(mismatches),
                "users": mismatches
            },
            "extra_engagements": {
                "count": len(extra_engagements),
                "users": extra_engagements
            }
        }
    }
@api_router.get("/export/pdf/{post_id}")
async def export_analysis_pdf(post_id: str, _: str = Depends(authenticate_admin)):
    analysis = await analyze_engagement(post_id)
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"Etkileşim Analizi: {analysis.post_title}", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Summary
    summary_data = [
        ['Platform', analysis.platform.upper()],
        ['Toplam Yönetici', str(analysis.total_management)],
        ['Etkileşim Yapan', str(analysis.total_engaged)],
        ['Etkileşim Oranı', f"{analysis.engagement_percentage}%"]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return {"pdf_data": buffer.getvalue().hex()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()