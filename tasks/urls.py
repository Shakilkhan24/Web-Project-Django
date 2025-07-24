from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/new/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/update/', views.task_update, name='task_update_alt'),  # Alternative URL for updates
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('kanban/', views.kanban, name='kanban'),
    path('dashboard/', views.dashboard, name='dashboard'),
]