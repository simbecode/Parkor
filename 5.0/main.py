import os
import sys
import datetime as dt
from tqdm import tqdm
from data_fetcher import DataFetcher
from data_analyzer import DataAnalyzer
from utils import calculate_values_count, calculate_page_count, get_area_name
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QStringListModel, QUrl
from PyQt5.QtGui import QDesktopServices

class AnalyzerThread(QThread):
    analysis_done = pyqtSignal(object)  # 분석 완료 시그널, 분석기 객체 전달
    
    def __init__(self, list_views):
        super().__init__()
        self.list_views = list_views
        self.analyzer = None

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
    def run(self):
        total_area = [
            "0011", "0012", "0013", "0022", "0023",
            "0031", "0032", "0033", "0041", "0042", 
            "0051", "0052", "0053", "0061", "0062", "0063",
            "0071", "0072", "0073", "0081", "0082", "0083",
            "0091", "0092", "0093", "0101", "0102", "0103",
            "0111", "0112", "0113", "0121", "0122", "0123",
            "0131", "0132", "0133", "0141", "0142", "0143",
            "0151", "0152", "0153", "0161", "0162", "0163",
            "0171", "0172", "0173", "0181", "0182", "0183",
            "0191", "0192", "0193", "0201", "0202", "0203",
            "0211", "0212", "0213", "0221", "0222", "0223",
            "0231", "0232", "0233", "0241", "0242", "0243",
            "0251", "0252", "0253", "0261", "0262", "0263",
            "0271", "0272", "0273", "0281", "0282", "0283",
            "0291", "0301", "0302", "0303",
            "0311", "0312", "0313", "0321", "0322", 
            "0331", "0332", "0333", "0341", "0342", "0343",
            "0351", "0352", "0353", "0361", "0362", "0363",
            "0371", "0372", "0373", "0381", "0382", "0383",
            "0391", "0392", "0393", "0401", "0402", "0403",
            "0411", "0412", "0413", "0421", "0422", "0423",
            "0431", "0432", "0433", "0441", "0442", "0443",
            "0451", "0452", "0453"
        ]
        values_cnt = calculate_values_count()  
        page_count = calculate_page_count()
        start = dt.datetime.now().strftime('%Y-%m-%d')
        end = dt.datetime.now().strftime('%Y-%m-%d')

        self.analyzer = DataAnalyzer(self.list_views)
        self.analyzer.set_values_count(values_cnt)
        
        for area in total_area:
            area_name = get_area_name(area)
            data = DataFetcher.fetch_data_for_area(area, start, end, page_count)
            self.analyzer.analyze_data(data, area_name)

        
        self.analysis_done.emit(self.analyzer)

def display_results(analyzer, window):
    # 분석이 완료되었음을 상태 표시줄에 표시
    window.statusBar().showMessage('End')

def start_analysis(window):
    list_views = [window.listView_1, window.listView_2, window.listView_3, window.listView_4, window.listView_5]
    analyzer_thread = AnalyzerThread(list_views)
    analyzer_thread.analysis_done.connect(lambda analyzer: display_results(analyzer, window))
    analyzer_thread.start()
    
    return analyzer_thread

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # uic.loadUi("C:\\SI\\Program\\dust\\5.0\\main.ui", self)
        
        if getattr(sys, 'frozen', False):
            # PyInstaller로 패키징된 경우
            ui_path = os.path.join(sys._MEIPASS, 'main.ui')
        else:
            # 직접 실행하는 경우
            ui_path = os.path.join(os.path.dirname(__file__), 'main.ui')
        uic.loadUi(ui_path, self)
        self.statusBar().showMessage('Ready')
        
        # 모델 생성 및 QListView에 설정
        self.setup_list_view(self.listView_1)
        self.setup_list_view(self.listView_2)
        self.setup_list_view(self.listView_3)
        self.setup_list_view(self.listView_4)
        self.setup_list_view(self.listView_5)

        # 분석 시작
        self.analyzer_thread = start_analysis(self)
        self.statusBar().showMessage('Start')

    def setup_list_view(self, list_view):
        model = QStringListModel()
        list_view.setModel(model)
        list_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # 더블 클릭 편집 비활성화
        list_view.doubleClicked.connect(self.on_item_double_clicked)

    def on_item_double_clicked(self, index):
        text = index.data()
        if text:
            area_code = self.extract_area_code(text)
            start = dt.datetime.now().strftime('%Y-%m-%d')
            end = dt.datetime.now().strftime('%Y-%m-%d')
            self.open_in_browser(area_code, "1", start, end)
    
    def extract_area_code(self, text):
        # 텍스트에서 area 코드를 추출하는 로직을 여기에 추가
        # 예시: 텍스트가 "area_code: 0011, data: ..." 형태라면 아래와 같이 추출 가능
        parts = text.split(",")
        for part in parts:
            if "area_code" in part:
                return part.split(":")[1].strip()
        return text  # 기본적으로 텍스트 자체를 반환

    def open_in_browser(self, area_code, page, start, end):
        # area_code에 맞는 URL 생성
        url = QUrl(f"http://aican.nifos.go.kr/data/obsrrData.do#")
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
