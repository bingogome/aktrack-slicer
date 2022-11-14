"""
MIT License
Copyright (c) 2022 Yihao Liu
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import vtk, math, slicer, json


def setTranslation(p, T):
    T.SetElement(0,3,p[0])
    T.SetElement(1,3,p[1])
    T.SetElement(2,3,p[2])

def setRotation(rotm, T):
    T.SetElement(0,0,rotm[0][0])
    T.SetElement(0,1,rotm[0][1])
    T.SetElement(0,2,rotm[0][2])
    T.SetElement(1,0,rotm[1][0])
    T.SetElement(1,1,rotm[1][1])
    T.SetElement(1,2,rotm[1][2])
    T.SetElement(2,0,rotm[2][0])
    T.SetElement(2,1,rotm[2][1])
    T.SetElement(2,2,rotm[2][2])

def setTransform(rotm, p, T):
    setRotation(rotm, T)
    setTranslation(p, T)