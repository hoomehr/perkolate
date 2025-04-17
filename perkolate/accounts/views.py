from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, UserUpdateForm

def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to the page user was trying to access
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def profile(request):
    """User profile view"""
    user = request.user
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def user_list(request):
    """View for listing users (admin only)"""
    if not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard')
    
    users = User.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def user_detail(request, pk):
    """View user details (admin only or own profile)"""
    user = get_object_or_404(User, pk=pk)
    
    # Only admins can view other profiles
    if user != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to view this profile.')
        return redirect('dashboard')
    
    return render(request, 'accounts/user_detail.html', {'profile_user': user})
