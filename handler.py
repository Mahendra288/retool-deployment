import json


def hello(event, context):
    print("event:", event)
    print("context:", context)

    return {
        "status_code": 200,
    }
