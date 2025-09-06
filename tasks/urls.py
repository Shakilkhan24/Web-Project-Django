from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/new/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:pk>/update/', views.task_update, name='task_update_alt'),  # Alternative URL for updates
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/export-csv/', views.export_tasks_csv, name='export_tasks_csv'),
    path('tasks/import-csv/', views.import_tasks_csv, name='import_tasks_csv'),
    path('progress/', views.kanban, name='kanban'),
    path('dashboard/', views.dashboard, name='dashboard'),
]