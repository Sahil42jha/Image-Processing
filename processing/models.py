from django.db import models


class ProcessingRequest(models.Model):
    """
    Represents a processing request for image data.

    Attributes:
        request_id (str): A unique identifier for the request.
        created_at (datetime): The timestamp when the request was created.
        completed (bool): A flag indicating whether the processing is complete.
        result_file (FileField): A file field to store the result CSV or any other output.
    """

    request_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    result_file = models.FileField(upload_to="results/", null=True, blank=True)


class Product(models.Model):
    """
    Represents a product related to a processing request.

    Attributes:
        request (ForeignKey): The associated processing request.
        serial_number (int): A unique serial number for the product.
        name (str): The name of the product.
        input_image_urls (str): A JSON or comma-separated list of URLs for input images.
        output_image_urls (str): A JSON or comma-separated list of URLs for output images (optional).
        processed (bool): A flag indicating whether the product has been processed.
    """

    request = models.ForeignKey(ProcessingRequest, on_delete=models.CASCADE)
    serial_number = models.IntegerField()
    name = models.CharField(max_length=255)
    input_image_urls = models.TextField()
    output_image_urls = models.TextField(blank=True)
    processed = models.BooleanField(default=False)
