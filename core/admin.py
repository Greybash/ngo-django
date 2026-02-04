from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Donation, VolunteerApplication, Job, JobApplication, Page, ModelVillage, UserProfile

# UserProfile Inline for User Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['phone', 'country_code', 'country', 'state', 'city', 'pin_code', 'address']

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Donation Admin
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'amount', 'status', 'created_at']
    list_filter = ['status', 'cause', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    
    fieldsets = (
        ('Donor Information', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone', 'country_code')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'pincode', 'country') 
        }),
        ('Donation Details', {
            'fields': ('amount', 'cause', 'show_name')
        }),
        ('Payment Information', {
            'fields': ('order_id', 'payment_id', 'signature', 'status')
        }),
    )
    
    def get_donor_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_donor_name.short_description = 'Donor Name'

# Volunteer Application Admin
@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'area_of_interest', 'status', 'created_at']
    list_filter = ['status', 'area_of_interest', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_volunteers', 'reject_volunteers']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'name', 'email', 'phone', 'address')
        }),
        ('Volunteer Details', {
            'fields': ('area_of_interest', 'availability', 'experience', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def approve_volunteers(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} volunteer(s) approved successfully.')
    approve_volunteers.short_description = 'Approve selected volunteers'
    
    def reject_volunteers(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} volunteer(s) rejected.')
    reject_volunteers.short_description = 'Reject selected volunteers'

# Job Admin
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'location', 'employment_type', 'is_active', 'deadline', 'created_at']
    list_filter = ['is_active', 'employment_type', 'created_at']
    search_fields = ['title', 'location', 'description']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Job Details', {
            'fields': ('title', 'description', 'requirements')
        }),
        ('Location & Type', {
            'fields': ('location', 'employment_type', 'salary_range')
        }),
        ('Status & Deadline', {
            'fields': ('is_active', 'deadline', 'created_at')
        }),
    )

# Job Application Admin
@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'job', 'status', 'created_at']
    list_filter = ['status', 'job', 'created_at']
    search_fields = ['name', 'email', 'job__title']
    readonly_fields = ['created_at', 'resume']
    actions = ['mark_as_reviewed', 'mark_as_shortlisted', 'mark_as_rejected']
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('user', 'name', 'email', 'phone')
        }),
        ('Application Details', {
            'fields': ('job', 'resume', 'cover_letter', 'status')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(status='reviewed')
        self.message_user(request, f'{updated} application(s) marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark as reviewed'
    
    def mark_as_shortlisted(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f'{updated} application(s) shortlisted.')
    mark_as_shortlisted.short_description = 'Mark as shortlisted'
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} application(s) rejected.')
    mark_as_rejected.short_description = 'Mark as rejected'

# Page Admin
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'created_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']

# Model Village Admin
@admin.register(ModelVillage)
class ModelVillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'start_date', 'is_active']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name', 'location', 'description']
    readonly_fields = ['start_date']
    
    fieldsets = (
        ('Village Information', {
            'fields': ('name', 'location', 'image')
        }),
        ('Details', {
            'fields': ('description', 'goals', 'impact')
        }),
        ('Status', {
            'fields': ('start_date', 'is_active')
        }),
    )