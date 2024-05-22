from werkzeug.exceptions import HTTPException
from flask import make_response
import json

class BusinessValidationError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        data = { "error_code" : error_code, "error_message": error_message }
        self.response = make_response(json.dumps(data), status_code)

class BookNotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('Book not found', status_code)

class SectionNotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('Section not found', status_code)

class IssueNotFoundError(HTTPException):
    def __init__(self, status_code):
        self.response = make_response('Issue not found', status_code)

class OtherError(HTTPException):
    def __init__(self, status_code, description):
        self.response = make_response(description, status_code)