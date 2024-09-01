from django.urls import path

from processing.views import StatusCheckView, UploadCSVView

# URL patterns for the processing app
urlpatterns = [
    path("upload/", UploadCSVView.as_view(), name="upload-csv"),
    path("status/", StatusCheckView.as_view(), name="status-check"),
]
