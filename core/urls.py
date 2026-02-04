from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),
    
    # Public pages
    path('', views.home, name='home'),
    path('what-we-do/', views.what_we_do, name='what_we_do'),
    path("model-village/", views.model_village, name="model_village"),

    
    # Donation
    path('donate/', views.donate, name='donate'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancelled/', views.payment_cancelled, name='payment_cancelled'),
    path('donation-success/<int:donation_id>/', views.donation_success, name='donation_success'),
    
    # Volunteer
    path('volunteer/', views.volunteer, name='volunteer'),
    path('volunteer-success/', views.volunteer_success, name='volunteer_success'),
    
    # Jobs
    path('jobs/', views.jobs, name='jobs'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job-application-success/', views.job_application_success, name='job_application_success'),
    
    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/volunteers/', views.manage_volunteers, name='manage_volunteers'),
    path('admin-dashboard/jobs/', views.manage_jobs, name='manage_jobs'),
    path('admin-dashboard/jobs/create/', views.create_job, name='create_job'),
    path('admin-dashboard/jobs/<int:job_id>/applications/', views.manage_applications, name='manage_applications'),
    path('admin-dashboard/jobs/<int:job_id>/applications/export/', views.export_applications, name='export_applications'),
    path('admin-dashboard/donations/', views.donation_reports, name='donation_reports'),
]