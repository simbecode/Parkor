import requests
import pandas as pd
import logging
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DataFetcher:
    BASE_URL = "https://aican.nifos.go.kr"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": BASE_URL,
        "Referer": f"{BASE_URL}/data/obsrrData.do",
        "X-Requested-With": "XMLHttpRequest",
    }

    @staticmethod
    def get_data(area, page, start, end):
        url = f"{DataFetcher.BASE_URL}/data/pastInfoVw.do"
        params = {
            "obsrrTpCd": area,
            "pageIndex": page,
            "fromDate": start,
            "toDate": end
        }

        try:
            response = requests.post(url=url, data=params, headers=DataFetcher.HEADERS, timeout=15)
            response.raise_for_status()

            html_content = StringIO(response.text)
            return pd.read_html(html_content)[0]
        except requests.HTTPError as e:
            logging.warning(f"[{area}] p{page} HTTP 에러: {e}")
        except requests.RequestException as e:
            logging.warning(f"[{area}] p{page} 요청 실패: {e}")
        except Exception as e:
            logging.warning(f"[{area}] p{page} 오류 발생: {e}")

        return pd.DataFrame()

    @staticmethod
    def fetch_data_for_area(area, start, end, pages):
        df_list = [DataFetcher.get_data(area, page + 1, start, end) for page in range(pages)]
        valid = [df for df in df_list if not df.empty]
        if not valid:
            return pd.DataFrame()
        return pd.concat(valid, ignore_index=True)
