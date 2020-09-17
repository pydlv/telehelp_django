from django.urls import path

from api.password_change import views

urlpatterns = [
    path('change-password/', views.ChangePasswordView.as_view()),
    path('request-password-reset/', views.RequestPasswordResetView.as_view()),
    path('reset-password/<str:token>', views.ResetPasswordView.as_view())
]
