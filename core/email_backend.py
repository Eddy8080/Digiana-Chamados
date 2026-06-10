"""
Backend SMTP compatível com Python 3.12.

O Django 3.2 passa keyfile/certfile para smtplib.SMTP_SSL, mas Python 3.12
removeu esses parâmetros. Este backend só os repassa quando não são None.
"""
import smtplib

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.utils import DNS_NAME


class Py312SMTPEmailBackend(EmailBackend):

    def open(self):
        if self.connection:
            return False
        params = {'local_hostname': DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            params['timeout'] = self.timeout
        if self.use_ssl:
            if self.ssl_keyfile:
                params['keyfile'] = self.ssl_keyfile
            if self.ssl_certfile:
                params['certfile'] = self.ssl_certfile
        try:
            klass = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
            self.connection = klass(self.host, self.port, **params)
            if not self.use_ssl and self.use_tls:
                self.connection.ehlo()
                starttls_params = {}
                if self.ssl_keyfile:
                    starttls_params['keyfile'] = self.ssl_keyfile
                if self.ssl_certfile:
                    starttls_params['certfile'] = self.ssl_certfile
                self.connection.starttls(**starttls_params)
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
