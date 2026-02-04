from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Sum, Count
from django.utils import timezone
from django.core.mail import send_mail
from datetime import timedelta, datetime
import razorpay
from django.contrib.auth.models import User
from .models import Donation, VolunteerApplication, Job, JobApplication, Page, ModelVillage, UserProfile
from .forms import VolunteerForm, JobApplicationForm
import csv
from django.http import HttpResponse

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def is_admin(user):
    return user.is_staff or user.is_superuser


# Authentication Views
def login_page(request):
    
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'login.html')

def signup_page(request):
   
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Validation
        if not all([first_name, last_name, email, password1, password2]):
            messages.error(request, 'All fields are required!')
            return render(request, 'signup.html')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'signup.html')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long!')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered! Please login instead.')
            return render(request, 'signup.html')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists!')
            return render(request, 'signup.html')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=email,  # Using email as username
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log the user in immediately after signup
            # Specify backend explicitly when multiple backends are configured
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome {first_name}! Your account has been created successfully.')
            return redirect('home')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            #print(f"Signup error: {e}")  # Debug print
            return render(request, 'signup.html')
    
    return render(request, 'signup.html')  

# Public Views
def home(request):
    return render(request, 'home.html')

def model_village(request):
    return render(request, "model_village.html")
def what_we_do(request):
    return render(request, 'what_we_do.html')

@login_required
def donate(request):
    # Get top donors
    top_donors = Donation.objects.filter(
        status='completed'
    ).values('first_name', 'last_name', 'show_name').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')[:10]
    
    # Format top donors list
    formatted_donors = []
    for donor in top_donors:
        if donor['show_name']:
            name = f"{donor['first_name']} {donor['last_name']}"
        else:
            name = "Anonymous Donor"
        formatted_donors.append({
            'name': name,
            'total_amount': donor['total_amount']
        })
    
    if request.method == 'POST':
        amount = int(float(request.POST.get('amount')) * 100)
        cause = request.POST.get('cause')
        
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        }
        order = razorpay_client.order.create(data=order_data)
        
        # Create donation with all fields
        donation = Donation.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            country_code=request.POST.get('country_code', '+91'),
            phone=request.POST.get('phone'),
            country=request.POST.get('country', 'India'),
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pin_code'),
            address=request.POST.get('address'),
            amount=amount / 100,
            cause=cause,
            order_id=order['id'],
            status='pending',
            show_name=request.POST.get('show_name') == 'on'
        )
        
        context = {
            'order_id': order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount,
            'donation_id': donation.id
        }
        return render(request, 'payment.html', context)
    
    # Get user profile data for auto-fill
    user_data = {}
    if request.user.is_authenticated:
        user_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        
        # Get profile data if exists
        try:
            profile = request.user.profile
            user_data.update({
                'phone': profile.phone,
                'country_code': profile.country_code,
                'country': profile.country,
                'state': profile.state,
                'city': profile.city,
                'pin_code': profile.pin_code,
                'address': profile.address,
            })
        except UserProfile.DoesNotExist:
            pass
    
    return render(request, 'donate.html', {
        'user_data': user_data,
        'top_donors': formatted_donors
    })

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')
        
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
            
            donation = Donation.objects.get(order_id=order_id)
            donation.payment_id = payment_id
            donation.signature = signature
            donation.status = 'completed'
            donation.save()
            
            # Update user profile with latest information
            if donation.user:
                profile, created = UserProfile.objects.get_or_create(user=donation.user)
                profile.phone = donation.phone
                profile.country_code = donation.country_code
                profile.country = donation.country
                profile.state = donation.state
                profile.city = donation.city
                profile.pin_code = donation.pin_code
                profile.address = donation.address
                profile.save()
            
            messages.success(request, 'Thank you for your donation!')
            return redirect('donation_success', donation_id=donation.id)
        except:
            messages.error(request, 'Payment verification failed')
            return redirect('donate')
    
    return redirect('donate')

@csrf_exempt
def payment_cancelled(request):
    """Handle cancelled payments"""
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            donation = Donation.objects.get(order_id=order_id)
            donation.status = 'cancelled'
            donation.save()
        except Donation.DoesNotExist:
            pass
    
    messages.warning(request, 'Payment was cancelled. You can try again.')
    return redirect('donate')

@login_required
def donation_success(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)
    return render(request, 'donation_success.html', {'donation': donation})

