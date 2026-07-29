import os
import sys
import json
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
from PyQt5.QtGui import QIcon, QKeySequence

APP_VERSION = "6.2"


class PandasTableModel(QtCore.QAbstractTableModel):
    """상세 창에서 pandas DataFrame을 읽기 전용으로 표시하는 모델."""

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data if data is not None else pd.DataFrame()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self._data.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self._data.columns)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return None
        value = self._data.iat[index.row(), index.column()]
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        column = self._data.columns[index.column()]
        column_text = (
            " ".join(str(part) for part in column)
            if isinstance(column, tuple)
            else str(column)
        )
        if "차이" in column_text:
            try:
                return f"{float(value):.2f}"
            except (TypeError, ValueError):
                pass
        return str(value)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            column = self._data.columns[section]
            if isinstance(column, tuple):
                parts = [
                    str(part) for part in column
                    if str(part) and not str(part).startswith("Unnamed:")
                ]
                if not parts:
                    return ""

                group = parts[0]
                measurement = parts[-1]
                measurement = (
                    measurement
                    .replace("(㎍/m³)", "")
                    .replace("(ug/m³)", "")
                    .replace("(℃)", "")
                    .replace("(%)", "")
                    .replace("(㎧)", "")
                    .replace("(degree)", "")
                    .strip()
                )

                if group == "산림 미세먼지 농도":
                    return f"산림 {measurement}"
                if group == "산업유래 휘발성유기화합물 미세먼지 농도":
                    return f"산업 {measurement}"
                if group == "관측시간":
                    return "관측시간"
                return measurement
            return str(column)
        return str(self._data.index[section])


def filter_detail_data(raw_data, issue_type, negative_tail=6):
    """목록의 이상 유형에 맞는 행만 상세 표에 반환한다."""
    if raw_data is None or raw_data.empty:
        return pd.DataFrame()

    data = raw_data.copy()

    if issue_type == "누락 데이터":
        if "관측시간" not in data.columns:
            return pd.DataFrame()

        observed = pd.to_datetime(
            data["관측시간"].iloc[:, 0]
            if isinstance(data["관측시간"], pd.DataFrame)
            else data["관측시간"],
            errors="coerce"
        ).dropna()
        expected_count = calculate_values_count()
        if expected_count <= 0:
            return pd.DataFrame(columns=["관측시간", "상태"])

        today = pd.Timestamp.now().normalize()
        expected = pd.date_range(today, periods=expected_count, freq="10min")
        missing = expected.difference(pd.DatetimeIndex(observed))
        return pd.DataFrame({
            "관측시간": missing.strftime("%Y-%m-%d %H:%M"),
            "상태": "누락"
        })

    if issue_type == "제로값 발생":
        try:
            particulate = data[[
                "산림 미세먼지 농도",
                "산업유래 휘발성유기화합물 미세먼지 농도"
            ]]
        except KeyError:
            return pd.DataFrame()
        numeric = particulate.apply(pd.to_numeric, errors="coerce")
        return data.loc[numeric.eq(0).any(axis=1)].copy()

    if issue_type == "통합 센서 문제":
        weather_columns = ["온도(℃)", "습도(%)", "풍속(㎧)", "풍향(degree)"]
        try:
            weather = data[weather_columns]
        except KeyError:
            return pd.DataFrame()
        return data.loc[weather.isna().any(axis=1)].copy()

    if issue_type == "차이값 음수 문제":
        try:
            particulate = data[[
                "산림 미세먼지 농도",
                "산업유래 휘발성유기화합물 미세먼지 농도"
            ]].iloc[:-2]
        except KeyError:
            return pd.DataFrame()
        if particulate.shape[1] != 6:
            return pd.DataFrame()

        numeric = particulate.apply(pd.to_numeric, errors="coerce")
        differences = numeric.iloc[:, :3].to_numpy() - numeric.iloc[:, 3:6].to_numpy()
        difference_data = pd.DataFrame(
            differences,
            index=particulate.index,
            columns=["PM10 차이", "PM2.5 차이", "PM1.0 차이"]
        )
        recent = difference_data.tail(negative_tail)
        negative_rows = recent.lt(0).any(axis=1)
        indexes = recent.index[negative_rows]
        result = data.loc[indexes].copy()
        for column in difference_data.columns:
            result[column] = difference_data.loc[indexes, column]
        return result

    return data


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
            # 표시 문자열(지점명)이 변경되더라도 상세 데이터 조회가 깨지지
            # 않도록 서버 요청에 사용한 관측소 코드를 기준으로도 보관한다.
            self.analyzer.raw_data_by_area_code[area] = data.copy()
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
    window.current_analyzer = None

    def on_analysis_done(analyzer):
        analyzer_thread.status_update.disconnect()  # 완료 후 상태바 덮어쓰기 방지
        window.current_analyzer = analyzer
        display_results(analyzer, window)

    analyzer_thread.analysis_done.connect(on_analysis_done)
    analyzer_thread.status_update.connect(window.statusBar().showMessage)
    analyzer_thread.start()
    return analyzer_thread

