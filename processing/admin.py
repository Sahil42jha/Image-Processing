from django.contrib import admin

from processing.models import ProcessingRequest, Product


class ProductInline(admin.TabularInline):
    """
    Inline admin for the Product model, displayed within the ProcessingRequest admin.

    Attributes:
        model (Product): The Product model.
        extra (int): Number of empty forms to display (0 in this case).
        readonly_fields (list): Fields that are displayed as read-only.
    """

    model = Product
    extra = 0
    readonly_fields = [
        "serial_number",
        "name",
        "input_image_urls",
        "output_image_urls",
        "processed",
    ]


@admin.register(ProcessingRequest)
class ProcessingRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for the ProcessingRequest model.

    Attributes:
        list_display (list): Fields to display in the list view.
        readonly_fields (list): Fields that are displayed as read-only.
        inlines (list): Inline models to include in the admin interface.
        ordering (list): Default ordering of records.
        list_filter (list): Fields to filter the records.
    """

    list_display = ["id", "request_id", "created_at", "completed"]
    readonly_fields = ["request_id", "created_at", "completed"]
    inlines = [ProductInline]
    ordering = ["-created_at"]
    list_filter = ["completed"]
    search_fields = ["request_id"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for the Product model.

    Attributes:
        list_display (list): Fields to display in the list view.
        readonly_fields (list): Fields that are displayed as read-only.
        list_filter (list): Fields to filter the records.
    """

    list_display = [
        "id",
        "name",
        "serial_number",
        "input_image_urls",
        "output_image_urls",
        "processed",
        "request",
    ]
    readonly_fields = [
        "name",
        "serial_number",
        "input_image_urls",
        "output_image_urls",
        "processed",
        "request",
    ]
    list_filter = ["processed"]
    search_fields = ["name", "serial_number"]
