import requests
import pandas as pd
from io import StringIO

class DataFetcher:
    @staticmethod
    def get_data(area, page, start, end):
        url = "http://aican.nifos.go.kr/data/pastInfoVw.do"
        params = {
            "obsrrTpCd": area,
            "pageIndex": page,
            "fromDate": start,
            "toDate": end
        }
        

        try:
            response = requests.post(url=url, data=params)
            response.raise_for_status()

            html_content = StringIO(response.text)
            return pd.read_html(html_content)[0]
        except requests.HTTPError as e:
            print(f"HTTP 에러: {e}")
        except requests.RequestException as e:
            print(f"요청 실패: {e}")
        except Exception as e:
            print(f"오류 발생: {e}")

        return pd.DataFrame()

    @staticmethod
    def fetch_data_for_area(area, start, end, pages):
        df_list = [DataFetcher.get_data(area, page+1, start, end) for page in range(pages)]
        return pd.concat(df_list, ignore_index=True)
