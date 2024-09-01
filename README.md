# Start the Django development server
python3 manage.py runserver

# Start the Celery worker for handling tasks
celery -A image_processor worker -l info
