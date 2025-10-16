from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================================================
# DATABASE (CORE TABLES ONLY)
# ============================================================================

# Users table
users = {
    "producerboy": {
        "username": "producerboy",
        "email": "producerboy@example.com",
        "verified": True,
        "plan": "Pro",  # Free, Starter, Pro
        "stripe_account_id": "acct_xxxxx",
        "created_at": datetime.now() - timedelta(days=90),
    }
}

# Products table
products = [
    {
        "id": "1",
        "title": "Dark Melody Loop",
        "type": "loop",
        "price": 4.99,
        "bpm": "140",
        "key": "Cm",
        "format": "WAV",
        "file_size": "4.2 MB",
        "description": "Haunting melody perfect for dark trap beats",
        "image": None,
        "tags": ["metro boomin", "ambient", "dark"],
        "owner_username": "producerboy",
        "status": "published",
        "slug": "dark-melody-loop",
        "created_at": datetime.now() - timedelta(days=15),
    },
    {
        "id": "2",
        "title": "Hard 808",
        "type": "sample",
        "price": 1.99,
        "key": "C",
        "format": "WAV",
        "file_size": "0.3 MB",
        "description": "Hardest 808 (not spinz tho)",
        "image": None,
        "tags": ["808", "hard", "one shot"],
        "owner_username": "producerboy",
        "status": "published",
        "slug": "hard-808",
        "created_at": datetime.now() - timedelta(days=8),
    },
    {
        "id": "3",
        "title": "Trap Drums Vol.1",
        "type": "kit",
        "price": 19.99,
        "format": "WAV",
        "file_size": "19.3 MB",
        "description": "Top industry quality drumzzz",
        "image": "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400",
        "tags": ["hard", "trap", "drum kit"],
        "owner_username": "producerboy",
        "status": "published",
        "slug": "trap-drums-vol1",
        "created_at": datetime.now() - timedelta(days=22),
    },
    {
        "id": "4",
        "title": "Chill Guitar Loop",
        "type": "loop",
        "price": 5.99,
        "bpm": "85",
        "key": "Am",
        "format": "WAV",
        "file_size": "5.3 MB",
        "description": "Cool ass guitar loop",
        "image": None,
        "tags": ["chill", "guitar", "melody", "atmospheric"],
        "owner_username": "producerboy",
        "status": "draft",
        "slug": "chill-guitar-loop",
        "created_at": datetime.now() - timedelta(days=5),
    },
]

# Orders table
orders = [
    {
        "id": "ORD-001",
        "product_id": "1",
        "buyer_email": "customer1@example.com",
        "amount": 4.99,
        "status": "completed",
        "created_at": datetime.now() - timedelta(minutes=2),
    },
    {
        "id": "ORD-002",
        "product_id": "2",
        "buyer_email": "customer2@example.com",
        "amount": 1.99,
        "status": "completed",
        "created_at": datetime.now() - timedelta(hours=8),
    },
    {
        "id": "ORD-003",
        "product_id": "4",
        "buyer_email": "customer3@example.com",
        "amount": 5.99,
        "status": "completed",
        "created_at": datetime.now() - timedelta(hours=15),
    },
    {
        "id": "ORD-004",
        "product_id": "3",
        "buyer_email": "customer4@example.com",
        "amount": 19.99,
        "status": "completed",
        "created_at": datetime.now() - timedelta(days=1),
    },
    {
        "id": "ORD-005",
        "product_id": "1",
        "buyer_email": "customer5@example.com",
        "amount": 4.99,
        "status": "completed",
        "created_at": datetime.now() - timedelta(days=2),
    },
]

# ============================================================================
# COMPUTED DATA (FROM DB QUERIES - NO STORAGE NEEDED)
# ============================================================================


def get_dashboard_stats(username):
    """Calculate dashboard stats from orders + products"""
    user_products = [p for p in products if p["owner_username"] == username]
    user_orders = [
        o for o in orders if any(p["id"] == o["product_id"] for p in user_products)
    ]

    total_revenue = sum(o["amount"] for o in user_orders)
    total_sales = len(user_orders)
    active_products = len(user_products)

    return {
        "total_revenue": total_revenue,
        "revenue_change": 12.5,  # Calculate from previous period
        "total_sales": total_sales,
        "sales_change": 8.3,
        "active_products": active_products,
        "profile_views": 3400,  # Would come from analytics table
        "views_change": 15.2,
        "unread_notifications": 3,
    }


