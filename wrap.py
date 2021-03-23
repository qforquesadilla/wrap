import os
import sys
import json
import subprocess
from functools import partial

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide2.QtCore import QFile

'''
Wrap
'''


class Wrap(object):

    def __init__(self):
        '''
        '''

        # variables
        self.block = ''
        self.var = ''
        self.exePath = ''
        self.scrPath = ''
        self.target = []

        # config
        self.toolRootDir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.configPath = os.path.abspath(os.path.join(self.toolRootDir,'data/config.json'))
        if not self.setupConfig():
            return

        # ui
        self.ui()
        self.mainUi.show()

        self.mainUi.block_txt.setText(self.block)
        self.mainUi.var_le.setText(self.var)
        self.mainUi.exe_le.setText(self.exePath)
        self.mainUi.scr_le.setText(self.scrPath)

        # commands
        self.linkCommands()

        print('\n\n########\n# WRAP #\n########\n')
        sys.exit(self.app.exec_())


    def setupConfig(self):
        '''
        '''

        # load config
        try:
            with open(self.configPath) as c:
                self.configData = json.load(c)
        except Exception as err:
            print("Failed to load config: {}".format(self.configPath))
            print(str(err))
            return False
        
        # apply test setting (TEMPORARY!)
        self.block = self.configData.get("block", None)
        self.var = self.configData.get("var", None)
        self.exePath = self.configData.get("exePath", None)
        self.scrPath = self.configData.get("scrPath", None)

        return True


    def ui(self):
        '''
        '''

        # define ui file paths
        self.app = QApplication(sys.argv)
        mainUiPath = os.path.abspath(os.path.join(self.toolRootDir,'interface/main.ui')).replace('\\', '/')
        previewUiPath = os.path.abspath(os.path.join(self.toolRootDir,'interface/preview.ui')).replace('\\', '/')

        # open ui files
        loader = QUiLoader()
        mainUiFile = QFile(mainUiPath)
        mainUiFile.open(QFile.ReadOnly)
        previewUiFile = QFile(previewUiPath)
        previewUiFile.open(QFile.ReadOnly)

        # create ui objects
        self.mainUi = loader.load(mainUiFile)
        self.previewUi = loader.load(previewUiFile)


    def linkCommands(self):
        '''
        '''

        # main ui
        self.mainUi.test_pbt.clicked.connect(self.setTarget)
        self.mainUi.exe_tbt.clicked.connect(partial(self.setPath, 'exe'))
        self.mainUi.scr_tbt.clicked.connect(partial(self.setPath, 'scr'))
        self.mainUi.finalize_pbt.clicked.connect(self.finalize)

        # preview ui
        self.previewUi.run_pbt.clicked.connect(partial(self.runCmd, True))
        self.previewUi.ccl_pbt.clicked.connect(partial(self.runCmd, False))


    def setTarget(self):
        '''
        '''

        self.var = self.mainUi.var_le.text()
        self.block = self.mainUi.block_txt.toPlainText()

        # run block
        try:
            exec(self.block)
        except Exception as err:
            print('Failed to run process')
            print(str(err))
            return

        # set value to self.target
        try:
            exec('self.target = {}'.format(self.var))
        except Exception as err:
            print('Failed to get targets')
            print(str(err))
            return

        print('\nTarget:')
        for tgt in self.target:
            print(tgt)


    def setPath(self, mode = None):
        '''
        '''

        if mode == 'exe':
            fileFlt = 'Executable (*.exe)'
            lineEdit = self.mainUi.exe_le
        else:
            fileFlt = 'Python Script (*.py)'
            lineEdit = self.mainUi.scr_le
            
        path, flt = QFileDialog.getOpenFileName(caption='File Selection',
                                                dir='.',
                                                filter=fileFlt)

        if not path:
            return

        lineEdit.setText(path)


    def finalize(self):
        '''
        '''

        # confirm target items
        self.setTarget()

        if self.target == []:
            print("No target to process")
            return

        # set paths
        self.exePath = self.mainUi.exe_le.text().replace("\\", "/")
        self.scrPath = self.mainUi.scr_le.text().replace("\\", "/")

        for path in [self.exePath, self.scrPath]:
            if not os.path.exists(path):
                print('Not found: {}'.format(path))
                return

        # construct codes
        self.cmd_tmp = '''target = {TARGET}\
        \n\
        \ntotal = len(target)\
        \nfor counter, tgt in enumerate(target, 1):\
        \n    \
        \n    print("\\n\\n# %s out of %s #" % (counter, total))\
        \n    print("Target: %s" % tgt)\
        \n    \
        \n    # create subprocess command\
        \n    cmd_lst = []\
        \n    cmd_lst.append("{EXE}")\
        \n    cmd_lst.append("{WRAPPER}")\
        \n    cmd_lst.append(tgt)\
        \n    cmd_lst.append("stdin = subprocess.PIPE")\
        \n    cmd_lst.append("stdout = subprocess.PIPE")\
        \n    cmd_lst.append("stderr = subprocess.PIPE")\
        \n    \
        \n    cmd = " ".join(cmd_lst)\
        \n    print("Cmd: %s\\n" % cmd)\
        \n    print("="*150)\
        \n    \
        \n    # run
        \n    process = subprocess.Popen(cmd,\
        \n                                shell=True,\
        \n                                stdout=subprocess.PIPE,\
        \n                                stderr=subprocess.PIPE)\
        \n    \
        \n    [a, b] = process.communicate()\
        \n    for msg in [a, b]:\
        \n        if msg != "":\
        \n            print(msg)\
        \n    \
        \n    print("="*150)'''
        self.cmd = self.cmd_tmp.format(
                                    TARGET=self.target,
                                    EXE=self.exePath,
                                    WRAPPER=self.scrPath)
                                    #ARG="ahoy")

        targetStr = '\n'.join(self.target)

        self.previewUi.show()
        self.previewUi.tgt_txt.setText(targetStr)
        self.previewUi.cmd_txt.setText(self.cmd)


    def runCmd(self, run=False):
        '''
        '''

        if not run:
            self.previewUi.close()
            print('\nCanceled')
            return

        self.cmd = self.previewUi.cmd_txt.toPlainText()

        try:
            exec(self.cmd)
        except Exception as err:
            print('Failed to run process')
            print(str(err))
            return


if __name__ == "__main__":
    Wrap()










# maintain selection
# kill all if parent ui dies
