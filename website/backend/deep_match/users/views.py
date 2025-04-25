from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .models import User
from django.contrib.auth import get_user_model
from plagiarism.models import PlagiarismReport
import plotly.express as px

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
            messages.error(request, "Invalid email or password.")

    return render(request, 'users/login.html')

def welcome(request):

    reports = PlagiarismReport.objects.filter(user=request.user).order_by('-uploaded_at')
    total_reports = reports.count()

    high_plag_reports = reports.filter(plagiarism_percent__gte=80)
    mid_plag_reports = reports.filter(plagiarism_percent__gte=50, plagiarism_percent__lt=80)
    low_plag_reports = reports.filter(plagiarism_percent__lt=50)

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

    # Create a horizontal bar chart using Plotly Express
    fig = px.bar(x=counts, y=categories, orientation='h',
                title="Plagiarism Report Counts",
                labels={'x': 'Number of Reports', 'y': 'Plagiarism Level'},
                text=counts,  # Display count values inside the bars
                color=categories,  # Color bars based on categories (discrete color)
                color_discrete_sequence=['#A8DADC', '#FFE156', '#6A0572'])  # Custom discrete colors

    # Add hover information and customize the bars
    fig.update_traces(texttemplate='%{text}', textposition='inside', marker=dict(line=dict(color='black', width=1)))

    # Customize layout for a cleaner appearance
    fig.update_layout(
        title_font_size=24,
        title_x=0.5,  # Center the title
        xaxis_title="Number of Reports",
        yaxis_title="Plagiarism Level",
        template="none",  # Remove default Plotly background template for a cleaner look
        plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent plot background
        paper_bgcolor='rgba(0, 0, 0, 0)',  # Transparent paper background
        showlegend=False,  # Hide legend as it is unnecessary for this chart
        margin=dict(l=100, r=50, t=50, b=50),  # Adjust margins for better spacing
    )

    # Render the chart as HTML
    graph_html = fig.to_html(full_html=False)


    teacher_reports = PlagiarismReport.objects.filter(user=request.user).select_related('session').order_by('-uploaded_at')

    from collections import defaultdict

    # Group by session
    report_data = defaultdict(list)
    for report in teacher_reports:
        if report.session:
            report_data[report.session].append(report)

    # Prepare summary data
    report_summary = []
    for session, reports in report_data.items():
        report_summary.append({
            'session_name': str(session),  # Customize if session has name
            'session_id': session.id,
            'report_count': len(reports),
            'date': reports[0].uploaded_at.strftime('%Y-%m-%d'),
            'reports': reports,
        })

    # Sort by date (latest first)
    report_summary.sort(key=lambda x: x['date'], reverse=True)

    if request.user.role == 'student':
        return render(request, 'plagiarism/dashboard_student.html', {'user': request.user, 'reports': reports, 'total_reports': total_reports, 'bar_graph': graph_html})
    else:
        return render(request, 'plagiarism/dashboard_teacher.html', {'user': request.user, 'report_summary': report_summary})

def logout_view(request):
    logout(request)
    return redirect('index')