def get_recent_activity(username):
    """Generate activity from orders (most recent first)"""
    user_products = {p["id"]: p for p in products if p["owner_username"] == username}
    recent_orders = sorted(
        [o for o in orders if o["product_id"] in user_products],
        key=lambda x: x["created_at"],
        reverse=True,
    )[:5]

    activity = []
    for order in recent_orders:
        product = user_products[order["product_id"]]
        time_diff = datetime.now() - order["created_at"]

        if time_diff.days > 0:
            time_str = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
        elif time_diff.seconds // 3600 > 0:
            hours = time_diff.seconds // 3600
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = time_diff.seconds // 60
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"

        activity.append(
            {
                "icon": "shopping-bag",
                "color": "00FFBB",
                "title": f"New sale: {product['title']}",
                "time": time_str,
                "amount": f"{order['amount']:.2f}",
            }
        )

    return activity


def get_top_products(username, limit=3):
    """Get top products by sales count"""
    user_products = [p.copy() for p in products if p["owner_username"] == username]

    # Count sales for each product and add stats
    for product in user_products:
        product_orders = [o for o in orders if o["product_id"] == product["id"]]
        product["sales_count"] = len(product_orders)
        product["downloads"] = len(product_orders)
        product["revenue"] = sum(o["amount"] for o in product_orders)
        product["views"] = product["downloads"] * 3

    # Sort and return top N
    return sorted(user_products, key=lambda x: x["sales_count"], reverse=True)[:limit]


def enrich_products_with_stats(username):
    """Add revenue, downloads, views to products"""
    user_products = [p.copy() for p in products if p["owner_username"] == username]

    for product in user_products:
        # Calculate stats from orders
        product_orders = [o for o in orders if o["product_id"] == product["id"]]
        product["downloads"] = len(product_orders)
        product["revenue"] = sum(o["amount"] for o in product_orders)
        product["views"] = product["downloads"] * 3  # Rough estimate

    return user_products


# ============================================================================
# ROUTES
# ============================================================================


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "app_name": "kitzz",
            "current_year": datetime.now().year,
            "user": None,
        },
    )


@app.get("/signup")
def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/profile/{username}")
def profile(request: Request, username: str):
    profile_user = users.get(username)
    if not profile_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_products = [p for p in products if p["owner_username"] == username]
    stats = {"total_products": len(user_products)}

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "profile_user": profile_user,
            "stats": stats,
            "products": user_products,
            "is_own_profile": False,
            "user": None,
        },
    )


@app.get("/profile/{username}/product/{product_id}")
def product_detail(request: Request, product_id: str, username: str):
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product["creator"] = users.get(username)
    related = [
        p for p in products if p["id"] != product_id and p["owner_username"] == username
    ]

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "product": product,
            "related_products": related[:3],
            "user": None,
        },
    )


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================
@app.get("/dashboard/analytics")
def dashboard_analytics(request: Request):
    username = "producerboy"
    user_products = enrich_products_with_stats(username)

    # Calculate analytics data
    total_revenue = sum(p["revenue"] for p in user_products)
    total_sales = sum(p["downloads"] for p in user_products)
    total_views = sum(p["views"] for p in user_products)

    analytics = {
        "total_revenue": total_revenue,
        "revenue_change": 12.5,
        "total_sales": total_sales,
        "sales_change": 8.3,
        "conversion_rate": (total_sales / total_views * 100) if total_views > 0 else 0,
        "conversion_change": 3.2,
        "avg_order_value": total_revenue / total_sales if total_sales > 0 else 0,
        "aov_change": 5.7,
        "best_day": "Tuesday",
        "best_day_revenue": 89.95,
        "best_product": "Trap Drums Vol.1",
        "peak_hour": "2-3 PM EST",
        "new_customers": 12,
        "return_rate": 18,
        "refund_rate": 0.5,
        "avg_response": "2.3h",
    }

    # Get popular tags from all products
    all_tags = {}
    for product in user_products:
        for tag in product.get("tags", []):
            all_tags[tag] = all_tags.get(tag, 0) + 1

    popular_tags = [
        {"name": tag, "count": count}
        for tag, count in sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:8]
    ]

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "user": users[username],
            "analytics": analytics,
            "top_products": sorted(
                user_products, key=lambda x: x["revenue"], reverse=True
            )[:5],
            "popular_tags": popular_tags,
        },
    )


@app.get("/dashboard")
def display_dashboard(request: Request):
    username = "producerboy"

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": users[username],
            "stats": get_dashboard_stats(username),
            "recent_activity": get_recent_activity(username),
            "top_products": get_top_products(username),
        },
    )


