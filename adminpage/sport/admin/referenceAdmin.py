from admin_auto_filters.filters import AutocompleteFilter
from django import forms
from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html

from sport.admin.utils import custom_order_filter
from sport.models import Reference
from .site import site


class StudentTextFilter(AutocompleteFilter):
    title = "student"
    field_name = "student"


class ReferenceAcceptRejectForm(forms.ModelForm):
    def clean_comment(self):
        if self.cleaned_data['hours'] == 0 and self.cleaned_data['comment'] == '':
            raise forms.ValidationError('Please, specify reject reason in the comment field')
        return self.cleaned_data['comment']

    class Meta:
        model = Reference
        fields = (
            "student",
            "semester",
            "hours",
            "comment"
        )



@admin.register(Reference, site=site)
class ReferenceAdmin(admin.ModelAdmin):
    form = ReferenceAcceptRejectForm

    list_display = (
        "student",
        "semester",
        "image",
        "uploaded",
        "approval",
    )

    list_filter = (
        StudentTextFilter,
        ("semester", custom_order_filter(("-start",))),
        "approval"
    )

    fields = (
        "student",
        "semester",
        "uploaded",
        ("hours", "comment"),
        "reference_image",
    )

    readonly_fields = (
        "student",
        "semester",
        "uploaded",
        "reference_image",
    )

    autocomplete_fields = (
        "student",
    )

    ordering = (F("approval").asc(nulls_first=True), "uploaded")

    def save_model(self, request, obj, form, change):
        if 'comment' in form.changed_data or 'hours' in form.changed_data:
            super().save_model(request, obj, form, change)

    def reference_image(self, obj):
        return format_html(
            '<a href="{}"><img style="width: 50%" src="{}" /></a>',
            obj.image.url,
            obj.image.url
        )

    reference_image.short_description = 'Reference'
    reference_image.allow_tags = True

    class Media:
        pass
