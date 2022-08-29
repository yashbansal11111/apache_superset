# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#
import logging
import os
from datetime import timedelta
from typing import Optional

from cachelib.file import FileSystemCache
from celery.schedules import crontab

logger = logging.getLogger()


def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "The environment variable {} was missing, abort...".format(
                var_name
            )
            raise EnvironmentError(error_msg)


DATABASE_DIALECT = get_env_variable("DATABASE_DIALECT")
DATABASE_USER = get_env_variable("DATABASE_USER")
DATABASE_PASSWORD = get_env_variable("DATABASE_PASSWORD")
DATABASE_HOST = get_env_variable("DATABASE_HOST")
DATABASE_PORT = get_env_variable("DATABASE_PORT")
DATABASE_DB = get_env_variable("DATABASE_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = "%s://%s:%s@%s:%s/%s" % (
    DATABASE_DIALECT,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB,
)

REDIS_HOST = get_env_variable("REDIS_HOST")
REDIS_PORT = get_env_variable("REDIS_PORT")
REDIS_CELERY_DB = get_env_variable("REDIS_CELERY_DB", "0")
REDIS_RESULTS_DB = get_env_variable("REDIS_RESULTS_DB", "1")

RESULTS_BACKEND = FileSystemCache("/app/superset_home/sqllab")

WEBDRIVER_TYPE = "chrome"
WEBDRIVER_OPTION_ARGS = [
    "--force-device-scale-factor=2.0",
    "--high-dpi-support=2.0",
    "--headless",
    "--disable-gpu",
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-extensions",
]
class CeleryConfig(object):
    BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB}"
    CELERY_IMPORTS = ("superset.sql_lab",)
    CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_RESULTS_DB}"
    CELERYD_LOG_LEVEL = "DEBUG"
    CELERYD_PREFETCH_MULTIPLIER = 1
    CELERY_ACKS_LATE = False
    CELERYBEAT_SCHEDULE = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=10, hour=0),
        },
    }


CELERY_CONFIG = CeleryConfig

FEATURE_FLAGS = {"ALERT_REPORTS": True,
                "EMBEDDED_SUPERSET": True}
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False
WEBDRIVER_BASEURL = "http://superset:8088/"
# The base URL for the email report hyperlinks.
WEBDRIVER_BASEURL_USER_FRIENDLY = WEBDRIVER_BASEURL

SQLLAB_CTAS_NO_LIMIT = True

#
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden
#
try:
    import superset_config_docker
    from superset_config_docker import *  # noqa

    logger.info(
        f"Loaded your Docker configuration at " f"[{superset_config_docker.__file__}]"
    )
except ImportError:
    logger.info("Using default Docker config...")

ENABLE_SCHEDULED_EMAIL_REPORTS = True
EMAIL_NOTIFICATIONS = True  # all the emails are sent using dryrun
SMTP_HOST = 'smtp.gmail.com'
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = "bansal.yash111@gmail.com"
SMTP_PORT = 587
SMTP_PASSWORD = "ykqbhpzdqpklrueo"
SMTP_MAIL_FROM = "bansal.yash111@gmail.com"

ENABLE_CHUNK_ENCODING = False


SCHEDULED_QUERIES = {
    # This information is collected when the user clicks "Schedule query",
    # and saved into the `extra` field of saved queries.
    # See: https://github.com/mozilla-services/react-jsonschema-form
    'JSONSCHEMA': {
        'title': 'Schedule',
        'description': (
            'In order to schedule a query, you need to specify when it '
            'should start running, when it should stop running, and how '
            'often it should run. You can also optionally specify '
            'dependencies that should be met before the query is '
            'executed. Please read the documentation for best practices '
            'and more information on how to specify dependencies.'
        ),
        'type': 'object',
        'properties': {
            'output_table': {
                'type': 'string',
                'title': 'Output table name',
            },
            'start_date': {
                'type': 'string',
                'title': 'Start date',
                # date-time is parsed using the chrono library, see
                # https://www.npmjs.com/package/chrono-node#usage
                'format': 'date-time',
                'default': 'tomorrow at 9am',
            },
            'end_date': {
                'type': 'string',
                'title': 'End date',
                # date-time is parsed using the chrono library, see
                # https://www.npmjs.com/package/chrono-node#usage
                'format': 'date-time',
                'default': '9am in 30 days',
            },
            'schedule_interval': {
                'type': 'string',
                'title': 'Schedule interval',
            },
            'dependencies': {
                'type': 'array',
                'title': 'Dependencies',
                'items': {
                    'type': 'string',
                },
            },
        },
    },
    'UISCHEMA': {
        'schedule_interval': {
            'ui:placeholder': '@daily, @weekly, etc.',
        },
        'dependencies': {
            'ui:help': (
                'Check the documentation for the correct format when '
                'defining dependencies.'
            ),
        },
    },
    'VALIDATION': [
        # ensure that start_date <= end_date
        {
            'name': 'less_equal',
            'arguments': ['start_date', 'end_date'],
            'message': 'End date cannot be before start date',
            # this is where the error message is shown
            'container': 'end_date',
        },
    ],
    # link to the scheduler; this example links to an Airflow pipeline
    # that uses the query id and the output table as its name
    'linkback': (
        'https://airflow.example.com/admin/airflow/tree?'
        'dag_id=query_${id}_${extra_json.schedule_info.output_table}'
    ),
}
