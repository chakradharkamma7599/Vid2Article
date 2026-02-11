from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib import messages

from .models import Blog

import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------- HOME ----------------
@login_required
def index(request):
    return render(request, 'index.html')


# ---------------- YOUTUBE TITLE ----------------
def yt_title(link):
    try:
        res = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": link, "format": "json"},
            timeout=10
        )
        res.raise_for_status()
        return res.json().get("title", "Unknown Title")
    except Exception as e:
        print("YT TITLE ERROR:", e)
        return "Unknown Title"


# ---------------- AI GENERATION ----------------
def generate_blog_article(title):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise Exception("OPENROUTER_API_KEY not found")

    prompt = f"""
Write a SHORT blog-style description (4 to 5 lines only) for the following YouTube video.

Video Title:
{title}

Rules:
- Title first
- Max 5 lines
- Simple English
- No markdown
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mixtral-8x7b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 300
        },
        timeout=60
    )

    response.raise_for_status()
    data = response.json()

    return data["choices"][0]["message"]["content"]


# ---------------- GENERATE & SAVE BLOG ----------------
@csrf_exempt
@login_required
def generate_article(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        yt_link = data.get("link")

        if not yt_link:
            return JsonResponse({"error": "No link provided"}, status=400)

        title = yt_title(yt_link)
        article = generate_blog_article(title)

        blog = Blog.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            content=article
        )

        return JsonResponse({
            "success": True,
            "blog_id": blog.id
        })

    except Exception as e:
        print("GENERATE ERROR:", e)
        return JsonResponse({"error": "Something went wrong"}, status=500)


# ---------------- BLOG DETAILS ----------------
@login_required
def blog_detail(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, user=request.user)
    return render(
        request,
        "Article_Generator/blog_detail.html",
        {"blog": blog}
    )


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user:
            login(request, user)
            return redirect('/')

        messages.error(request, "Invalid username or password")
        return redirect('/login/')

    return render(request, 'login.html')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('/login/')


# ---------------- SIGNUP ----------------
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        # Empty fields check
        if not username or not email or not password:
            return render(request, 'signup.html', {
                'error': 'All fields are required'
            })

        # Password mismatch
        if password != confirm:
            return render(request, 'signup.html', {
                'error': 'Passwords do not match'
            })

        # Username exists
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {
                'error': 'Username already exists'
            })

        # Email exists
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {
                'error': 'Email already registered'
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)
        return redirect('/')   # ✅ SUCCESS REDIRECT

    return render(request, 'signup.html')
