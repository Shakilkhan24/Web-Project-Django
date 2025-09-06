from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Task
from .forms import TaskForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import csv
from io import StringIO
from datetime import datetime
from django.core.exceptions import ValidationError

# Create your views here.

def home(request):
    return render(request, 'tasks/home.html')

def login_view(request):
    """Custom login view with proper form handling"""
    if request.user.is_authenticated:
        return redirect('task_list')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('task_list')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'account/login.html', {'form': form})

def logout_view(request):
    """Custom logout view that handles both GET and POST requests"""
    if request.method == 'POST':
        # Handle logout form submission
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home')
    else:
        # Show logout confirmation page for GET requests
        if request.user.is_authenticated:
            return render(request, 'account/logout.html')
        else:
            # If user is not authenticated, redirect to login
            return redirect('login')

@login_required
def task_list(request):
    # Get sort order from request (ascending/descending only)
    sort_order = request.GET.get('sort_order', 'asc')
    
    print(f"Sort order: {sort_order}")
    
    # Filter tasks by current user only
    tasks_queryset = Task.objects.filter(user=request.user)
    
    # Validate sort_order parameter
    if sort_order not in ['asc', 'desc']:
        print(f"Invalid sort_order: {sort_order}, defaulting to 'asc'")
        sort_order = 'asc'
    
    # Apply ordering based on sort_order
    if sort_order == 'desc':
        tasks_queryset = tasks_queryset.order_by('-last_updated')
    else:
        tasks_queryset = tasks_queryset.order_by('last_updated')
    
    # Convert to list for template
    tasks = list(tasks_queryset.values())
    
    print(f"Found {len(tasks)} tasks for user {request.user.username} after sorting")
    
    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_order': sort_order
    }
    return render(request, 'tasks/task_list.html', context)

@login_required
def dashboard(request):
    # Filter tasks by current user only
    tasks = Task.objects.filter(user=request.user)
    
    # Fix the status choices to match the model
    not_started = tasks.filter(status='not_started').count()
    working = tasks.filter(status='working').count()
    stuck = tasks.filter(status='stuck').count()
    done = tasks.filter(status='done').count()
    
    # Additional user-specific stats
    total_tasks = tasks.count()
    high_priority_tasks = tasks.filter(priority='high').count()
    critical_priority_tasks = tasks.filter(priority='critical').count()
    
    context = {
        'not_started': not_started,
        'working': working,
        'stuck': stuck,
        'done': done,
        'total_tasks': total_tasks,
        'high_priority_tasks': high_priority_tasks,
        'critical_priority_tasks': critical_priority_tasks,
        'user': request.user
    }
    return render(request, 'tasks/dashboard.html', context)

@login_required
def kanban(request):
    # Filter tasks by current user only
    tasks = Task.objects.filter(user=request.user)
    
    # Calculate task durations and group by status
    status_data = {}
    for status_choice in Task.STATUS_CHOICES:
        status_code = status_choice[0]
        status_name = status_choice[1]
        
        status_tasks = tasks.filter(status=status_code)
        task_durations = []
        
        for task in status_tasks:
            duration = (task.end_date - task.start_date).days
            task_durations.append({
                'title': task.title,
                'duration': duration,
                'start_date': task.start_date.isoformat(),
                'end_date': task.end_date.isoformat()
            })
        
        status_data[status_code] = {
            'name': status_name,
            'tasks': task_durations,
            'count': len(task_durations)
        }
    
    context = {
        'status_data': status_data
    }
    return render(request, 'tasks/progress.html', context)

