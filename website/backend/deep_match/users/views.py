from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .models import User
from django.contrib.auth import get_user_model
from plagiarism.models import PlagiarismReport
import plotly.express as px
import pandas as pd
import re

def index(request):
    return render(request, 'index.html')

User = get_user_model()

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('retypepassword')
        role = request.POST.get('role')

        errors = []

        # Full name validation
        if not re.fullmatch(r'[A-Za-z ]{2,50}', name):
            errors.append("Full name must contain only letters and be 2 to 50 characters long.")

        # Username already exists
        if User.objects.filter(username=username).exists():
            errors.append("Username already taken.")

        # Username length
        if len(username) < 3 or len(username) > 20:
            errors.append("Username must be between 3 and 20 characters.")

        # Email already exists
        if User.objects.filter(email=email).exists():
            errors.append("Email already registered.")

        # Password confirmation
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # If there are errors, show them all
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('register')

        user = User.objects.create_user(
            name=name,
            username=username,
            email=email,
            password=password,
            role=role
        )

        messages.success(request, "Registration successful! Please log in.")
        return redirect('register')

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
                labels={'x': 'Plagiarism Level', 'y': 'Number of Reports'},
                color=categories,  # Color bars based on categories
                color_discrete_sequence=['#A8DADC', '#FFE156', '#6A0572'])  # Custom colors


    # Render the chart as HTML
    bar_graph_html = fig.to_html(full_html=False)

    # Prepare data for Line chart
    line_data = {
        'Uploaded At': [report.uploaded_at for report in student_reports],
        'Plagiarism %': [report.plagiarism_percent for report in student_reports],
        'File Name': [report.original_file_name or report.file_name for report in student_reports]
    }

    line_df = pd.DataFrame(line_data)

    # Create line chart
    line_fig = px.line(
        line_df,
        x='Uploaded At',
        y='Plagiarism %',
        markers=True,
        hover_name='File Name',
        width=750,
        height=450
    )

    # Enhance line and marker styles
    line_fig.update_traces(
        line=dict(width=3),
        marker=dict(size=8),
        mode='lines+markers'
    )

    # Apply improved layout
    line_fig.update_layout(
        yaxis=dict(
            range=[0, 100],
            title='Plagiarism %',
            ticks='outside',
            showline=True,
            linecolor='black',
            showgrid=True,
            gridcolor='lightgray'
        ),
        xaxis=dict(
            title='Time',  
            showticklabels=False,  
            showgrid=True,
            zeroline=False,
            visible=True            
        ),
        plot_bgcolor='white',
        width=750,
        height=450,
        font=dict(
            family="Arial",
            size=14,
            color="black"
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Arial"
        ),
        margin=dict(l=40, r=20, t=30, b=40)  # Extra bottom margin for x-axis title
    )
        
    line_graph_html = line_fig.to_html(full_html=False)


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
    session_avg_data = [] 
    pdf_count = 0
    py_count = 0 
    for i, (session, reports) in enumerate(report_data.items(), start=1):

        pdf_count += sum(1 for report in reports if report.file_name.lower().endswith('.pdf'))
        py_count += sum(1 for report in reports if report.file_name.lower().endswith('.py'))

        report_name = reports[0].report_name if reports else None
        date = reports[0].uploaded_at.strftime('%Y-%m-%d') if reports else None

        # Calculate average plagiarism for this session
        avg_plagiarism = sum(report.plagiarism_percent for report in reports) / len(reports)


        report_summary.append({
            'session_name': str(session),  # Customize if session has name
            'session_id': session.id,
            'report_count': len(reports),
            'date': reports[0].uploaded_at.strftime('%Y-%m-%d'),
            'reports': reports,
            'report_name': report_name,
        })

        # Prepare session data for line graph
        session_avg_data.append({
        'Check #': f'Check {i}',  # Label for X-axis
        'Average Plagiarism %': avg_plagiarism,
        'Session': str(session),
        'Date': date
    })

    # prepare data
    data = {
        'File Type': ['Python Files', 'PDF Files'],
        'Count': [py_count, pdf_count]
    }

    df = pd.DataFrame(data)

    # create bar plot with colored bars
    fig_teacher = px.bar(df, x='File Type', y='Count', color='File Type')
    bar_graph_html_teacher = fig_teacher.to_html(full_html=False)

    # Sort by date (latest first)
    report_summary.sort(key=lambda x: x['date'], reverse=True)

    if session_avg_data:
        # Create DataFrame for line graph
        session_avg_df = pd.DataFrame(session_avg_data)
        session_avg_df = session_avg_df[::-1]

        line_fig_teacher = px.line(
            session_avg_df,
            x='Check #',
            y='Average Plagiarism %',
            markers=True,
            hover_name='Session',
            width=750,
            height=450
        )

        line_fig_teacher.update_traces(
            line=dict(width=3),          # Slightly thicker line
            marker=dict(size=8),         # Slightly larger markers
            mode='lines+markers'
        )

        line_fig_teacher.update_layout(
            yaxis=dict(
                range=[0, 100],
                title='Average Plagiarism %',
                ticks='outside',
                showline=True,
                linecolor='black',
                showgrid=True,
                gridcolor='lightgray'
            ),
            xaxis=dict(
                title='Time',  # No x-axis title
                showticklabels=False,
                showgrid=False,
                zeroline=False,
                visible=True
            ),
            plot_bgcolor='white',
            font=dict(
                family="Arial",
                size=14,
                color="black"
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font_family="Arial"
            ),
            margin=dict(l=40, r=20, t=30, b=30)
        )
        line_graph_html_teacher = line_fig_teacher.to_html(full_html=False)
    else:
        line_graph_html_teacher = "<p>No plagiarism reports available to display.</p>"

    if request.user.role == 'student':
        return render(request, 'plagiarism/dashboard_student.html', {'user': request.user, 'reports': student_reports, 'total_reports': total_reports, 'bar_graph': bar_graph_html, 'line_graph': line_graph_html})
    else:
        return render(request, 'plagiarism/dashboard_teacher.html', {'user': request.user, 'report_summary': report_summary, 'total_teacher_reports': total_teacher_reports, 'bar_graph_teacher': bar_graph_html_teacher, 'line_graph_teacher': line_graph_html_teacher})

def logout_view(request):
    logout(request)
    return redirect('index')
