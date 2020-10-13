from edc_call_manager.model_caller import ModelCaller, DAILY
from edc_call_manager.decorators import register
from flourish_maternal.models import SubjectConsent, MaternalLocator
from edc_call_manager.models import Call, Log, LogEntry

from ..models import WorkList


@register(WorkList)
class WorkListFollowUpModelCaller(ModelCaller):
    call_model = (Call)
    locator_model = (MaternalLocator, 'subject_identifier')
    consent_model = (SubjectConsent, 'subject_identifier')
    log_entry_model = LogEntry
    log_model = Log
    interval = DAILY
