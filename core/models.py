from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Extended user profile for storing additional donor information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    country_code = models.CharField(max_length=5, default='+91')
    country = models.CharField(max_length=100, default='India')
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    pin_code = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=255, default='Not provided')
    
    def __str__(self):
        return f"{self.user.get_full_name()} Profile"

class Donation(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    CAUSES = [
        ('education', 'Education'),
        ('healthcare', 'Healthcare'),
        ('environment', 'Environment'),
        ('poverty', 'Poverty Alleviation'),
        ('women_empowerment', 'Women Empowerment'),
        ('general', 'General Fund'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(default='')
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    phone = models.CharField(max_length=15, default='')
    # Personal Information
    
    country_code = models.CharField(max_length=5, default='+91')
    phone = models.CharField(max_length=15, default='')
    
    # Address Information
    country = models.CharField(max_length=100, default='India')
     # Option A: With default values (if fields are required)
    address = models.CharField(max_length=255, default='Not provided')
    city = models.CharField(max_length=100, default='Not provided')
    state = models.CharField(max_length=100, default='Not provided')
    pincode = models.CharField(max_length=10, default='000000')
    
    # Donation Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    cause = models.CharField(max_length=50, choices=CAUSES, default='general')
    
    # Payment Information
    payment_id = models.CharField(max_length=200, blank=True)
    order_id = models.CharField(max_length=200, blank=True)
    signature = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Privacy
    show_name = models.BooleanField(default=True, help_text="Show my name in top donors list")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - ₹{self.amount}"
    
    def get_display_name(self):
        """Return display name based on privacy settings"""
        if self.show_name:
            return f"{self.first_name} {self.last_name}"
        return "Anonymous Donor"

class VolunteerApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    INTEREST_AREAS = [
        ('teaching', 'Teaching'),
        ('healthcare', 'Healthcare'),
        ('environment', 'Environment'),
        ('fundraising', 'Fundraising'),
        ('events', 'Event Management'),
        ('admin', 'Administrative Work'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=255, default='Not provided')
    area_of_interest = models.CharField(max_length=50, choices=INTEREST_AREAS)
    availability = models.CharField(max_length=200)
    experience = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.area_of_interest}"

class Job(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=50, default='Full-time')
    salary_range = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['job', 'email']
    
    def __str__(self):
        return f"{self.name} - {self.job.title}"

class Page(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    meta_description = models.CharField(max_length=160, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class ModelVillage(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    description = models.TextField()
    goals = models.TextField()
    impact = models.TextField()
    image = models.ImageField(upload_to='villages/', blank=True)
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name