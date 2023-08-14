---
title: pyinstaller打包报错
date: 2023-08-14 12:54:30
tags:
---



[TOC]

# Pyinstaller打包

## 打包指令

```python
>pyinstaller -D -w xxx.py
```

## 其他参数

```python
-F
等同于
--onefile
# 打包为单个文件，如果项目仅为一个.py文件时可用，多个文件不可
```

```python
-D
--onedir
# 打包为一个目录
```

```python
--key=keys
# 使用keys进行加密打包
```

```python
-w
--windowed
--noconsole
# 去掉控制台窗口，执行时不会启动命令行(windows系统)
```

```python
-c
--console
# 打开控制台窗口，使用控制台子系统执行,当程序启动的时候会打开命令行(默认)
```

```python
-i file.ico
--icon=<file.ico>
# 程序的图标
```

```python
-h
--help
# help查看命令
```

```python
# 其他(不常用)
-v, --version #版本
```

## 打包产生的文件

### 打包单文件

- exe文件

  生成的可执行文件可以在 dist 文件夹中找到

  包含了你的 Python 代码和所有依赖项，以便你可以在其他计算机上运行它而无需安装 Python 解释器或其他依赖库。

  生成的可执行文件的名称通常与你的 Python 脚本文件的名称相同（默认情况下）

### 打包多文件

- build

  临时文件夹，包含已经编译但尚未打包成最终可执行文件的文件和目录。在打包过程完成后，这个文件夹可以被删除，因为这些临时文件已经不再需要。

- dist

  最终结果文件夹。其中最重要的文件是exe或应用程序的主文件。此文件夹中的其他文件和目录可能会包含有关打包过程中使用的库、依赖项和资源的信息。

- .spec

  配置文件，它是一个 Python 脚本文件，用于指定打包过程的参数和选项。

  如果在打包时提供了 .spec 文件，PyInstaller 将使用该文件中指定的配置进行打包，否则将使用默认配置。

  `pyinstaller yourscript.spec`

# 打包环境

## anaconda环境

输入命令后打包报错，百度未能解决

```shell
Traceback (most recent call last):
  File "C:\Users\神殒魔灭\AppData\Roaming\Python\Python39\site-packages\PyInstaller\isolated\_parent.py", line 372, in call
    return isolated.call(function, *args, **kwargs)
  File "C:\Users\神殒魔灭\AppData\Roaming\Python\Python39\site-packages\PyInstaller\isolated\_parent.py", line 293, in call
    ok, output = loads(b64decode(self._read_handle.readline()))
EOFError: EOF read where object expected

OSError: [Errno 22] Invalid argument
```

### 系统环境

打包成功后报错

```shell
Error loading Python DLL
'D:\AudioReceptionTesterbuild\audioReceptionTester\python39.dl'.
LoadLibrary:找不到指定的模块。
```

这是因为程序是在anaconda环境下写的，系统环境没有下载相应模块，所以有缺失错误。

除此之外，pyinstaller会将无用的模块也导入进去，所以不推荐此打包方法。

### 虚拟环境(anaconda prompt)

所谓的虚拟环境，就是创建一个没有第三方库和模块的 Python 环境。

```shell
# conda命令
1、导出虚拟环境的列表
conda env list
2、导出当前环境的包
conda list
3、启动/切换至名为name的Python环境
conda activate name
4、退出虚拟环境
conda deactivate
5、创建新的、名为name的、Python版本为3.x的虚拟环境
conda create -n name python==3.x
```

**步骤：**

1. 创建虚拟环境

   ```python
   conda create -n env_1 python==3.10.8
   # 问你新环境是否需要安装这些包，Y确定即可
   ```

   ```shell
   # 如果报错
   Collecting package metadata (current_repodata.json): failed
   
   UnavailableInvalidChannel: HTTP 404 NOT FOUND for channel simple <https://pypi.mirrors.ustc.edu.cn/simple>
   
   The channel is not accessible or is invalid.
   
   You will need to adjust your conda configuration to proceed.
   Use `conda config --show channels` to view your configuration's current state,
   and use `conda config --show-sources` to view config file locations.
   # 搜索.condarc文件删除即可
   ```

2. 进入虚拟环境

   ```shell
   conda activate audiotool
   
   当(base) D:\AudioReceptionTester>
   变成(audiotool) D:\AudioReceptionTester>
   表示已经进入
   ```

   

3. 安装需要的第三方包

   如果程序还用到了其他的第三方库，那么就需要把这些库给添加进虚拟环境，添加方式就是直接在当前环境下用 pip。

   ```shell
   # 镜像
   -i https://pypi.tuna.tsinghua.edu.cn/simple
   -i https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
   -i https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
   -i https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
   ```

4. 更极致的exe大小

   如果想让其小到不能再小，那么就要尽可能地删去虚拟环境里面的一些用不到的包（用 pip uninstall 来删）

   ```shell
   # 查看安装的包
   conda list
   ```

## 安装第三方包问题

- 引用与包名不一致

  ```python
  # 举例：serial包
  # 在import时就是serial
  # 实际上pip安装的是pyserial包
  import serial
  pip install pyserial
  ```

- 引用奇怪

  ```python
  # 举例：还是serial
  # 这次是serial.tools
  import serial.tools.list_ports
  pip install serial.tools
  ```

- 安装一个包中附带其他包

  ```python
  # 举例：pandas
  # pandas安装时候包含了numpy
  # 如果卸载numpy，会提醒缺失moudle numpy
  ```

- 内置模块不用安装

  ```python
  # 举例：os, time, sys
  # 会报错ERROR，找不到这个包
  ```

## 其他问题

- .spec文件每次打包时都要删掉

  .spec文件是打包的配置文件，打包时会默认按照这个文件内容执行，如果你发现修改报错后，依然报同样的问题，请查看.spec文件是否删除。

# 参考资料

[用 Pyinstaller 模块将 Python 程序打包成 exe 文件（全网最全面最详细）](http://www.taodudu.cc/news/show-5085357.html?action=onClick)

[【环境问题】Anaconda环境下使用pyinstaller封装exe](https://blog.csdn.net/zhengyuyin/article/details/127800237)

[PyInstaller 中文文档](https://blog.csdn.net/nainaiwink/article/details/130862534)

