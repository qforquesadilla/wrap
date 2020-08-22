import os
import sys
import subprocess
from functools import partial

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide2.QtCore import QFile

"""
Wrap
"""


class run():

    def __init__(self):

        self.var = ""
        self.items = []
        self.exe_path = ""
        self.scr_path = ""
        self.block = ""

        self.ui()
        self.ui.show()

        self.linkCommands()
        print("\n\n########\n# WRAP #\n########\n")

        sys.exit(self.app.exec_())
        


    def ui(self):
        self.app = QApplication(sys.argv)
        ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'interface/widget.ui')).replace('\\', '/')
        preview_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'interface/preview.ui')).replace('\\', '/')

        loader = QUiLoader()

        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)

        preview_file = QFile(preview_path)
        preview_file.open(QFile.ReadOnly)

        self.ui = loader.load(ui_file)
        self.preview = loader.load(preview_file)


    def linkCommands(self):

        # main ui
        self.ui.items_pbt.clicked.connect(self.previewItems)
        self.ui.exe_tbt.clicked.connect(partial(self.setPath, "exe"))
        self.ui.scr_tbt.clicked.connect(partial(self.setPath, "scr"))
        self.ui.finalize_pbt.clicked.connect(self.finalize)

        # preview ui
        self.preview.run_pbt.clicked.connect(partial(self.runProcess, True))
        self.preview.ccl_pbt.clicked.connect(partial(self.runProcess, False))


    def previewItems(self):
        self.var = self.ui.var_le.text()
        self.block = self.ui.items_txt.toPlainText()

        try:
            exec(self.block)
        except Exception as err:
            print("Failed to run process")
            print(err)
            return

        try:
            exec("self.items = {}".format(self.var))
        except Exception as err:
            print("Failed to pass value to variable")
            print(err)
            return

        print("\nItems: %s" % self.items)


    def setPath(self, mode = None):

        if mode == "exe":
            file_flt = "Executable (*.exe)"
            lineedit = self.ui.exe_le
        else:
            file_flt = "Python Script (*.py)"
            lineedit = self.ui.scr_le
            
        path, flt = QFileDialog.getOpenFileName(caption="File Selection",
                                                dir=".",
                                                filter=file_flt)

        if not path:
            return

        lineedit.setText(path)


    def finalize(self):

        # prepare
        self.previewItems()

        if self.items == []:
            print("No item to process")
            return

        self.exe_path = self.ui.exe_le.text()
        self.scr_path = self.ui.scr_le.text()

        for path in [self.exe_path, self.scr_path]:
            if not os.path.exists(path):
                print("Not found: {}".format(path))
                return

        # construct codes
        self.process_tmp = """
for counter, i in enumerate(self.items):

    print('\\n')
    print(counter)

    val = self.items[counter]
    print(val)

    cmd = '"{EXE}" "{WRAPPER}"'
    cmd += ' %s' % val
    cmd += ' stdin = subprocess.PIPE,'
    cmd += ' stdout = subprocess.PIPE,'
    cmd += ' stderr = subprocess.PIPE'
    print(cmd)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    [a, b] = process.communicate()

    for msg in [a, b]:
        if msg != "":
            print(msg)
"""
        self.process = self.process_tmp.format(
                                    EXE=self.exe_path,
                                    WRAPPER=self.scr_path)
                                    #ARG="ahoy")

        items_str = "\n".join(self.items)

        self.preview.show()
        self.preview.items_txt.setText(items_str)
        self.preview.process_txt.setText(self.process)


    def runProcess(self, run=False):

        if not run:
            self.preview.close()
            print("\nCanceled")
            return

        self.process = self.preview.process_txt.toPlainText()

        try:
            exec(self.process)
        except Exception as err:
            print("Failed to run process")
            print(err)
            return



if __name__ == "__main__":
    run()










# maintain selection
# kill all if parent ui dies