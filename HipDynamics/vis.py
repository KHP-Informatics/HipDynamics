# -*- coding: utf-8 -*-
#!/usr/bin/python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime


class QuickPlot:

    @property
    def fixYaxis(self):
        return self.__fixYaxis

    @fixYaxis.setter
    def fixYaxis(self, f):
        self.__fixYaxis = f

    @property
    def outputPath(self):
        return self.__outputPath

    @outputPath.setter
    def outputPath(self, op):
        self.__outputPath = op

    def __init__(self, data):
        self.data = pd.DataFrame(data[1:len(data)], columns=data[0])
        self.index = self.data.filter(regex="index-")
        self.colours = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
        self.fixYaxis = False
        self.outputPath = '/'

    def plot(self, indexBy, labelWith, withMeasure, show=True, saveFigure=False, figsize=(16, 10)):
        self.indexBy = indexBy
        self.indexName = 'index-{}'.format(indexBy)
        self.indexVals = self.data[self.indexName].unique()
        self.labelWith = labelWith
        self.withMeasure = withMeasure
        self.nPlots = len(self.indexVals)
        self.nCols = self.determineNumberOfCols()

        plt.close('all')
        plt.style.use('ggplot')
        fig, ax = plt.subplots(ncols=self.nCols, nrows=int(self.nPlots/self.nCols), figsize=figsize)
        if self.nCols == 1:
            self.plotRows(ax, 0)
        else:
            for colIdx in range(self.nCols):
                self.plotRows(ax, colIdx)
        plt.tight_layout()

        if saveFigure:
            path = self.outputPath + 'HipDynamics_{}.png'.format(datetime.datetime.now().strftime('%d-%m-%Y_%H-%M-%S'))
            plt.savefig(path)
        if show:
            plt.show()


    def plotRows(self, ax, colIdx):
        nRows = int(self.nPlots / self.nCols)
        for rowIdx in range(nRows):
            selectData = self.data[self.data[self.indexName] == self.indexVals[(rowIdx%nRows) + (nRows*colIdx)]]
            plotY = selectData.filter(regex=self.withMeasure)
            plotY_mtrx = np.array(plotY.as_matrix(columns=None), dtype=float)
            labelWithVals = np.array(self.index.loc[plotY.index.values, 'index-{}'.format(self.labelWith)])

            if self.nCols == 1:
                axI = ax[rowIdx]
            else:
                axI = ax[rowIdx][colIdx]

            self.plotFigure(axI, plotY_mtrx, plotY.columns.values,
                            self.indexVals[(rowIdx%nRows) + (nRows*colIdx)], labelWithVals)

    def determineNumberOfCols(self):
        nCols = 1
        if self.nPlots > 4:
            nCols = 2
        if self.nPlots > 11:
            nCols = 3
        return nCols

    def plotFigure(self, ax, mtrx, cols, indexVal, labelWithVals, fontsize=10):
        N = int(len(list(cols)))
        N_half = int(N/2)
        for i in range(len(mtrx)):
            ax.plot(np.arange(N), mtrx[i], color=self.colours[i % 8], label=labelWithVals[i])
        ax.set_ylabel(self.capitaliseFirstCharacter(self.withMeasure))
        ax.set_xlabel("Features")
        ax.set_xticks(np.arange(N_half)*2)
        ax.set_xticklabels(np.arange(N_half)*2, rotation=270, fontsize=fontsize)
        ax.set_title('{}: {}'.format(self.indexBy, indexVal), fontsize=fontsize)
        ax.legend(loc='upper right', title=self.labelWith, fontsize=8)
        if self.fixYaxis:
            ax.set_ylim((-0.05, 0.05))

    def capitaliseFirstCharacter(self, str):
        rendered = str
        rendered = rendered[0].capitalize() + rendered[1:len(rendered)]
        return rendered

