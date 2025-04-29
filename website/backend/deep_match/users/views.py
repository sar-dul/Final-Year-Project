from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .models import User
from django.contrib.auth import get_user_model
from plagiarism.models import PlagiarismReport
import plotly.express as px
import pandas as pd

def index(request):
    return render(request, 'index.html')

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

    return render(request, 'users/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('welcome')  # Change to your desired redirect URL
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'users/login.html')

def welcome(request):

    student_reports = PlagiarismReport.objects.filter(user=request.user).order_by('-uploaded_at')
    total_reports = student_reports.count()

    high_plag_reports = student_reports.filter(plagiarism_percent__gte=80)
    mid_plag_reports = student_reports.filter(plagiarism_percent__gte=50, plagiarism_percent__lt=80)
    low_plag_reports = student_reports.filter(plagiarism_percent__lt=50)

    high_count = high_plag_reports.count()
    mid_count = mid_plag_reports.count()
    low_count = low_plag_reports.count()

    bar_graph_data = {
        'high': high_count,
        'mid': mid_count,
        'low': low_count
    }

    # Prepare the data for the chart
    categories = ['High', 'Medium', 'Low']
    counts = [bar_graph_data['high'], bar_graph_data['mid'], bar_graph_data['low']]

    # Create a simple vertical bar chart
    fig = px.bar(x=categories, y=counts,
                title="Plagiarism Report Counts",
                labels={'x': 'Plagiarism Level', 'y': 'Number of Reports'},
                color=categories,  # Color bars based on categories
                color_discrete_sequence=['#A8DADC', '#FFE156', '#6A0572'])  # Custom colors


    # Render the chart as HTML
    graph_html = fig.to_html(full_html=False)


    teacher_reports = PlagiarismReport.objects.filter(user=request.user).select_related('session').order_by('-uploaded_at')
    total_teacher_reports = teacher_reports.count()

    from collections import defaultdict

    # Group by session
    report_data = defaultdict(list)
    for report in teacher_reports:
        if report.session:
            report_data[report.session].append(report)

    # Prepare summary data
    report_summary = []
    pdf_count = 0
    py_count = 0 
    for session, reports in report_data.items():

        pdf_count += sum(1 for report in reports if report.file_name.lower().endswith('.pdf'))
        py_count += sum(1 for report in reports if report.file_name.lower().endswith('.py'))

        report_name = reports[0].report_name if reports else None

        report_summary.append({
            'session_name': str(session),  # Customize if session has name
            'session_id': session.id,
            'report_count': len(reports),
            'date': reports[0].uploaded_at.strftime('%Y-%m-%d'),
            'reports': reports,
            'report_name': report_name,
        })

    # prepare data
    data = {
        'File Type': ['Python Files', 'PDF Files'],
        'Count': [py_count, pdf_count]
    }

    df = pd.DataFrame(data)

    # create bar plot with colored bars
    fig_teacher = px.bar(df, x='File Type', y='Count', color='File Type', title='File Counts')
    graph_html_teacher = fig_teacher.to_html(full_html=False)

    # Sort by date (latest first)
    report_summary.sort(key=lambda x: x['date'], reverse=True)

    if request.user.role == 'student':
        return render(request, 'plagiarism/dashboard_student.html', {'user': request.user, 'reports': student_reports, 'total_reports': total_reports, 'bar_graph': graph_html})
    else:
        return render(request, 'plagiarism/dashboard_teacher.html', {'user': request.user, 'report_summary': report_summary, 'total_teacher_reports': total_teacher_reports, 'bar_graph_teacher': graph_html_teacher})

def logout_view(request):
    logout(request)
    return redirect('index')
