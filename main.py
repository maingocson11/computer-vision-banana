# main.py
from fastapi import FastAPI, Request, Form, Depends, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.datastructures import URL
from starlette.responses import StreamingResponse
from bson import ObjectId
from pydantic import BaseModel
import csv
import os
import io
from groq import Groq

from database import (add_user, verify_user, get_detection_history, get_image_by_id, update_user, get_user_details, get_avatar,
                      add_post, get_all_posts, get_post_by_id, add_comment, get_comments_for_post, toggle_like_post)

app = FastAPI()

# Cần có SECRET_KEY để sử dụng session
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

# Cấu hình để tìm tệp tĩnh (static) và mẫu (templates)
app.mount("/static", StaticFiles(directory="."), name="static")
templates = Jinja2Templates(directory=".")

# --- Cấu hình Groq API ---
# Lưu ý: Hãy đặt GROQ_API_KEY của bạn vào biến môi trường
# Ví dụ: export GROQ_API_KEY="YOUR_API_KEY"
try:
    # Lấy API Key từ biến môi trường. KHÔNG viết key trực tiếp vào code.
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    if not GROQ_API_KEY:
        print("Cảnh báo: Biến môi trường 'GROQ_API_KEY' chưa được thiết lập. Chatbot sẽ không hoạt động.")
    
    client = Groq(api_key=GROQ_API_KEY)

except Exception as e:
    print(f"Lỗi khi cấu hình Groq: {e}")
    client = None

def get_current_username(request: Request):
    return request.session.get("username")

@app.get("/", response_class=HTMLResponse)
async def home(username: str = Depends(get_current_username)):
    if username:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request}
    )
@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if verify_user(username, password):
        request.session["username"] = username
        # FastAPI không có flash messages tích hợp như Flask, ta sẽ chuyển hướng trực tiếp
        response = RedirectResponse(url="/dashboard", status_code=303)
        return response
    else:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"request": request, "error": "Tên đăng nhập hoặc mậ t khẩu không đúng."}
        )

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request}
    )
@app.post("/register", response_class=HTMLResponse)
async def register_post(request: Request, username: str = Form(...), password: str = Form(...), avatar: UploadFile = File(None)):
    avatar_data = None
    if avatar and avatar.filename:
        # Đọc dữ liệu của file ảnh
        avatar_data = await avatar.read()

    if add_user(username, password, avatar_data):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"request": request, "success": "Đăng ký thành công! Vui lòng đăng nhập."}
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"request": request, "error": "Tên đăng nhập đã tồn tại."}
        )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    # Lấy thông tin người dùng để có avatar_id
    user_details = get_user_details(username)
    avatar_id = user_details.get("avatar_id") if user_details else None

    # Lấy danh sách ảnh cho slider
    slider_images = []
    slider_dir = "images/slider"
    # Kiểm tra xem thư mục có tồn tại không
    if os.path.exists(slider_dir) and os.path.isdir(slider_dir):
        for filename in sorted(os.listdir(slider_dir)): # sorted() để đảm bảo thứ tự ảnh nhất quán
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                # Tạo đường dẫn tương đối cho URL
                slider_images.append(os.path.join(slider_dir, filename).replace("\\", "/"))

    history = get_detection_history(username)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"request": request, "username": username, "history": history, "slider_images": slider_images, "avatar_id": avatar_id}
    )

@app.get("/detect")
async def streamlit_redirect(username: str = Depends(get_current_username)):
    """Chuyển hướng đến ứng dụng Streamlit với username trong query params"""
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    # Chuyển hướng đến URL của Streamlit (mặc định là cổng 8501)
    url = URL("http://localhost:8501").include_query_params(username=username)
    return RedirectResponse(url)

@app.get("/edit-profile", response_class=HTMLResponse)
async def edit_profile_get(request: Request, username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user_details = get_user_details(username)
    avatar_id = user_details.get("avatar_id") if user_details else None

    return templates.TemplateResponse(
        request=request,
        name="edit_profile.html",
        context={"request": request, "current_username": username, "current_avatar_id": avatar_id}
    )

@app.post("/edit-profile", response_class=HTMLResponse)
async def edit_profile_post(request: Request, 
                            new_username: str = Form(None), 
                            new_password: str = Form(None), 
                            confirm_password: str = Form(None),
                            avatar: UploadFile = File(None)):
    current_username = request.session.get("username")
    if not current_username:
        return RedirectResponse(url="/login", status_code=303)

    avatar_data = None
    if avatar and avatar.filename:
        avatar_data = await avatar.read()

    if new_password and new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="edit_profile.html",
            context={"request": request, "current_username": current_username, "error": "Mậ t khẩu xác nhận không khớp."}
        )

    # Gọi hàm cập nhật từ database.py
    result = update_user(current_username, new_username.strip() if new_username else None, new_password if new_password else None, avatar_data)

    if result["success"]:
        # Nếu đổi username thành công, cập nhật session và đăng xuất để đăng nhập lại
        if new_username and new_username.strip() != current_username:
            request.session.pop("username", None)
            return templates.TemplateResponse(
                request=request,
                name="login.html",
                context={"request": request, "success": "Đổi thông tin thành công! Vui lòng đăng nhập lại với thông tin mới."}
            )
        return templates.TemplateResponse(
            request=request,
            name="edit_profile.html",
            context={"request": request, "current_username": new_username or current_username, "success": result["message"]}
        )
    else:
        return templates.TemplateResponse(
            request=request,
            name="edit_profile.html",
            context={"request": request, "current_username": current_username, "error": result["message"]}
        )

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/image/{file_id}")
async def get_image(file_id: str, username: str = Depends(get_current_username)):
    """Route để hiển thị ảnh từ GridFS"""
    if not username:
        return Response("Unauthorized", status_code=401)
    
    try:
        image_data = get_image_by_id(ObjectId(file_id))
        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        return Response(f"Error: {e}", status_code=404)

