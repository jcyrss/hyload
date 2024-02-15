## Introduction

`hyload` is a performance testing framework.

It is used to test Web/HTTP API server, as the following figure shows.

![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/90c0e86d-b7c6-44f1-9580-cc34703f0968)

It provides a high-performance Python library to develop load testing. So you could run your test program on Windows， MacOS and Linux.

Based on gevent, by launching multiple hyload workers, it could reach about tens of thousands of requests per second and hundreds of thousands of concurrent connections on a single machine.

It also provides a VS Code extension to let you observe realtime statistics, remote multi-host deploy and remote launching test. VS Code extension includes a code-helper to facilitate developing.

![Code_ibIhaJDp3d](https://github.com/jcyrss/baiyueheiyu/assets/10496014/10d76802-37b0-4c73-bf12-48432a5720ef)

  
## Installation

Including install hyload library and hyload vscode extension

- hyload library

  just run `pip3 install hyload` 


- hyload VS Code extension
  
  search `hyload` in VS Code marketplace and install it

  ![image](https://github.com/jcyrss/baiyueheiyu/assets/10496014/ef128b00-0870-43a3-8051-36eaafe1b282)
    
  
## User Guide

Please refer to https://jcyrss.github.io/hyload