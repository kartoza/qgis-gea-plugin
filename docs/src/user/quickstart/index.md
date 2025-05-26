---
title: EPAL-Eligible Project Area Locator
summary: Visualise historical imagery, access different landscape maps and generate reports for potential afforestation sites.
    - Ketan Bamniya
date: 19-06-2024
some_url: https://github.com/kartoza/qgis-gea-plugin
copyright: Copyright 2024
contact: marketing@geoterra360.pt
license: the reforestation tool is made available to Eligible Project Area Locator (EPAL) under a non-exclusive, sub-licensable, perpetual, irrevocable, royalty-free licence. This which allows EPAL to use and replicate the QGIS plugin and tool for the appointed project areas in Kenya, Uganda, and Malawi; and any other carbon offset future project areas managed, operated, and undertaken by EPAL. The reforestation tool concept, functionality, and operations, as well as the physical QGIS plugin are covered, considered, and always remain the Intellectual Property of GT360.
---

# Quick Start Documentation

The EPAL-Eligible Project Area Locator Tool consists of two main components:

1. A QGIS project that contains all the data for the area of interest, such as Malawi as outlined above.

2. The EPAL-Eligible Project Area Locator Plugin that helps users view current, recent, and historical imagery of an area and easily draw boundaries for proposed reforestation projects.

To use the tool, a few dependencies are required:

1. QGIS: The tool runs in QGIS geographical software, which needs to be installed on the user's computer.

The following Quick Start documentation will guide users on how to set up the tool with its dependencies:

1. Get QGIS.
2. The project file for an area of interest.
5. Install the EPAL-Eligible Project Area Locator Plugin.

## 1. How to install QGIS:

* QGIS, short for Quantum Geographic Information System, is a free and open-source software used for working with geospatial data. This data can be easily edited and analysed within QGIS. As a cross-platform application, it is widely used in geographic data applications and runs on different operating systems, including Windows, Mac, and Linux. QGIS is written in Python, C++, and Qt.

- **Step 1: Visit the QGIS Website:** Open your web browser and go to the QGIS official website: [QGIS Download Page](https://www.qgis.org/download/).

![Download QGIS](./img/quick-start-11.png)

- **Step 2: Choose Your Operating System:** On the download page, you will see options for different operating systems (Windows, macOS, Linux, etc.). Select the download option that matches your operating system.

    Click on the 1️⃣ `Download for Windows`. To view the versions available for download.

    - **Choose Your Version:** On the download page, you will see multiple versions of QGIS. Choose the version that is recommended for your needs. Generally, the Long Term Release (LTR) is recommended for most users as it is the most stable version. Download the LTR.

    ![Download QGIS](./img/quick-start-12.png)


- **Step 3: Installing QGIS**

Once the download is complete, locate the downloaded file in your Downloads folder or the location you specified. Double-click the installer file to start the installation process.

## Follow the Installation Wizard:

- The QGIS Setup Wizard will open. Follow the prompts: Click `Next` to start the installation process.

![Install QGIS](./img/quick-start-13.png)

- The second window will include all the licenses that you have to agree with in order to get `QGIS` installed. Check the 1️⃣ `I accept the terms in the License Agreement` box then click on the 2️⃣ `Next` button.

![Install QGIS](./img/quick-start-14.png)

- Next, you will be prompted to select the install location. This is the same thing as the installation path and this is where your QGIS version will be installed. It is recommended to go with the default one which is `C:\Program Files\QGIS 3.34` for Windows. Please note that the QGIS version number may vary based on the current LTR.

- Select the components you wish to install. For a full installation, leave all options checked and click `Next`.

![Install QGIS](./img/quick-start-15.png)

- Click `Install` to begin the installation.

- Complete the Installation: The installer will copy the necessary files to your computer. This process may take a few minutes. Once the installation is complete, click `Finish` to exit the Setup Wizard.

## Launch QGIS:
You can now launch QGIS from your Start menu or desktop shortcut.

## For MacOS Users

If you are using macOS, follow the instructions provided here:

When attempting to launch QGIS for the first time on macOS, there is a chance that macOS will `initially block it due to its origin from the internet. To enable its execution, follow these steps:

1. Navigate to `System Preferences`.
2. Select `Security & Privacy`.
3. In the `General` tab, you will encounter a notification indicating that QGIS is being blocked. Click on the `Open Anyway` button.

![MacOS](./img/quick-start-16.png)

4. A confirmation dialog will pop up. Click `Open` to commence QGIS.

## 2. Accessing Project The project file for an area of interest:

- **Project Folder Delivery:** You need to ask for the project folder from your head office containing all the necessary data for your project. 

The QGIS project for the user's area of interest will be shared via a zip folder likely from a link for download from the head office supplier. 

Once the project has downloaded onto your computer extract the folder to a destination of your choice.

Open the project folder that contains the following files and folders

![Project folder](./img/quick-start-23.png)

1️⃣ The QGIS Project file.

2️⃣ The project geopackage that contains all the supporting vector data.

3️⃣ The masks folder contains the exclusion masks raster data that supports the project.

4️⃣ The images folder that contains the Landsat images that support the project

### Opening the EPAL QGIS Project

To open the QGIS `project` right click on the project file that ends in .qgz and choose to open it with QGIS

![Open with QGIS](./img/quick-start-24.png)

QGIS will then open with the following project and map layers viewable. 

![QGIS Project](./img/quick-start-25.png)

## 5. How to Install EPAL-Eligible Project Area Locator Tool


You need to have the plugin URL. To get the plugin URL, visit to the [Plugins GitHub Repository](https://github.com/kartoza/qgis-gea-plugin)

![Plugins GitHub Repository](./img/quick-start-20.png)

* Copy the URL into the clipboard

### Steps to Install the Plugin

- **Open QGIS:** Launch the QGIS application on your computer.

- **Access the Plugins Menu:** Click on the 1️⃣ `Plugins` option available in the navbar section at the top of the QGIS window. Upon clicking you will see the other option for plugin.

![Plugins option](./img/quick-start-1.png)

- **Manage and Install Plugins** Select the 1️⃣ `Manage and Install Plugins..` option from the dropdown menu.

![Option](./img/quick-start-2.png)

- **Add Plugin URL:** Click on the 1️⃣ `Settings` option and then click on the 2️⃣ `Add` button to add the plugin URL.

![Add URL](./img/quick-start-17.png)

Upon clicking the pop-up will open to add the URL. Enter the 1️⃣ `Name` and 2️⃣ `URL` in the respective fields. Click on the 3️⃣ `OK` button, to add the plugin.

![Install plugin](./img/quick-start-18.png)

You will see the plugin is added successfully.

![Plugin](./img/quick-start-19.png)

- **Install Plugin:** To install the plugin click on the 1️⃣ `All` option and search for the  2️⃣ `QGIS EPAL-Eligible Project Area Locator tool` plugin. Click on the 3️⃣ `Plugin` name, to enable the install button and then click on the 4️⃣ `Install` button, to install the plugin.

![Install Plugin](./img/quick-start-21.png)

After successful installation, you will see the plugin icon.

![Plugin Icon](./img/quick-start-22.png)

## Conclusion

By following the steps outlined in this Quick Start Guide, you will be able to set up your environment for effective use of plugins, access essential project data, and install necessary plugins such as Planet_Explorer. This setup will enable you to view, analyse, and manage geospatial data, including streamed imagery from Google, as well as local data like Landsat images and vector data layers.
