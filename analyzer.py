from dataclasses import dataclass
import json
import requests


@dataclass
class QueryReq:
    query: str

    def to_dict(self):
        return {"query": self.query}


class RestClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password

    def build_v1_url(self, *paths) -> str:
        """Build a V1 API URL by joining paths to the base URL."""
        full_path = "/".join(["proton/v1"] + [p.strip("/") for p in paths])
        return f"{self.base_url.rstrip('/')}/{full_path}"

    def request(self, method: str, url: str, data=None) -> bytes:
        """Make an HTTP request and return the response body."""
        headers = {"Content-Type": "application/json"}

        try:
            if data:
                payload = data.to_dict() if hasattr(data, "to_dict") else data
                response = requests.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    auth=(self.username, self.password),
                )
            else:
                response = requests.request(method=method, url=url, headers=headers)

            if response.status_code != 200:
                raise Exception(
                    f"Request failed with status code {response.status_code}: {response.content}"
                )

            return response.content
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}")


class Client:
    def __init__(self, username, password, host, port=3218):
        base_url = f"http://{host}:{port}/"
        self.rest_client = RestClient(base_url, username, password)
        self.analyze_sql_path = "sqlanalyzer"  # Assuming this is the path

    def analyze_sql(self, sql: str) -> dict:
        """Analyze SQL query and return the analysis result."""

        url = self.rest_client.build_v1_url(self.analyze_sql_path)
        request = QueryReq(query=sql)

        try:
            resp_body = self.rest_client.request("POST", url, request)
            result_data = json.loads(resp_body)
            return result_data
        except json.JSONDecodeError as e:
            raise Exception(f"failed to decode analyze response: {e}")
        except Exception as e:
            raise Exception(f"Analyze SQL failed: {e}")
