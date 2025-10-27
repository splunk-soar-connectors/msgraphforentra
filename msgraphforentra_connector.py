# File: msgraphforentra_connector.py
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
#
#

import ast
import grp
import hashlib
import json
import os
import pwd
import re
import time
import traceback
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode

import encryption_helper
import msal
import phantom.app as phantom
import requests
from bs4 import BeautifulSoup
from django.http import HttpResponse
from phantom.action_result import ActionResult
from phantom.base_connector import BaseConnector

import msgraphforentra_consts as consts


def _handle_oauth_start(request, path_parts):
    # get the asset id, the state file is created for each asset
    asset_id = request.GET.get("asset_id")
    if not asset_id:
        return HttpResponse("ERROR: Asset ID not found in URL", content_type="text/plain", status=404)

    # Load the state that was created for the asset
    state = _load_app_state(asset_id)
    if not state:
        return HttpResponse(
            "ERROR: The asset ID is invalid or an error occurred while reading the state file",
            content_type="text/plain",
            status=400,
        )

    # get the url to point to the authorize url of OAuth
    admin_consent_url = state.get("admin_consent_url")

    if not admin_consent_url:
        return HttpResponse(
            "App state is invalid, admin_consent_url key not found",
            content_type="text/plain",
            status=400,
        )

    # Redirect to this link, the user will then require to enter credentials interactively
    response = HttpResponse(status=302)
    response["Location"] = admin_consent_url

    return response


def _handle_rest_request(request, path_parts):
    """Handle requests for authorization.

    :param request: Data given to REST endpoint
    :param path_parts: parts of the URL passed
    :return: dictionary containing response parameters
    """

    if len(path_parts) < 2:
        return HttpResponse("error: True, message: Invalid REST endpoint request", content_type="text/plain", status=404)

    call_type = path_parts[1]

    # To handle authorize request in test connectivity action
    if call_type == "start_oauth":
        return _handle_login_redirect(request, "authorization_url")

    # To handle response from microsoft login page
    if call_type == "result":
        return_val = _handle_login_response(request)
        asset_id = request.GET.get("state")  # nosemgrep
        if asset_id and asset_id.isalnum():
            app_dir = os.path.dirname(os.path.abspath(__file__))
            auth_status_file_path = f"{app_dir}/{asset_id}_{consts.MSGENTRA_TC_FILE}"
            real_auth_status_file_path = os.path.abspath(auth_status_file_path)
            if not os.path.dirname(real_auth_status_file_path) == app_dir:
                return HttpResponse("Error: Invalid asset_id", content_type="text/plain", status=400)
            open(auth_status_file_path, "w").close()
            try:
                uid = pwd.getpwnam("apache").pw_uid
                gid = grp.getgrnam("phantom").gr_gid
                os.chown(auth_status_file_path, uid, gid)
                os.chmod(auth_status_file_path, "0664")
            except Exception:
                pass

        return return_val
    return HttpResponse("error: Invalid endpoint", content_type="text/plain", status=404)


def _handle_login_redirect(request, key):
    """This function is used to redirect login request to Microsoft login page.

    :param request: Data given to REST endpoint
    :param key: Key to search in state file
    :return: response authorization_url/admin_consent_url
    """

    asset_id = request.GET.get("asset_id")
    if not asset_id:
        return HttpResponse("ERROR: Asset ID not found in URL", content_type="text/plain", status=400)
    state = _load_app_state(asset_id)
    if not state:
        return HttpResponse("ERROR: Invalid asset_id", content_type="text/plain", status=400)
    url = state.get(key)
    if not url:
        return HttpResponse(f"App state is invalid, {key} not found.", content_type="text/plain", status=400)
    response = HttpResponse(status=302)
    response["Location"] = url
    return response


def _load_app_state(asset_id, app_connector=None):
    """This function is used to load the current state file.

    :param asset_id: asset_id
    :param app_connector: Object of app_connector class
    :return: state: Current state file as a dictionary
    """

    asset_id = str(asset_id)
    if not asset_id or not asset_id.isalnum():
        if app_connector:
            app_connector.debug_print("In _load_app_state: Invalid asset_id")
        return {}

    app_dir = os.path.dirname(os.path.abspath(__file__))
    state_file = f"{app_dir}/{asset_id}_state.json"
    real_state_file_path = os.path.abspath(state_file)
    if not os.path.dirname(real_state_file_path) == app_dir:
        if app_connector:
            app_connector.debug_print("In _load_app_state: Invalid asset_id")
        return {}

    state = {}
    try:
        with open(real_state_file_path) as state_file_obj:
            state_file_data = state_file_obj.read()
            state = json.loads(state_file_data)
    except Exception as e:
        if app_connector:
            app_connector.debug_print(f"In _load_app_state: Exception: {e!s}")

    if app_connector:
        app_connector.debug_print("Loaded state: ", state)

    return state


def _save_app_state(state, asset_id, app_connector):
    """This function is used to save current state in file.

    :param state: Dictionary which contains data to write in state file
    :param asset_id: asset_id
    :param app_connector: Object of app_connector class
    :return: status: phantom.APP_SUCCESS
    """

    asset_id = str(asset_id)
    if not asset_id or not asset_id.isalnum():
        if app_connector:
            app_connector.debug_print("In _save_app_state: Invalid asset_id")
        return {}

    app_dir = os.path.split(__file__)[0]
    state_file = f"{app_dir}/{asset_id}_state.json"

    real_state_file_path = os.path.abspath(state_file)
    if not os.path.dirname(real_state_file_path) == app_dir:
        if app_connector:
            app_connector.debug_print("In _save_app_state: Invalid asset_id")
        return {}

    if app_connector:
        app_connector.debug_print("Saving state: ", state)

    try:
        with open(real_state_file_path, "w+") as state_file_obj:
            state_file_obj.write(json.dumps(state))
    except Exception as e:
        print(f"Unable to save state file: {e!s}")

    return phantom.APP_SUCCESS


def _handle_login_response(request):
    """This function is used to get the login response of authorization request from Microsoft login page.

    :param request: Data given to REST endpoint
    :return: HttpResponse. The response displayed on authorization URL page
    """

    asset_id = request.GET.get("state")
    if not asset_id:
        return HttpResponse(f"ERROR: Asset ID not found in URL\n{json.dumps(request.GET)}", content_type="text/plain", status=400)

    # Check for error in URL
    error = request.GET.get("error")
    error_description = request.GET.get("error_description")

    # If there is an error in response
    if error:
        message = f"Error: {error}"
        if error_description:
            message = f"{message} Details: {error_description}"
        return HttpResponse(f"Server returned {message}", content_type="text/plain", status=400)

    code = request.GET.get(consts.MSGENTRA_CODE_STRING)

    # If code is not available
    if not code:
        return HttpResponse(f"Error while authenticating\n{json.dumps(request.GET)}", content_type="text/plain", status=400)

    state = _load_app_state(asset_id)

    # If value of admin_consent is not available, value of code is available
    try:
        state[consts.MSGENTRA_CODE_STRING] = code
        state[consts.MSGENTRA_STATE_IS_ENCRYPTED] = True
    except Exception as e:
        return HttpResponse(f"{consts.MSGENTRA_DECRYPTION_ERROR}: {e!s}", content_type="text/plain", status=400)

    _save_app_state(state, asset_id, None)

    return HttpResponse("Code received. Please close this window, the action will continue to get new token.", content_type="text/plain")


def _get_dir_name_from_app_name(app_name):
    """Get name of the directory for the app.

    :param app_name: Name of the application for which directory name is required
    :return: app_name: Name of the directory for the application
    """

    app_name = "".join([x for x in app_name if x.isalnum()])
    app_name = app_name.lower()
    if not app_name:
        app_name = "app_for_phantom"
    return app_name