@app.get("/dashboard/products")
def dashboard_products(request: Request):
    username = "producerboy"
    user_products = enrich_products_with_stats(username)

    return templates.TemplateResponse(
        "dashboard_products.html",
        {
            "request": request,
            "user": users[username],
            "products": user_products,
            "stats": get_dashboard_stats(username),
        },
    )


@app.get("/dashboard/orders")
def dashboard_orders(request: Request):
    username = "producerboy"
    user_products = {p["id"]: p for p in products if p["owner_username"] == username}
    user_orders = [
        {**o, "product_title": user_products[o["product_id"]]["title"]}
        for o in orders
        if o["product_id"] in user_products
    ]

    return templates.TemplateResponse(
        "dashboard_orders.html",
        {
            "request": request,
            "user": users[username],
            "orders": user_orders,
        },
    )


@app.get("/dashboard/products/{product_id}")
def edit_product(request: Request, product_id: str):
    username = "producerboy"

    # Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check ownership
    if product["owner_username"] != username:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Enrich with stats
    product_copy = product.copy()
    product_orders = [o for o in orders if o["product_id"] == product_id]
    product_copy["downloads"] = len(product_orders)
    product_copy["revenue"] = sum(o["amount"] for o in product_orders)
    product_copy["views"] = product_copy["downloads"] * 3

    return templates.TemplateResponse(
        "product_edit.html",
        {
            "request": request,
            "user": users[username],
            "product": product_copy,
        },
    )


@app.post("/dashboard/products/{product_id}")
async def update_product(request: Request, product_id: str):
    username = "producerboy"

    # Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check ownership
    if product["owner_username"] != username:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get form data
    form_data = await request.form()

    # Update product
    product["title"] = form_data.get("title", product["title"])
    product["description"] = form_data.get("description", product["description"])
    product["type"] = form_data.get("type", product["type"])
    product["price"] = float(form_data.get("price", product["price"]))
    product["bpm"] = form_data.get("bpm", product.get("bpm"))
    product["key"] = form_data.get("key", product.get("key"))
    product["format"] = form_data.get("format", product["format"])
    product["status"] = "published" if form_data.get("published") else "draft"

    # Handle image upload (simplified - in production, save to disk/S3)
    image = form_data.get("image")
    if image and hasattr(image, "filename") and image.filename:
        # In production: save file and update product["image"] with URL
        pass

    # Redirect back to products page
    return RedirectResponse(
        url="/dashboard/products", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/dashboard/products/{product_id}/delete")
def delete_product(product_id: str):
    username = "producerboy"

    # Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check ownership
    if product["owner_username"] != username:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Remove product
    products.remove(product)

    # Remove associated orders (in production, keep for records)
    # global orders
    # orders = [o for o in orders if o["product_id"] != product_id]

    return RedirectResponse(
        url="/dashboard/products", status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/dashboard/products/{product_id}/analytics")
def product_analytics(request: Request, product_id: str):
    username = "producerboy"

    # Find the product
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check ownership
    if product["owner_username"] != username:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Enrich with stats
    product_copy = product.copy()
    product_orders = [o for o in orders if o["product_id"] == product_id]
    product_copy["downloads"] = len(product_orders)
    product_copy["revenue"] = sum(o["amount"] for o in product_orders)
    product_copy["views"] = product_copy["downloads"] * 3

    # Analytics data (mock - in production, calculate from real data)
    analytics = {
        "total_revenue": product_copy["revenue"],
        "total_sales": product_copy["downloads"],
        "total_views": product_copy["views"],
        "conversion_rate": (product_copy["downloads"] / product_copy["views"] * 100)
        if product_copy["views"] > 0
        else 0,
        "avg_order_value": product_copy["price"],
        "revenue_change": 15.3,
        "sales_change": 12.1,
        "views_change": 8.7,
    }

    return templates.TemplateResponse(
        "product_analytics.html",
        {
            "request": request,
            "user": users[username],
            "product": product_copy,
            "analytics": analytics,
        },
    )


# ============================================================================
# AUTH ROUTES
# ============================================================================

router = APIRouter(prefix="/auth")


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(data: AuthRequest):
    # TODO: Implement registration
    return {"message": "User created"}


@router.post("/login")
def login(data: AuthRequest):
    # TODO: Implement login
    return {"access_token": "jwt_token_here", "token_type": "bearer"}


app.include_router(router)
