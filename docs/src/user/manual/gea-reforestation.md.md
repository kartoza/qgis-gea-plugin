# GEA Reforestation QGIS Plugin User Manual

![Shared folder](./img/gea-reforestation-1.png)

1. **Preparing the QGIS Project:** To start using the GEA Reforestation Tool, you need to extract the project folder shared by the Head office.

    ![Extracted folders](./img/gea-reforestation-2.png)

    After extracting the .zip folder the extracted folder will show in the location you have specified. Click on the extracted folder to view the files/folders inside. The project folder should contain the following files/folders:

    * Masks: This folder contains Exclusion Masks data.
    * Images: This folder contains historical Landsat imagery data.
    * Malawi_2.gpkg: This is a package for vector data.
    * QGIS project file (project.qgz): This is the main file that contains the QGIS project settings.
    * Plugin.zip: this contains the GEA reforestation tool to be loaded in QGIS

    ![Files/folders](./img/gea-reforestation-3.png)

3. **Opening the QGIS Project:** If the user does not have QGIS installed, please refer to the complete documentation on how to [install QGIS](../quickstart/index.md). 

    - Once installed, right-click on the project.qgz file and select `Open with QGIS` to open the project.

        ![Open with QGIS](./img/gea-reforestation-4.png)

4. **Navigating the QGIS Interface:** The QGIS interface is divided into several useful areas:

    3.1 **Menu Toolbar**
    The menu toolbar offers many options, some of which are:

    * **Settings:** The user can use the settings option for managing the user profile, style and many more.

        ![Settings](./img/gea-reforestation-5.png)

    * **Plugins:** The user can use the plugin option to manage plugins like installing, uninstalling, and upgrading plugins.

        ![Plugins](./img/gea-reforestation-6.png)

    3.2 **Attribute Toolbar**

    ![Attribut toolbar](./img/gea-reforestation-7.png)

    The attribute toolbar offers many options, some of which are:

    1. **Pan:** Allows the user to pan the map to a specific location.
    2. **Zoom in:** Zooms in on the map to show more detail.
    3. **Zoom out:** Zooms out of the map to show a wider area.
    4. **Full zoom:** Zooms in or out to the maximum extent.
    5. **Show map tips:** Displays additional information about the map, such as coordinates and scale.

    3.3 **Vector Toolbar:**

    ![Vector toolbar](./img/gea-reforestation-8.png)

    The vector toolbar offers many options, some of which are:

    1. **Current edits:** Displays the current editing state of the layer.
    2. **Toggle editing:** Toggles the editing mode on or off.
    3. **Save layer edits:** Saves any changes made to the layer.
    4. **Add polygon feature:** Creates a new polygon feature on the map.

    ### 3.4 Layer List

    The user can use the QGIS project with emphasis on the Layers List panel to contextualise and review the area of interest. The Layers List for all of the areas of interest (`Malawi 2` shown here) includes the following:

    ![Layers List](./img/layer-list-1.png)

    - Malawi 2 Area of Interest
    - Malawi 2 Buffer
    - Proposed Site Boundaries
    - Gea Afforestation Tool-Malawi 2
    - Administrative Areas
    - Exclusion Masks
    - Current Google Imagery
    - Recent NICFI Imagery
    - Historical Landsat Imagery

    1. **Malawi 2 Area of Interest:** Check the `Malawi 2 Area of Interest` checkbox to visualise the area of interest, it will be shown on the map canvas with a black line.

    ![Area of interest](./img/layer-list-2.png)

    2. **Malawi 2 Buffer:** Check the `Malawi 2 Buffer` checkbox to visualise the buffer area, it will be shown on the map canvas with a yellow line.

    ![Buffer](./img/layer-list-3.png)

    3. **Proposed Site Boundaries:** Displays the proposed boundaries created by the user for the project. Check the `Proposed Site Boundaries` checkbox and The proposed boundaries will be shown on the map canvas with a red line.

    ![Proposed boundaries](./img/layer-list-4.png)

    4. **Administrative Areas:** This includes three options with checkboxes that allow users to visualise different administrative areas on the map canvas.

    ![Administrative areas](./img/layer-list-5.png)

    - **Malawi 2 Country:** Displays the country boundaries of Malawi. Check the `Malawi 2 Country` checkbox to visualise the country boundaries, it will be shown on the map canvas with a green line.

        ![Country areas](./img/layer-list-6.png)

    - **Malawi 2 District:** Displays the district boundaries within Malawi. Check the `Malawi 2 District` checkbox to visualise the district boundaries, it will be shown on the map canvas with a white line. Zoom in to view this on the map canvas.

        ![District areas](./img/layer-list-7.png)

    - **Malawi 2 Sub-divisional Administrative Unit:** Displays the sub-divisional administrative units within Malawi. Check the `Malawi 2 Sub-divisional Administrative Unit` checkbox to visualise the sub-divisional administrative unit boundaries, it will be shown on the map canvas with a blue line. Zoom in further after the district boundaries are shown on the map canvas to view the sub-divisional administrative units.

        ![sub-divisional administrative units areas](./img/layer-list-8.png)

    5. **Exclusion Masks:**

    ![Exclusion Masks](./img/layer-list-9.png)

    There are four exclusion masks available for the user. The user can use these exclusion masks to check where they cannot do a project. To use the exclusion mask, check the checkbox available in front of the exclusion mask. The four exclusion masks are:

    **Malawi 2 Grass Exclusion Mask**
        ![Grass](./img/layer-list-10.png)

    **Malawi 2 Wetland Exclusion Mask**
        ![Wetland](./img/layer-list-11.png)

    **Malawi 2 Forest Exclusion Mask**
        ![Forest](./img/layer-list-12.png)

    **Malawi 2 Soil Carbon Exclusion Mask**
        ![Soil Carbon](./img/layer-list-13.png)

    > Additional Notes on Viewing Different Imagery Layers:
    To effectively view the different imagery layers (Google Imagery, NICFI, and Landsat), you need to toggle the visibility of these layers.

    6. **Current Google Imagery:** Displays the most recent Google imagery. Check the relevant checkbox to view `Current Google imagery`.

    ![Google Imagery](./img/layer-list-14.png)

    7. **Recent NICFI Imagery:**

    - **Turn Off Google Imagery/Historical Landsat Imagery to View NICFI Imagery:** In the Layers panel, locate the Google Imagery/Historical Landsat Imagery layer. Click the checkbox next to the Google Imagery/Historical Landsat Imagery layer to turn it off. This will allow the NICFI imagery to be visible.

    ![NICFI Imagery](./img/layer-list-15.png)

    Through Norway’s International Climate & Forests Initiative (NICFI), users can now access Planet’s high-resolution, analysis-ready mosaics of the world’s tropics in order to help reduce and reverse the loss of tropical forests, combat climate change, conserve biodiversity, and facilitate sustainable development for non-commercial uses.

    To use the NICFI imagery the user must log in to the Planet_Explorer plugin.

    For detailed documentation on how to log in click [here](./login.md)

    Displays recent NICFI imagery. Check the relevant checkbox to view recent NICFI imagery.

    ![NICFI Imagery](./img/layer-list-16.png)
    ![NICFI Imagery](./img/layer-list-18.png)

    8. **Historical Landsat Imagery:** Displays historical Landsat imagery. Check the relevant checkbox to view historical Landsat imagery. The user can use the historical imagery to compare the current and historical imagery differences.

    - **Turn Off Google Imagery/NICFI Imagery to View Landsat Imagery:** In the Layers panel, locate the Google Imagery/NICFI imagery layer. Click the checkbox next to the Google Imagery/NICFI imagery layer to turn it off. This will reveal the Landsat imagery layer below.

    ![Historical Landsat Imagery](./img/layer-list-17.png)

    By using the layers list effectively, the user can customise the visualisation of different layers and gain valuable insights for the project.

    ### 3.5 Map Canvas

    The map canvas is the main area where the user can view and interact with the map. Users can use the map canvas to:

    * Zoom in and out using the zoom tools.
    * Pan the map using the pan tool.
    * Identify features on the map using the identify tool.
    * Add new features to the map using the vector toolbar.

    By following these steps and using the various tools and options in the QGIS interface, the user can effectively use the GEA Reforestation QGIS Plugin to manage and analyse your reforestation project data.
