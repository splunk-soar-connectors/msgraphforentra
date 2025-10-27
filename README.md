# MS Graph for Entra

Publisher: Splunk <br>
Connector Version: 1.0.3 <br>
Product Vendor: Microsoft <br>
Product Name: Microsoft Entra <br>
Minimum Product Version: 6.3.0

This app integrates with Microsoft Entra to execute various generic and investigative actions

## Port Information

The app uses HTTP(S) protocol for communicating with the Microsoft Entra service. Below
are the default ports used by Splunk SOAR.

| SERVICE NAME | TRANSPORT PROTOCOL | PORT |
|--------------|--------------------|------|
| http | tcp | 80 |
| https | tcp | 443 |

## Explanation of Asset Configuration Parameters

- Tenant ID - It is the Directory ID of the Microsoft Entra ID on the Microsoft
  Azure portal.
- Client ID - It is the Application ID of an application configured in the Microsoft Entra ID.
- Client Secret - It is the secret string used by the application to prove its identity when
  requesting a token. It can be generated for the configured application on the Microsoft Entra ID.
- Non-Interactive Auth - It is used to determine the authentication method. If it is checked then
  non-Interactive auth will be used otherwise interactive auth will be used. Whenever this
  checkbox is toggled then the test connectivity action must be run again. NOTE: Non-Interactive Auth
  must be checked for Certificate Based Authentication.
- Certificate Thumbprint - Obtained from Microsoft Entra, after uploading certificate.
- Certificate Private Key - Certificate Private Key in PEM format.
- Timeout - It is used to make configurable timeout for all actions.

## Explanation of Asset Configuration Parameters for On Poll

- Maximum risk detections/risky users for scheduled/interval polling for each cycle - In each polling cycle, risk detections and risky users are fetched for schedule and interval polling based on the provided value (Default 500). Containers are created per risk detection and per risky user.
- Start time for schedule/interval/manual poll (Use this format: 1970-01-01T00:00:00Z) - It is used to filter the risk detections and risky users based on start time, if nothing is provided, then it will take last week as start time. <br> **NOTE: Start time is used to filter based on riskLastUpdatedDateTime property of risky user and lastUpdatedDateTime of risk detection**
- Filter risk detections based on property (example: status ne 'active') - It is used to add extra filters on risk detection properties.
- Filter risky users based on property (example: status ne 'active') - It is used to add extra filters on risky user properties.

## Explanation of On Poll Behavior

- The "Maximum risk detections/risk users for scheduled/interval polling for each cycle" parameter functions exclusively with scheduled and interval polling.
- For Example,if the "Maximum risk detections/risk users for scheduled/interval polling for each cycle" parameter is set to 100, the 'on_poll' feature must incorporate up to 100 distinct risk detections or risky users, based on the provided filters and start times parameter values.

## Configure and set up permissions of the app created on the Microsoft Azure portal

<div style="margin-left: 2em">

#### Create the app

1. Navigate to <https://portal.azure.com> .
1. Log in with a user that has permission to create an app in the Microsoft Entra ID.
1. Select the 'Microsoft Entra ID'.
1. Select the 'App registrations' menu from the left-side panel.
1. Select the 'New Registration' option at the top of the page.
1. In the registration form, choose a name for your application and then click 'Register'.

#### Add permissions

7. Select the 'API Permissions' menu from the left-side panel.
1. Click on 'Add a permission'.
1. Under the 'Select an API' section, select 'APIs my organization uses'.
1. Search for 'Microsoft Graph' keyword in the search box and click on the displayed option for it.
1. Provide the following Delegated and Application permissions to the app.
   - **Application Permissions**

     - IdentityRiskEvent.Read.All (for "list risk detections")
     - IdentityRiskyUser.Read.All (for "list risky users")
     - IdentityRiskyUser.ReadWrite.All (for "dismiss users risk")
     - AuditLog.Read.All (for "list sigins")
     - Directory.Read.All (for "list sigins")
     - Device.Read.All (for "list devices")

   - **Delegated Permissions**

     - IdentityRiskEvent.Read.All (for "list risk detections")
     - IdentityRiskyUser.Read.All (for "list risky users")
     - IdentityRiskyUser.ReadWrite.All (for "dismiss users risk")
     - AuditLog.Read.All (for "list sigins")
     - Directory.Read.All (for "list sigins")
     - Device.Read.All (for "list devices")