def hash_values_sha256(values):
    all_values = b"".join(str(v).encode("utf-8") for v in values)
    return hashlib.sha256(all_values).hexdigest()


class RetVal(tuple):
    def __new__(cls, val1, val2=None):
        return tuple.__new__(RetVal, (val1, val2))


class MsGraphForEntra_Connector(BaseConnector):
    def __init__(self):
        # Call the BaseConnectors init first
        super().__init__()
        self._state = None
        self._tenant = None
        self._client_id = None
        self._access_token = None
        self._refresh_token = None
        self._client_secret = None
        self._non_interactive = None
        self._asset_id = None
        self._cba_auth = None
        self._certificate_thumbprint = None
        self._certificate_private_key = None

    def load_state(self):
        """
        Load the contents of the state file to the state dictionary and decrypt it.

        :return: loaded state
        """
        state = super().load_state()
        if not isinstance(state, dict):
            self.debug_print("Resetting the state file with the default format")
            state = {"app_version": self.get_app_json().get("app_version")}
            return state
        return self._decrypt_state(state)

    def save_state(self, state):
        """
        Encrypt and save the current state dictionary to the state file.

        :param state: state dictionary
        :return: status
        """
        return super().save_state(self._encrypt_state(state))

    def update_state_fields(self, value, helper_function, error_message):
        try:
            return helper_function(value, self._asset_id)
        except Exception as ex:
            self.debug_print(f"{error_message}: {self._get_error_message_from_exception(ex)}")
        return None

    def check_state_fields(self, state, helper_function, error_message):
        access_token = state.get("access_token")
        if access_token:
            state["access_token"] = self.update_state_fields(access_token, helper_function, error_message)
        refresh_token = state.get("refresh_token")
        if refresh_token:
            state["refresh_token"] = self.update_state_fields(refresh_token, helper_function, error_message)
        return state

    def _decrypt_state(self, state):
        """
        Decrypts the state.

        :param state: state dictionary
        :return: decrypted state
        """
        if not state.get("is_encrypted"):
            return state
        return self.check_state_fields(state, encryption_helper.decrypt, consts.MSGENTRA_DECRYPTION_ERROR)

    def _encrypt_state(self, state):
        """
        Encrypts the state.

        :param state: state dictionary
        :return: encrypted state
        """

        state = self.check_state_fields(state, encryption_helper.encrypt, consts.MSGENTRA_ENCRYPTION_ERROR)
        state["is_encrypted"] = True

        return state

    def _process_empty_response(self, response, action_result):
        """This function is used to process empty response.

        :param response: response data
        :param action_result: object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        if response.status_code in [200, 204]:
            return RetVal(phantom.APP_SUCCESS, {})

        return RetVal(
            action_result.set_status(
                phantom.APP_ERROR, f"Status Code: {response.status_code}. Error: Empty response and no information in the header"
            ),
            None,
        )

    def _process_html_response(self, response, action_result):
        """This function is used to process html response.

        :param response: response data
        :param action_result: object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        # An html response, treat it like an error
        status_code = response.status_code

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            # Remove the script, style, footer and navigation part from the HTML message
            for element in soup(["script", "style", "footer", "nav"]):
                element.extract()
            error_text = soup.text
            split_lines = error_text.split("\n")
            split_lines = [x.strip() for x in split_lines if x.strip()]
            error_text = "\n".join(split_lines)
        except Exception:
            error_text = "Cannot parse error details"

        if not error_text:
            error_text = "Error message unavailable. Please check the asset configuration and|or the action parameters"

        message = f"Status Code: {status_code}. Data from server:\n{error_text}\n"

        message = message.replace("{", "{{").replace("}", "}}")

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_json_response(self, response, action_result):
        """This function is used to process json response.

        :param response: response data
        :param action_result: object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        try:
            # Process a json response
            resp_json = response.json()
        except Exception as e:
            return RetVal(
                action_result.set_status(
                    phantom.APP_ERROR, f"Unable to parse JSON response. Error: {self._get_error_message_from_exception(e)}"
                ),
                None,
            )

        # Please specify the status codes here
        if 200 <= response.status_code < 399:
            return RetVal(phantom.APP_SUCCESS, resp_json)

        message = None

        # Check whether the response contains error and error description fields
        # This condition will be used in test_connectivity
        if not isinstance(resp_json.get("error"), dict) and resp_json.get("error_description"):
            err = "Error:{}, Error Description:{} Please check your asset configuration parameters and run the test connectivity".format(
                resp_json.get("error"), resp_json.get("error_description")
            )
            message = f"Error from server. Status Code: {response.status_code} Data from server: {err}"

        # For other actions
        if isinstance(resp_json.get("error"), dict) and resp_json.get("error", {}).get(consts.MSGENTRA_CODE_STRING):
            msg = resp_json.get("error", {}).get("message")
            if "text/html" in msg:
                msg = BeautifulSoup(msg, "html.parser")
                for element in msg(["title"]):
                    element.extract()
                message = "Error from server. Status Code: {} Error Code: {} Data from server: {}".format(
                    response.status_code, resp_json.get("error", {}).get(consts.MSGENTRA_CODE_STRING), msg.text
                )
            else:
                message = "Error from server. Status Code: {} Error Code: {} Data from server: {}".format(
                    response.status_code, resp_json.get("error", {}).get(consts.MSGENTRA_CODE_STRING), msg
                )

        if not message:
            message = "Error from server. Status Code: {} Data from server: {}".format(
                response.status_code, response.text.replace("{", "{{").replace("}", "}}")
            )

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _process_response(self, response, action_result):
        """This function is used to process html response.

        :param response: response data
        :param action_result: object of Action Result
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message)
        """

        # store the response_text in debug data, it will get dumped in the logs if the action fails
        if hasattr(action_result, "add_debug_data"):
            action_result.add_debug_data({"r_status_code": response.status_code})
            action_result.add_debug_data({"r_text": response.text})
            action_result.add_debug_data({"r_headers": response.headers})

        # Process each 'Content-Type' of response separately

        if "json" in response.headers.get("Content-Type", ""):
            return self._process_json_response(response, action_result)

        if "text/javascript" in response.headers.get("Content-Type", ""):
            return self._process_json_response(response, action_result)

        # Process an HTML response, Do this no matter what the api talks.
        # There is a high chance of a PROXY in between SOAR and the rest of
        # world, in case of errors, PROXY's return HTML, this function parses
        # the error and adds it to the action_result.
        if "html" in response.headers.get("Content-Type", ""):
            return self._process_html_response(response, action_result)

        # it's not content-type that is to be parsed, handle an empty response
        if not response.text:
            return self._process_empty_response(response, action_result)

        # everything else is actually an error at this point
        message = "Can't process response from server. Status Code: {} Data from server: {}".format(
            response.status_code, response.text.replace("{", "{{").replace("}", "}}")
        )

        return RetVal(action_result.set_status(phantom.APP_ERROR, message), None)

    def _validate_integer(self, action_result, parameter, key, allow_zero=True):
        if parameter is not None:
            try:
                if not float(parameter).is_integer():
                    return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_VALID_INTEGER_MSG.format(key)), None

                parameter = int(parameter)
            except Exception:
                return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_VALID_INTEGER_MSG.format(key)), None

            # Negative value validation
            if parameter < 0:
                return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_NON_NEG_INT_MSG.format(key)), None

            # Zero value validation
            if not allow_zero and parameter == 0:
                return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_NON_NEG_NON_ZERO_INT_MSG.format(key)), None

        return phantom.APP_SUCCESS, parameter

    def _get_error_message_from_exception(self, e):
        """
        Get appropriate error message from the exception.
        :param e: Exception object
        :return: error message
        """

        error_code = None
        error_msg = consts.MSGENTRA_ERROR_MSG_UNAVAILABLE

        self.error_print("Error occurred.", e)

        try:
            if hasattr(e, "args"):
                if len(e.args) > 1:
                    error_code = e.args[0]
                    error_msg = e.args[1]
                elif len(e.args) == 1:
                    error_msg = e.args[0]
        except Exception:
            self.debug_print("Error occurred while fetching exception information")

        if not error_code:
            error_text = f"Error Message: {error_msg}"
        else:
            error_text = f"Error Code: {error_code}. Error Message: {error_msg}"

        return error_text

    def _update_request(self, action_result, endpoint, headers=None, params=None, data=None, method="get"):
        """This function is used to update the headers with access_token before making REST call.

        :param endpoint: REST endpoint that needs to appended to the service address
        :param action_result: object of ActionResult class
        :param headers: request headers
        :param params: request parameters
        :param data: request body
        :param method: GET/POST/PUT/DELETE/PATCH (Default will be GET)
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        response obtained by making an API call
        """

        if not headers:
            headers = {}

        if not self._non_interactive:
            token_data = {
                "client_id": self._client_id,
                "grant_type": consts.MSGENTRA_REFRESH_TOKEN_STRING,
                "refresh_token": self._refresh_token,
                "client_secret": self._client_secret,
                "resource": consts.MSGENTRA_RESOURCE_URL,
            }
        else:
            token_data = {
                "client_id": self._client_id,
                "grant_type": consts.MSGENTRA_CLIENT_CREDENTIALS_STRING,
                "client_secret": self._client_secret,
                "resource": consts.MSGENTRA_RESOURCE_URL,
            }

        if not self._access_token and not self._cba_auth:
            if self._non_interactive:
                status = self._generate_new_access_token(action_result=action_result, data=token_data)

                if phantom.is_fail(status):
                    return action_result.get_status(), None

            if not self._non_interactive and not self._refresh_token:
                # If none of the access_token and refresh_token is available
                return action_result.set_status(phantom.APP_ERROR, status_message=consts.MSGENTRA_TOKEN_NOT_AVAILABLE_MSG), None

            if not self._non_interactive:
                # If refresh_token is available and access_token is not available, generate new access_token
                status = self._generate_new_access_token(action_result=action_result, data=token_data)

                if phantom.is_fail(status):
                    return action_result.get_status(), None

        headers.update(
            {
                "Authorization": f"Bearer {self._access_token}",
                "Accept": "application/json",
                "User-Agent": consts.MSGENTRA_USER_AGENT.format(product_version=self.get_app_json().get("app_version")),
                "Content-Type": "application/json",
            }
        )

        ret_val, resp_json = self._make_rest_call(
            action_result=action_result, endpoint=endpoint, headers=headers, params=params, data=data, method=method
        )

        # If token is expired, generate new token
        if consts.MSGENTRA_TOKEN_EXPIRED in action_result.get_message():
            self.debug_print("***** EXPIRED TOKEN")
            # Token is invalid, so set it to None to regenerate
            self._access_token = None
            status = self._generate_new_access_token(action_result=action_result, data=token_data)

            if phantom.is_fail(status):
                return action_result.get_status(), None

            action_result.set_status(phantom.APP_SUCCESS, "Token generated successfully")
            headers.update({"Authorization": f"Bearer {self._access_token}"})

            ret_val, resp_json = self._make_rest_call(
                action_result=action_result, endpoint=endpoint, headers=headers, params=params, data=data, method=method
            )
        else:
            self.debug_print("***** TOKEN WAS NOT EXPIRED")

        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        return phantom.APP_SUCCESS, resp_json

    def _make_rest_call(self, endpoint, action_result, headers=None, params=None, data=None, method="get", verify=True):
        """Function that makes the REST call to the app.

        :param endpoint: REST endpoint that needs to appended to the service address
        :param action_result: object of ActionResult class
        :param headers: request headers
        :param params: request parameters
        :param data: request body
        :param method: GET/POST/PUT/DELETE/PATCH (Default will be GET)
        :param verify: verify server certificate (Default True)
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        response obtained by making an API call
        """

        resp_json = None
        if headers is None:
            headers = {}

        headers.update({"User-Agent": consts.MSGENTRA_USER_AGENT.format(product_version=self.get_app_json().get("app_version"))})
        try:
            request_func = getattr(requests, method)
        except AttributeError:
            return RetVal(action_result.set_status(phantom.APP_ERROR, f"Invalid method: {method}"), resp_json)

        flag = True
        while flag:
            try:
                response = request_func(endpoint, data=data, headers=headers, verify=verify, params=params, timeout=self._timeout)
            except Exception as e:
                self.debug_print(f"Exception Message - {e!s}")
                return RetVal(
                    action_result.set_status(
                        phantom.APP_ERROR, f"Error Connecting to server. Details: {self._get_error_message_from_exception(e)}"
                    ),
                    resp_json,
                )

            if response.status_code == 429 and response.headers["Retry-After"]:
                retry_time = int(response.headers["Retry-After"])
                if retry_time > 300:  # throw error if wait time greater than 300 seconds
                    flag = False
                    return RetVal(
                        action_result.set_status(phantom.APP_ERROR, f"Error occured : {response.status_code}, {response.text!s}"),
                        resp_json,
                    )
                self.debug_print(f"Retrying after {retry_time} seconds")
                time.sleep(retry_time + 1)
            else:
                flag = False

        return self._process_response(response, action_result)

    def _get_asset_name(self, action_result):
        """Get name of the asset using SOAR URL.

        :param action_result: object of ActionResult class
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message), asset name
        """

        asset_id = self.get_asset_id()
        rest_endpoint = consts.MSGENTRA_SOAR_ASSET_INFO_URL.format(asset_id=asset_id)
        url = f"{consts.MSGENTRA_SOAR_BASE_URL.format(soar_base_url=self.get_phantom_base_url())}{rest_endpoint}"
        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=url, verify=False)

        if phantom.is_fail(ret_val):
            return ret_val, None

        asset_name = resp_json.get("name")
        if not asset_name:
            return action_result.set_status(phantom.APP_ERROR, f"Asset Name for id: {asset_id} not found.", None)
        return phantom.APP_SUCCESS, asset_name

    def _get_phantom_base_url_entra(self, action_result):
        """Get base url of phantom.

        :param action_result: object of ActionResult class
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        base url of phantom
        """

        url = f"{consts.MSGENTRA_SOAR_BASE_URL.format(soar_base_url=self.get_phantom_base_url())}{consts.MSGENTRA_SOAR_SYS_INFO_URL}"
        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=url, verify=False)
        if phantom.is_fail(ret_val):
            return ret_val, None

        soar_base_url = resp_json.get("base_url").rstrip("/")
        if not soar_base_url:
            return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_BASE_URL_NOT_FOUND_MSG), None
        return phantom.APP_SUCCESS, soar_base_url

    def _get_app_rest_url(self, action_result):
        """Get URL for making rest calls.

        :param action_result: object of ActionResult class
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS(along with appropriate message),
        URL to make rest calls
        """

        ret_val, soar_base_url = self._get_phantom_base_url_entra(action_result)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        ret_val, asset_name = self._get_asset_name(action_result)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        self.save_progress(f"Using SOAR base URL as: {soar_base_url}")
        app_json = self.get_app_json()
        app_name = app_json["name"]

        app_dir_name = _get_dir_name_from_app_name(app_name)
        url_to_app_rest = "{}/rest/handler/{}_{}/{}".format(soar_base_url, app_dir_name, app_json["appid"], asset_name)
        return phantom.APP_SUCCESS, url_to_app_rest

    def _get_private_key(self, action_result):
        # When the private key is copied/pasted to an asset parameter
        # SOAR converts \n to spaces. This code fixes that and rebuilds
        # the private key as it should be

        if self._certificate_private_key is not None:
            p = re.compile("(-----.*?-----) (.*) (-----.*?-----)")
            m = p.match(self._certificate_private_key)

            if m:
                private_key = "\n".join([m.group(1), m.group(2).replace(" ", "\n"), m.group(3)])
                return phantom.APP_SUCCESS, private_key
            else:
                return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_CBA_KEY_ERROR), None

    def _generate_new_cba_access_token(self, action_result):
        self.save_progress("Generating token using Certificate Based Authentication...")

        # Certificate Based Authentication requires both Certificate Thumbprint and Certificate Private Key
        if not (self._certificate_thumbprint and self._certificate_private_key):
            self.save_progress(consts.MSGENTRA_CBA_AUTH_ERROR)
            return self.set_status(phantom.APP_ERROR), None

        # Check non-interactive is enabled for CBA auth
        if not self._non_interactive:
            self.save_progress(consts.MSGENTRA_CBA_INTERACTIVE_ERROR)
            return self.set_status(phantom.APP_ERROR), None

        ret_val, self._private_key = self._get_private_key(action_result)
        if phantom.is_fail(ret_val):
            return action_result.get_status(), None

        authority = f"{consts.MSGENTRA_LOGIN_BASE_URL}/{self._tenant}"
        scope = [f"{consts.MSGENTRA_RESOURCE_URL}/.default"]

        try:
            app = msal.ConfidentialClientApplication(
                self._client_id,
                authority=authority,
                client_credential={"thumbprint": self._certificate_thumbprint, "private_key": self._private_key},
            )
            self.debug_print(f"Got app instance: {app}")
        except Exception as e:
            self.debug_print(f"Exception from MSAL call: {e}")
            return (
                action_result.set_status(
                    phantom.APP_ERROR,
                    f"Please check your configured parameters. Error while using certificate to authenticate. {e}",
                ),
                None,
            )

        result = None
        # Removing the check here, and just generating a new token
        # if self._access_token is None:

        result = app.acquire_token_for_client(scopes=scope)
        self.debug_print(f"Result from MSAL call: {result}")
        self._state = self.load_state()
        if result.get("access_token") is None:
            self.debug_print(f"No access token, result is\n{result}")
            return self.set_status(phantom.APP_ERROR), f"Return from MSAL api call {result}"

        self._access_token = result["access_token"]
        self._state["access_token"] = result["access_token"]
        # Save state
        self.save_state(self._state)
        self._state = self.load_state()

        return phantom.APP_SUCCESS

    def _generate_new_access_token(self, action_result, data):
        """This function is used to generate new access token using the code obtained on authorization.

        :param action_result: object of ActionResult class
        :param data: Data to send in REST call
        :return: status phantom.APP_ERROR/phantom.APP_SUCCESS
        """

        stack_list = traceback.format_stack()
        self.debug_print(f"_generate_new_access_token traceback: {stack_list}")
        # If using Certificate Based Auth, call separate function to generate and return new access token
        if self._cba_auth is True:
            retval = self._generate_new_cba_access_token(action_result=action_result)
            self.debug_print(f"retval from _generate_new_cba_access_token: {retval}")
            if phantom.is_fail(retval):
                self.debug_print(f"Failed to get token using CBA")
                self.save_progress(f"Failed to get token using CBA")
                return action_result.set_status(phantom.APP_ERROR, f"Failed to get token using CBA")
            else:
                return phantom.APP_SUCCESS

        req_url = f"{consts.MSGENTRA_LOGIN_BASE_URL}{consts.MSGENTRA_SERVER_TOKEN_URL.format(tenant_id=quote(self._tenant))}"

        ret_val, resp_json = self._make_rest_call(action_result=action_result, endpoint=req_url, data=urlencode(data), method="post")

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        if resp_json.get(consts.MSGENTRA_ID_TOKEN_STRING):
            resp_json.pop(consts.MSGENTRA_ID_TOKEN_STRING)

        try:
            self._access_token = resp_json[consts.MSGENTRA_ACCESS_TOKEN_STRING]
            if consts.MSGENTRA_REFRESH_TOKEN_STRING in resp_json:
                self._refresh_token = resp_json[consts.MSGENTRA_REFRESH_TOKEN_STRING]
        except Exception as e:
            err = self._get_error_message_from_exception(e)
            return action_result.set_status(phantom.APP_ERROR, f"Error occurred while generating access token {err}")

        self._state[consts.MSGENTRA_ACCESS_TOKEN_STRING] = self._access_token
        self._state[consts.MSGENTRA_REFRESH_TOKEN_STRING] = self._refresh_token
        self._state[consts.MSGENTRA_STATE_IS_ENCRYPTED] = True

        try:
            self.save_state(self._state)
        except Exception:
            return action_result.set_status(
                phantom.APP_ERROR,
                "Error occurred while parsing the state file. Please delete the state file and run the test connectivity again.",
            )

        self._state = self.load_state()

        # Scenario -
        #
        # If the corresponding state file doesn't have correct owner, owner group or permissions,
        # the newly generated token is not being saved to state file and automatic workflow for token has been stopped.
        # So we have to check that token from response and token which are saved
        # to state file after successful generation of new token are same or not.

        if self._access_token != self._state.get(consts.MSGENTRA_ACCESS_TOKEN_STRING):
            message = (
                "Error occurred while saving the newly generated access token (in place of the expired token) in the state file."
                " Please check the owner, owner group, and the permissions of the state file. The SOAR user should have "
                "the correct access rights and ownership for the corresponding state file (refer to readme file for more information)"
            )
            return action_result.set_status(phantom.APP_ERROR, message)

        if not self._non_interactive and self._refresh_token and self._refresh_token != self._state.get(consts.MSGENTRA_REFRESH_TOKEN_STRING):
            message = (
                "Error occurred while saving the newly generated refresh token in the state file."
                " Please check the owner, owner group, and the permissions of the state file. The SOAR user should have "
                "the correct access rights and ownership for the corresponding state file (refer to readme file for more information)"
            )
            return action_result.set_status(phantom.APP_ERROR, message)

        return phantom.APP_SUCCESS

    def _wait(self, action_result):
        """This function is used to hold the action till user login for 105 seconds.

        :param action_result: Object of ActionResult class
        :return: status (success/failed)
        """

        app_dir = os.path.dirname(os.path.abspath(__file__))
        # file to check whether the request has been granted or not
        auth_status_file_path = f"{app_dir}/{self.get_asset_id()}_{consts.MSGENTRA_TC_FILE}"
        time_out = False

        # wait-time while request is being granted for 105 seconds
        for _ in range(consts.MSGENTRA_TC_STATUS_WAIT_TIME // consts.MSGENTRA_TC_STATUS_SLEEP):
            self.send_progress("Waiting...")
            if os.path.isfile(auth_status_file_path):
                time_out = True
                os.unlink(auth_status_file_path)
                break
            time.sleep(consts.MSGENTRA_TC_STATUS_SLEEP)

        if not time_out:
            self.send_progress("")
            return action_result.set_status(phantom.APP_ERROR, "Timeout. Please try again later")
        self.send_progress("Authenticated")
        return phantom.APP_SUCCESS

    def _remove_tokens(self, action_result):
        if len(list(filter(lambda x: x in action_result.get_message(), consts.MSGENTRA_ASSET_PARAM_CHECK_LIST_ERRORS))) > 0:
            if self._state.get(consts.MSGENTRA_TOKEN_STRING, {}).get(consts.MSGENTRA_ACCESS_TOKEN_STRING):
                self._state[consts.MSGENTRA_TOKEN_STRING].pop(consts.MSGENTRA_ACCESS_TOKEN_STRING)
            if self._state.get(consts.MSGENTRA_TOKEN_STRING, {}).get(consts.MSGENTRA_REFRESH_TOKEN_STRING):
                self._state[consts.MSGENTRA_TOKEN_STRING].pop(consts.MSGENTRA_REFRESH_TOKEN_STRING)
            if self._state.get(consts.MSGENTRA_CODE_STRING):
                self._state.pop(consts.MSGENTRA_CODE_STRING)

    def _nuke_tokens_from_state_file(self):
        self.debug_print(f"Nuking access_token from state file")
        if self._state.get(consts.MSGENTRA_ACCESS_TOKEN_STRING):
            self._state.pop(consts.MSGENTRA_ACCESS_TOKEN_STRING)
            self.save_state(self._state)

    def _handle_test_connectivity(self, param):
        """Testing of given credentials and obtaining authorization for all other actions.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress(consts.MSGENTRA_MAKING_CONNECTION_MSG)

        if not self._state:
            self._state = {}

        if self._cba_auth:
            self.debug_print("In CBA Auth, running test connectivity")
            # We already have a auth_token at this point
            self.save_progress(consts.MSGENTRA_ALERTS_INFO_MSG)

            url = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_RISK_EVENTS_ENDPOINT}"
            params = {"$top": 1}  # page size of the result set

            ret_val, message = self._update_request(action_result=action_result, endpoint=url, params=params)
            if phantom.is_fail(ret_val):
                self.send_progress("")
                self._remove_tokens(action_result)
                # self.save_progress(message)
                self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG)
                return action_result.set_status(phantom.APP_ERROR, message)

            self.save_progress(consts.MSGENTRA_RECEIVED_RISK_DETECTION_INFO_MSG)
            self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_PASSED_MSG)
            return action_result.set_status(phantom.APP_SUCCESS)

        if not self._non_interactive:
            # Get initial REST URL
            ret_val, app_rest_url = self._get_app_rest_url(action_result)
            if phantom.is_fail(ret_val):
                self._remove_tokens(action_result)
                self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG)
                return action_result.get_status()

            # Append /result to create redirect_uri
            redirect_uri = f"{app_rest_url}/result"
            self._state["redirect_uri"] = redirect_uri

            self.save_progress(consts.MSGENTRA_OAUTH_URL_MSG)
            self.save_progress(redirect_uri)

            # Authorization URL used to make request for getting code which is used to generate access token
            authorization_url = consts.MSGENTRA_AUTHORIZE_URL.format(
                tenant_id=quote(self._tenant),
                client_id=quote(self._client_id),
                redirect_uri=redirect_uri,
                state=self.get_asset_id(),
                response_type=consts.MSGENTRA_CODE_STRING,
                resource=consts.MSGENTRA_RESOURCE_URL,
            )
            authorization_url = f"{consts.MSGENTRA_LOGIN_BASE_URL}{authorization_url}"

            self._state["authorization_url"] = authorization_url

            # URL which would be shown to the user
            url_for_authorize_request = f"{app_rest_url}/start_oauth?asset_id={self.get_asset_id()}&"
            _save_app_state(self._state, self.get_asset_id(), self)

            self.save_progress(consts.MSGENTRA_AUTHORIZE_USER_MSG)
            self.save_progress(url_for_authorize_request)  # nosemgrep

            # Wait time for authorization
            time.sleep(consts.MSGENTRA_AUTHORIZE_WAIT_TIME)

            # Wait for some while user login to Microsoft
            status = self._wait(action_result=action_result)

            # Empty message to override last message of waiting
            self.send_progress("")
            if phantom.is_fail(status):
                self._remove_tokens(action_result)
                self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG)
                return action_result.get_status()

            self.save_progress(consts.MSGENTRA_CODE_RECEIVED_MSG)
            self._state = _load_app_state(self.get_asset_id(), self)

            # if code is not available in the state file
            if not self._state or not self._state.get(consts.MSGENTRA_CODE_STRING):
                self._remove_tokens(action_result)
                return action_result.set_status(phantom.APP_ERROR, status_message=consts.MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG)

            current_code = self._state.get(consts.MSGENTRA_CODE_STRING)

        self.save_progress(consts.MSGENTRA_GENERATING_ACCESS_TOKEN_MSG)

        if not self._non_interactive:
            data = {
                "client_id": self._client_id,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                consts.MSGENTRA_CODE_STRING: current_code,
                "resource": consts.MSGENTRA_RESOURCE_URL,
                "client_secret": self._client_secret,
            }
        else:
            data = {
                "client_id": self._client_id,
                "grant_type": consts.MSGENTRA_CLIENT_CREDENTIALS_STRING,
                "client_secret": self._client_secret,
                "resource": consts.MSGENTRA_RESOURCE_URL,
            }
        # For first time access, new access token is generated
        ret_val = self._generate_new_access_token(action_result=action_result, data=data)

        if phantom.is_fail(ret_val):
            self.send_progress("")
            self._remove_tokens(action_result)
            self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG)
            return action_result.get_status()

        self.save_progress(consts.MSGENTRA_ALERTS_INFO_MSG)

        url = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_RISK_EVENTS_ENDPOINT}"
        params = {"$top": 1}  # page size of the result set

        ret_val, _ = self._update_request(action_result=action_result, endpoint=url, params=params)
        if phantom.is_fail(ret_val):
            self.send_progress("")
            self._remove_tokens(action_result)
            self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_FAILED_MSG)
            return action_result.get_status()

        self.save_progress(consts.MSGENTRA_RECEIVED_RISK_DETECTION_INFO_MSG)
        self.save_progress(consts.MSGENTRA_TEST_CONNECTIVITY_PASSED_MSG)
        return action_result.set_status(phantom.APP_SUCCESS)

    def _paginator(self, action_result, limit, page_size, endpoint, filter, orderby=None):
        """
        This method is used to get the "limit" of riskDetections and riskyUsers in one call

        :param action_result: Object of ActionResult class
        :param limit: Number of resource to be returned
        :param page_size: (Optional but useful during testing) Limits amount of events returned by each call
        :param endpoint: Endpoint to make REST call
        :param filter: Used to filter events
        """

        resource_list = []
        next_page_token = ""

        while True:
            params = {}
            if not next_page_token and filter:
                params["$filter"] = filter
            if not next_page_token and page_size:
                params["$top"] = page_size
            if not next_page_token and orderby:
                params["$orderby"] = orderby
            if next_page_token:
                endpoint = next_page_token

            # make rest call
            ret_val, response = self._update_request(endpoint=endpoint, action_result=action_result, params=params)

            if phantom.is_fail(ret_val):
                return action_result.get_status()

            if not response:
                return action_result.set_status(phantom.APP_ERROR, consts.MSGENTRA_UNEXPECTED_RESPONSE_ERROR)
            try:
                for ele in response["value"]:
                    resource_list.append(ele)
            except Exception as e:
                error_message = self._get_error_message_from_exception(e)
                self.debug_print(f"{consts.MSGENTRA_UNEXPECTED_RESPONSE_ERROR}: {error_message}")
                return action_result.set_status(phantom.APP_ERROR, f"Error occurred while fetching data. Details: {error_message}")
            if not response.get(consts.MSGENTRA_NEXT_PAGE_TOKEN):
                break

            next_page_token = response[consts.MSGENTRA_NEXT_PAGE_TOKEN]

            if len(resource_list) >= limit:
                break

        return resource_list[:limit]

    def _handle_list_risk_detections(self, param):
        """This function is used to handle the list risk events action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress(f"In action handler for: {self.get_action_identifier()}")

        action_result = self.add_action_result(ActionResult(dict(param)))

        limit = param.get(consts.MSGENTRA_INCIDENT_LIMIT, consts.MSGENTRA_INGESTION_DEFAULT_LIMIT)
        filter = param.get(consts.MSGENTRA_INCIDENT_FILTER)
        orderby = param.get(consts.MSGENTRA_INCIDENT_ORDER_BY)
        page_size = consts.MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE

        ret_val, limit = self._validate_integer(action_result, limit, consts.MSGENTRA_LIMIT_KEY, allow_zero=False)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_RISK_EVENTS_ENDPOINT}"

        risk_detection_list = self._paginator(action_result, limit, page_size, endpoint, filter, orderby)

        if not risk_detection_list and not isinstance(risk_detection_list, list):
            return action_result.get_status()

        for risk_detection in risk_detection_list:
            action_result.add_data(risk_detection)

        summary = action_result.update_summary({})
        summary["total_risk_detections"] = len(risk_detection_list)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_risky_users(self, param):
        """This function is used to handle the list risky users action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        limit = param.get(consts.MSGENTRA_INCIDENT_LIMIT, consts.MSGENTRA_INGESTION_DEFAULT_LIMIT)
        filter = param.get(consts.MSGENTRA_INCIDENT_FILTER)
        orderby = param.get(consts.MSGENTRA_INCIDENT_ORDER_BY)
        page_size = consts.MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE

        ret_val, limit = self._validate_integer(action_result, limit, consts.MSGENTRA_LIMIT_KEY, allow_zero=False)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_RISKY_USERS_ENDPOINT}"

        risky_users_list = self._paginator(action_result, limit, page_size, endpoint, filter, orderby)

        if not risky_users_list and not isinstance(risky_users_list, list):
            return action_result.get_status()

        for risky_user in risky_users_list:
            action_result.add_data(risky_user)

        summary = action_result.update_summary({})
        summary["total_risky_users"] = len(risky_users_list)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_signins(self, param):
        """This function is used to handle the list signins action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        limit = param.get(consts.MSGENTRA_INCIDENT_LIMIT, consts.MSGENTRA_INGESTION_DEFAULT_LIMIT)
        page_size = consts.MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE
        filter = param.get(consts.MSGENTRA_INCIDENT_FILTER)
        orderby = param.get(consts.MSGENTRA_INCIDENT_ORDER_BY)
        # Filtering on time is mandatory otherwise this API call will time out
        filter_start_datetime = param[consts.MSGENTRA_FILTER_START_DATETIME]
        filter_end_datetime = param[consts.MSGENTRA_FILTER_END_DATETIME]

        # Build filter
        datetime_filter = f"createdDateTime ge {filter_start_datetime} and createdDateTime le {filter_end_datetime}"
        if filter is None:
            filter = datetime_filter
        else:
            filter = f"{datetime_filter} and {filter}"

        ret_val, limit = self._validate_integer(action_result, limit, consts.MSGENTRA_LIMIT_KEY, allow_zero=False)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_SIGNINS_ENDPOINT}"

        signins = self._paginator(action_result, limit, page_size, endpoint, filter, orderby)

        if not signins and not isinstance(signins, list):
            return action_result.get_status()

        for signin in signins:
            action_result.add_data(signin)

        summary = action_result.update_summary({})
        summary["total_signins"] = len(signins)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_get_signin(self, param):
        """This function is used to handle the get signin action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        signin_id = param[consts.MSGENTRA_SIGNIN_ID]

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_GET_SIGNIN_ENDPOINT}/{signin_id}"

        # For some strange reason, even though the endpoint is specifying a unique object by ID,
        # it will fail with 403 gateway timeout unless you specify a "top" and "limit" of 1.
        params = {"$top": 1, "$limit": 1}

        ret_val, signin = self._update_request(action_result=action_result, endpoint=endpoint, params=params)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        if not signin and not isinstance(signin, list):
            return action_result.get_status()

        action_result.add_data(signin)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_list_devices(self, param):
        """This function is used to handle the list devices action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        limit = param.get(consts.MSGENTRA_INCIDENT_LIMIT, consts.MSGENTRA_INGESTION_DEFAULT_LIMIT)
        page_size = consts.MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE
        filter = param.get(consts.MSGENTRA_INCIDENT_FILTER)
        orderby = param.get(consts.MSGENTRA_INCIDENT_ORDER_BY)

        ret_val, limit = self._validate_integer(action_result, limit, consts.MSGENTRA_LIMIT_KEY, allow_zero=False)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_DEVICES_ENDPOINT}"

        devices = self._paginator(action_result, limit, page_size, endpoint, filter, orderby)

        if not devices and not isinstance(devices, list):
            return action_result.get_status()

        for device in devices:
            action_result.add_data(device)

        summary = action_result.update_summary({})
        summary["total_devices"] = len(devices)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _handle_dismiss_users_risk(self, param):
        """This function is used to handle the dismiss users risk action.

        :param param: Dictionary of input parameters
        :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR)
        """

        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        action_result = self.add_action_result(ActionResult(dict(param)))

        userids = param.get("userids")
        # userids can be a string or a list, convert everything to a list
        try:
            userid_list = ast.literal_eval(userids)
        except (ValueError, SyntaxError):
            userid_list = userids.split(",")
            userid_list = [x.strip() for x in userid_list]

        body_json = f'{{ "userids": {json.dumps(userid_list)} }}'

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_DISMISS_RISKY_USERS_ENDPOINT}"
        ret_val, response = self._update_request(endpoint=endpoint, action_result=action_result, params=None, method="post", data=body_json)

        if phantom.is_fail(ret_val):
            return action_result.get_status()

        action_result.add_data(response)

        return action_result.set_status(phantom.APP_SUCCESS, consts.MSGENTRA_DISMISSED_RISKY_USER_SUCCESSFULLY)

    @staticmethod
    def _check_invalid_since_utc_time(time: datetime) -> bool:
        """Determine that given time is not before 1970-01-01T00:00:00Z.
        Parameters:
            :param time: object of time
        Returns:
            :return: bool(True/False)
        """
        # Check that given time must not be before 1970-01-01T00:00:00Z.
        return time < datetime.strptime("1970-01-01T00:00:00Z", consts.MSGENTRA_APP_DT_STR_FORMAT)

    def _check_date_format(self, action_result, date):
        try:
            # Check for the time is in valid format or not
            time = datetime.strptime(date, consts.MSGENTRA_APP_DT_STR_FORMAT)
            # Taking current UTC time as end time
            end_time = datetime.utcnow()
            if self._check_invalid_since_utc_time(time):
                return action_result.set_status(phantom.APP_ERROR, consts.LOG_UTC_SINCE_TIME_ERROR)
            # Checking future date
            if time >= end_time:
                message = consts.LOG_GREATER_EQUAL_TIME_ERROR.format(consts.LOG_CONFIG_TIME_POLL_NOW)
                return action_result.set_status(phantom.APP_ERROR, message)
        except Exception as e:
            message = f"Invalid date string received. Error occurred while checking date format. Error: {e!s}"
            return action_result.set_status(phantom.APP_ERROR, message)
        return phantom.APP_SUCCESS

    def _handle_on_poll(self, param):
        action_result = self.add_action_result(ActionResult(dict(param)))
        self.save_progress(f"In action handler for: {self.get_action_identifier()}")
        config = self.get_config()

        # params for list risk detections and list risky users
        start_time_scheduled_poll = config.get(consts.MSGENTRA_CONFIG_START_TIME_SCHEDULED_POLL)
        filter_risk_detections = config.get(consts.MSGENTRA_CONFIG_FILTER_RISK_DETECTIONS_SCHEDULED_POLL)
        filter_risky_users = config.get(consts.MSGENTRA_CONFIG_FILTER_RISKY_USERS_SCHEDULED_POLL)
        risk_detections_last_modified_time = (datetime.now() - timedelta(days=consts.MSGENTRA_DEFAULT_LOOKBACK_DAYS)).strftime(
            consts.MSGENTRA_APP_DT_STR_FORMAT
        )  # Let's fall back to the last 7 days

        risky_users_last_modified_time = (datetime.now() - timedelta(days=consts.MSGENTRA_DEFAULT_LOOKBACK_DAYS)).strftime(
            consts.MSGENTRA_APP_DT_STR_FORMAT
        )  # Let's fall back to the last 7 days

        if start_time_scheduled_poll:
            ret_val = self._check_date_format(action_result, start_time_scheduled_poll)
            # if date format is not valid
            if phantom.is_fail(ret_val):
                self.save_progress(action_result.get_message())
                return action_result.set_status(phantom.APP_ERROR)

            # set start time as the last modified time to, hence data is fetched from that point.
            risk_detections_last_modified_time = start_time_scheduled_poll
            risky_users_last_modified_time = start_time_scheduled_poll

        if self.is_poll_now():
            max_ingestions = int(param.get(phantom.APP_JSON_CONTAINER_COUNT))
        else:
            max_ingestions = config.get(consts.MSGENTRA_CONFIG_MAX_INGESTION, consts.MSGENTRA_INGESTION_DEFAULT_LIMIT)
            ret_val, max_ingestions = self._validate_integer(action_result, max_ingestions, "max_ingestions")

            if phantom.is_fail(ret_val):
                return action_result.get_status()

            if self._state.get(consts.STATE_FIRST_RUN, True):
                self._state[consts.STATE_FIRST_RUN] = False
            else:
                # Risk detections
                last_time_risk_detections = self._state.get(consts.STATE_RISK_DETECTIONS_LAST_TIME)
                if last_time_risk_detections:
                    risk_detections_last_modified_time = last_time_risk_detections
                last_time_risky_users = self._state.get(consts.STATE_RISKY_USERS_LAST_TIME)
                if last_time_risky_users:
                    risky_users_last_modified_time = last_time_risky_users

        # Start of risk detection ingestion
        risk_detections_start_time_filter = f"{consts.MSGENTRA_RISK_DETECTION_JSON_LAST_MODIFIED} ge {risk_detections_last_modified_time}"
        poll_filter = (
            risk_detections_start_time_filter
            if not filter_risk_detections
            else f"{filter_risk_detections} and {risk_detections_start_time_filter}"
        )

        orderby = consts.MSGENTRA_RISK_DETECTIONS_ORDER_BY

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_RISK_EVENTS_ENDPOINT}"
        self.duplicate_container = 0

        risk_detections_list = self._paginator(
            action_result, max_ingestions, consts.MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE, endpoint, poll_filter, orderby
        )
        if not risk_detections_list and not isinstance(risk_detections_list, list):  # Failed to fetch risk detections, regardless of the reason
            self.save_progress("Failed to retrieve risk detections")
            return action_result.get_status()

        self.save_progress(f"Successfully fetched {len(risk_detections_list)} risk detections.")

        # Ingest the risk detections
        for risk_detection in risk_detections_list:
            # Create artifact from the incident and alerts
            artifacts = []
            artifacts.append(self._create_artifacts(risk_detection, eventType="riskDetection"))

            # Ingest artifacts for incidents and alerts
            try:
                self._ingest_artifacts_new(
                    artifacts, name=f"Risk Detection: {risk_detection['riskEventType']}", key=risk_detection["id"], eventType="riskyDetection"
                )
            except Exception as e:
                self.debug_print(f"Error occurred while saving artifacts for risk detections. Error: {e!s}")

        if risk_detections_list:
            if consts.MSGENTRA_RISK_DETECTION_JSON_LAST_MODIFIED not in risk_detections_list[-1]:
                return action_result.set_status(
                    phantom.APP_ERROR,
                    f"Could not extract {consts.MSGENTRA_RISK_DETECTION_JSON_LAST_MODIFIED} from latest ingested risk detection.",
                )
            self._state[consts.STATE_RISK_DETECTIONS_LAST_TIME] = risk_detections_list[-1].get(consts.MSGENTRA_RISK_DETECTION_JSON_LAST_MODIFIED)
            self.save_state(self._state)

        # Start of risky users code
        risky_users_start_time_filter = f"{consts.MSGENTRA_RISKY_USERS_JSON_LAST_MODIFIED} ge {risky_users_last_modified_time}"
        poll_filter = risky_users_start_time_filter if not filter_risky_users else f"{filter_risky_users} and {risky_users_start_time_filter}"

        orderby = consts.MSGENTRA_RISKY_USERS_ORDER_BY

        endpoint = f"{consts.MSGENTRA_MSGRAPH_API_BASE_URL}{consts.MSGENTRA_LIST_RISKY_USERS_ENDPOINT}"
        self.duplicate_container = 0

        risky_users_list = self._paginator(
            action_result, max_ingestions, consts.MSGENTRA_INGESTION_DEFAULT_PAGE_SIZE, endpoint, poll_filter, orderby
        )
        if not risky_users_list and not isinstance(risky_users_list, list):  # Failed to fetch risk detections, regardless of the reason
            self.save_progress("Failed to retrieve risky users")
            return action_result.get_status()

        self.save_progress(f"Successfully fetched {len(risky_users_list)} risky users.")

        # Ingest the risky users
        for risky_user in risky_users_list:
            # Create artifact from the incident and alerts
            artifacts = []
            artifacts.append(self._create_artifacts(risky_user, eventType="riskyUser"))

            # Ingest artifacts for incidents and alerts
            try:
                self._ingest_artifacts_new(
                    artifacts, name=f"Risky User: {risky_user['userDisplayName']}", key=risky_user["id"], eventType="riskyUser"
                )
            except Exception as e:
                self.debug_print(f"Error occurred while saving artifacts for riskyUsers. Error: {e!s}")

        if risky_users_list:
            if consts.MSGENTRA_RISKY_USERS_JSON_LAST_MODIFIED not in risky_users_list[-1]:
                return action_result.set_status(
                    phantom.APP_ERROR,
                    f"Could not extract {consts.MSGENTRA_RISKY_USERS_JSON_LAST_MODIFIED} from latest ingested risky user.",
                )
            self._state[consts.STATE_RISKY_USERS_LAST_TIME] = risky_users_list[-1].get(consts.MSGENTRA_RISKY_USERS_JSON_LAST_MODIFIED)
            self.save_state(self._state)

        return action_result.set_status(phantom.APP_SUCCESS)

    def _ingest_artifacts_new(self, artifacts, name, key, eventType):
        """Save the artifacts into the given container ID(cid) and if not given create new container with given key(name).
        Parameters:
            :param artifacts: list of artifacts of IoCs or incidents results
            :param name: name of the container in which data will be ingested
            :param key: source ID of the container in which data will be ingested
        Returns:
            :return: status(phantom.APP_SUCCESS/phantom.APP_ERROR), message, cid(container_id)
        """
        container = {"name": name, "description": f"{eventType} ingested using MS Entra API", "source_data_identifier": key}

        ret_val, message, cid = self.save_container(container)
        if phantom.is_fail(ret_val):
            self.debug_print(f"Error occurred while creating container, reason: {message}")
            return

        if message in "Duplicate container found":
            self.duplicate_container += 1
            self.debug_print(f"Duplicate container count: {self.duplicate_container}")

        for artifact in artifacts:
            artifact["container_id"] = cid
        ret_val, message, _ = self.save_artifacts(artifacts)

    @staticmethod
    def _create_alert_artifacts(alert):
        return {"label": "alert", "name": alert.get("title"), "source_data_identifier": alert.get("id"), "data": alert, "cef": alert}

    @staticmethod
    def _create_artifacts(event, eventType):
        def flatten_data(y):
            out = {}

            def flatten(x, name=""):
                if type(x) is dict:
                    for a in x:
                        flatten(x[a], name + a + "_")
                elif type(x) is list:
                    i = 0
                    for a in x:
                        flatten(a, name + str(i) + "_")
                        i += 1
                else:
                    out[name[:-1]] = x

            flatten(y)
            return out

        label = ""
        name = ""

        if eventType == "riskDetection":
            label = "risk detection"
            name = event["riskEventType"]
        elif eventType == "riskyUser":
            label = "risky user"
            name = event["userDisplayName"]

        return {"label": label, "name": name, "source_data_identifier": event.get("id"), "data": flatten_data(event), "cef": flatten_data(event)}

    def handle_action(self, param):
        ret_val = phantom.APP_SUCCESS

        # Get the action that we are supposed to execute for this App Run
        action_id = self.get_action_identifier()

        self.debug_print("action_id", self.get_action_identifier())

        if action_id == "test_connectivity":
            ret_val = self._handle_test_connectivity(param)
        elif action_id == "list_risk_detections":
            ret_val = self._handle_list_risk_detections(param)
        elif action_id == "list_risky_users":
            ret_val = self._handle_list_risky_users(param)
        elif action_id == "list_signins":
            ret_val = self._handle_list_signins(param)
        elif action_id == "get_signin":
            ret_val = self._handle_get_signin(param)
        elif action_id == "dismiss_users_risk":
            ret_val = self._handle_dismiss_users_risk(param)
        elif action_id == "list_devices":
            ret_val = self._handle_list_devices(param)
        elif action_id == "on_poll":
            ret_val = self._handle_on_poll(param)

        return ret_val

    def initialize(self):
        # Load the state in initialize
        config = self.get_config()
        self._asset_id = self.get_asset_id()

        # Load the state in initialize, use it to store data
        # that needs to be accessed across actions
        self._state = self.load_state()

        action_id = self.get_action_identifier()
        action_result = ActionResult()
        self._asset_id = self.get_asset_id()
        self._non_interactive = config.get("non_interactive", False)
        self._tenant = config[consts.MSGENTRA_CONFIG_TENANT_ID]
        self._client_id = config[consts.MSGENTRA_CONFIG_CLIENT_ID]
        self._client_secret = config.get(consts.MSGENTRA_CONFIG_CLIENT_SECRET)
        self._timeout = config.get(consts.MSGENTRA_CONFIG_TIMEOUT, consts.DEFAULT_TIMEOUT)
        self._certificate_thumbprint = config.get(consts.MSGENTRA_CONFIG_CERTIFICATE_THUMBPRINT)
        self._certificate_private_key = config.get(consts.MSGENTRA_CONFIG_CERTIFICATE_PRIVATE_KEY)

        # If any of these values are different between config and state, we will
        # nuke the cached auth_token
        self.critical_config_names = [
            consts.MSGENTRA_CONFIG_TENANT_ID,
            consts.MSGENTRA_CONFIG_CLIENT_ID,
            consts.MSGENTRA_CONFIG_CLIENT_SECRET,
            consts.MSGENTRA_CONFIG_CERTIFICATE_THUMBPRINT,
            consts.MSGENTRA_CONFIG_CERTIFICATE_PRIVATE_KEY,
        ]

        critical_fields = [config.get(x) for x in self.critical_config_names]
        critical_hash = hash_values_sha256(critical_fields)

        if self._state.get("critical_field_hash") != critical_hash:
            # A critical field has changed in config, nuke the state file
            self.debug_print(f"A critical config value changed, nuking state file")
            self._nuke_tokens_from_state_file()

        # Must either supply client_secret, or both thumbprint and private key
        if self._client_secret is None:
            if self._certificate_thumbprint is None or self._certificate_private_key is None:
                return self.set_status(phantom.APP_ERROR, consts.MSGENTRA_CBA_FIELDS_ERROR)

        if self._client_secret is not None:
            if self._certificate_thumbprint is not None or self._certificate_private_key is not None:
                return self.set_status(phantom.APP_ERROR, consts.MSGENTRA_FIELD_CONFLICT_ERROR)

        if self._client_secret is not None:
            self._cba_auth = False
        else:
            self._cba_auth = True
            # Check non-interactive is enabled for CBA auth
            if self._non_interactive is False:
                return self.set_status(phantom.APP_ERROR, consts.MSGENTRA_CBA_INTERACTIVE_ERROR)

        ret_val, self._timeout = self._validate_integer(action_result, self._timeout, consts.MSGENTRA_TIMEOUT_KEY)
        if phantom.is_fail(ret_val):
            return action_result.get_status()

        if not isinstance(self._state, dict):
            self.debug_print("Resetting the state file with the default format")
            self._state = {"app_version": self.get_app_json().get("app_version")}
            if not self._non_interactive:
                return self.set_status(phantom.APP_ERROR, consts.MSGENTRA_STATE_FILE_CORRUPT_ERROR)

        self._access_token = self._state.get(consts.MSGENTRA_ACCESS_TOKEN_STRING, None)
        self._refresh_token = self._state.get(consts.MSGENTRA_REFRESH_TOKEN_STRING, None)
        self.debug_print(f"Action id = {action_id}")
        if not self._non_interactive and action_id != "test_connectivity" and (not self._access_token or not self._refresh_token):
            token_data = {
                "client_id": self._client_id,
                "grant_type": consts.MSGENTRA_REFRESH_TOKEN_STRING,
                "refresh_token": self._refresh_token,
                "client_secret": self._client_secret,
                "resource": consts.MSGENTRA_RESOURCE_URL,
            }
            self.debug_print("Calling generate_new_access_token from initialize")
            ret_val = self._generate_new_access_token(action_result=action_result, data=token_data)

            if phantom.is_fail(ret_val):
                return self.set_status(phantom.APP_ERROR, f"{consts.MSGENTRA_RUN_CONNECTIVITY_MSG}. {action_result.get_message()}")

        return phantom.APP_SUCCESS

    def finalize(self):
        self.debug_print("In finalize()")
        # Save the state, this data is saved across actions and app upgrades

        # Create hash of multiple fields, so if they are changed we can invalidate tokens
        config = self.get_config()
        critical_fields = [config.get(x) for x in self.critical_config_names]
        critical_hash = hash_values_sha256(critical_fields)
        self.debug_print(f"Critical field hash: {critical_hash}")
        self._state["critical_field_hash"] = critical_hash
        self.save_state(self._state)
        return phantom.APP_SUCCESS


def main():
    import argparse
    import sys

    argparser = argparse.ArgumentParser()

    argparser.add_argument("input_test_json", help="Input Test JSON file")
    argparser.add_argument("-u", "--username", help="username", required=False)
    argparser.add_argument("-p", "--password", help="password", required=False)
    argparser.add_argument("-v", "--verify", action="store_true", help="verify", required=False, default=False)

    args = argparser.parse_args()
    session_id = None

    username = args.username
    password = args.password
    verify = args.verify

    if username is not None and password is None:
        # User specified a username but not a password, so ask
        import getpass

        password = getpass.getpass("Password: ")

    if username and password:
        try:
            login_url = f"{BaseConnector._get_phantom_base_url()}login"

            print("Accessing the Login page")
            r = requests.get(login_url, verify=verify, timeout=consts.DEFAULT_TIMEOUT)
            csrftoken = r.cookies["csrftoken"]

            data = dict()
            data["username"] = username
            data["password"] = password
            data["csrfmiddlewaretoken"] = csrftoken

            headers = dict()
            headers["Cookie"] = f"csrftoken={csrftoken}"
            headers["Referer"] = login_url

            print("Logging into Platform to get the session id")
            r2 = requests.post(login_url, verify=verify, data=data, headers=headers, timeout=consts.DEFAULT_TIMEOUT)
            session_id = r2.cookies["sessionid"]
        except Exception as e:
            print(f"Unable to get session id from the platform. Error: {e!s}")
            sys.exit(1)

    with open(args.input_test_json) as f:
        in_json = f.read()
        in_json = json.loads(in_json)
        print(json.dumps(in_json, indent=4))

        connector = MsGraphForEntra_Connector()
        connector.print_progress_message = True

        if session_id is not None:
            in_json["user_session_token"] = session_id
            connector._set_csrf_info(csrftoken, headers["Referer"])

        ret_val = connector._handle_action(json.dumps(in_json), None)
        print(json.dumps(json.loads(ret_val), indent=4))

    sys.exit(0)


if __name__ == "__main__":
    main()

# Comment to test pre-commit
