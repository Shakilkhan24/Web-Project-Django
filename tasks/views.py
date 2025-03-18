from django.shortcuts import render, get_object_or_404, redirect
from .models import Task
from .forms import TaskForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pandas as pd

# Create your views here.

def task_list(request):
    # Get all tasks and convert to DataFrame
    tasks = Task.objects.all().values()
    df = pd.DataFrame.from_records(tasks)
    
    # Get sorting parameters from request
    sort_by = request.GET.get('sort_by', 'id')
    sort_order = request.GET.get('sort_order', 'asc')
    
    print(f"Sorting by: {sort_by}, Order: {sort_order}")
    
    # Validate sort_by parameter
    valid_columns = ['id', 'title', 'status', 'priority', 'budget', 'start_date', 'end_date']
    if sort_by not in valid_columns:
        print(f"Invalid sort_by: {sort_by}, defaulting to 'id'")
        sort_by = 'id'
    
    # Validate sort_order parameter
    if sort_order not in ['asc', 'desc']:
        print(f"Invalid sort_order: {sort_order}, defaulting to 'asc'")
        sort_order = 'asc'
    
    # Handle special cases for sorting
    if sort_by == 'status':
        # Map status choices to their order for proper sorting
        status_order = {status[0]: idx for idx, status in enumerate(Task.STATUS_CHOICES)}
        df['status_order'] = df['status'].map(status_order)
        sort_by = 'status_order'
    elif sort_by == 'priority':
        # Map priority choices to their order for proper sorting
        priority_order = {priority[0]: idx for idx, priority in enumerate(Task.PRIORITY_CHOICES)}
        df['priority_order'] = df['priority'].map(priority_order)
        sort_by = 'priority_order'
    
    # Apply sorting
    try:
        df = df.sort_values(by=sort_by, ascending=(sort_order == 'asc'))
        print("Sorting successful")
    except Exception as e:
        print(f"Sorting error: {str(e)}")
        df = df.sort_values(by='id', ascending=True)
    
    # Convert back to list of dictionaries
    sorted_tasks = df.to_dict('records')
    
    context = {
        'tasks': sorted_tasks,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'current_sort': sort_by.replace('_order', ''),  # Remove the _order suffix
        'current_order': sort_order
    }
    return render(request, 'tasks/task_list.html', context)

@csrf_exempt
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
def task_update(request, pk):
    if request.method == "POST":
        task = get_object_or_404(Task, pk=pk)
        data = json.loads(request.body)
        setattr(task, data['field'], data['value'])
        task.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@csrf_exempt
def task_delete(request, pk):
    if request.method == "POST":
        try:
            task = get_object_or_404(Task, pk=pk)
            task.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }, status=500)
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)
