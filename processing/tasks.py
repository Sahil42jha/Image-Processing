import csv
import io
import logging
import os
from io import BytesIO

import requests
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

from processing.models import ProcessingRequest

logger = logging.getLogger(__name__)


class ImageProcessingTask:
    """
    Class-based task to handle image processing for a given ProcessingRequest.

    Attributes:
        request_id (str): The unique identifier for the processing request.
    """

    def __init__(self, request_id):
        self.request_id = request_id
        try:
            self.processing_request = ProcessingRequest.objects.get(
                request_id=request_id
            )
        except ProcessingRequest.DoesNotExist:
            logger.error(
                f"ProcessingRequest with request ID {request_id} does not exist."
            )
            raise ValueError(
                f"ProcessingRequest with request ID {request_id} does not exist."
            )
        self.output_directory = os.path.join(settings.MEDIA_ROOT, "processed_images")
        os.makedirs(self.output_directory, exist_ok=True)

    def process_images(self):
        """
        Processes the images for each product in the request, saves them with reduced quality,
        and generates a CSV file with the input and output image URLs.
        """
        products = self.processing_request.product_set.all()
        output_data = []

        for product in products:
            input_urls = product.input_image_urls.split(",")
            output_urls = []

            for url in input_urls:
                logger.info(f"Processing image from URL: {url}")
                try:
                    response = requests.get(url)
                    response.raise_for_status()

                    img = Image.open(BytesIO(response.content))
                    img_io = BytesIO()
                    img.save(img_io, format=img.format, quality=50)

                    filename = "compressed_" + os.path.basename(url)
                    file_path = os.path.join(self.output_directory, filename)

                    with open(file_path, "wb") as f:
                        f.write(img_io.getvalue())

                    image_url = os.path.join(
                        settings.MEDIA_URL, "processed_images", filename
                    )
                    output_urls.append(image_url)

                except requests.RequestException as e:
                    logger.error(f"Failed to fetch image from URL {url}: {str(e)}")
                    raise ValueError(f"Failed to fetch image from URL {url}: {str(e)}")
                except IOError as e:
                    logger.error(f"Failed to save image to file {filename}: {str(e)}")
                    raise ValueError(
                        f"Failed to save image to file {filename}: {str(e)}"
                    )
                except Exception as e:
                    logger.error(f"Failed to process image from URL {url}: {str(e)}")
                    continue

            product.output_image_urls = ",".join(output_urls)
            product.processed = True
            product.save()

            output_data.append(
                {
                    "Serial Number": product.serial_number,
                    "Product Name": product.name,
                    "Input Image Urls": product.input_image_urls,
                    "Output Image Urls": product.output_image_urls,
                }
            )

        try:
            self.generate_csv(output_data)
        except Exception as e:
            logger.error(f"Failed to generate CSV file: {str(e)}")
            raise ValueError(f"Failed to generate CSV file: {str(e)}")

        try:
            self.complete_request()
        except Exception as e:
            logger.error(f"Failed to complete request: {str(e)}")
            raise ValueError(f"Failed to complete request: {str(e)}")

    def generate_csv(self, output_data):
        """
        Generates a CSV file summarizing the processing results and saves it to the model's FileField.

        Args:
            output_data (list): A list of dictionaries containing processed data for each product.
        """
        try:
            csv_file = io.StringIO()
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "Serial Number",
                    "Product Name",
                    "Input Image Urls",
                    "Output Image Urls",
                ],
            )
            writer.writeheader()
            writer.writerows(output_data)

            csv_file.seek(0)
            csv_file_content = csv_file.getvalue().encode("utf-8")
            content_file = ContentFile(csv_file_content, "result_file.csv")
            self.processing_request.result_file.save(
                "results/result_file.csv", content_file, save=True
            )
            logger.info(f"CSV file saved to: {self.processing_request.result_file.url}")

        except Exception as e:
            logger.error(f"Failed to generate and save CSV file: {str(e)}")
            raise ValueError(f"Failed to generate and save CSV file: {str(e)}")

    def complete_request(self):
        """
        Marks the processing request as completed.
        """
        try:
            self.processing_request.completed = True
            self.processing_request.save()
            logger.info(f"Task completed for request ID: {self.request_id}")
        except Exception as e:
            logger.error(f"Failed to update request status to completed: {str(e)}")
            raise ValueError(f"Failed to update request status to completed: {str(e)}")

    @classmethod
    @shared_task
    def run(cls, request_id):
        """
        Class method to run the image processing task.

        Args:
            request_id (str): The unique identifier for the processing request.
        """
        logger.info(f"Task request received for request ID: {request_id}")
        try:
            task_instance = cls(request_id)
            task_instance.process_images()
        except ValueError as e:
            logger.error(f"Error processing request ID {request_id}: {str(e)}")
