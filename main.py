#!/usr/bin/env python3

# from CODE.detectYesNo import check_chess
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QSizePolicy

import cv2
import numpy as np
import sys
import time
import os
import math

import checkAlign
from connectPLC import PLC
from detectYesNo import check_chess
from detectYesNo import Detect
from checkOnJig import CheckOn


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class Thread(QThread):
    progress = pyqtSignal()

    def run(self):
        while True:
            self.progress.emit()
            time.sleep(0.1)

class Query(QThread):
    progress = pyqtSignal()

    def run(self):
        while True:
            self.progress.emit()
            time.sleep(0.5)

class Camera(QThread):
    setup = pyqtSignal()

    def run(self):
        self.setup.emit()

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        # QT Config
        self.title = "PLC-UET"
        self.icon = QIcon(resource_path('data/icon/uet.png'))

        # Declare Main Variable
        self.total = 0
        self.number_tested = 0
        self.number_success = 0
        self.number_error1 = 0
        self.number_error2 = 0
        self.number_error3 = 0
        self.count = 0

        self.cap_detect = any
        self.cap_check = any
        self.get_cap_detect = False
        self.get_cap_check = False

        self.Controller = PLC()
        self.command = ""

        # Run QT
        self.initUI()
    
    def initUI(self):

        # Config Main Window
        self.setWindowTitle(self.title)
        self.setWindowIcon(self.icon)
        self.setWindowState(Qt.WindowFullScreen)
        self.setStyleSheet("background-color: rgb(171, 171, 171);")

        # Config Auto Fit Screen Scale Variables
        self.sg = QDesktopWidget().screenGeometry()
        self.width_rate = self.sg.width() / 1920
        self.height_rate = self.sg.height() / 1080
        self.font_rate = math.sqrt(self.sg.width()*self.sg.width() + self.sg.height()*self.sg.height()) / math.sqrt(1920*1920 + 1080*1080)
        
        # Show MCNEX LOGO
        self.mcnex_logo = QLabel(self)
        self.mcnex_pixmap = QPixmap(resource_path('data/icon/mcnex.png')).scaled(181 * self.width_rate, 141 * self.width_rate, Qt.KeepAspectRatio)
        self.mcnex_logo.setPixmap(self.mcnex_pixmap)
        self.mcnex_logo.setGeometry(50 * self.width_rate, 1 * self.height_rate, 181 * self.width_rate, 141 * self.height_rate)
        
         # Show UET LOGO
        self.uet_logo = QLabel(self)
        self.uet_pixmap = QPixmap(resource_path('data/icon/uet.png')).scaled(111 * self.width_rate, 111 * self.width_rate, Qt.KeepAspectRatio)
        self.uet_logo.setPixmap(self.uet_pixmap)
        self.uet_logo.setGeometry(250 * self.width_rate, 10 * self.height_rate, 111 * self.width_rate, 111 * self.height_rate)

        # Show Title
        self.title_label = QLabel("HỆ THỐNG KIỂM TRA LINH KIỆN", self)
        self.title_label.setGeometry(400 * self.width_rate, 17 * self.height_rate, 1800 * self.width_rate, 95 * self.height_rate)
        font_title = QFont('', int(25 * self.font_rate), QFont.Bold)
        self.title_label.setFont(font_title)
        self.title_label.setStyleSheet("color: rgb(255, 255, 255);")

         # Show Current Time
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setGeometry(1470 * self.width_rate, 20 * self.height_rate, 430 * self.width_rate, 95 * self.height_rate)
        font_timer = QFont('', int(25 * self.font_rate), QFont.Bold)
        self.time_label.setFont(font_timer)
        timer = QTimer(self)
        timer.timeout.connect(self.updateTimer)
        timer.start(1000)
        self.time_label.setStyleSheet("color: rgb(255, 255, 255);")

        # # Show Detect Camera
        # self.cam1_name = QLabel("DETECT CAMERA", self)
        # self.cam1_name.setGeometry(55 * self.width_rate, 127 * self.height_rate, 582 * self.width_rate, 60 * self.height_rate)
        # self.cam1_name.setAlignment(Qt.AlignCenter)
        # self.cam1_name.setStyleSheet("background-color: rgb(50, 130, 184);"
        #                             "color: rgb(255, 255, 255);"
        #                             "font: bold 14pt;")
        # self.cam1 = QLabel(self)
        # self.cam1.setGeometry(55 * self.width_rate, 185 * self.height_rate, 582 * self.width_rate, 410 * self.height_rate)
        # self.cam1.setStyleSheet("border-color: rgb(50, 130, 184);"
        #                         "border-width: 5px;"
        #                         "border-style: inset;")
        
        # Show Check Camera
        self.cam2_name = QLabel("CHECK CAMERA", self)
        self.cam2_name.setGeometry(960 * self.width_rate, 127 * self.height_rate, 456 * self.width_rate, 60 * self.height_rate)
        self.cam2_name.setAlignment(Qt.AlignCenter)
        self.cam2_name.setStyleSheet("background-color: rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
        self.cam2 = QLabel(self)
        self.cam2.setGeometry(960 * self.width_rate, 185 * self.height_rate, 456 * self.width_rate, 410 * self.height_rate)
        self.cam2.setStyleSheet("border-color: rgb(50, 130, 184);"
                                "border-width: 5px;"
                                "border-style: inset;")

        # Set Font
        self.font = QFont('', int(14 * self.font_rate), QFont.Bold)

        
        # Trays Information
        self.tray = []
        for i in range(4):
            tray_name = QLabel("TRAY {}".format(i+1), self)
            tray_name.setGeometry((55 + 456*i - 5) * self.width_rate, 606 * self.height_rate, 432 * self.width_rate, 55 * self.height_rate)
            tray_name.setAlignment(Qt.AlignCenter)
            tray_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
            table_margin = QLabel(self)
            table_margin.setGeometry((55 + 456*i - 5) * self.width_rate, 661 * self.height_rate, 432 * self.width_rate, 405 * self.height_rate)
            table_margin.setStyleSheet("border-color: rgb(50, 130, 184);"
                                        "border-width: 5px;"
                                        "border-style: inset;")
            table = QTableWidget(8, 6, self)
            table.setGeometry((55 + 456*i) * self.width_rate, 666 * self.height_rate, int(422 * self.width_rate) + 1, int(396 * self.height_rate) + 0.5)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()
            for j in range(6):
                table.setColumnWidth(j, 70 * self.width_rate)
            for j in range(8):
                table.setRowHeight(j, 49 * self.height_rate)
            table.setFont(self.font)
            table.setStyleSheet("color: rgb(255, 255, 255);")
            self.tray.append(table)
        
        self.tray2 = []
        for i in range(2):
            tray_name = QLabel("NG {}".format(i+1), self)
            tray_name.setGeometry((55 + 456*i - 5) * self.width_rate, 127 * self.height_rate, 432 * self.width_rate, 55 * self.height_rate)
            tray_name.setAlignment(Qt.AlignCenter)
            tray_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")
            table_margin = QLabel(self)
            table_margin.setGeometry((55 + 456*i - 5) * self.width_rate, 181 * self.height_rate, 432 * self.width_rate, 405 * self.height_rate)
            table_margin.setStyleSheet("border-color: rgb(50, 130, 184);"
                                        "border-width: 5px;"
                                        "border-style: inset;")
            table = QTableWidget(8, 6, self)
            table.setGeometry((55 + 456*i) * self.width_rate, 186 * self.height_rate, int(422 * self.width_rate) + 1, int(396 * self.height_rate) + 0.5)
            table.horizontalHeader().hide()
            table.verticalHeader().hide()
            for j in range(6):
                table.setColumnWidth(j, 70 * self.width_rate)
            for j in range(8):
                table.setRowHeight(j, 49 * self.height_rate)
            table.setFont(self.font)
            table.setStyleSheet("color: rgb(255, 255, 255);")
            self.tray2.append(table)

        # Table Info Area        
        self.s_name = QLabel("INFORMATION", self)
        self.s_name.setGeometry(1450 * self.width_rate, 127 * self.height_rate, 399 * self.width_rate, 60 * self.height_rate)
        self.s_name.setAlignment(Qt.AlignCenter)
        self.s_name.setStyleSheet("background-color:rgb(50, 130, 184);"
                                    "color: rgb(255, 255, 255);"
                                    "font: bold 14pt;")

        self.statistic_table = QTableWidget(5, 2, self)
        self.statistic_table.setGeometry(1450 * self.width_rate, 185 * self.height_rate, int(399 * self.width_rate) + 1, int(410 * self.height_rate) + 1)
        self.statistic_table.horizontalHeader().hide()
        self.statistic_table.verticalHeader().hide()
        self.statistic_table.setFont(self.font)
        self.statistic_table.setStyleSheet("color: rgb(255, 255, 255);"
                                            "text-align: center;"
                                            "border-width: 5px;"
                                            "border-style: inset;"
                                            "border-color: rgb(50, 130, 184);")
        for j in range(2):
            self.statistic_table.setColumnWidth(j, 195 * self.width_rate)
        for j in range(5):
            self.statistic_table.setRowHeight(j, 80 * self.height_rate)
        tested_item = QTableWidgetItem("TESTED")
        tested_item.setTextAlignment(Qt.AlignCenter)
        tested_item.setFont(self.font)
        self.statistic_table.setItem(0, 0, tested_item)

        success_item = QTableWidgetItem("SUCCESS")
        success_item.setTextAlignment(Qt.AlignCenter)
        success_item.setFont(self.font)
        self.statistic_table.setItem(1, 0, success_item)

        error1_item = QTableWidgetItem("NEED RETEST")
        error1_item.setTextAlignment(Qt.AlignCenter)
        error1_item.setFont(self.font)
        self.statistic_table.setItem(2, 0, error1_item)

        error2_item = QTableWidgetItem("CONNECTION ERROR")
        error2_item.setTextAlignment(Qt.AlignCenter)
        error2_item.setFont(self.font)
        self.statistic_table.setItem(3, 0, error2_item)

        error3_item = QTableWidgetItem("FAILURE")
        error3_item.setTextAlignment(Qt.AlignCenter)
        error3_item.setFont(self.font)
        self.statistic_table.setItem(4, 0, error3_item)

        # Exit Button
        self.exit_button = QPushButton(self)
        self.exit_pixmap = QPixmap(resource_path('data/icon/close.png')).scaled(100 * self.width_rate, 100 * self.width_rate, Qt.KeepAspectRatio)
        self.exit_icon = QIcon(self.exit_pixmap)
        self.exit_button.setIcon(self.exit_icon)
        self.exit_button.setIconSize(QSize(50, 50))
        self.exit_button.setGeometry(1878 * self.width_rate, -8 * self.height_rate, 50 * self.width_rate, 50 * self.height_rate)
        self.exit_button.setHidden(0)
        self.exit_button.setStyleSheet("border: none")
        self.exit_button.clicked.connect(self.close)

        # # Create Thread
        # self.camera_thread = Camera()
        # self.camera_thread.setup.connect(self.setup_camera)
        # self.main_thread = Thread()
        # self.main_thread.progress.connect(self.main_process)
        # self.plc_thread = Query()
        # self.main_thread.progress.connect(self.get_command)

        # # Run Thread
        # self.camera_thread.start()
        # self.main_thread.start()
        # self.plc_thread.start()

    # Hàm stream CAMERA DETECT lên giao diện
    def update_detect_image(self, img):
        rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        self.cam1.setPixmap(QPixmap.fromImage(convertToQtFormat))
    
    # Hàm stream CAMERA CHECK lên giao diện
    def update_check_image(self, img):
        rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        self.cam2.setPixmap(QPixmap.fromImage(convertToQtFormat))
    
    # Hàm cập nhật bảng số liệu
    def update_statistic(self, data):
        self.number_tested += 1

        # Reset giá trị đếm khi kiểm tra hết linh kiện
        if self.count == 42:
            self.count = 0
        
        # Bỏ qua khi không có linh kiện trong mảng dữ liệu
        while self.Controller.data[self.count] != 1:
            self.count += 1
        
        # Cập nhật số liệu Kiểm tra
        tested = QTableWidgetItem("{}".format(self.number_tested) + " / {}".format(self.total))
        tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,1,tested)
        ratio_tested = QTableWidgetItem("{} %".format(int(self.number_tested / self.total * 100)))
        ratio_tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,2,ratio_tested)
        
        # Lấy số liệu linh kiện
        tray_idx = self.count // 21
        row = 6 - self.count % 21 % 7
        col = self.count % 21 // 7

        # Thông báo đẩy
        if data == "1":
            self.number_success += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(67, 138, 94))
            self.textBox.appendPlainText("Linh Kiện Tray {}".format(tray_idx+1) + " Hàng {}".format(row+1) + " Cột {}".format(col+1) + " Hoạt Động Tốt!\n")
        elif data == "0":
            self.number_error3 += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(232, 80, 91))
            self.textBox.appendPlainText("Linh Kiện Tray {}".format(tray_idx+1) + " Hàng {}".format(row+1) + " Cột {}".format(col+1) + " Bị Hỏng!\n")
        elif data == "-1":
            self.number_error1 += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(255, 255, 51))
            self.textBox.appendPlainText("Linh Kiện Tray {}".format(tray_idx+1) + " Hàng {}".format(row+1) + " Cột {}".format(col+1) + " Gặp Lỗi Vị Trí Trên Jig. Đề Nghị Kiểm Tra!\n")
        elif data == "404":
            self.number_error2 += 1
            self.tray[tray_idx].item(row,col).setBackground(QColor(255, 128, 0))
            self.textBox.appendPlainText("Linh Kiện Tray {}".format(tray_idx+1) + " Hàng {}".format(row+1) + " Cột {}".format(col+1) + " Gặp Lỗi Kết Nối Với Bộ Test. Đề Nghị Kiểm Tra!\n")

        # Cập nhật số liệu
        success = QTableWidgetItem("{}".format(self.number_success) + " / {}".format(self.number_tested))
        success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,1,success)
        ratio_success = QTableWidgetItem("{} %".format(int(self.number_success / self.number_tested * 100)))
        ratio_success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,2,ratio_success)

        error1 = QTableWidgetItem("{}".format(self.number_error1) + " / {}".format(self.number_tested))
        error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,1,error1)
        ratio_error1 = QTableWidgetItem("{} %".format(int(self.number_error1 / self.number_tested * 100)))
        ratio_error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,2,ratio_error1)

        error2 = QTableWidgetItem("{}".format(self.number_error2) + " / {}".format(self.number_tested))
        error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,1,error2)
        ratio_error2 = QTableWidgetItem("{} %".format(int(self.number_error2 / self.number_tested * 100)))
        ratio_error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,2,ratio_error2)

        error3 = QTableWidgetItem("{}".format(self.number_error3) + " / {}".format(self.number_tested))
        error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,1,error3)
        ratio_error3 = QTableWidgetItem("{} %".format(int(self.number_error3 / self.number_tested * 100)))
        ratio_error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,2,ratio_error3)
        
        # Linh kiện kiểm tra xong sẽ xóa khỏi mảng dữ liệu
        self.Controller.data[self.count] = 0
        self.count += 1
    
    # Hàm Khởi tạo giá trị cho Bảng số liệu
    def init_statistic(self):
        tested = QTableWidgetItem("{}".format(0) + " / {}".format(self.total))
        tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,1,tested)
        ratio_tested = QTableWidgetItem("{} %".format(0))
        ratio_tested.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(0,2,ratio_tested)

        success = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,1,success)
        ratio_success = QTableWidgetItem("{} %".format(0))
        ratio_success.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(1,2,ratio_success)

        error1 = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,1,error1)
        ratio_error1 = QTableWidgetItem("{} %".format(0))
        ratio_error1.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(2,2,ratio_error1)

        error2 = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,1,error2)
        ratio_error2 = QTableWidgetItem("{} %".format(0))
        ratio_error2.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(3,2,ratio_error2)

        error3 = QTableWidgetItem("{}".format(0) + " / {}".format(0))
        error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,1,error3)
        ratio_error3 = QTableWidgetItem("{} %".format(0))
        ratio_error3.setTextAlignment(Qt.AlignCenter)
        self.statistic_table.setItem(4,2,ratio_error3)
    
    def update_data(self, data):
        
        # Update Data to Table
        c = 0
        for k in range(2):
            for j in range(3):
                for i in range(6,-1,-1):
                    self.tray[k].setItem(i,j,QTableWidgetItem())
                    if(int(data[c])):
                        self.tray[k].item(i,j).setBackground(QColor(102, 102, 255))
                        self.total += 1
                    c += 1

        # Send Data to PLC -> Send Command to PLC -> Grip
        self.Controller.data = data
        self.Controller.sendData()
        self.Controller.command = "Grip"
        self.Controller.sendCommand()

    # Hàm cập nhật giờ   
    def updateTimer(self):
        cr_time = QTime.currentTime()
        time = cr_time.toString('hh:mm AP')
        self.time_label.setText(time)

    def main_process(self):
        if self.command == "Idle":
            # Kiểm tra xem đã nhận Camera Check chưa
            if self.get_cap_detect == True:

                # Reset Main Variables
                self.total = 0
                self.number_tested = 0
                self.number_success = 0
                self.number_error1 = 0
                self.number_error2 = 0
                self.number_error3 = 0
                self.count = 0

                # Hiện Video khi chờ
                self.cap_detect.set(3, 1920)
                self.cap_detect.set(4, 1080)
                ret, image = self.cap_detect.read()
                image = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao diện
                self.update_detect_image(image)
        elif self.command == "Detect":
            # Kiểm tra xem đã nhận Camera Check chưa
            if self.get_cap_detect == True:
                
                # Lấy dữ liệu từ camera
                self.cap_detect.set(3, 1920)
                self.cap_detect.set(4, 1080)
                ret, image = self.cap_detect.read()
                resize_img = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao diện
                detect = Detect()

                # Xử lý Ảnh
                detect.image = check_chess(image)
                detect.thresh()

                # Detect YES/NO
                result = detect.check(detect.crop_tray_1)
                result = np.append(result, detect.check(detect.crop_tray_2))
                result = np.append(result, detect.check(detect.crop_tray_3))
                result = np.append(result, detect.check(detect.crop_tray_4))
                self.update_detect_image(resize_img) # Đưa ảnh lên giao diện

                # Gửi kết quả Detect YES/NO cho PLC và Table  
                self.update_data(result)
                self.init_statistic()
                self.command = "Wait"
            
        elif self.command == "Check":
            # Kiểm tra xem đã nhận Camera Check chưa
            if self.get_cap_check == True:
                self.cap_check.set(3, 1920)
                self.cap_check.set(4, 1080)
                ret, image = self.cap_check.read() # Lấy dữ liệu từ camera
                resize_img = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao diện
                
                # Kiểm tra Jig
                CheckOn = CheckOn()
                CheckOn.image = image[150:280, 245:445]

                # Nếu không có linh kiện trên Jig
                if CheckOn.check(CheckOn.calc_mean()) == 0:
                    self.command = "SOS"
                
                # Nếu có linh kiện trên Jig
                else:
                    # Kiểm tra lệch
                    resize_img1 = cv2.resize(image, (int(717 * self.width_rate), int(450 * self.height_rate)), interpolation = cv2.INTER_AREA) # Resize cho Giao diện
                    # resize_img1 = cv2.resize(image, (1920, 1080))
                    # mean = checkAlign.crop_image(image)
                    # mean = checkAlign.calc_mean_all()
                    check = checkAlign.check(image)

                    self.update_check_image(resize_img1) # Đưa video lên giao diện
                    
                    # Kết quả trả về linh kiện không lệch
                    if check:
                        # Đổi State -> Gửi State mới cho PLC
                        self.Controller.command = "Grip-1"
                        self.Controller.sendCommand()
                    
                    # Kết quả trả về linh kiện lệch
                    else:
                        # Đổi State -> Gửi State mới cho PLC
                        self.Controller.command = "Grip-0"
                        self.Controller.sendCommand()
                    
                    # Đổi State: Chờ lệnh
                    self.command = "Wait"

        # Nhận kết quả từ PLC -> Cập nhật bảng số liệu -> Gửi lệnh cho PLC tiếp tục gắp linh kiện mới -> Chờ tay gắp
        elif self.command == "1":
            self.update_statistic(self.command)
            self.Controller.command = "Grip"
            self.Controller.sendCommand()
            self.command = "Wait"
        elif self.command == "0":
            self.update_statistic(self.command)
            self.Controller.command = "Grip"
            self.Controller.sendCommand()
            self.command = "Wait"
        elif self.command == "-1":
            self.update_statistic(self.command)
            self.Controller.command = "Grip"
            self.Controller.sendCommand()
            self.command = "Wait"
        elif self.command == "404":
            self.update_statistic(self.command)
            self.Controller.command = "Grip"
            self.Controller.sendCommand()
            self.command = "Wait"
        
        # Kết thúc -> Xuất ra thông báo
        elif self.command == "Report":
            if self.report_one_time:
                self.report_one_time = False
                QMessageBox.about(self, "Kiểm Tra Hoàn Tất", "Đã Kiểm Tra " + str(self.total) + " linh kiện!\n" + "Còn " + str(self.number_error1) + " linh kiện cần kiểm tra lại!")
                self.command = ""

    # Init Camera
    def setup_camera(self):
        self.cap_detect = cv2.VideoCapture(0) # Khai báo USB Camera Detect Config
        self.get_cap_detect = True
        self.cap_check = cv2.VideoCapture(0) # Khai báo USB Camera Check Config
        self.get_cap_check = True

    
    # Loop Get Command from PLC
    def get_command(self):
        self.command = self.Controller.queryCommand()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())
