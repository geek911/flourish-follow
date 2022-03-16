import datetime
import imp
import re

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormMixin
from edc_base.view_mixins import EdcBaseViewMixin
from edc_dashboard.view_mixins import (
    ListboardFilterViewMixin, SearchFormViewMixin, )
from edc_dashboard.views import ListboardView
from edc_navbar import NavbarViewMixin

from .download_report_mixin import DownloadReportMixin
from .filters import AppointmentListboardViewFilters
from ..forms import AppointmentsWindowForm
from ..model_wrappers import FollowAppointmentModelWrapper
from ..models import FollowExportFile


class AppointmentListboardView(NavbarViewMixin, EdcBaseViewMixin,
                               ListboardFilterViewMixin, SearchFormViewMixin,
                               DownloadReportMixin, ListboardView, FormMixin):
    form_class = AppointmentsWindowForm
    listboard_template = 'flourish_follow_appt_listboard_template'
    listboard_url = 'flourish_follow_appt_listboard_url'
    listboard_panel_style = 'info'
    listboard_fa_icon = "fa-user-plus"

    model = 'edc_appointment.appointment'
    listboard_view_filters = AppointmentListboardViewFilters()
    model_wrapper_cls = FollowAppointmentModelWrapper
    navbar_name = 'flourish_follow'
    navbar_selected_item = 'appointments'
    # ordering = '-timepoint_datetime'
    paginate_by = 10
    search_form_url = 'flourish_follow_appt_listboard_url'

    def get_ordering(self):

        sort_by = self.request.GET.get('sort_by', None)

        if sort_by:
            return None
        return None

    def get_success_url(self):
        return reverse('flourish_follow:flourish_follow_appt_listboard_url')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset_filter_options(self, request, *args, **kwargs):
        options = super().get_queryset_filter_options(request, *args, **kwargs)
        if kwargs.get('subject_identifier', None):
            options.update(
                {'subject_identifier': kwargs.get('subject_identifier')})
        return options

    def extra_search_options(self, search_term):
        q = Q()
        if re.match('^[A-Z]+$', search_term):
            q = Q(first_name__exact=search_term)
        return q

    def export(self, queryset=None, start_date=None, end_date=None):
        """Export data.
        """
        data = []
        if start_date and end_date:
            queryset = queryset.objects.filter(
                created__date__gte=start_date,
                created__date__lte=end_date)
        for obj in queryset:
            # removed names, because it defies the protocol
            data.append(
                {'subject_identifier': getattr(obj, 'subject_identifier'),
                 'earliest_date_due': getattr(obj, 'earliest_date_due'),
                 'latest_date_due': getattr(obj, 'latest_date_due'),
                 'ideal_date_due': getattr(obj, 'ideal_date_due'),
                 'appt_datetime': getattr(obj, 'appt_datetime')})
        df = pd.DataFrame(data)
        self.download_data(
            description='Appointment and windows',
            start_date=start_date,
            end_date=end_date,
            report_type='appointments_window_periods',
            df=df)



    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        if self.request.GET.get('export') == 'yes':
            queryset = context.get('object_list')  # from ListView
            self.export(queryset=queryset)
            msg = (f'File generated successfully.  Go to the download list to download file.')
            messages.add_message(
                self.request, messages.SUCCESS, msg)
        appointment_downloads = FollowExportFile.objects.filter(
            description='Appointment and windows').order_by('uploaded_at')
        context.update(appointment_downloads=appointment_downloads)
        return context


    def get_queryset(self):
        qs = super().get_queryset()

        start_date = self.request.GET.get('start_date', None)
        end_date = self.request.GET.get('end_date', None)

        if start_date and end_date:
            qs = qs.filter(appt_datetime__date__range=[start_date, end_date])
        return qs