@app.get("/avatar/{file_id}")
async def get_avatar_image(file_id: str):
    """Route để hiển thị ảnh đại diện từ GridFS"""
    try:
        # Không cần check username vì avatar có thể được hiển thị công khai (hoặc tùy chỉnh sau)
        image_data = get_avatar(ObjectId(file_id))
        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        return Response(f"Error: {e}", status_code=404)

@app.get("/export_history")
async def export_history(username: str = Depends(get_current_username)):
    """Route để xuất lịch sử ra file CSV"""
    if not username:
        return Response("Unauthorized", status_code=401)

    history = get_detection_history(username)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID File', 'Tên file gốc', 'Số đối tượng', 'Ngày tải lên'])
    
    for item in history:
        writer.writerow([str(item['_id']), item['original_filename'], item['num_objects'], item['uploadDate'].strftime("%d-%m-%Y %H:%M:%S")])
    
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition":"attachment;filename=detection_history.csv"})

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(chat_message: ChatMessage, username: str = Depends(get_current_username)):
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not client:
         return JSONResponse(status_code=500, content={"error": "API Key của Groq chưa được cấu hình trên server."})
    try:
        # Gửi tin nhắn đến Groq và nhận phản hồi
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": chat_message.message,
                }
            ],
            model="llama-3.1-8b-instant", # hoặc một model khác của Groq như "mixtral-8x7b-32768"
        )
        
        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}
    except Exception as e:
        print(f"Lỗi Groq API: {e}")
        return JSONResponse(status_code=500, content={"error": f"Đã có lỗi xảy ra khi giao tiếp với AI: {e}"})

# --- Forum Routes ---

@app.get("/forum", response_class=HTMLResponse)
async def forum_page(request: Request, username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    posts = get_all_posts()
    user_details = get_user_details(username)
    avatar_id = user_details.get("avatar_id") if user_details else None
    
    return templates.TemplateResponse(
        request=request,
        name="forum.html",
        context={"request": request, "username": username, "posts": posts, "avatar_id": avatar_id}
    )

@app.get("/create-post", response_class=HTMLResponse)
async def create_post_get(request: Request, username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    user_details = get_user_details(username)
    avatar_id = user_details.get("avatar_id") if user_details else None
    return templates.TemplateResponse(
        request=request,
        name="create_post.html",
        context={"request": request, "username": username, "avatar_id": avatar_id}
    )

@app.post("/create-post", response_class=HTMLResponse)
async def create_post_post(request: Request, title: str = Form(...), content: str = Form(...), username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    add_post(username, title, content)
    return RedirectResponse(url="/forum", status_code=303)

@app.get("/post/{post_id}", response_class=HTMLResponse)
async def post_detail_page(request: Request, post_id: str, username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    post = get_post_by_id(ObjectId(post_id))
    if not post:
        raise HTTPException(status_code=404, detail="Bài đăng không tồn tại")

    author_details = get_user_details(post['author_username'])
    post['author_avatar_id'] = author_details.get('avatar_id') if author_details else None

    comments = get_comments_for_post(ObjectId(post_id))
    user_details = get_user_details(username)
    avatar_id = user_details.get("avatar_id") if user_details else None
    
    return templates.TemplateResponse(
        request=request,
        name="post_detail.html",
        context={"request": request, "username": username, "post": post, "comments": comments, "avatar_id": avatar_id}
    )

@app.post("/post/{post_id}/comment", response_class=RedirectResponse)
async def post_comment(request: Request, post_id: str, content: str = Form(...), username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    add_comment(ObjectId(post_id), username, content)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@app.post("/post/{post_id}/like", response_class=RedirectResponse)
async def like_post(request: Request, post_id: str, username: str = Depends(get_current_username)):
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    toggle_like_post(ObjectId(post_id), username)
    # Chuyển hướng người dùng trở lại trang họ đang xem
    referer = request.headers.get("referer")
    return RedirectResponse(url=referer or f"/post/{post_id}", status_code=303)

if __name__ == "__main__":
    import uvicorn
    # Chạy FastAPI server với uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)