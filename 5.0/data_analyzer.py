import pandas as pd
import numpy as np
from PyQt5.QtCore import QStringListModel
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataAnalyzer:
    def __init__(self, list_views):
        self.final_count_data_zero = []
        self.final_weather_state = []
        self.final_zero_state = []
        self.final_under_date = []
        self.final_count_data_name = []
        self.values_cnt = None
        self.list_views = list_views

    def set_values_count(self, values_cnt):
        self.values_cnt = values_cnt

    def clean_data(self, data):
        filtered_data = data[~data.apply(lambda row: row.str.contains("조회된 이력이 없습니다.").all(), axis=1)]
        return filtered_data

    def analyze_data(self, data_concat, bad_area):
        data_concat = self.clean_data(data_concat)
        if data_concat.empty:
            self.final_count_data_zero.append(bad_area)
            self.append_to_list_view(self.list_views[0], bad_area)
            return

        # 데이터 전처리
        try:
            processed_data = self.process_data(data_concat)
        except Exception as e:
            logging.error(f"데이터 처리 오류: {e}")
            return

        # 조건 및 결과 처리
        try:
            self.handle_counts_and_conditions(bad_area, processed_data)
        except Exception as e:
            logging.error(f"조건 및 결과 처리 오류: {e}")

    def process_data(self, data):
        time_data = data[['관측시간']]
        minus_time_data = time_data.iloc[:-2]
        result_nancheck = data[['온도(℃)', '습도(%)', '풍속(㎧)', '풍향(degree)']]
        normal_data = data[['산림 미세먼지 농도', '산업유래 휘발성유기화합물 미세먼지 농도']].iloc[:-2]
        normal_data.columns = ['col1', 'col2', 'col3', 'col4', 'col5', 'col6']
        sub1_data = normal_data[['col1', 'col2', 'col3']]
        sub2_data = normal_data[['col4', 'col5', 'col6']]
        sub2_data.columns = ['col1', 'col2', 'col3']

        result_data = sub1_data.astype(float).sub(sub2_data.astype(float))
        result_data.columns = ['pm10', 'pm2.5', 'pm1.0']
        time_add_result_data = pd.concat([minus_time_data, result_data], axis=1)

        return {
            "result_data": result_data,
            "time_add_result_data": time_add_result_data,
            "result_nancheck": result_nancheck,
            "normal_data": normal_data,
            "time_data": time_data
        }

    def handle_counts_and_conditions(self, bad_area, processed_data):
        result_data = processed_data["result_data"]
        time_add_result_data = processed_data["time_add_result_data"]
        result_nancheck = processed_data["result_nancheck"]
        normal_data = processed_data["normal_data"]
        time_data = processed_data["time_data"]

        condition_under = (result_data < 0).any()
        condition_zero = (normal_data == 0).any()
        check_for_nan = result_nancheck.isnull().values.any()

        data_index_cnt = len(processed_data["time_data"].index)

        if self.values_cnt is None:
            raise ValueError("values_cnt 값이 설정되지 않았습니다.")
        
        if data_index_cnt < self.values_cnt - 10:
            if data_index_cnt == 0:
                self.final_count_data_zero.append(bad_area)
            else:
                recent_time = time_data.values[-1] if len(time_data.values) > 1 else None
                if recent_time is not None and isinstance(recent_time, np.ndarray) and recent_time.size > 0:
                    datetime_str = recent_time[0]
                    try:
                        recent_time_str = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M").strftime("%H:%M")
                        self.final_count_data_name.append((bad_area, data_index_cnt, recent_time_str))
                        self.append_to_list_view(self.list_views[1], f"{bad_area}, {data_index_cnt}, {recent_time_str}")
                    except ValueError as e:
                        logging.error(f"시간 형식 변환 오류: {e}")
        
        if condition_zero.any():
            zero_values_mask = (normal_data == 0)
            zero_counts = zero_values_mask.sum().sum()
            if zero_counts > 0:
                self.final_zero_state.append((bad_area, zero_counts))
                self.append_to_list_view(self.list_views[2], f"{bad_area}, {zero_counts}")

        if condition_under.any():
            result_data_tail_6 = result_data.tail(6)
            final_result_data_tail_6 = (result_data_tail_6 < 0).any()
            final_plus_result_data_tail_6 = (result_data_tail_6 > 0).any()
            if final_result_data_tail_6.any() and not final_plus_result_data_tail_6.any():
                min_value_row = time_add_result_data.tail(6).min()
                max_value_row = time_add_result_data.tail(6).max()
                
                # 관측시간/관측시간 항목 제거
                min_value_row = min_value_row.drop(labels='관측시간', errors='ignore')
                max_value_row = max_value_row.drop(labels='관측시간', errors='ignore')

                # 문자열이 아닌 데이터만 남기기
                min_value_row = min_value_row.apply(pd.to_numeric, errors='coerce').dropna()
                max_value_row = max_value_row.apply(pd.to_numeric, errors='coerce').dropna()
                
                # 최저값과 최고값 추출 후 소수 첫 번째 자리까지 반올림
                min_value = round(min_value_row.min(), 1)
                max_value = round(max_value_row.max(), 1)
                
                self.final_under_date.append((bad_area, min_value, max_value))
                self.append_to_list_view(self.list_views[4], f"{bad_area}, Min: {min_value}, Max: {max_value}")

        if check_for_nan:
            nan_counts = result_nancheck.isnull().sum().sum()
            self.final_weather_state.append((bad_area, nan_counts))
            
            # NaN이 포함된 행의 최근 시간만 가져오기
            nan_time_data = processed_data["time_data"][result_nancheck.isnull().any(axis=1)]
            if not nan_time_data.empty:
                recent_nan_time = nan_time_data.iloc[-1, 0]
                try:
                    # 시간만 추출하여 시:분 형식으로 변환
                    recent_nan_time_str = datetime.strptime(recent_nan_time, "%Y-%m-%d %H:%M").strftime("%H:%M")
                    self.append_to_list_view(self.list_views[3], f"{bad_area}, {nan_counts}, {recent_nan_time_str}")
                except ValueError as e:
                    logging.error(f"시간 형식 변환 오류: {e}")
            else:
                self.append_to_list_view(self.list_views[3], f"{bad_area}, {nan_counts}")

    def append_to_list_view(self, list_view, text):
        try:
            model = list_view.model()
            current_list = model.stringList()
            current_list.append(text)
            model.setStringList(current_list)
        except Exception as e:
            logging.error(f"리스트 뷰 업데이트 중 오류 발생: {e}")
