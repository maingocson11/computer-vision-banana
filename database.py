# database.py
import pymongo
import bcrypt
import gridfs
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Kết nối tới MongoDB
# Thay thế chuỗi kết nối bằng chuỗi của bạn
MONGO_URI = "mongodb://localhost:27017/"

try:
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
    client.admin.command('ping')
    db = client["user_authentication"]
    users_collection = db["users"]
    posts_collection = db["posts"]
    comments_collection = db["comments"]
    fs = gridfs.GridFS(db)
except:
    # MongoDB không khả dụng - tạo mock objects
    client = None
    db = None
    users_collection = None
    posts_collection = None
    comments_collection = None
    fs = None

def hash_password(password):
    """Mã hóa mật khẩu"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed_password):
    """Kiểm tra mật khẩu"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def add_user(username, password, avatar_data=None):
    """Thêm người dùng mới vào cơ sở dữ liệu"""
    if users_collection.find_one({"username": username}):
        return False  # Tên người dùng đã tồn tại
    
    avatar_id = None
    if avatar_data:
        # Lưu ảnh đại diện vào GridFS và lấy file_id
        avatar_id = fs.put(avatar_data, filename=f"avatar_{username}", content_type="image/png")

    hashed_password = hash_password(password)

    # Lấy thời gian hiện tại theo múi giờ Việt Nam
    vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now_in_vietnam = datetime.now(vietnam_tz)
    # Định dạng lại theo yêu cầu: ngày-tháng-năm-giờ-phút-giây (24h)
    formatted_time = now_in_vietnam.strftime("%d-%m-%Y-%H-%M-%S")

    users_collection.insert_one({
        "username": username, 
        "password": hashed_password,
        "created_at": formatted_time, # Lưu chuỗi thời gian đã định dạng
        "avatar_id": avatar_id
    })
    return True

def verify_user(username, password):
    """Xác thực người dùng"""
    user = users_collection.find_one({"username": username})
    # So sánh mật khẩu người dùng nhập (sau khi mã hóa) với mật khẩu đã lưu trong DB.
    # user['password'] đã là dạng bytes từ DB.
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return True
    return False

def get_user_details(username):
    """Lấy thông tin chi tiết của người dùng"""
    if users_collection is None:
        return {}  # Return empty dict if MongoDB unavailable
    try:
        user = users_collection.find_one({"username": username})
        return user if user else {}
    except:
        return {}

def save_detection_result(username, original_filename, num_objects, image_data):
    """Lưu kết quả nhận diện (ảnh và metadata) vào GridFS"""
    if fs is None:
        return  # Skip saving if MongoDB unavailable
    try:
        # Chuyển đổi PIL Image thành bytes
        img_byte_arr = BytesIO()
        image_data.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Lưu file vào GridFS và thêm metadata
        fs.put(
            img_byte_arr,
            filename=f"{username}_{original_filename}",
            username=username,
            original_filename=original_filename,
            num_objects=num_objects,
            uploadDate=datetime.utcnow()
        )
    except:
        pass  # Silently fail if save fails

def get_detection_history(username):
    """Lấy lịch sử nhận diện của một người dùng"""
    # Tìm tất cả các file có metadata username khớp
    history = list(db.fs.files.find({"username": username}).sort("uploadDate", -1))
    return history

def get_image_by_id(file_id):
    """Lấy dữ liệu ảnh từ GridFS bằng ID"""
    return fs.get(file_id).read()

def get_avatar(file_id):
    """Lấy ảnh đại diện từ GridFS"""
    try:
        return fs.get(file_id).read()
    except gridfs.errors.NoFile:
        return None

