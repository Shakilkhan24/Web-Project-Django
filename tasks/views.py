from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Task
from .forms import TaskForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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
    # Get sorting parameters from request
    sort_by = request.GET.get('sort_by', 'id')
    sort_order = request.GET.get('sort_order', 'asc')
    
    print(f"Sorting by: {sort_by}, Order: {sort_order}")
    
    # Start with all tasks queryset
    tasks_queryset = Task.objects.all()
    
    # Validate sort_by parameter
    valid_columns = ['id', 'title', 'status', 'priority', 'budget', 'start_date', 'end_date', 'last_updated']
    if sort_by not in valid_columns:
        print(f"Invalid sort_by: {sort_by}, defaulting to 'id'")
        sort_by = 'id'
    
    # Validate sort_order parameter
    if sort_order not in ['asc', 'desc']:
        print(f"Invalid sort_order: {sort_order}, defaulting to 'asc'")
        sort_order = 'asc'
    
    # Handle special cases for sorting
    if sort_by == 'status':
        # Create a custom ordering for status
        status_order = []
        for status_choice in Task.STATUS_CHOICES:
            status_order.append(status_choice[0])
        
        # Use Django's order_by with Case/When for custom ordering
        from django.db.models import Case, When, IntegerField
        status_ordering = Case(
            *[When(status=status, then=idx) for idx, status in enumerate(status_order)],
            output_field=IntegerField()
        )
        
        if sort_order == 'asc':
            tasks_queryset = tasks_queryset.annotate(status_order=status_ordering).order_by('status_order')
        else:
            tasks_queryset = tasks_queryset.annotate(status_order=status_ordering).order_by('-status_order')
            
    elif sort_by == 'priority':
        # Create a custom ordering for priority
        priority_order = []
        for priority_choice in Task.PRIORITY_CHOICES:
            priority_order.append(priority_choice[0])
        
        from django.db.models import Case, When, IntegerField
        priority_ordering = Case(
            *[When(priority=priority, then=idx) for idx, priority in enumerate(priority_order)],
            output_field=IntegerField()
        )
        
        if sort_order == 'asc':
            tasks_queryset = tasks_queryset.annotate(priority_order=priority_ordering).order_by('priority_order')
        else:
            tasks_queryset = tasks_queryset.annotate(priority_order=priority_ordering).order_by('-priority_order')
    else:
        # For other fields, use standard Django ordering
        order_field = sort_by if sort_order == 'asc' else f'-{sort_by}'
        tasks_queryset = tasks_queryset.order_by(order_field)
    
    # Convert to list for template
    tasks = list(tasks_queryset.values())
    
    print(f"Found {len(tasks)} tasks after sorting")
    
    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_sort': sort_by,
        'current_order': sort_order
    }
    return render(request, 'tasks/task_list.html', context)

@login_required
def dashboard(request):
    tasks = Task.objects.all()
    # Fix the status choices to match the model
    not_started = tasks.filter(status='not_started').count()
    working = tasks.filter(status='working').count()
    stuck = tasks.filter(status='stuck').count()
    done = tasks.filter(status='done').count()
    
    context = {
        'not_started': not_started,
        'working': working,
        'stuck': stuck,
        'done': done
    }
    return render(request, 'tasks/dashboard.html', context)

@login_required
def kanban(request):
    tasks = Task.objects.all()
    context = {
        'tasks': tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES
    }
    return render(request, 'tasks/kanban.html', context)

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
            
            task = Task.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                owner=data['owner'],
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
                'message': 'Task created successfully'
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
            task = get_object_or_404(Task, pk=pk)
            data = json.loads(request.body)
            field = data.get('field')
            value = data.get('value')
            
            if not field:
                return JsonResponse({'success': False, 'error': 'Field is required'})
            
            # Validate field exists on model
            if not hasattr(task, field):
                return JsonResponse({'success': False, 'error': f'Invalid field: {field}'})
            
            setattr(task, field, value)
            task.save()
            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def task_delete(request, pk):
    if request.method == "POST":
        try:
            task = get_object_or_404(Task, pk=pk)
            task.delete()
            return JsonResponse({'success': True})
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