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
        self.__block = ''
        self.__var = ''
        self.__exePath = ''
        self.__scrPath = ''
        self.target = []

        # config
        self.__toolRootDir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.__configPath = os.path.abspath(os.path.join(self.__toolRootDir,'data/config.json'))
        if not self.__setupConfig():
            return

        # ui
        self.__buildUi()
        self.__mainUi.show()

        self.__mainUi.block_txt.setText(self.__block)
        self.__mainUi.var_le.setText(self.__var)
        self.__mainUi.exe_le.setText(self.__exePath)
        self.__mainUi.scr_le.setText(self.__scrPath)

        # commands
        self.__linkCommands()

        print('\n\n########\n# WRAP #\n########\n')
        sys.exit(self.__app.exec_())


    def __setupConfig(self):
        '''
        '''

        # load config
        try:
            with open(self.__configPath) as c:
                self.__configData = json.load(c)
        except Exception as err:
            print("Failed to load config: {}".format(self.__configPath))
            print(str(err))
            return False
        
        # apply test setting (TEMPORARY!)
        self.__block = self.__configData.get("block", None)
        self.__var = self.__configData.get("var", None)
        self.__exePath = self.__configData.get("exePath", None)
        self.__scrPath = self.__configData.get("scrPath", None)

        return True


    def __buildUi(self):
        '''
        '''

        # define ui file paths
        self.__app = QApplication(sys.argv)
        mainUiPath = os.path.abspath(os.path.join(self.__toolRootDir,'interface/main.ui')).replace('\\', '/')
        previewUiPath = os.path.abspath(os.path.join(self.__toolRootDir,'interface/preview.ui')).replace('\\', '/')

        # open ui files
        loader = QUiLoader()
        mainUiFile = QFile(mainUiPath)
        mainUiFile.open(QFile.ReadOnly)
        previewUiFile = QFile(previewUiPath)
        previewUiFile.open(QFile.ReadOnly)

        # create ui objects
        self.__mainUi = loader.load(mainUiFile)
        self.__previewUi = loader.load(previewUiFile)


    def __linkCommands(self):
        '''
        '''

        # main ui
        self.__mainUi.test_pbt.clicked.connect(self.__setTarget)
        self.__mainUi.exe_tbt.clicked.connect(partial(self.__setPath, 'exe'))
        self.__mainUi.scr_tbt.clicked.connect(partial(self.__setPath, 'scr'))
        self.__mainUi.finalize_pbt.clicked.connect(self.__finalize)

        # preview ui
        self.__previewUi.run_pbt.clicked.connect(partial(self.__runCmd, True))
        self.__previewUi.ccl_pbt.clicked.connect(partial(self.__runCmd, False))


    def __setTarget(self):
        '''
        '''

        self.__var = self.__mainUi.var_le.text()
        self.__block = self.__mainUi.block_txt.toPlainText()

        # run block
        try:
            exec(self.__block)
        except Exception as err:
            print('Failed to run process')
            print(str(err))
            return

        # set value to self.target
        try:
            exec('self.target = {}'.format(self.__var))
        except Exception as err:
            print('Failed to get targets')
            print(str(err))
            return

        print('\nTarget:')
        for tgt in self.target:
            print(tgt)


    def __setPath(self, mode = None):
        '''
        '''

        if mode == 'exe':
            fileFlt = 'Executable (*.exe)'
            lineEdit = self.__mainUi.exe_le
        else:
            fileFlt = 'Python Script (*.py)'
            lineEdit = self.__mainUi.scr_le
            
        path, flt = QFileDialog.getOpenFileName(caption='File Selection',
                                                dir='.',
                                                filter=fileFlt)

        if not path:
            return

        lineEdit.setText(path)


    def __finalize(self):
        '''
        '''

        # confirm target items
        self.__setTarget()

        if self.target == []:
            print("No target to process")
            return

        # set paths
        self.__exePath = self.__mainUi.exe_le.text().replace("\\", "/")
        self.__scrPath = self.__mainUi.scr_le.text().replace("\\", "/")

        for path in [self.__exePath, self.__scrPath]:
            if not os.path.exists(path):
                print('Not found: {}'.format(path))
                return

        # construct codes
        self.__cmdTmp = '''target = {TARGET}\
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
        self.__cmd = self.__cmdTmp.format(
                                    TARGET=self.target,
                                    EXE=self.__exePath,
                                    WRAPPER=self.__scrPath)
                                    #ARG='ahoy')

        targetStr = '\n'.join(self.target)

        self.__previewUi.show()
        self.__previewUi.tgt_txt.setText(targetStr)
        self.__previewUi.cmd_txt.setText(self.__cmd)


    def __runCmd(self, run=False):
        '''
        '''

        if not run:
            self.__previewUi.close()
            print('\nCanceled')
            return

        self.__cmd = self.__previewUi.cmd_txt.toPlainText()

        try:
            exec(self.__cmd)
        except Exception as err:
            print('Failed to run process')
            print(str(err))
            return


if __name__ == "__main__":
    Wrap()










# maintain selection
# kill all if parent ui dies
