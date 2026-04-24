from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler


def _normalize_validation_detail(detail):
    if isinstance(detail, dict):
        return {key: _normalize_validation_detail(value) for key, value in detail.items()}
    if isinstance(detail, list):
        return [_normalize_validation_detail(item) for item in detail]
    if isinstance(detail, ErrorDetail):
        return str(detail)
    return detail


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = "api_error"
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        code = "validation_error"
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        code = "authentication_error"
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        code = "permission_denied"
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = "not_found"

    payload = {
        "code": code,
        "detail": "Wystapil blad.",
    }

    if isinstance(response.data, dict):
        normalized = _normalize_validation_detail(response.data)
        if "detail" in normalized and isinstance(normalized["detail"], str):
            payload["detail"] = normalized["detail"]
        else:
            payload["detail"] = "Bledne dane wejsciowe."
            payload["fields"] = normalized
    elif isinstance(response.data, list):
        payload["detail"] = "Bledne dane wejsciowe."
        payload["fields"] = _normalize_validation_detail(response.data)
    else:
        payload["detail"] = str(response.data)

    response.data = {"error": payload}
    return response