def update_user(current_username, new_username=None, new_password=None, new_avatar_data=None):
    """Cập nhật thông tin người dùng (tên đăng nhập và/hoặc mật khẩu)"""
    update_data = {}
    user = users_collection.find_one({"username": current_username})
    if not user:
        return {"success": False, "message": "Người dùng không tồn tại."}
    
    # Kiểm tra xem new_username có tồn tại và khác với username hiện tại không
    if new_username and new_username != current_username:
        # Kiểm tra xem new_username đã được sử dụng chưa
        if users_collection.find_one({"username": new_username}):
            return {"success": False, "message": "Tên đăng nhập mới đã tồn tại."}
        update_data["username"] = new_username

    # Nếu có mật khẩu mới, mã hóa nó
    if new_password:
        update_data["password"] = hash_password(new_password)

    # Xử lý avatar mới
    if new_avatar_data:
        # Nếu có avatar cũ, xóa nó đi
        if user.get("avatar_id"):
            fs.delete(user["avatar_id"])
        # Thêm avatar mới và cập nhật ID
        update_data["avatar_id"] = fs.put(new_avatar_data, filename=f"avatar_{new_username or current_username}", content_type="image/png")

    # Nếu không có gì để cập nhật, trả về thành công
    if not update_data:
        return {"success": True, "message": "Không có thông tin nào được thay đổi."}

    # Thực hiện cập nhật trong users_collection
    users_collection.update_one({"username": current_username}, {"$set": update_data})

    # Nếu tên người dùng đã thay đổi, cập nhật tất cả các bản ghi lịch sử liên quan
    if "username" in update_data:
        db.fs.files.update_many(
            {"username": current_username},
            {"$set": {"username": new_username}}
        )
    
    return {"success": True, "message": "Cập nhật thông tin thành công."}

def add_post(author_username, title, content):
    """Thêm một bài đăng mới."""
    try:
        vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        now_in_vietnam = datetime.now(vietnam_tz)
        formatted_time = now_in_vietnam.strftime("%d-%m-%Y %H:%M:%S")
        post = {
            "author_username": author_username,
            "title": title,
            "content": content,
            "timestamp": formatted_time,
            "likes": []
        }
        result = posts_collection.insert_one(post)
        return result.inserted_id
    except Exception as e:
        print(f"Lỗi khi thêm bài đăng: {e}")
        return None

def get_all_posts():
    """Lấy tất cả bài đăng và thông tin tác giả."""
    pipeline = [
        {
            '$sort': {'timestamp': -1}
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'author_username',
                'foreignField': 'username',
                'as': 'author_details'
            }
        },
        {
            '$unwind': {
                'path': '$author_details',
                'preserveNullAndEmptyArrays': True
            }
        }
    ]
    return list(posts_collection.aggregate(pipeline))

def get_post_by_id(post_id):
    """Lấy một bài đăng bằng ID của nó."""
    return posts_collection.find_one({"_id": post_id})

def add_comment(post_id, author_username, content):
    """Thêm bình luận cho một bài đăng."""
    try:
        vietnam_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        now_in_vietnam = datetime.now(vietnam_tz)
        formatted_time = now_in_vietnam.strftime("%d-%m-%Y %H:%M:%S")
        comment = {
            "post_id": post_id,
            "author_username": author_username,
            "content": content,
            "timestamp": formatted_time
        }
        comments_collection.insert_one(comment)
        return True
    except Exception as e:
        print(f"Lỗi khi thêm bình luận: {e}")
        return False

def get_comments_for_post(post_id):
    """Lấy tất cả bình luận cho một bài đăng."""
    pipeline = [
        {'$match': {'post_id': post_id}},
        {'$sort': {'timestamp': 1}},
        {
            '$lookup': {
                'from': 'users',
                'localField': 'author_username',
                'foreignField': 'username',
                'as': 'author_details'
            }
        },
        {'$unwind': {'path': '$author_details', 'preserveNullAndEmptyArrays': True}}
    ]
    return list(comments_collection.aggregate(pipeline))

def toggle_like_post(post_id, username):
    """Thích hoặc bỏ thích một bài đăng."""
    post = posts_collection.find_one({"_id": post_id})
    if post:
        if username in post.get("likes", []):
            # Bỏ thích
            posts_collection.update_one({"_id": post_id}, {"$pull": {"likes": username}})
        else:
            # Thích
            posts_collection.update_one({"_id": post_id}, {"$push": {"likes": username}})
        return True
    return False