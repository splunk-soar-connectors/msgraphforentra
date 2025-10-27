# File: msgraphforentra_consts.py
#
# Copyright (c) 2022-2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.

# Define your constants here
MSGENTRA_USER_AGENT = "M365dPartner-Splunk-SOAR/{product_version}"
MSGENTRA_AUTHORIZATION_HEADER = "Bearer {token}"
MSGENTRA_APP_DT_STR_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

MSGENTRA_SOAR_BASE_URL = "{soar_base_url}rest"
MSGENTRA_SOAR_SYS_INFO_URL = "/system_info"
MSGENTRA_SOAR_ASSET_INFO_URL = "/asset/{asset_id}"
MSGENTRA_TC_FILE = "oauth_task.out"
MSGENTRA_CONFIG_TENANT_ID = "tenant_id"
MSGENTRA_CONFIG_CLIENT_ID = "client_id"
MSGENTRA_CONFIG_CLIENT_SECRET = "client_secret"  # pragma: allowlist secret
MSGENTRA_CONFIG_TIMEOUT = "timeout"
MSGENTRA_CONFIG_CERTIFICATE_THUMBPRINT = "certificate_thumbprint"
MSGENTRA_CONFIG_CERTIFICATE_PRIVATE_KEY = "certificate_private_key"  # pragma: allowlist secret

MSGENTRA_CBA_FIELDS_ERROR = (
    "Client Secret was not specified, in which case Certificate Thumbprint and Certificate Private Key Location are required"
)
MSGENTRA_CBA_AUTH_ERROR = "Certificate Based Authentication requires both Certificate Thumbprint and Certificate Private Key"
MSGENTRA_FIELD_CONFLICT_ERROR = (
    "Client Secret was specified as well as Certificate Thumbprint or Certificate Private Key Location. "
    "If Client Secret has a value, Certificate Thumbprint and Certificate Private Key Location values must"
    " be removed. Alternatively, if Certificate Thumbprint"
    " and Certificate Private Key Location have values, Client Secret value must be removed"
)
MSGENTRA_CBA_INTERACTIVE_ERROR = "Certificate Based Authorization requires Non-Interactive Auth to be checked"
MSGENTRA_CBA_KEY_ERROR = "Error occurred while parsing the private key, is it in .PEM format?"

MSGENTRA_TOKEN_STRING = "token"
MSGENTRA_ACCESS_TOKEN_STRING = "access_token"
MSGENTRA_CODE_STRING = "code"
MSGENTRA_REFRESH_TOKEN_STRING = "refresh_token"
MSGENTRA_ID_TOKEN_STRING = "id_token"
MSGENTRA_CLIENT_CREDENTIALS_STRING = "client_credentials"
MSGENTRA_BASE_URL_NOT_FOUND_MSG = "Splunk SOAR Base URL not found in System Settings. Please specify this value in System Settings"
MSGENTRA_AUTHORIZE_URL = (
    "/{tenant_id}/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}"
    "&response_type={response_type}&state={state}&resource={resource}"
)
MSGENTRA_RECEIVED_RISK_DETECTION_INFO_MSG = "Received risk detection info"

MSGENTRA_LIST_RISK_EVENTS_ENDPOINT = "/identityProtection/riskDetections"
MSGENTRA_LIST_RISKY_USERS_ENDPOINT = "/identityProtection/riskyUsers"
MSGENTRA_DISMISS_RISKY_USERS_ENDPOINT = "/identityProtection/riskyUsers/dismiss"
MSGENTRA_LIST_SIGNINS_ENDPOINT = "/auditLogs/signins"
MSGENTRA_GET_SIGNIN_ENDPOINT = "/auditLogs/signins"
MSGENTRA_LIST_DEVICES_ENDPOINT = "/devices"
MSGENTRA_SERVER_TOKEN_URL = "/{tenant_id}/oauth2/token"
MSGENTRA_LOGIN_BASE_URL = "https://login.microsoftonline.com"
MSGENTRA_RESOURCE_URL = "https://graph.microsoft.com"
MSGENTRA_MSGRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
MSGENTRA_AUTHORIZE_USER_MSG = "Please authorize user in a separate tab using URL"
MSGENTRA_GENERATING_ACCESS_TOKEN_MSG = "Generating access token"
MSGENTRA_ALERTS_INFO_MSG = "Getting info about alerts"
MSGENTRA_MAKING_CONNECTION_MSG = "Making Connection..."
MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG = "Test Connectivity Failed"
MSGENTRA_TEST_CONNECTIVITY_PASSED_MSG = "Test Connectivity Passed"
MSGENTRA_OAUTH_URL_MSG = "Using OAuth URL:"
MSGENTRA_CODE_RECEIVED_MSG = "Code Received"
MSGENTRA_CLIENT_CREDENTIALS_STRING = "client_credentials"
MSGENTRA_TOKEN_NOT_AVAILABLE_MSG = "Token not available. Please run test connectivity first"
MSGENTRA_TOKEN_EXPIRED = "Status Code: 401"
MSGENTRA_STATE_FILE_CORRUPT_ERROR = "Error occurred while loading the state file due to its unexpected format. \
    Resetting the state file with the default format. \
    Please run the 'test connectivity' action again."

MSGENTRA_AUTHORIZE_WAIT_TIME = 15
MSGENTRA_TC_STATUS_SLEEP = 3
MSGENTRA_TC_STATUS_WAIT_TIME = 105

