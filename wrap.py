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
        TBA
        '''

        # variables
        self.__textBlock = ''
        self.__variable = ''
        self.__executablePath = ''
        self.__scriptPath = ''
        self.targets = []

        # config
        self.__toolRootDir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.__configPath = os.path.normpath(os.path.join(self.__toolRootDir, 'data/config.json'))
        self.__setupConfig()

        # ui & commands
        self.__buildUi()
        self.__mainUi.show()

        self.__mainUi.textBlockTE.setText(self.__textBlock)
        self.__mainUi.testLE.setText(self.__variable)
        self.__mainUi.executableLE.setText(self.__executablePath)
        self.__mainUi.scriptLE.setText(self.__scriptPath)

        self.__linkCommands()

        print('\n\n########\n# WRAP #\n########\n')
        sys.exit(self.__app.exec_())


    def __setupConfig(self):
        '''
        TBA
        '''

        # load json
        with open(self.__configPath) as c:
            configData = json.load(c)
        
        # apply test setting (TEMPORARY! DEMO!)
        self.__textBlock = configData.get('textBlock', None)
        self.__variable = configData.get('variable', None)
        self.__executablePath = configData.get('executablePath', None)
        self.__scriptPath = configData.get('scriptPath', None)


    def __buildUi(self):
        '''
        TBA
        '''

        # define ui file paths
        self.__app = QApplication(sys.argv)
        mainUiPath = os.path.normpath(os.path.join(self.__toolRootDir, 'interface/main.ui')).replace('\\', '/')
        previewUiPath = os.path.normpath(os.path.join(self.__toolRootDir, 'interface/preview.ui')).replace('\\', '/')

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
        TBA
        '''

        # main ui
        self.__mainUi.testPB.clicked.connect(self.__onTestPressed)
        self.__mainUi.executableTB.clicked.connect(partial(self.__onSetPath, 'exe'))
        self.__mainUi.scriptTB.clicked.connect(partial(self.__onSetPath, 'scr'))
        self.__mainUi.finalizePB.clicked.connect(self.__onFinalizePressed)
        self.__mainUi.demoPB.clicked.connect(self.__onDemoPressed)

        # preview ui
        self.__previewUi.runPB.clicked.connect(partial(self.__onRunPressed, True))
        self.__previewUi.cancelPB.clicked.connect(partial(self.__onRunPressed, False))


    def __onTestPressed(self):
        '''
        TBA
        '''

        self.__variable = self.__getLineEdit(self.__mainUi.testLE)
        self.__textBlock = self.__getTextEdit(self.__mainUi.textBlockTE)

        # run block
        try:
            exec(self.__textBlock)
        except Exception as err:
            print('Failed to run process')
            print(str(err))
            return

        # set value to self.targets
        try:
            exec('self.targets = {}'.format(self.__variable))
        except Exception as err:
            print('Failed to get targets')
            print(str(err))
            return

        print('\nTarget:')
        for tgt in self.targets:
            print(tgt)


    def __onSetPath(self, mode = None):
        '''
        TBA
        '''

        if mode == 'exe':
            fileFlt = 'Executable (*.exe)'
            lineEdit = self.__mainUi.executableLE
        else:
            fileFlt = 'Python Script (*.py)'
            lineEdit = self.__mainUi.scriptLE
            
        path, flt = QFileDialog.getOpenFileName(caption='File Selection',
                                                dir='.',
                                                filter=fileFlt)

        if not path:
            return

        lineEdit.setText(path)



    def __onDemoPressed(self):
        '''
        TBA
        '''

        print('ahoy')


    def __onFinalizePressed(self):
        '''
        TBA
        '''

        # confirm target items
        self.__onTestPressed()

        if self.targets == []:
            print('No target to process')
            return

        # set paths
        self.__executablePath = self.__getLineEdit(self.__mainUi.executableLE).replace('\\', '/')
        self.__scriptPath = self.__getLineEdit(self.__mainUi.scriptLE).replace('\\', '/')

        for path in [self.__executablePath, self.__scriptPath]:
            if not os.path.exists(path):
                print('Not found: {}'.format(path))
                return

        # construct codes
        self.__cmdTmp = '''targets = {TARGET}\
        \n\
        \ntotal = len(targets)\
        \nfor counter, target in enumerate(targets, 1):\
        \n    \
        \n    print("\\n\\n# %s out of %s #" % (counter, total))\
        \n    print("Target: %s" % target)\
        \n    \
        \n    # create subprocess command\
        \n    cmd_lst = []\
        \n    cmd_lst.append("{EXE}")\
        \n    cmd_lst.append("{WRAPPER}")\
        \n    cmd_lst.append(target)\
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
                                    TARGET=self.targets,
                                    EXE=self.__executablePath,
                                    WRAPPER=self.__scriptPath)
                                    #ARG='ahoy')

        targetStr = '\n'.join(self.targets)

        self.__previewUi.show()
        self.__previewUi.targetTE.setText(targetStr)
        self.__previewUi.commandTE.setText(self.__cmd)


    def __onRunPressed(self, run=False):
        '''
        TBA
        '''

        if not run:
            self.__previewUi.close()
            print('\nCanceled')
            return

        self.__cmd = self.__getTextEdit(self.__previewUi.commandTE)

        try:
            exec(self.__cmd)
        except Exception as err:
            print('Failed to run process')
            print(str(err))
            return


    ########
    # MISC #
    ########


    def __getLineEdit(self, qLineEdit):
        '''
        TBA
        '''

        return qLineEdit.text()


    def __getTextEdit(self, qTextEdit):
        '''
        TBA
        '''

        return qTextEdit.toPlainText()


if __name__ == '__main__':
    Wrap()


# TODO: maintain selection
# TODO: all if parent ui dies
