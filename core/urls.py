from django.urls import path
from . import views

urlpatterns = [
    # A única URL necessária no app 'core' é a da página inicial
    path('', views.HomeView.as_view(), name='home'),
    
]