@login_required
def volunteer(request):
    if request.method == 'POST':
        form = VolunteerForm(request.POST)
        if form.is_valid():
            volunteer = form.save(commit=False)
            if request.user.is_authenticated:
                volunteer.user = request.user
            volunteer.save()
            messages.success(request, 'Application submitted!')
            return redirect('volunteer_success')
    else:
        form = VolunteerForm()
    
    return render(request, 'volunteer.html', {'form': form})

@login_required
def volunteer_success(request):
    return render(request, 'volunteer_success.html')

@login_required
def jobs(request):
    jobs_list = Job.objects.filter(is_active=True)
    return render(request, 'jobs.html', {'jobs': jobs_list})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if user has already applied for this job
    has_applied = JobApplication.objects.filter(
        job=job,
        user=request.user
    ).exists()

    if request.method == 'POST':
        # Prevent duplicate submissions
        if has_applied:
            messages.warning(request, 'You have already applied for this job.')
            return redirect('job_detail', job_id=job_id)
            
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.user = request.user

            try:
                application.save()
                messages.success(request, 'Application submitted successfully!')
                return redirect('job_application_success')

            except IntegrityError:
                messages.error(
                    request,
                    'You have already applied for this job using this email.'
                )
    else:
        form = JobApplicationForm()

    return render(request, 'job_detail.html', {
        'job': job,
        'form': form,
        'has_applied': has_applied
    })
@login_required
def job_application_success(request):
    return render(request, 'job_application_success.html')

