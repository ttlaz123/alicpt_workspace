# Connection Test

[![hackmd-github-sync-badge](https://hackmd.io/b2G1tS3eRxKrlJbYMOO3NQ/badge)](https://hackmd.io/b2G1tS3eRxKrlJbYMOO3NQ)


## 1. Update the code
If you followed [visual studio install tutorial](https://github.com/shu-xiao/alicptfts/blob/main/readme/VisualStudioInstallTutorial.md) and download the software, please use git pull to update the code (require Internet). Or please follow the step 4 in install tutorial to download the software. Git is built in Visual Studio.

![](https://i.imgur.com/xu6Xo2Y.png)
Open the Git menu in Visual Studio and click **pull** item.

## 2. check the test code
If you update the code, you should see some new files in right panel. The test code we will use locates at alicptfts/alicptfts/UnitTest/connectTest.py

If you don't see the right handside panel or it looks different. Please press CTRL+ALT+L or open View menu and click Solution Explorer.

## 3. Test program
### 3.1 Connnecting XPS
Before testing, please connect XPS controller to laptop.
### 3.2 Check connecting IP
You can skip the step if don't change the connecting IP. 
Open the browser and enter the XPS IP, check that you can access the XPS web interface. (You don't need to login.)

If you change the XPS connecting IP, please change the hostIP to the IP you set.
https://github.com/shu-xiao/alicptfts/blob/main/alicptfts/UnitTest/connectTest.py#L46

### 3.3 Test
Click the green triangle botton and see what's going on.

Here is the test result from my laptop. Since I don't have XPS.

**Please report the error massages and exit code after the test**.

![](https://i.imgur.com/Z1RDnNp.png)
