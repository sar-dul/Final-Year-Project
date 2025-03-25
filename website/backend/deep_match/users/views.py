from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .models import User
from django.contrib.auth import get_user_model

def index(request):
    return render(request, 'index.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        user = User.objects.create_user(
            name=name,
            username=username,
            email=email,
            password=password,
            role=role
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect('login')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('welcome')  # Change to your desired redirect URL
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'login.html')

def welcome(request):
    # if not request.user.is_authenticated:
    #     return redirect('login')
    return render(request, 'home.html', {'user': request.user})

def logout_view(request):
    logout(request)
    return redirect('index')
