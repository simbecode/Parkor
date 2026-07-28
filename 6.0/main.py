import os
import sys
import logging
import datetime as dt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_fetcher import DataFetcher
from data_analyzer import DataAnalyzer
from utils import calculate_values_count, calculate_page_count, get_area_name, get_area_code
from settings_dialog import SettingsDialog
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QStringListModel, QUrl
from PyQt5.QtGui import QDesktopServices, QIcon

class AnalyzerThread(QThread):
    analysis_done = pyqtSignal(object)   # 분석 완료 시그널
    status_update  = pyqtSignal(str)     # 상태바 텍스트 업데이트 시그널
    
    def __init__(self, list_views, total_area, missing_threshold, negative_tail, zero_threshold):
        super().__init__()
        self.list_views = list_views
        self.total_area = total_area
        self.missing_threshold = missing_threshold
        self.negative_tail = negative_tail
        self.zero_threshold = zero_threshold
        self.analyzer = None
    # 모든 지점 번호
    # def run(self):
    #     total_area = [
    #         "0011", "0012", "0013", "0021", "0022", "0023",
    #         "0031", "0032", "0033", "0041", "0042", "0043",
    #         "0051", "0052", "0053", "0061", "0062", "0063",
    #         "0071", "0072", "0073", "0081", "0082", "0083",
    #         "0091", "0092", "0093", "0101", "0102", "0103",
    #         "0111", "0112", "0113", "0121", "0122", "0123",
    #         "0131", "0132", "0133", "0141", "0142", "0143",
    #         "0151", "0152", "0153", "0161", "0162", "0163",
    #         "0171", "0172", "0173", "0181", "0182", "0183",
    #         "0191", "0192", "0193", "0201", "0202", "0203",
    #         "0211", "0212", "0213", "0221", "0222", "0223",
    #         "0231", "0232", "0233", "0241", "0242", "0243",
    #         "0251", "0252", "0253", "0261", "0262", "0263",
    #         "0271", "0272", "0273", "0281", "0282", "0283",
    #         "0291", "0292", "0293", "0301", "0302", "0303",
    #         "0311", "0312", "0313", "0321", "0322", "0323",
    #         "0331", "0332", "0333", "0341", "0342", "0343",
    #         "0351", "0352", "0353", "0361", "0362", "0363",
    #         "0371", "0372", "0373", "0381", "0382", "0383",
    #         "0391", "0392", "0393", "0401", "0402", "0403",
    #         "0411", "0412", "0413", "0421", "0422", "0423",
    #         "0431", "0432", "0433", "0441", "0442", "0443",
    #         "0451", "0452", "0453"
    #     ]
    # 수정 지점 번호
    AREA_WORKERS = 15  # 관측소 동시 수집 스레드 수 (서버 부하 고려하여 조정)

    def run(self):
        total_area = self.total_area
        values_cnt = calculate_values_count()
        page_count = calculate_page_count()
        start = dt.datetime.now().strftime('%Y-%m-%d')
        end = dt.datetime.now().strftime('%Y-%m-%d')

        self.analyzer = DataAnalyzer(
            self.list_views,
            missing_threshold=self.missing_threshold,
            negative_tail=self.negative_tail,
            zero_threshold=self.zero_threshold
        )
        self.analyzer.set_values_count(values_cnt)

        total = len(total_area)

        # ── 1단계: 모든 관측소 데이터를 병렬로 수집 ──────────────────────
        fetched = {}  # {area: DataFrame}
        done_count = 0

        def fetch_one(area):
            return area, DataFetcher.fetch_data_for_area(area, start, end, page_count)

        with ThreadPoolExecutor(max_workers=self.AREA_WORKERS) as executor:
            future_to_area = {executor.submit(fetch_one, area): area for area in total_area}
            for future in as_completed(future_to_area):
                area = future_to_area[future]
                try:
                    area_code, data = future.result()
                    fetched[area_code] = data
                except Exception as e:
                    logging.warning(f"[{area}] 수집 오류: {e}")
                    fetched[area] = pd.DataFrame()
                finally:
                    done_count += 1
                    self.status_update.emit(f"수집 중...  {done_count} / {total}  ({start})")

        # ── 2단계: 수집된 데이터를 원래 순서대로 순차 분석 ───────────────
        # (Qt 모델 업데이트 및 공유 리스트 수정이 있어 순차 처리)
        self.status_update.emit("분석 중...")
        for area in total_area:
            area_name = get_area_name(area)
            data = fetched.get(area, pd.DataFrame())
            self.analyzer.analyze_data(data, area_name)

        self.analysis_done.emit(self.analyzer)