1. 'Grant Admin Consent' for it.
1. Again click on 'Add a permission'.
1. Under the 'Select an API' section, select 'Microsoft APIs'.
1. Click on the 'Microsoft Graph' option.
1. Provide the following Delegated permission to the app.
   - **Delegated Permission**

     - offline_access

#### Create a client secret or jump to next section to use Certificate Based Authentication

17. Select the 'Certificates & secrets' menu from the left-side panel.
01. Select 'New client secret' button to open a pop-up window.
01. Provide the description, select an appropriate option for deciding the client secret expiration
    time, and click on the 'Add' button.
01. Click 'Copy to clipboard' to copy the generated secret value and paste it in a safe place. You
    will need it to configure the asset and will not be able to retrieve it later.

#### Using Certificate Based Authentication

21. Select the 'Certificates & secrets' menu from the left-side panel.
01. Select the 'Certificates' tab.
01. Click 'Upload Certificate' and choose a '\*.crt' file that contains the server certificate.
01. Select the 'Thumbprint' for the newly uploaded certificate and copy it somewhere to be
    used when configuring the SOAR app.

#### Copy your application id and tenant id

21. Select the 'Overview' menu from the left-side panel.
01. Copy the **Application (client) ID** and **Directory (tenant) ID** . You will need these to
    configure the SOAR asset.

## Configure the MS Graph for Entra SOAR app's asset

When creating an asset for the app,

- Check the checkbox **Non-Interactive Auth** if you want to use Non-Interactive authentication
  mechanism otherwise Interactive auth mechanism will be used.

- Provide the client ID of the app created during the previous step of app creation in the 'Client
  ID' field.

- Provide the client secret of the app created during the previous step of app creation in the
  'Client Secret' field. -or- If using Certificate Based Authenticaion, do not not enter anything
  in this field, instead, complete the next three steps.

- For Certificate Based Authentication only: Provide the 'Certificate Thumbprint' recorded above from Microsoft Entra.

- For Certificate Based Authentication only: Provide the 'Certificate Private Key' (cut and paster the .pem file contents).

- For Certificate Based Authentication only: Ensure the 'Non-Interactive Auth' checkbox is checked.

- Provide the tenant ID of the app created during the previous step of Azure app creation in the
  'Tenant ID' field. For getting the value of tenant ID, navigate to the Microsoft Entra ID; The value displayed in the 'Tenant ID'.

- Save the asset with the above values.

- After saving the asset, a new uneditable field will appear in the 'Asset Settings' tab of the
  configured asset for the MS Graph for Entra app on SOAR. Copy the URL mentioned in the 'POST
  incoming for MS Graph for Entra to this location' field. Add a suffix '/result' to the URL
  copied in the previous step. The resulting URL looks like the one mentioned below.

  https://\<soar_host>/rest/handler/msgraphforentra\_\<appid>/\<asset_name>/result

- Add the URL created in the earlier step into the 'Redirect URIs' section of the 'Authentication'
  menu for the registered app that was created in the previous steps on the Microsoft Azure
  portal. For the 'Redirect URIs' section, follow the below steps.

  1. Below steps are required only in case of Interactive auth (i.e. If checkbox is unchecked)
  1. Navigate to the 'Microsoft Entra ID' on the Microsoft Azure portal.
  1. Click on the 'App registrations' menu from the left-side panel.
  1. Click on the earlier created app. You can search for the app by name or client ID.
  1. Navigate to the 'Authentication' menu of the app on the left-side panel.
  1. Click on the 'Add a platform' button and select 'Web' from the displayed options.
  1. Enter the URL created in the earlier section in the 'Redirect URIs' text-box.
  1. Select the 'ID tokens' checkbox and click 'Save'.
  1. This will display the 'Redirect URIs' under the 'Web' section displayed on the page.

## Interactive Method to run Test Connectivity

- Here make sure that the 'Non-Interactive Auth' checkbox is unchecked in asset configuration.
- After setting up the asset and user, click the 'TEST CONNECTIVITY' button. A pop-up window will
  be displayed with appropriate test connectivity logs. It will also display a specific URL on
  that pop-up window.
- Open this URL in a separate browser tab. This new tab will redirect to the Microsoft login page
  to complete the login process to grant the permissions to the app.
- Log in using the same Microsoft account that was used to configure the Microsoft Entra
  workflow and the application on the Microsoft Azure Portal. After logging in, review the
  requested permissions listed and click on the 'Accept' button.
- This will display a successful message of 'Code received. Please close this window, the action
  will continue to get new token.' on the browser tab.
- Finally, close the browser tab and come back to the 'Test Connectivity' browser tab. The pop-up
  window should display a 'Test Connectivity Passed' message.

