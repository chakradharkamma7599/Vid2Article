from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # AI blog generation (AJAX)
    path('generate-article/', views.generate_article, name='generate_article'),

    # Blog pages
    path('blog/<int:blog_id>/', views.blog_detail, name='blog_detail'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
]