class DetailDialog(QtWidgets.QDialog):
    def __init__(
        self, parent, area_name, area_code, issue_type, raw_text, start, end,
        raw_data=None, negative_tail=6
    ):
        super().__init__(parent)
        self.area_code = area_code
        self.start = start
        self.end = end
        self.setWindowTitle("상세 보기")
        self.resize(1100, 650)
        self.setMinimumSize(700, 450)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        form.addRow("지점명", QtWidgets.QLabel(area_name))
        form.addRow("관측소 코드", QtWidgets.QLabel(area_code))
        form.addRow("이상 유형", QtWidgets.QLabel(issue_type))
        form.addRow("조회일", QtWidgets.QLabel(start if start == end else f"{start} ~ {end}"))

        detail_label = QtWidgets.QLabel(raw_text)
        detail_label.setWordWrap(True)
        form.addRow("상세 내용", detail_label)
        layout.addLayout(form)

        filtered_data = filter_detail_data(raw_data, issue_type, negative_tail)
        layout.addWidget(QtWidgets.QLabel(f"필터된 원본 데이터 — {issue_type}"))
        self.data_table = QtWidgets.QTableView()
        self.data_model = PandasTableModel(filtered_data, self.data_table)
        self.data_table.setModel(self.data_model)
        self.data_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.data_table.setSortingEnabled(False)
        self.data_table.setWordWrap(False)
        self.data_table.setTextElideMode(QtCore.Qt.ElideNone)
        self.data_table.setStyleSheet(
            "QTableView::item { padding-left: 3px; padding-right: 3px; }"
            "QHeaderView::section { padding-left: 3px; padding-right: 3px; }"
        )
        self.data_table.verticalHeader().setDefaultSectionSize(27)
        self.data_table.verticalHeader().setMinimumWidth(28)
        self.data_table.verticalHeader().setMaximumWidth(42)
        self.data_table.horizontalHeader().setMinimumSectionSize(55)
        self.data_table.horizontalHeader().setMaximumSectionSize(420)
        self.data_table.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel)
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        header.setDefaultSectionSize(82)
        header.setStretchLastSection(False)

        # 관측시간을 제외한 측정값 컬럼은 남은 폭을 균등 분배한다.
        # 상세창 크기가 달라져도 전체 센서 값이 한 화면에 들어온다.
        for column_index in range(self.data_model.columnCount()):
            column_name = self.data_model.headerData(
                column_index, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole
            )
            if column_name == "관측시간":
                header.setSectionResizeMode(
                    column_index, QtWidgets.QHeaderView.Fixed)
                self.data_table.setColumnWidth(column_index, 132)
            elif self.data_model.columnCount() >= 6:
                header.setSectionResizeMode(
                    column_index, QtWidgets.QHeaderView.Stretch)
            else:
                self.data_table.setColumnWidth(column_index, 100)
        layout.addWidget(self.data_table, 1)

        if filtered_data.empty:
            empty_label = QtWidgets.QLabel(
                "이 필터 조건에 해당하는 원본 데이터가 없습니다."
            )
            empty_label.setStyleSheet("color: gray;")
            layout.addWidget(empty_label)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()
        open_button = QtWidgets.QPushButton("연동 사이트 열기")
        close_button = QtWidgets.QPushButton("닫기")
        open_button.clicked.connect(self.open_in_browser)
        close_button.clicked.connect(self.accept)
        button_row.addWidget(open_button)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

    def open_in_browser(self):
        if self.parent():
            self.parent().open_in_browser(self.area_code, self.start, self.end)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # uic.loadUi("C:\\SI\\Program\\dust\\5.0\\main.ui", self)
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        uic.loadUi(os.path.join(base_path, 'main.ui'), self)
        self.setWindowTitle(f"{self.windowTitle()} {APP_VERSION}")
        self.current_analyzer = None

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
            area_name = text.split(",")[0].strip()
            area_code = self.extract_area_code(text)
            if not area_code:
                QtWidgets.QMessageBox.warning(self, "상세 보기", "관측소 코드를 찾을 수 없습니다.")
                return  # 코드 조회 실패 시 브라우저 열기 중단
            start = dt.datetime.now().strftime('%Y-%m-%d')
            end = dt.datetime.now().strftime('%Y-%m-%d')
            issue_type = self.get_issue_type(self.sender())
            raw_data = None
            negative_tail = SettingsDialog.load_negative_tail()
            if self.current_analyzer is not None:
                raw_data = self.current_analyzer.raw_data_by_area_code.get(area_code)
                negative_tail = self.current_analyzer.negative_tail
            dlg = DetailDialog(
                self, area_name, area_code, issue_type, text, start, end,
                raw_data, negative_tail
            )
            dlg.exec_()

    def get_issue_type(self, list_view):
        issue_types = {
            self.listView_1: "조회 이력 없음",
            self.listView_2: "누락 데이터",
            self.listView_3: "제로값 발생",
            self.listView_4: "통합 센서 문제",
            self.listView_5: "차이값 음수 문제",
        }
        return issue_types.get(list_view, "이상 항목")
    
    def extract_area_code(self, text):
        # listView 표시 텍스트 형식: "area_name, ..." (첫 번째 쉼표 앞이 area_name)
        area_name = text.split(",")[0].strip()
        code = get_area_code(area_name)
        if code:
            return code
        # 역방향 조회 실패 시 경고 후 빈 문자열 반환 (잘못된 코드로 요청 방지)
        logging.warning(f"area_code 조회 실패 — area_name: '{area_name}'")
        return ""

    def open_in_browser(self, area_code, start, end):
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            QtWidgets.QMessageBox.warning(
                self,
                "웹 연동 모듈 없음",
                "자동 지점 선택에는 PyQtWebEngine이 필요합니다.\n"
                "다음 명령으로 설치한 뒤 다시 실행해 주세요.\n\n"
                "pip install PyQtWebEngine"
            )
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(
            f"공식 측정데이터 — {get_area_name(area_code)} ({area_code})"
        )
        dialog.resize(1280, 820)
        dialog.setMinimumSize(900, 600)

        close_shortcut = QtWidgets.QShortcut(
            QKeySequence(QtCore.Qt.Key_Escape), dialog
        )
        close_shortcut.setContext(QtCore.Qt.ApplicationShortcut)
        close_shortcut.activated.connect(dialog.reject)

        layout = QtWidgets.QVBoxLayout(dialog)
        info = QtWidgets.QLabel(
            f"관측지점: {get_area_name(area_code)} ({area_code})"
            f"  |  조회일: {start if start == end else f'{start} ~ {end}'}"
        )
        layout.addWidget(info)

        web_view = QWebEngineView(dialog)
        layout.addWidget(web_view, 1)

        area_json = json.dumps(area_code)
        start_json = json.dumps(start)
        end_json = json.dumps(end)
        integration_script = f"""
            (function() {{
                var attempts = 0;
                var timer = setInterval(function() {{
                    attempts += 1;
                    var area = document.getElementById('groupCd');
                    var from = document.getElementById('fromDt');
                    var to = document.getElementById('toDt');

                    if (area && from && to && typeof fnGetPastInfoVw === 'function') {{
                        area.value = {area_json};
                        from.value = {start_json};
                        to.value = {end_json};
                        area.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        fnGetPastInfoVw(1);
                        clearInterval(timer);
                    }} else if (attempts >= 40) {{
                        clearInterval(timer);
                    }}
                }}, 250);
            }})();
        """

        def apply_station_filter(ok):
            if ok:
                web_view.page().runJavaScript(integration_script)

        web_view.loadFinished.connect(apply_station_filter)
        web_view.setUrl(
            QUrl("https://aican.nifos.go.kr/data/obsrrData.do?tabNo=2")
        )
        dialog.exec_()

def main():
    # Qt WebEngine을 사용하는 상세 연동창보다 먼저 공유 OpenGL 컨텍스트 설정
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