## Non-Interactive Method to run Test Connectivity

- Here make sure that the 'Non-Interactive Auth' checkbox is checked in asset configuration.
- Click on the 'TEST CONNECTIVITY' button, it should run the test connectivity action without any
  user interaction.

## Explanation of Test Connectivity Workflow for Interactive auth and Non-Interactive auth

- This app uses (version 1.0) OAUTH 2.0 authorization code workflow APIs for generating the
  [access_token] and [refresh_token] pairs if the authentication method is interactive else
  [access_token] if authentication method is non-interactive is used for all the API calls to
  the Microsoft Entra instance.

- Interactive authentication mechanism is a user-context based workflow and the permissions of the
  user also matter along with the API permissions set to define the scope and permissions of the
  generated tokens.

- Non-Interactive authentication mechanism is a user-context based workflow and the permissions of
  the user also matter along with the API permissions set to define the scope and permissions of
  the generated token.

- The step-by-step process for the entire authentication mechanism is explained below.

  - The first step is to get an application created in a specific tenant on the Microsoft Entra ID. Generate the [client_secret] for the configured application. The
    detailed steps have been mentioned in the earlier section.

  - Configure the MS Graph for Entra app's asset with appropriate values for [tenant_id],
    [client_id], and [client_secret] configuration parameters.

  - Run the test connectivity action for Interactive method.

    - Internally, the connectivity creates a URL for hitting the /authorize endpoint for the
      generation of the authorization code and displays it on the connectivity pop-up window.
      The user is requested to hit this URL in a browser new tab and complete the
      authorization request successfully resulting in the generation of an authorization code.
    - The authorization code generated in the above step is used by the connectivity to make
      the next API call to generate the [access_token] and [refresh_token] pair. The
      generated authorization code, [access_token], and [refresh_token] are stored in the
      state file of the app on the Splunk SOAR server.
    - The authorization code can be used only once to generate the pair of [access_token]
      and [refresh_token]. If the [access_token] expires, then the [refresh_token] is
      used internally automatically by the application to re-generate the [access_token] by
      making the corresponding API call. This entire autonomous workflow will seamlessly work
      until the [refresh_token] does not get expired. Once the [refresh_token] expires,
      the user will have to run the test connectivity action once again to generate the
      authorization code followed by the generation of an entirely fresh pair of
      [access_token] and [refresh_token]. The default expiration time for the
      [access_token] is 1 hour and that of the [refresh_token] is 90 days.
    - The successful run of the Test Connectivity ensures that a valid pair of
      [access_token] and [refresh_token] has been generated and stored in the app's state
      file. These tokens will be used in all the actions' execution flow to authorize their
      API calls to the Microsoft Entra instance.

  - Run the test connectivity action for Non-Interactive method.

    - Internally, the application authenticates to Azure AD token issuance endpoint and
      requests an [access_token] then it will generate the [access_token].
    - The [access_token] generated in the above step is used by the test connectivity to
      make the next API call to verify the [access_token]. The generated [access_token] is
      stored in the state file of the app on the Splunk SOAR server.
    - If the [access_token] expires, then application will automatically re-generate the
      [access_token] by making the corresponding API call.
    - The successful run of the Test Connectivity ensures that a valid [access_token] has
      been generated and stored in the app's state file. This token will be used in all the
      actions execution flow to authorize their API calls to the Microsoft Entra
      instance.

## State file permissions

Please check the permissions for the state file as mentioned below.

#### State file path

- state file path on instance: /opt/phantom/local_data/app_states/\<appid>/\<asset_id>\_state.json

#### State file permissions

- File rights: rw-rw-r-- (664) (The Splunk SOAR user should have read and write access for the
  state file)
- File owner: Appropriate Splunk SOAR user

## Notes

- \<appid> - The app ID will be available in the Redirect URI which gets populated in the field
  'POST incoming for MS Graph for Entra to this location' when the MS Graph for Entra app
  asset is configured e.g.
  https://\<splunk_soar_host>/rest/handler/msgraphforentra\_\<appid>/\<asset_name>/result
- \<asset_id> - The asset ID will be available on the created asset's Splunk SOAR web URL e.g.
  https://\<splunk_soar_host>/apps/\<app_number>/asset/\<asset_id>/

#### The app is configured and ready to be used now.

### Configuration variables

