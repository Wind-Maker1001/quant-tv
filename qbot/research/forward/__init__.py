"""Leakage-safe, append-only paper forward-test primitives.

Importing this package has no network, broker, or trading side effects.
"""

from .activation import (
    ForwardActivation,
    ForwardActivationError,
    activation_id,
    load_forward_activation,
    register_forward_activation,
)
from .contract import (
    forward_contract_json,
    forward_contract_payload,
    forward_contract_sha256,
    selected_forward_model_parameters,
)
from .model_bundle import (
    BundleExistsError,
    BundleIntegrityError,
    FinalModelFit,
    FrozenModelBundle,
    ModelBundleError,
    fit_and_save_model_bundle,
    fit_final_model,
    load_model_bundle,
    save_model_bundle,
)
from .policy import ForwardTiming, ForwardTimingError, classify_forward_timing
from .integrity import (
    ForwardIntegrityError,
    ForwardWorkflowLockError,
    assert_no_link_components,
    research_source_sha256,
    workflow_lock,
)

from .signal_recorder import (
    FORWARD_PREDICTION_COLUMNS,
    FORWARD_SIGNAL_COLUMNS,
    SignalLockError,
    SignalLockTimeoutError,
    SignalRecord,
    SignalRecorder,
    SignalRecorderError,
    SignalValidationError,
    SignalVersionConflictError,
    finalize_signal_record,
    load_prediction_record,
    load_signal_record,
    record_signals,
)

__all__ = [
    "BundleExistsError",
    "BundleIntegrityError",
    "FinalModelFit",
    "FORWARD_PREDICTION_COLUMNS",
    "FORWARD_SIGNAL_COLUMNS",
    "ForwardActivation",
    "ForwardActivationError",
    "ForwardIntegrityError",
    "ForwardTiming",
    "ForwardTimingError",
    "ForwardWorkflowLockError",
    "FrozenModelBundle",
    "ModelBundleError",
    "SignalLockError",
    "SignalLockTimeoutError",
    "SignalRecord",
    "SignalRecorder",
    "SignalRecorderError",
    "SignalValidationError",
    "SignalVersionConflictError",
    "activation_id",
    "assert_no_link_components",
    "classify_forward_timing",
    "fit_and_save_model_bundle",
    "fit_final_model",
    "finalize_signal_record",
    "forward_contract_json",
    "forward_contract_payload",
    "forward_contract_sha256",
    "load_forward_activation",
    "load_model_bundle",
    "load_prediction_record",
    "load_signal_record",
    "record_signals",
    "register_forward_activation",
    "research_source_sha256",
    "save_model_bundle",
    "selected_forward_model_parameters",
    "workflow_lock",
]
