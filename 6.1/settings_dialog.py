from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton,
    QLabel, QSpinBox, QDialogButtonBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings
from utils import get_area_name

# 전체 지점 목록 (모든 관측소 코드)
ALL_AREAS = [
    "0011", "0012", "0013", "0021", "0022", "0023",
    "0031", "0032", "0033", "0041", "0042", "0043",
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
    "0291", "0292", "0293", "0301", "0302", "0303",
    "0311", "0312", "0313", "0321", "0322", "0323",
    "0331", "0332", "0333", "0341", "0342", "0343",
    "0351", "0352", "0353", "0361", "0362", "0363",
    "0371", "0372", "0373", "0381", "0382", "0383",
    "0391", "0392", "0393", "0401", "0402", "0403",
    "0411", "0412", "0413", "0421", "0422", "0423",
    "0431", "0432", "0433", "0441", "0442", "0443",
    "0451", "0452", "0453",
]

# 기본 활성 지점 (프로그램 초기값)
DEFAULT_AREAS = [
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
    "0451", "0452", "0453",
]


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.resize(420, 500)
        self.settings = QSettings("SITECH", "ParkorAnalyzer")
        self._build_ui()
        self._load_settings()

    # ── UI 구성 ────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_area_tab(), "지점 선택")
        self.tabs.addTab(self._build_analysis_tab(), "분석 설정")
        layout.addWidget(self.tabs)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText("확인")
        btn_box.button(QDialogButtonBox.Cancel).setText("취소")
        btn_box.accepted.connect(self._save_and_accept)
        btn_box.rejected.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 4, 8, 4)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_box)
        layout.addLayout(btn_layout)

    def _build_area_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 검색 + 전체선택/해제
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("지점 검색...")
        self.search_edit.textChanged.connect(self._filter_areas)
        search_row.addWidget(self.search_edit)

        btn_all = QPushButton("전체 선택")
        btn_all.clicked.connect(self._select_all)
        btn_none = QPushButton("전체 해제")
        btn_none.clicked.connect(self._select_none)
        search_row.addWidget(btn_all)
        search_row.addWidget(btn_none)
        layout.addLayout(search_row)

        # 지점 체크박스 리스트
        self.area_list = QListWidget()
        self.area_list.setAlternatingRowColors(True)
        self.area_list.itemChanged.connect(self._update_count)
        layout.addWidget(self.area_list)

        # 선택 카운트 라벨
        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        return widget

    def _build_analysis_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # 누락 데이터 허용 오차
        layout.addWidget(QLabel("누락 데이터 허용 오차"))
        desc1 = QLabel("현재 시각 기준 예상 건수보다 몇 건 이상 부족할 때 누락으로 판정할지")
        desc1.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(desc1)
        self.spin_missing = QSpinBox()
        self.spin_missing.setRange(0, 999)
        self.spin_missing.setValue(10)
        self.spin_missing.setFixedWidth(80)
        layout.addWidget(self.spin_missing)

        layout.addSpacing(16)

        # 음수 판정 구간
        layout.addWidget(QLabel("음수 판정 구간"))
        desc2 = QLabel("최근 몇 개 데이터가 전부 음수일 때 이상으로 판정할지")
        desc2.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(desc2)
        self.spin_negative = QSpinBox()
        self.spin_negative.setRange(1, 99)
        self.spin_negative.setValue(6)
        self.spin_negative.setFixedWidth(80)
        layout.addWidget(self.spin_negative)

        layout.addSpacing(16)

        # 제로값 최소 개수
        layout.addWidget(QLabel("제로값 최소 개수"))
        desc3 = QLabel("제로값이 몇 개 이상일 때 이상으로 판정할지")
        desc3.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(desc3)
        self.spin_zero = QSpinBox()
        self.spin_zero.setRange(1, 9999)
        self.spin_zero.setValue(1)
        self.spin_zero.setFixedWidth(80)
        layout.addWidget(self.spin_zero)

        layout.addStretch()
        return widget

    # ── 지점 목록 조작 ──────────────────────────────────────────────
    def _populate_areas(self, selected_set):
        self.area_list.blockSignals(True)
        self.area_list.clear()
        for code in ALL_AREAS:
            name = get_area_name(code)
            item = QListWidgetItem(f"{code}  {name}")
            item.setData(Qt.UserRole, code)
            item.setCheckState(Qt.Checked if code in selected_set else Qt.Unchecked)
            self.area_list.addItem(item)
        self.area_list.blockSignals(False)
        self._update_count()

    def _filter_areas(self, text):
        for i in range(self.area_list.count()):
            item = self.area_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _select_all(self):
        self.area_list.blockSignals(True)
        for i in range(self.area_list.count()):
            item = self.area_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.Checked)
        self.area_list.blockSignals(False)
        self._update_count()

    def _select_none(self):
        self.area_list.blockSignals(True)
        for i in range(self.area_list.count()):
            item = self.area_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.Unchecked)
        self.area_list.blockSignals(False)
        self._update_count()

    def _update_count(self):
        checked = sum(
            1 for i in range(self.area_list.count())
            if self.area_list.item(i).checkState() == Qt.Checked
        )
        self.count_label.setText(f"선택됨: {checked} / {len(ALL_AREAS)}개 지점")

    # ── QSettings 저장 / 불러오기 ────────────────────────────────────
    def _load_settings(self):
        saved = self.settings.value("selected_areas", DEFAULT_AREAS)
        # QSettings가 단일 문자열로 반환할 수 있어 방어 처리
        if isinstance(saved, str):
            saved = [saved] if saved else DEFAULT_AREAS
        self._populate_areas(set(saved))

        self.spin_missing.setValue(int(self.settings.value("missing_threshold", 10)))
        self.spin_negative.setValue(int(self.settings.value("negative_tail", 6)))
        self.spin_zero.setValue(int(self.settings.value("zero_threshold", 1)))

    def _save_and_accept(self):
        selected = [
            self.area_list.item(i).data(Qt.UserRole)
            for i in range(self.area_list.count())
            if self.area_list.item(i).checkState() == Qt.Checked
        ]
        self.settings.setValue("selected_areas", selected)
        self.settings.setValue("missing_threshold", self.spin_missing.value())
        self.settings.setValue("negative_tail", self.spin_negative.value())
        self.settings.setValue("zero_threshold", self.spin_zero.value())
        self.accept()

    # ── 외부에서 현재 설정값 읽기 ────────────────────────────────────
    @staticmethod
    def load_selected_areas():
        s = QSettings("SITECH", "ParkorAnalyzer")
        saved = s.value("selected_areas", DEFAULT_AREAS)
        if isinstance(saved, str):
            saved = [saved] if saved else DEFAULT_AREAS
        # ALL_AREAS 순서를 유지하면서 선택된 것만 반환
        saved_set = set(saved)
        return [code for code in ALL_AREAS if code in saved_set]

    @staticmethod
    def load_missing_threshold():
        return int(QSettings("SITECH", "ParkorAnalyzer").value("missing_threshold", 10))

    @staticmethod
    def load_negative_tail():
        return int(QSettings("SITECH", "ParkorAnalyzer").value("negative_tail", 6))

    @staticmethod
    def load_zero_threshold():
        return int(QSettings("SITECH", "ParkorAnalyzer").value("zero_threshold", 1))