This table lists the configuration variables required to operate MS Graph for Entra. These variables are specified when configuring a Microsoft Entra asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**tenant_id** | required | string | Tenant ID |
**client_id** | required | string | Client ID |
**client_secret** | optional | password | Client Secret |
**certificate_thumbprint** | optional | password | Certificate Thumbprint |
**certificate_private_key** | optional | password | Certificate Private Key (.PEM) |
**timeout** | optional | numeric | HTTP API timeout in seconds |
**non_interactive** | optional | boolean | Non-Interactive Auth |
**max_ingestions** | optional | numeric | Maximum risk detections/risk users for scheduled/interval polling for each cycle |
**start_time** | optional | string | Start time for schedule/interval/manual poll (Use this format: 1970-01-01T00:00:00Z) |
**filter_risk_detections** | optional | string | Filter risk detections based on property (example: status ne 'active') |
**filter_risky_users** | optional | string | Filter risky users based on property (example: status ne 'active') |

### Supported Actions

[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration <br>
[on poll](#action-on-poll) - Callback action for the on_poll ingest functionality <br>
[dismiss users risk](#action-dismiss-users-risk) - Dismiss the risk of one or more users <br>
[list risk detections](#action-list-risk-detections) - List risk detections <br>
[list risky users](#action-list-risky-users) - List risky users <br>
[list devices](#action-list-devices) - List devices <br>
[list signins](#action-list-signins) - List user signins <br>
[get signin](#action-get-signin) - Get user signin

## action: 'test connectivity'

Validate the asset configuration for connectivity using supplied configuration

Type: **test** <br>
Read only: **True**

#### Action Parameters

No parameters are required for this action

#### Action Output

No Output

## action: 'on poll'

Callback action for the on_poll ingest functionality

Type: **ingest** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**start_time** | optional | Parameter ignored in this app | numeric | |
**end_time** | optional | Parameter ignored in this app | numeric | |
**container_count** | optional | Parameter ignored for schedule/interval polling only | numeric | |
**artifact_count** | optional | Parameter ignored in this app | numeric | |
**container_id** | optional | Parameter ignored in this app | numeric | |

#### Action Output

No Output

## action: 'dismiss users risk'

Dismiss the risk of one or more users

Type: **generic** <br>
Read only: **False**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**userids** | optional | One or more userids to dismiss risk for | string | `entra risky userid` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success |
action_result.message | string | | Successfully dismissed risk for specified userids |
action_result.parameter.userids | string | `entra risky userid` | ba9e3378-9e5c-4159-a022-e6fee173bf35 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'list risk detections'

List risk detections

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**limit** | optional | Maximum number of risk detections to return (Defaults to 50) | numeric | |
**filter** | optional | Filter risk detections based on property | string | |
**orderby** | optional | Sort the risk detections based on property | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.data.\*.id | string | `sha256` | |
action_result.data.\*.source | string | | IdentityProtection |
action_result.data.\*.userId | string | | ba9e3378-9e5c-4159-a022-e6fee173bf35 |
action_result.data.\*.activity | string | | signin |
action_result.data.\*.location.city | string | | Paris |
action_result.data.\*.location.state | string | | Paris |
action_result.data.\*.location.geoCoordinates.latitude | numeric | | 48.87276 |
action_result.data.\*.location.geoCoordinates.longitude | numeric | | 2.27278 |
action_result.data.\*.location.countryOrRegion | string | | FR |
action_result.data.\*.ipAddress | string | | 2a0e:e701:1198::1 |
action_result.data.\*.requestId | string | | aea71ec6-4431-421e-ac52-0592973b3c00 |
action_result.data.\*.riskLevel | string | | medium |
action_result.data.\*.riskState | string | | dismissed |
action_result.data.\*.riskDetail | string | | adminDismissedAllRiskForUser |
action_result.data.\*.correlationId | string | | 6fe21b2f-63b3-4590-a440-2cd21c9f0bff |
action_result.data.\*.riskEventType | string | | anonymizedIPAddress |
action_result.data.\*.additionalInfo | string | | [{"Key":"userAgent","Value":"Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0"},{"Key":"mitreTechniques","Value":"T1090.003,T1078"}] |
action_result.data.\*.tokenIssuerType | string | | AzureAD |
action_result.data.\*.userDisplayName | string | | Lee Gu |
action_result.data.\*.activityDateTime | string | | 2025-01-27T19:00:24.0871469Z |
action_result.data.\*.detectedDateTime | string | | 2025-01-27T19:00:24.0871469Z |
action_result.data.\*.userPrincipalName | string | `email` | LeeG@tlp5x.onmicrosoft.com |
action_result.data.\*.detectionTimingType | string | | realtime |
action_result.data.\*.lastUpdatedDateTime | string | | 2025-01-27T19:52:10.3086944Z |
action_result.status | string | | success |
action_result.message | string | | Total risk detections: 1 |
action_result.summary.total_risk_detections | numeric | | 1 |
action_result.parameter.limit | numeric | | 50 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |
action_result.parameter.filter | string | | |
action_result.parameter.orderby | string | | |

## action: 'list risky users'

List risky users

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**limit** | optional | Maximum number of risky users to return (Defaults to 50) | numeric | |
**filter** | optional | Filter risky users based on property | string | |
**orderby** | optional | Sort the risky users based on property | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.data.\*.id | string | `entra risky userid` | a75e9d70-b67e-42f7-bbd3-8c586e4b8d2e |
action_result.data.\*.isDeleted | boolean | | False |
action_result.data.\*.riskLevel | string | | none |
action_result.data.\*.riskState | string | | dismissed |
action_result.data.\*.riskDetail | string | | adminDismissedAllRiskForUser |
action_result.data.\*.isProcessing | boolean | | False |
action_result.data.\*.userDisplayName | string | | Ian Wills |
action_result.data.\*.userPrincipalName | string | `email` | iwills@tlp5x.onmicrosoft.com |
action_result.data.\*.riskLastUpdatedDateTime | string | | 2024-06-05T17:33:50.0817259Z |
action_result.status | string | | success |
action_result.message | string | | Total risky users: 4 |
action_result.summary.total_risky_users | numeric | | 4 |
action_result.parameter.limit | numeric | | 50 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |
action_result.parameter.filter | string | | |
action_result.parameter.orderby | string | | |

## action: 'list devices'

List devices

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**limit** | optional | Maximum number of devices to return (Defaults to 50) | numeric | |
**offset** | optional | Number of devices to skip (Defaults to 0) | numeric | |
**filter** | optional | Filter devices based on property | string | |
**orderby** | optional | Sort the devices based on property | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.parameter.limit | numeric | | |
action_result.parameter.offset | numeric | | |
action_result.parameter.filter | string | | |
action_result.parameter.orderby | string | | |
summary.total_objects | numeric | | |
action_result.message | string | | |
action_result.status | string | | |
summary.total_objects_successful | numeric | | |

## action: 'list signins'

List user signins

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**limit** | optional | Maximum number of signins to return (Defaults to 50) | numeric | |
**filter_start_datetime** | required | Start time to filter sigins by. Format can be YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ | string | |
**filter_end_datetime** | required | End time to filter sigins by. Format can be YYYY-MM-DD or YYYY-MM-DDThh:mm:ssZ | string | |
**filter** | optional | Filter signins based on property | string | |
**orderby** | optional | Sort the signins based on property | string | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.data.\*.id | string | `entra signin id` | 32753854-58f3-40f2-bef7-ae9db94b1800 |
action_result.data.\*.appId | string | | c44b4083-3bb0-49c1-b47d-974e53cbdf3c |
action_result.data.\*.status.errorCode | numeric | | 0 |
action_result.data.\*.status.failureReason | string | | Other. |
action_result.data.\*.status.additionalDetails | string | | MFA requirement satisfied by claim in the token |
action_result.data.\*.userId | string | | a75e9d70-b67e-42f7-bbd3-8c586e4b8d2e |
action_result.data.\*.location.city | string | | Denver |
action_result.data.\*.location.state | string | | Colorado |
action_result.data.\*.location.geoCoordinates.altitude | string | | |
action_result.data.\*.location.geoCoordinates.latitude | numeric | | 39.74249 |
action_result.data.\*.location.geoCoordinates.longitude | numeric | | -104.9856 |
action_result.data.\*.location.countryOrRegion | string | | US |
action_result.data.\*.ipAddress | string | `ip` | 216.147.121.134 |
action_result.data.\*.riskState | string | | none |
action_result.data.\*.resourceId | string | | c44b4083-3bb0-49c1-b47d-974e53cbdf3c |
action_result.data.\*.riskDetail | string | | none |
action_result.data.\*.deviceDetail.browser | string | | Chrome 131.0.0 |
action_result.data.\*.deviceDetail.deviceId | string | | |
action_result.data.\*.deviceDetail.isManaged | boolean | | False |
action_result.data.\*.deviceDetail.trustType | string | | |
action_result.data.\*.deviceDetail.displayName | string | | |
action_result.data.\*.deviceDetail.isCompliant | boolean | | False |
action_result.data.\*.deviceDetail.operatingSystem | string | | MacOs |
action_result.data.\*.clientAppUsed | string | | Browser |
action_result.data.\*.correlationId | string | | aca6d53e-4b3b-49a3-a505-3eca2fab8f49 |
action_result.data.\*.isInteractive | boolean | | True |
action_result.data.\*.appDisplayName | string | | Azure Portal |
action_result.data.\*.createdDateTime | string | | 2025-01-28T12:40:41Z |
action_result.data.\*.userDisplayName | string | | Ian Wills |
action_result.data.\*.userPrincipalName | string | `email` | iwills@tlp5x.onmicrosoft.com |
action_result.data.\*.resourceDisplayName | string | | Azure Portal |
action_result.data.\*.riskLevelAggregated | string | | none |
action_result.data.\*.riskLevelDuringSignIn | string | | none |
action_result.data.\*.conditionalAccessStatus | string | | notApplied |
action_result.status | string | | success |
action_result.message | string | | Total signins: 1 |
action_result.summary.total_signins | numeric | | 1 |
action_result.parameter.limit | numeric | | 1 |
action_result.parameter.filter | string | | userDisplayName eq 'Ian Wills' |
action_result.parameter.filter_end_datetime | string | | 2025-01-30 |
action_result.parameter.filter_start_datetime | string | | 2025-01-26 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |
action_result.parameter.orderby | string | | |

## action: 'get signin'

Get user signin

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**signin_id** | required | Signin ID | string | `entra signin id` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.data.\*.id | string | | 32753854-58f3-40f2-bef7-ae9db94b1800 |
action_result.data.\*.appId | string | | c44b4083-3bb0-49c1-b47d-974e53cbdf3c |
action_result.data.\*.status.errorCode | numeric | | 0 |
action_result.data.\*.status.failureReason | string | | Other. |
action_result.data.\*.status.additionalDetails | string | | MFA requirement satisfied by claim in the token |
action_result.data.\*.userId | string | | a75e9d70-b67e-42f7-bbd3-8c586e4b8d2e |
action_result.data.\*.location.city | string | | Denver |
action_result.data.\*.location.state | string | | Colorado |
action_result.data.\*.location.geoCoordinates.altitude | string | | |
action_result.data.\*.location.geoCoordinates.latitude | numeric | | 39.74249 |
action_result.data.\*.location.geoCoordinates.longitude | numeric | | -104.9856 |
action_result.data.\*.location.countryOrRegion | string | | US |
action_result.data.\*.ipAddress | string | `ip` | 216.147.121.134 |
action_result.data.\*.riskState | string | | none |
action_result.data.\*.resourceId | string | | c44b4083-3bb0-49c1-b47d-974e53cbdf3c |
action_result.data.\*.riskDetail | string | | none |
action_result.data.\*.deviceDetail.browser | string | | Chrome 131.0.0 |
action_result.data.\*.deviceDetail.deviceId | string | | |
action_result.data.\*.deviceDetail.isManaged | boolean | | False |
action_result.data.\*.deviceDetail.trustType | string | | |
action_result.data.\*.deviceDetail.displayName | string | | |
action_result.data.\*.deviceDetail.isCompliant | boolean | | False |
action_result.data.\*.deviceDetail.operatingSystem | string | | MacOs |
action_result.data.\*.clientAppUsed | string | | Browser |
action_result.data.\*.correlationId | string | | aca6d53e-4b3b-49a3-a505-3eca2fab8f49 |
action_result.data.\*.isInteractive | numeric | | True |
action_result.data.\*.@odata.context | string | `url` | https://graph.microsoft.com/v1.0/$metadata#auditLogs/signIns/$entity |
action_result.data.\*.appDisplayName | string | | Azure Portal |
action_result.data.\*.createdDateTime | string | | 2025-01-28T12:40:41Z |
action_result.data.\*.userDisplayName | string | | Ian Wills |
action_result.data.\*.userPrincipalName | string | `email` | iwills@tlp5x.onmicrosoft.com |
action_result.data.\*.resourceDisplayName | string | | Azure Portal |
action_result.data.\*.riskLevelAggregated | string | | none |
action_result.data.\*.riskLevelDuringSignIn | string | | none |
action_result.data.\*.conditionalAccessStatus | string | | notApplied |
action_result.status | string | | success |
action_result.message | string | | |
action_result.parameter.signin_id | string | `entra signin id` | 32753854-58f3-40f2-bef7-ae9db94b1800 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2025 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
