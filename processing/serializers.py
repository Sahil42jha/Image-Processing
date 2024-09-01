from rest_framework import serializers

from processing.models import ProcessingRequest, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "serial_number",
            "name",
            "input_image_urls",
            "output_image_urls",
            "processed",
            "request_file",
        ]


class ProcessingRequestSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessingRequest
        fields = ["request_id", "created_at", "completed"]
