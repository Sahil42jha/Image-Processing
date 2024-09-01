import csv
import logging
import uuid
from io import StringIO

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from image_processor.response import APIResponse, ErrorAPIResponse
from processing import messages
from processing.models import ProcessingRequest, Product
from processing.serializers import ProcessingRequestSerializer
from processing.tasks import ImageProcessingTask

logger = logging.getLogger(__name__)


class UploadCSVView(APIView):
    """
    Handles the upload of a CSV file containing product information.

    The uploaded CSV is parsed, and products are stored in the database.
    An asynchronous task is triggered to process the images associated with each product.

    Attributes:
        parser_classes (tuple): Specifies the parsers used to handle file uploads.

    Methods:
        post(request, format=None):
            Processes the uploaded CSV file, validates its content, and stores product data.
            Triggers an asynchronous task to process the images.
    """

    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):
        """
        Handles POST requests for uploading a CSV file.

        Validates the presence and format of the uploaded file, reads the CSV content, and
        stores product data. If successful, triggers an asynchronous image processing task.

        Args:
            request: The HTTP request object containing the uploaded file.
            format: The format in which the response should be returned (optional).

        Returns:
            Response: A JSON response with the request ID if successful, or an error message
                      if any validation fails.
        """
        request_id = str(uuid.uuid4())
        logger.info(
            "Received CSV upload request. Request ID: {request_id}".format(
                request_id=request_id
            )
        )

        try:
            if "file" not in request.FILES:
                logger.error(
                    "No file uploaded for request ID: {request_id}".format(
                        request_id=request_id
                    )
                )
                return ErrorAPIResponse(
                    message=messages.NO_UPLOADED_FILE,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_obj = request.FILES.get("file")
            if not file_obj.name.endswith(".csv"):
                logger.error(
                    "Uploaded file is not a CSV for request ID: {request_id}".format(
                        request_id=request_id
                    )
                )
                return ErrorAPIResponse(
                    message=messages.NOT_CSV_FILE, status=status.HTTP_400_BAD_REQUEST
                )

            processing_request = ProcessingRequest.objects.create(request_id=request_id)
            logger.info(
                "Processing request created. Request ID: {request_id}".format(
                    request_id=request_id
                )
            )

            # Ensure we seek to the start of the file
            file_obj.seek(0)

            # Read the CSV content
            file_content = file_obj.read().decode("utf-8")
            file_wrapper = StringIO(
                file_content
            )  # Use StringIO to handle in-memory text streams
            reader = csv.DictReader(file_wrapper)

            fieldnames = reader.fieldnames
            if fieldnames is None:
                logger.error(
                    "Failed to read CSV file for request ID: {request_id}".format(
                        request_id=request_id
                    )
                )
                return ErrorAPIResponse(
                    message=messages.CSV_FILE_READ_ERROR,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check for required columns
            required_columns = ["Serial Number", "Product Name", "Input Image Urls"]
            missing_columns = [col for col in required_columns if col not in fieldnames]

            if missing_columns:
                logger.error(
                    "Missing columns in CSV for request ID: {request_id}. Missing: {missing_columns}".format(
                        request_id=request_id,
                        missing_columns=", ".join(missing_columns),
                    )
                )
                return ErrorAPIResponse(
                    message=f'Missing columns: {", ".join(missing_columns)}',
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Process each row in the CSV
            for row in reader:
                Product.objects.create(
                    request=processing_request,
                    serial_number=row["Serial Number"],
                    name=row["Product Name"],
                    input_image_urls=row["Input Image Urls"],
                )
                logger.info(
                    "Product created for request ID: {request_id}, Serial Number: {serial_number}".format(
                        request_id=request_id, serial_number=row["Serial Number"]
                    )
                )

        except csv.Error as e:
            logger.error(
                "CSV processing error for request ID: {request_id}. Error: {error}".format(
                    request_id=request_id, error=str(e)
                )
            )
            return ErrorAPIResponse(
                message=messages.CSV_ERROR, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Unexpected error during CSV upload for request ID: {request_id}. Error: {error}".format(
                    request_id=request_id, error=str(e)
                )
            )
            return Response(
                message=messages.UPLOAD_CSV_EXCEPPTION,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Trigger asynchronous image processing task
            ImageProcessingTask.run(request_id)
            logger.info(
                "Image processing task triggered for request ID: {request_id}".format(
                    request_id=request_id
                )
            )
        except Exception as e:
            logger.error(
                "Error triggering image processing task for request ID: {request_id}. Error: {error}".format(
                    request_id=request_id, error=str(e)
                )
            )
            return ErrorAPIResponse(
                message=messages.IMAGE_PROCESSING_EXCEPTION,
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "CSV upload and image processing initiated successfully for request ID: {request_id}".format(
                request_id=request_id
            )
        )
        return APIResponse({"request_id": request_id}, status=status.HTTP_201_CREATED)


class StatusCheckView(APIView):
    """
    Provides the status of a processing request based on the provided request ID.

    Methods:
        get(request):
            Retrieves and returns the processing status and details of products associated
            with the given request ID.
    """

    def get(self, request):
        """
        Handles GET requests to check the status of a processing request.

        Retrieves the processing request and associated products from the database based
        on the provided request ID and returns their status.

        Args:
            request: The HTTP request object containing the request ID as a query parameter.

        Returns:
            Response: A JSON response with the processing request details, or an error message
                      if the request ID is not provided or does not exist.
        """
        try:
            request_id = request.query_params.get("request_id")

            if not request_id:
                logger.error("Missing request ID in status check request.")
                return ErrorAPIResponse(
                    message=messages.MISSING_REQUEST_ID,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            processing_request = get_object_or_404(
                ProcessingRequest, request_id=request_id
            )
            logger.info(
                "Status check for request ID: {request_id}".format(
                    request_id=request_id
                )
            )

            serializer = ProcessingRequestSerializer(processing_request)
            logger.info(
                "Status check successful for request ID: {request_id}".format(
                    request_id=request_id
                )
            )
            return APIResponse(data=serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(
                "Error during status check for request ID: {request_id}. Error: {error}".format(
                    request_id=request_id, error=str(e)
                )
            )
            return ErrorAPIResponse(message=messages.STATUS_EXCEPTION)
