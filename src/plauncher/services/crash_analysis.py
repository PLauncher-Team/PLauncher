from typing import Any, Callable


class CrashLogAnalyzerService:
    POLLINATIONS_URL = "https://text.pollinations.ai/"
    MCLO_URL = "https://api.mclo.gs/1/analyse"

    def __init__(
        self,
        http_client: Any,
        user_agent: str,
        logger: Callable[..., None] | None = None,
    ) -> None:
        self.http = http_client
        self.headers = {
            "User-Agent": user_agent,
            "Content-Type": "application/json",
        }
        self.logger = logger

    def analyze(self, messages: list[dict[str, str]], timeout: int = 30) -> str | Exception:
        pollinations_result = self._try_pollinations(messages, timeout)
        if not isinstance(pollinations_result, Exception) and pollinations_result != "None":
            self._log("Received response from Pollinations API")
            return pollinations_result

        mclo_result = self._try_mclo(messages, timeout)
        if not isinstance(mclo_result, Exception) and mclo_result:
            self._log("Received response from mclo.gs API")
            return mclo_result

        self._log("All crash analysis APIs failed", "ERROR")
        return mclo_result

    def _try_mclo(self, messages: list[dict[str, str]], timeout: int) -> str | Exception:
        try:
            response = self.http.post(
                self.MCLO_URL,
                json={"content": messages[1]["content"]},
                headers=self.headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return "\n".join(
                solution["message"]
                for problem in response.json()["analysis"]["problems"]
                for solution in problem["solutions"]
            )
        except Exception as error:
            self._log(f"mclo.gs analysis failed: {error}", "ERROR")
            return error

    def _try_pollinations(self, messages: list[dict[str, str]], timeout: int) -> str | Exception:
        try:
            response = self.http.post(
                self.POLLINATIONS_URL,
                json={"messages": messages},
                headers=self.headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.text
        except Exception as error:
            self._log(f"Pollinations analysis failed: {error}", "WARNING")
            return error

    def get_response(self, messages: list[dict[str, str]], timeout: int = 30) -> str | Exception:
        return self.analyze(messages, timeout)

    def _log(self, message: str, level: str = "INFO") -> None:
        if self.logger is not None:
            self.logger(message, level=level)
