

ERROR_FETCH_DM_INFO = "Error fetching DM code information."
ERROR_FETCH_USER = "Error fetching user."
ERROR_CREATE_USER = "Error creating user."
ERROR_VERIFY_PASSWORD = "Error verifying password."
ERROR_CREATE_CONTAINER = "An error occurred while creating the container."
ERROR_FETCH_CONTAINERS = "Error fetching the list of containers."
ERROR_RENAME_CONTAINER = "Error renaming container."
DM_NOT_FOUND = "DM code not found in the dm_info table."
USER_NOT_FOUND = "User not found."
USER_ALREADY_EXISTS = "A user with this login already exists."
PASSWORD_CORRECT = "Password is correct."
PASSWORD_INCORRECT = "Incorrect password."
CONTAINER_ALREADY_EXISTS = "A container with this name already exists."
CONTAINER_CREATED = "Container {} successfully created."
CONTAINER_RENAMED = "Container successfully renamed."
USER_CREATED = "User successfully created."
ERROR_ADD_DM_CODE = "Error adding DM code."
ERROR_FETCH_CONTAINER_NAME = "Error fetching container name."
CODE_NOT_FOUND = "This code was not found."
CODE_ALREADY_ADDED = "Code already added to container {container_name}."
CODE_ADDED_SUCCESS = "Code successfully added to the container and container status updated."
CONTAINER_NOT_FOUND = "Container with ID {container_id} not found."
ERROR_FETCH_DM_CODES = "Error fetching DM codes."
ERROR_UPDATE_CONTAINER_STATUS = "Error updating container status."
ERROR_GENERATE_CONTAINER_KIT = "Error generating container kit."
ERROR_REMOVE_DM_CODE = "Error removing DM code from the container."
ERROR_DELETE_CONTAINER = "Error deleting container."
CONTAINER_UPDATE_SUCCESS = "Container with ID {container_id} successfully updated to status 'packed'."
DM_CODE_NOT_FOUND = "DM code not found in the container."
DM_CODE_REMOVED = "DM code successfully removed from the container."
CONTAINER_CANNOT_BE_DELETED_STATUS = "Container with ID {container_id} cannot be deleted because its status is not 'new'."
CONTAINER_CANNOT_BE_DELETED_DMS = "Container with ID {container_id} cannot be deleted because it contains DM codes."
CONTAINER_DELETED = "Container '{container_name}' (ID {container_id}) successfully deleted."


ERROR_INVALID_LOGIN_OR_PASSWORD = "Invalid login or password"
ERROR_INVALID_TOKEN = "Invalid token"
ERROR_MISSING_AUTHORIZATION_TOKEN = "Authorization token missing"
ERROR_COULD_NOT_VALIDATE_CREDENTIALS = "Could not validate credentials"
SUCCESS_USER_CREATED = "User successfully created"
SUCCESS_ACCESS_TOKEN_CREATED = "Access token successfully created"
SUCCESS_REFRESH_TOKEN_CREATED = "Refresh token successfully created"

# messages.py

ERROR_GET_CONTAINERS = "An error occurred while retrieving the list of containers"
ERROR_PACKED_CONTAINER = "An error occurred while confirming the packed container"
ERROR_GET_CONTAINER_KIT = "An error occurred while retrieving the container kit"
ERROR_RETRIEVE_CONTAINER_KIT = "An error occurred while retrieving the container kit data"

SUCCESS_CONTAINER_CREATED = "Container successfully created"
SUCCESS_CONTAINER_RENAMED = "Container successfully renamed"
SUCCESS_CONTAINER_DELETED = "Container successfully deleted"
SUCCESS_CONTAINER_PACKED = "Container successfully confirmed as packed"
SUCCESS_CONTAINER_KIT_RETRIEVED = "Container kit successfully retrieved"
SUCCESS_CONTAINER_KIT_DOWNLOADED = "Container kit successfully downloaded"


# messages.py

ERROR_CONTAINER_NOT_FOUND = "Container not found."
ERROR_DM_NOT_FOUND = "DM code not found."
ERROR_ADD_DM = "An error occurred while adding the DM code to the container."
ERROR_DELETE_DM = "An error occurred while deleting the DM code from the container."
ERROR_INTERNAL_SERVER = "An error occurred: {error_message}"

SUCCESS_DM_ADDED = "DM code successfully added to the container."
SUCCESS_DM_DELETED = "DM code successfully deleted from the container."
SUCCESS_DM_STATUS_RETRIEVED = "DM code status successfully retrieved."