@csrf_exempt
@login_required
def task_create(request):
    if request.method == "POST":
        try:
            # Check if the content type is JSON
            if request.content_type != 'application/json':
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid content type. Expected application/json'
                }, status=400)
                
            data = json.loads(request.body)
            print("Received data:", data)
            
            # Validate required fields
            required_fields = ['title', 'status', 'priority', 'start_date', 'end_date', 'owner']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing or empty field: {field}'
                    }, status=400)
            
            # Create task with current user
            task = Task.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                owner=data['owner'],
                user=request.user,  # Associate task with current user
                status=data['status'],
                priority=data['priority'],
                notes=data.get('notes', ''),
                budget=data.get('budget'),
                start_date=data['start_date'],
                end_date=data['end_date']
            )
            return JsonResponse({
                'success': True,
                'id': task.id,
                'message': f'Task created successfully for {request.user.username}'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            print("Error creating task:", str(e))
            return JsonResponse({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

@csrf_exempt
@login_required
def task_update(request, pk):
    if request.method == "POST":
        try:
            # Ensure user can only update their own tasks
            task = get_object_or_404(Task, pk=pk, user=request.user)
            data = json.loads(request.body)
            field = data.get('field')
            value = data.get('value')
            
            if not field:
                return JsonResponse({'success': False, 'error': 'Field is required'})
            
            # Validate field exists on model and is not the user field
            if not hasattr(task, field) or field == 'user':
                return JsonResponse({'success': False, 'error': f'Invalid field: {field}'})
            
            setattr(task, field, value)
            task.save()
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found or access denied'}, status=404)
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def task_delete(request, pk):
    if request.method == "POST":
        try:
            # Ensure user can only delete their own tasks
            task = get_object_or_404(Task, pk=pk, user=request.user)
            task.delete()
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found or access denied'}, status=404)
        except Exception as e:
            print(f"Error deleting task: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)

@login_required
def export_tasks_csv(request):
    """Export user's tasks to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="tasks_{request.user.username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Title', 'Description', 'Owner', 'Status', 'Priority', 
        'Notes', 'Budget', 'Start Date', 'End Date', 'Last Updated'
    ])
    
    # Get user's tasks
    tasks = Task.objects.filter(user=request.user)
    
    # Write data rows
    for task in tasks:
        writer.writerow([
            task.title,
            task.description,
            task.owner,
            task.status,
            task.priority,
            task.notes or '',
            task.budget or '',
            task.start_date.strftime('%Y-%m-%d'),
            task.end_date.strftime('%Y-%m-%d'),
            task.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required
def import_tasks_csv(request):
    """Import tasks from CSV file"""
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Please select a CSV file to import.')
            return redirect('task_list')
        
        csv_file = request.FILES['csv_file']
        
        # Check file extension
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('task_list')
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            csv_data = csv.reader(StringIO(decoded_file))
            
            # Skip header row
            next(csv_data, None)
            
            imported_count = 0
            error_count = 0
            
            for row in csv_data:
                if len(row) >= 9:  # Ensure we have enough columns
                    try:
                        # Parse the row data
                        title = row[0].strip()
                        description = row[1].strip()
                        owner = row[2].strip()
                        status = row[3].strip()
                        priority = row[4].strip()
                        notes = row[5].strip()
                        budget_str = row[6].strip()
                        start_date_str = row[7].strip()
                        end_date_str = row[8].strip()
                        
                        # Validate required fields
                        if not title or not owner or not start_date_str or not end_date_str:
                            error_count += 1
                            continue
                        
                        # Parse budget
                        budget = None
                        if budget_str:
                            try:
                                budget = float(budget_str)
                            except ValueError:
                                budget = None
                        
                        # Parse dates
                        try:
                            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            error_count += 1
                            continue
                        
                        # Validate status and priority
                        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
                        valid_priorities = [choice[0] for choice in Task.PRIORITY_CHOICES]
                        
                        if status not in valid_statuses:
                            status = 'not_started'
                        if priority not in valid_priorities:
                            priority = 'medium'
                        
                        # Create task
                        Task.objects.create(
                            title=title,
                            description=description,
                            owner=owner,
                            user=request.user,
                            status=status,
                            priority=priority,
                            notes=notes if notes else None,
                            budget=budget,
                            start_date=start_date,
                            end_date=end_date
                        )
                        
                        imported_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        continue
            
            if imported_count > 0:
                messages.success(request, f'Successfully imported {imported_count} tasks.')
            if error_count > 0:
                messages.warning(request, f'Failed to import {error_count} tasks due to invalid data.')
            
        except Exception as e:
            messages.error(request, f'Error processing CSV file: {str(e)}')
    
    return redirect('task_list')