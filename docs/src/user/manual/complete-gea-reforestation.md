# GEA Reforestation Tool User Manual

Welcome to the GEA Reforestation Tool user manual. This guide will help you navigate and utilise the tool to visualise historical imagery, access different landscape maps, and generate reports for potential afforestation sites.

## Overview

The GEA Reforestation Tool is designed to assist users in identifying and evaluating potential afforestation sites by providing access to various historical and current landscape imagery. Key features of the tool include:

- Visualisation of historical imagery (Landsat)
- Visualisation of recent imagery (NICFI)
- Interactive map canvas
- Report generation for potential afforestation sites


**Features and Controls**

![GEA Reforestation](./img/complete-gea-reforestation-1.png)

1. **Historical Imagery (Landsat):** If checked the map canvas will display historical imagery from Landsat.

2. **Recent Imagery (NICFI):** If checked the map canvas will display recent imagery from NICFI.

3. **Slide Bar:** The slide bar allows users to view the selected imagery on the map canvas. The functionality of the slide bar depends on the checkbox selection:

    - **Historical Imagery Checkbox Checked:** The map canvas will display historical imagery from Landsat.

    ![Historical Imagery](./img/complete-gea-reforestation-2.png)

    - **Recent Imagery Checkbox Checked:** The map canvas will display recent imagery from NICFI.

    ![Recent Imagery](./img/complete-gea-reforestation-3.png)


    The user can use the slide bar by dragging the toggle to the next or previous increment to view the corresponding imagery on the map canvas.

4. **Play Button:** The play button allows users to play through the selected imagery. This feature is useful for visualising changes in the landscape over time.

    **Historical Imagery**

    ![Historical Imagery play](./img/Landsat-working.gif)

    **Recent Imagery**

    ![Recent Imagery play](./img/NICFIworking.gif)

5. **Drawing tool:** The user can use the drawing tool to draw polygons on the map canvas.
        
    ![Drawing tool](./img/complete-gea-reforestation-5.png)

    5.1 **Draw Project Area Button:** The user can use this button to draw the polygon on the map canvas. Before using the `Draw Project Area` button, ensure that the site reference has been provided. After drawing the polygon right-click. Upon clicking the pop-up will open for entering the ID, ID should be 1.

    ![Id popup](./img/complete-gea-reforestation-9.png)

    - **Error Handling:** If any of the fields is empty, an error message will be displayed for example for the site reference field the message would be: `Please add the site reference before starting drawing the project area.`

        ![Error message](./img/complete-gea-reforestation-4.png)

    - **Editing:** After drawing the polygon, you can edit it using the options available in the toolbar. The edit icon will appear in front of the project in the layer list, allowing modifications before saving.

        ![Edit options](./img/complete-gea-reforestation-6.png)

    5.2 **Project Inception Date:** To choose the project inception date, click on the field to open a calendar. Select the desired date from the calendar interface.

    ![Calander](./img/complete-gea-reforestation-7.png)

    5.3 **Site Reference:** Enter the site reference to identify the specific location or area for the project.

    5.4 **Version of the Site Reference:** Add the version number corresponding to the site reference for version control and tracking.

    5.5 **Author of the Site Capture:** Enter the name of the individual who captured or recorded the site details.

    5.6 **Country Dropdown:** Choose the country from the dropdown list to specify the location of the project.
    
    5.7 **Project Folder:** Select the project folder where plugin data is stored. The shape files will be saved in the `Sites` directory, which is automatically generated when you save the project.

    ![Sites directory](./img/complete-gea-reforestation-8.png)

    5.8 **Save Project Area Button:** Click the `Save Project Area` button to save the project after drawing the polygon. The shape files will be stored in the `Sites` directory.

    5.9 **Clear Button:** Use the `Clear` button to remove the polygon from the map. Note that the polygon must be cleared before saving the project, as shape files stored in the sites folder will not be deleted after saving.
