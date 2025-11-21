from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import CustomUserCreationForm


class CustomLoginView(LoginView):
    """
    Custom login view with Bootstrap styling.
    
    Redirects authenticated users to home page.
    """
    
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view redirecting to home."""
    
    next_page = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You have been logged out.')
        return super().dispatch(request, *args, **kwargs)


class RegisterView(CreateView):
    """
    User registration view.
    
    Creates new user account and automatically assigns to Viewers group.
    Logs in user immediately after successful registration.
    """
    
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            f'Welcome, {user.username}! Your account has been created.'
        )
        return redirect(self.success_url)


class CustomPasswordResetView(PasswordResetView):
    """Password reset request view."""
    
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset confirmation view."""
    
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordChangeView(PasswordChangeView):
    """Password change view for authenticated users."""
    
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('password_change_done')
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed.')
        return super().form_valid(form)


class PasswordChangeDoneView(TemplateView):
    """Password change confirmation view."""
    
    template_name = 'accounts/password_change_done.html'


class PasswordResetDoneView(TemplateView):
    """Password reset email sent confirmation."""
    
    template_name = 'accounts/password_reset_done.html'


class PasswordResetCompleteView(TemplateView):
    """Password reset complete confirmation."""
    
    template_name = 'accounts/password_reset_complete.html'


@login_required
def profile_view(request):
    """User profile view showing account details and group membership."""
    user = request.user
    groups = user.groups.all()
    is_editor = groups.filter(name='Editors').exists()
    
    context = {
        'user': user,
        'groups': groups,
        'is_editor': is_editor,
    }
    return render(request, 'accounts/profile.html', context)