def display_results(analyzer, window):
    now = dt.datetime.now().strftime('%H:%M:%S')
    total_issues = (
        len(analyzer.final_count_data_zero) +
        len(analyzer.final_count_data_name) +
        len(analyzer.final_zero_state) +
        len(analyzer.final_weather_state) +
        len(analyzer.final_under_date)
    )
    values_cnt = analyzer.values_cnt if analyzer.values_cnt is not None else 0
    window.statusBar().showMessage(
        f"분석 완료  |  {now}  |  예상 건수: {values_cnt}건  |  이상 감지: {total_issues}건"
    )

def start_analysis(window):
    list_views = [window.listView_1, window.listView_2, window.listView_3, window.listView_4, window.listView_5]
    total_area        = SettingsDialog.load_selected_areas()
    missing_threshold = SettingsDialog.load_missing_threshold()
    negative_tail     = SettingsDialog.load_negative_tail()
    zero_threshold    = SettingsDialog.load_zero_threshold()

    analyzer_thread = AnalyzerThread(list_views, total_area, missing_threshold, negative_tail, zero_threshold)

    def on_analysis_done(analyzer):
        analyzer_thread.status_update.disconnect()  # 완료 후 상태바 덮어쓰기 방지
        display_results(analyzer, window)

    analyzer_thread.analysis_done.connect(on_analysis_done)
    analyzer_thread.status_update.connect(window.statusBar().showMessage)
    analyzer_thread.start()
    return analyzer_thread

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # uic.loadUi("C:\\SI\\Program\\dust\\5.0\\main.ui", self)
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        uic.loadUi(os.path.join(base_path, 'main.ui'), self)

        icon_path = os.path.join(base_path, 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        now = dt.datetime.now().strftime('%Y-%m-%d')
        self.statusBar().showMessage(f"준비 중...  |  조회일: {now}")

        # 모델 생성 및 QListView에 설정
        self.setup_list_view(self.listView_1)
        self.setup_list_view(self.listView_2)
        self.setup_list_view(self.listView_3)
        self.setup_list_view(self.listView_4)
        self.setup_list_view(self.listView_5)

        # 메뉴바 — 설정
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("설정")
        open_settings_action = QtWidgets.QAction("설정 열기", self)
        open_settings_action.setShortcut("Ctrl+,")
        open_settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(open_settings_action)

        # 분석 시작
        self.analyzer_thread = start_analysis(self)
        self.statusBar().showMessage(f"수집 시작  |  조회일: {now}")

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_() == SettingsDialog.Accepted:
            # 설정 저장 후 리스트뷰 초기화 → 재분석
            for lv in [self.listView_1, self.listView_2, self.listView_3,
                       self.listView_4, self.listView_5]:
                lv.model().setStringList([])
            self.analyzer_thread = start_analysis(self)
            now = dt.datetime.now().strftime('%Y-%m-%d')
            self.statusBar().showMessage(f"재분석 시작  |  조회일: {now}")

    def setup_list_view(self, list_view):
        model = QStringListModel()
        list_view.setModel(model)
        list_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # 더블 클릭 편집 비활성화
        list_view.doubleClicked.connect(self.on_item_double_clicked)

    def on_item_double_clicked(self, index):
        text = index.data()
        if text:
            area_code = self.extract_area_code(text)
            if not area_code:
                return  # 코드 조회 실패 시 브라우저 열기 중단
            start = dt.datetime.now().strftime('%Y-%m-%d')
            end = dt.datetime.now().strftime('%Y-%m-%d')
            self.open_in_browser(area_code, "1", start, end)
    
    def extract_area_code(self, text):
        # listView 표시 텍스트 형식: "area_name, ..." (첫 번째 쉼표 앞이 area_name)
        area_name = text.split(",")[0].strip()
        code = get_area_code(area_name)
        if code:
            return code
        # 역방향 조회 실패 시 경고 후 빈 문자열 반환 (잘못된 코드로 요청 방지)
        logging.warning(f"area_code 조회 실패 — area_name: '{area_name}'")
        return ""

    def open_in_browser(self, area_code, page, start, end):
        base_url = "http://aican.nifos.go.kr/data/obsrrData.do"
        full_url = f"{base_url}?obsrrTpCd={area_code}&fromDate={start}&toDate={end}"
        url = QUrl(full_url)
        if QDesktopServices.openUrl(url):
            print(f"Opened {url.toString()} in default browser.")
        else:
            print(f"Failed to open {url.toString()}.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