# Constants relating to '_validate_integer'
MSGENTRA_VALID_INTEGER_MSG = "Please provide a valid integer value in the {} parameter"

MSGENTRA_NON_NEG_NON_ZERO_INT_MSG = "Please provide a valid non-zero positive integer value in the {} parameter"
MSGENTRA_NON_NEG_INT_MSG = "Please provide a valid non-negative integer value in the {} parameter"

# Constants relating to '_get_error_message_from_exception'
MSGENTRA_ERROR_MSG_UNAVAILABLE = "Error message unavailable. Please check the asset configuration and|or action parameters"

# For encryption and decryption
MSGENTRA_ENCRYPTION_ERROR = "Error occurred while encrypting the state file"
MSGENTRA_DECRYPTION_ERROR = "Error occurred while decrypting the state file"
MSGENTRA_UNEXPECTED_RESPONSE_ERROR = "Unexpected response retrieved"
MSGENTRA_STATE_IS_ENCRYPTED = "is_encrypted"

MSGENTRA_INCIDENT_LIMIT = "limit"
MSGENTRA_INCIDENT_OFFSET = "offset"
MSGENTRA_INCIDENT_FILTER = "filter"
MSGENTRA_INCIDENT_ORDER_BY = "orderby"
MSGENTRA_FILTER_START_DATETIME = "filter_start_datetime"
MSGENTRA_FILTER_END_DATETIME = "filter_end_datetime"
MSGENTRA_SIGNIN_ID = "signin_id"
MSGENTRA_ACTION_TAKEN = "action_taken"
MSGENTRA_INGESTION_DEFAULT_LIMIT = 50
MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE = 250
MSGENTRA_INCIDENT_DEFAULT_LIMIT_FOR_SCHEDULE_POLLING = 50
DEFAULT_TIMEOUT = 30
MSGENTRA_ALERT_DEFAULT_LIMIT = 2000
MSGENTRA_INCIDENT_DEFAULT_OFFSET = 0
MSGENTRA_NEXT_PAGE_TOKEN = "@odata.nextLink"
MSGENTRA_LIST_INCIDENTS_ENDPOINT = "/security/incidents"
MSGENTRA_DEFAULT_LOOKBACK_DAYS = 7

MSGENTRA_RUN_CONNECTIVITY_MSG = (
    "Please run test connectivity first to complete authorization flow and generate a token that the app can use to make calls to the server "
)
MSGENTRA_LIMIT_KEY = "'limit' action parameter"
MSGENTRA_OFFSET_KEY = "'offset' action parameter"
MSGENTRA_TIMEOUT_KEY = "'timeout' asset parameter"

MSGENTRA_DISMISSED_RISKY_USER_SUCCESSFULLY = "Successfully dismissed risk for specified userids"

MSGENTRA_HTTP_401_STATUS_CODE = "401"
MSGENTRA_UNAUTHORIZED_CLIENT_ERROR_MSG = "unauthorized_client"
MSGENTRA_INVALID_TENANT_ID_FORMAT_ERROR_CODE = "AADSTS900023"
MSGENTRA_INVALID_TENANT_ID_NOT_FOUND_ERROR_CODE = "AADSTS90002"

MSGENTRA_ASSET_PARAM_CHECK_LIST_ERRORS = [
    MSGENTRA_HTTP_401_STATUS_CODE,
    MSGENTRA_UNAUTHORIZED_CLIENT_ERROR_MSG,
    MSGENTRA_INVALID_TENANT_ID_FORMAT_ERROR_CODE,
    MSGENTRA_INVALID_TENANT_ID_NOT_FOUND_ERROR_CODE,
]

# For on_poll action:
MSGENTRA_APP_DT_STR_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
MSGENTRA_CONFIG_START_TIME_SCHEDULED_POLL = "start_time"
MSGENTRA_CONFIG_MAX_INGESTION = "max_ingestions"
MSGENTRA_CONFIG_FILTER_RISK_DETECTIONS_SCHEDULED_POLL = "filter_risk_detections"
MSGENTRA_CONFIG_FILTER_RISKY_USERS_SCHEDULED_POLL = "filter_risky_users"
STATE_FIRST_RUN = "first_run"

STATE_RISK_DETECTIONS_LAST_TIME = "risk_detections_last_time"
MSGENTRA_RISK_DETECTION_JSON_LAST_MODIFIED = "lastUpdatedDateTime"
MSGENTRA_RISK_DETECTIONS_ORDER_BY = "lastUpdatedDateTime"
MSGENTRA_RISKY_USERS_ORDER_BY = "riskLastUpdatedDateTime"

STATE_RISKY_USERS_LAST_TIME = "risky_users_last_time"
MSGENTRA_RISKY_USERS_JSON_LAST_MODIFIED = "riskLastUpdatedDateTime"

LOG_UTC_SINCE_TIME_ERROR = "Please provide time in the span of UTC time since Unix epoch 1970-01-01T00:00:00Z."
LOG_GREATER_EQUAL_TIME_ERROR = "Invalid {0}, can not be greater than or equal to current UTC time"
LOG_CONFIG_TIME_POLL_NOW = "'Time range for POLL NOW' or 'Start Time for Schedule/Manual POLL' asset configuration parameter"
