from http.server import BaseHTTPRequestHandler, HTTPServer
from string import Template
from typing import Optional
from urllib.parse import parse_qs, urlparse
from oauth2_cli_auth._timeout import _method_with_timeout, TimeoutException


class CallbackPageTemplate:
    SUCCESS_SVG = """
    <svg xmlns="http://www.w3.org/2000/svg" width="154px" height="154px">
        <g fill="none" stroke="#22AE73" stroke-width="2">
            <circle cx="77" cy="77" r="72" style="stroke-dasharray:480px, 480px; stroke-dashoffset: 960px;"></circle>
            <circle id="colored" fill="#22AE73" cx="77" cy="77" r="72" style="stroke-dasharray:480px, 480px; stroke-dashoffset: 960px;"></circle>
            <polyline class="st0" stroke="#fff" stroke-width="10" points="43.5,77.8 63.7,97.9 112.2,49.4 " style="stroke-dasharray:100px, 100px; stroke-dashoffset: 200px;"/>
        </g>
    </svg>
    """

    ERROR_SVG = """
    <svg xmlns="http://www.w3.org/2000/svg" width="154px" height="154px">
        <g fill="none" stroke="#F44812" stroke-width="2">
            <circle cx="77" cy="77" r="72" style="stroke-dasharray:480px, 480px; stroke-dashoffset: 960px;"></circle>
            <circle id="colored" fill="#F44812" cx="77" cy="77" r="72" style="stroke-dasharray:480px, 480px; stroke-dashoffset: 960px;"></circle>
            <polyline class="st0" stroke="#fff" stroke-width="10" points="43.5,77.8  112.2,77.8 " style="stroke-dasharray:100px, 100px; stroke-dashoffset: 200px;"/>
        </g>
    </svg>
    """

    PAGE_TEMPLATE = Template("""
    <html lang="$lang">
        <head>
            <title>$title</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <meta name="charset" content="utf-8">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                }

                @media (prefers-color-scheme: dark) {
                    body {
                        background: rgb(34, 39, 46);
                        color: rgb(173, 186, 199);
                    }
                }

                html, body {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100%;
                }

                h1 {
                    font-size: 4rem;
                }

                p {
                    font-size: 1.4rem;
                    max-width: 70ch;
                }

                .message {
                    text-align: center;
                }

                .animation-ctn {
                    text-align: center;
                }

                @keyframes checkmark {
                    0% {
                        stroke-dashoffset: 100px
                    }

                    100% {
                        stroke-dashoffset: 0px
                    }
                }

                @keyframes checkmark-circle {
                    0% {
                        stroke-dashoffset: 480px
                    }

                    100% {
                        stroke-dashoffset: 960px
                    }
                }

                @keyframes colored-circle {
                    0% {
                        opacity: 0
                    }

                    100% {
                        opacity: 100
                    }
                }

                .icon svg {
                    padding: 1rem;
                }

                .icon svg polyline {
                    -webkit-animation: checkmark 0.25s ease-in-out 0.7s backwards;
                    animation: checkmark 0.25s ease-in-out 0.7s backwards
                }

                .icon svg circle {
                    -webkit-animation: checkmark-circle 0.6s ease-in-out backwards;
                    animation: checkmark-circle 0.6s ease-in-out backwards;
                }

                .icon svg circle#colored {
                    -webkit-animation: colored-circle 0.6s ease-in-out 0.7s backwards;
                    animation: colored-circle 0.6s ease-in-out 0.7s backwards;
                }
            </style>
        </head>

        <body>
        <div class="message">
            <div class="animation-ctn">
                <div class="icon">
                    $svg
                </div>
            </div>

            <h1>$title</h1>
            <p>$message</p>
        </div>
        </body>
        </html>
        """)

    def render(self, title: str, message: str, lang: str = "en", has_error: bool = False):
        return self.PAGE_TEMPLATE.substitute(
            lang=lang,
            title=title,
            message=message,
            svg=self.ERROR_SVG if has_error else self.SUCCESS_SVG,
        )


class OAuthRedirectHandler(BaseHTTPRequestHandler):
    callback_template = CallbackPageTemplate()

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)

        has_error = "code" not in params or len(params['code']) != 1 or params['code'][0].strip() == ""

        if has_error:
            self.send_response(400)
            title = "Oh snap!"
            message = "Something went wrong trying to authenticate you. Please try going back in your browser, or restart the auth process."
        else:
            self.send_response(200)
            self.server._code = params["code"][0]
            title = "Success"
            message = "You have been authenticated successfully. You may close this browser window now and go back to the terminal"

        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            self.callback_template
            .render(
                lang="en",
                title=title,
                message=message,
                has_error=has_error
            )
            .encode("utf-8")
        )


class OAuthCallbackHttpServer(HTTPServer):
    """
    Simplistic HTTP Server to provide local callback URL for oauth2 provider
    """

    def __init__(self, port):
        super().__init__(("", port), OAuthRedirectHandler)

        self._code = None

    def get_code(self):
        return self._code

    @property
    def callback_url(self):
        return f"http://localhost:{self.server_port}"

    def wait_for_code(self, attempts: int = 3, timeout_per_attempt=10) -> Optional[int]:
        """
        Wait for the server to open the callback page containing the code query parameter.

        It tries for #attempts with a timeout of #timeout_per_attempts for each attempt.
        This prevents the CLI from getting stuck by unsolved callback URls

        :param attempts: Amount of attempts
        :param timeout_per_attempt: Timeout for each attempt to be successful
        :return: Code from callback page or None if the callback page is not called successfully
        """
        for i in range(0, attempts):
            try:
                _method_with_timeout(self.handle_request, timeout_seconds=timeout_per_attempt)
            except TimeoutException:
                continue
            if self.get_code() is not None:
                return self.get_code()

        return None