# ADMIN DASHBOARD VIEWS
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_donations = Donation.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    donations_count = Donation.objects.filter(status='completed').count()
    pending_volunteers = VolunteerApplication.objects.filter(status='pending').count()
    total_volunteers = VolunteerApplication.objects.filter(status='approved').count()
    pending_applications = JobApplication.objects.filter(status='pending').count()
    active_jobs = Job.objects.filter(is_active=True).count()
    
    recent_donations = Donation.objects.filter(status='completed').order_by('-created_at')[:10]
    recent_volunteers = VolunteerApplication.objects.order_by('-created_at')[:10]
    
    # Fix: Calculate percentages for donations by cause
    total_donation_amount = Donation.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 1
    donations_by_cause = Donation.objects.filter(status='completed').values('cause').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Add percentage calculation
    donations_by_cause_list = []
    for item in donations_by_cause:
        item['percentage'] = (item['total'] / total_donation_amount) * 100 if total_donation_amount > 0 else 0
        donations_by_cause_list.append(item)
    
    context = {
        'total_donations': total_donations,
        'donations_count': donations_count,
        'pending_volunteers': pending_volunteers,
        'total_volunteers': total_volunteers,
        'pending_applications': pending_applications,
        'active_jobs': active_jobs,
        'recent_donations': recent_donations,
        'recent_volunteers': recent_volunteers,
        'donations_by_cause': donations_by_cause_list,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_volunteers(request):
    volunteers = VolunteerApplication.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        volunteer_id = request.POST.get('volunteer_id')
        action = request.POST.get('action')
        
        volunteer = get_object_or_404(VolunteerApplication, id=volunteer_id)
        
        if action == 'approve':
            volunteer.status = 'approved'
            messages.success(request, f'{volunteer.name} has been approved!')
        elif action == 'reject':
            volunteer.status = 'rejected'
            messages.info(request, f'{volunteer.name} has been rejected.')
        
        volunteer.save()
        return redirect('manage_volunteers')
    
    return render(request, 'manage_volunteers.html', {'volunteers': volunteers})

@login_required
@user_passes_test(is_admin)
def manage_jobs(request):
    jobs_list = Job.objects.all().order_by('-created_at')
    return render(request, 'manage_jobs.html', {'jobs': jobs_list})

@login_required
@user_passes_test(is_admin)
def manage_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = JobApplication.objects.filter(job=job).order_by('-created_at')
    
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        status = request.POST.get('status')
        
        application = get_object_or_404(JobApplication, id=app_id)
        application.status = status
        application.save()
        
        messages.success(request, f'Application status updated to {status}')
        return redirect('manage_applications', job_id=job_id)
    
    return render(request, 'manage_applications.html', {'job': job, 'applications': applications})

@login_required
@user_passes_test(is_admin)
def donation_reports(request):
    donations = Donation.objects.filter(status='completed').order_by('-created_at')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        donations = donations.filter(created_at__gte=start_date)
    if end_date:
        donations = donations.filter(created_at__lte=end_date)
    
    total = donations.aggregate(Sum('amount'))['amount__sum'] or 0
    
    context = {
        'donations': donations,
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'donate_reports.html', context)


@login_required
@user_passes_test(is_admin)
def manage_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    applications = JobApplication.objects.filter(job=job).order_by('-created_at')
    
    # Calculate statistics by status
    pending_count = applications.filter(status='pending').count()
    reviewed_count = applications.filter(status='reviewed').count()
    shortlisted_count = applications.filter(status='shortlisted').count()
    rejected_count = applications.filter(status='rejected').count()
    
    if request.method == 'POST':
        app_id = request.POST.get('application_id')
        status = request.POST.get('status')
        
        application = get_object_or_404(JobApplication, id=app_id)
        application.status = status
        application.save()
        
        # Send email notification after status update
        try:
            if status == 'shortlisted':
                send_mail(
                    f'Application Update - {job.title}',
                    f'Dear {application.name},\n\nCongratulations! Your application for {job.title} has been shortlisted. We will contact you soon with next steps.\n\nBest regards,\nEvergreen Villages Trust',
                    settings.DEFAULT_FROM_EMAIL,
                    [application.email],
                    fail_silently=True,
                )
            elif status == 'rejected':
                send_mail(
                    f'Application Update - {job.title}',
                    f'Dear {application.name},\n\nThank you for your interest in the {job.title} position. After careful consideration, we have decided to move forward with other candidates.\n\nWe appreciate your time and wish you the best in your job search.\n\nBest regards,\nEvergreen Villages Trust',
                    settings.DEFAULT_FROM_EMAIL,
                    [application.email],
                    fail_silently=True,
                )
        except Exception as e:
            # Log error but don't stop the process
            print(f"Email sending failed: {e}")
        
        messages.success(request, f'Application status updated to {status}')
        return redirect('manage_applications', job_id=job_id)
    
    context = {
        'job': job,
        'applications': applications,
        'pending_count': pending_count,
        'reviewed_count': reviewed_count,
        'shortlisted_count': shortlisted_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'manage_applications.html', context)




@login_required
@user_passes_test(is_admin)
def export_applications(request, job_id):
    """Export job applications to CSV"""
    job = get_object_or_404(Job, id=job_id)
    applications = JobApplication.objects.filter(job=job).order_by('-created_at')
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="applications_{job.title.replace(" ", "_")}_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'ID',
        'Name',
        'Email',
        'Phone',
        'Status',
        'Applied On',
        'Resume URL',
        'Resume Filename',
        'Cover Letter Preview'
    ])
    
    # Write data rows
    for app in applications:
        # Get resume information
        if app.resume:
            resume_url = request.build_absolute_uri(app.resume.url)
            resume_filename = app.resume.name.split('/')[-1]  # Get just the filename
        else:
            resume_url = 'No resume uploaded'
            resume_filename = 'N/A'
        
        writer.writerow([
            app.id,
            app.name,
            app.email,
            app.phone,
            app.get_status_display(),
            app.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            resume_url,
            resume_filename,
            app.cover_letter[:100] + '...' if len(app.cover_letter) > 100 else app.cover_letter
        ])
    
    return response

@login_required
@user_passes_test(is_admin)
def create_job(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        employment_type = request.POST.get('employment_type', '').strip()
        location = request.POST.get('location', '').strip()
        salary_range = request.POST.get('salary_range', '').strip()
        description = request.POST.get('description', '').strip()
        requirements = request.POST.get('requirements', '').strip()
        deadline_raw = request.POST.get('application_deadline')
        is_active = request.POST.get('is_active') == 'on'

        # Convert date string → date object
        deadline = None
        if deadline_raw:
            try:
                deadline = datetime.strptime(deadline_raw, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid deadline date.")
                return render(request, 'create_job.html')

        # Validate required fields
        if not all([title, employment_type, location, description, requirements]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'create_job.html')

        Job.objects.create(
            title=title,
            employment_type=employment_type,
            location=location,
            salary_range=salary_range or '',
            description=description,
            requirements=requirements,
            deadline=deadline,      
        )

        messages.success(request, "Job created successfully!")
        return redirect('manage_jobs')

    return render(request, 'create_job.html')