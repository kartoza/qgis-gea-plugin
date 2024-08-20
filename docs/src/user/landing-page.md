# GEA REFORESTATION Landing Documentation

The user can refer to this video to learn how the tool works.

https://www.youtube.com/watch?v=Jx8Q_MGs0no

## Layers List

The Layers List allows users to manage and view various map layers on the map canvas. Users can:

- **Imagery Options:** View different types of imagery, including current Google imagery, recent NICFI imagery, and historical Landsat imagery.

- **Exclusion Masks:** Enable exclusion masks to check restricted areas before starting a project. It's recommended to check these masks to avoid including restricted areas in the project.

- **Administrative Areas:** Enable administrative areas from the dropdown to view different administrative boundaries on the map canvas.

## Toolbar

The Toolbar provides tools for interacting with the map canvas:

- **Zoom In/Out:** Adjust the zoom level of the map.

- **Pan Map:** Move the map view to different areas.

- **View Attribute Table:** Access and view attribute data associated with map layers.

## Slide Bar

The slide bar allows the user to view different images on the map canvas. There are two checkboxes available:

- **Historical Landsat:** For viewing historical Landsat imagery.

- **Recent NICFI:** For viewing recent NICFI imagery.

To change the images using the slide bar, drag the slider to the next increment or decrement point.

### Auto Play

The Auto Play feature allows users to play through the selected imageries automatically. To use this feature:

- Click the play button located at the end of the slide bar.

- If the user wants the imageries to play in a continuous loop, enable the loop checkbox.

> Note: To view the most recent NICFI imageries, users must log in to Planet Explore.

## Drawing Tool

The Drawing Tool allows users to define and manage project areas on the map canvas. This includes drawing polygons, editing existing shapes, and saving or clearing project areas. Proper usage of this tool is crucial to ensure accurate project delineation and reporting.

**Drawing on the Map Canvas**

- **Fill Required Fields:** Before drawing on the map canvas, the user should ensure that all the necessary fields are filled out. If any fields are missing, an error message will appear at the top of the plugin, prompting the user to complete the required information.

- **Draw Project Area:** Click the `Draw Project Area` button to begin drawing. While creating the polygon, avoid including areas marked as exclusion masks. This ensures that the project area does not overlap with restricted regions.

- **Editing Drawn Areas:** Use the following toolbar tools to modify the drawn area:

- **Add Polygon Feature:** Add new polygon features to the map canvas.

- **Current Edits:** Review and manage the ongoing edits.

- **Toggle Editing:** Switch between editing modes to make changes to the drawn area.

**Saving the P Area:**

- **Save Project Area:** Click the Save Project Area button to save the drawn polygon. The polygon will be stored as a (.shp) file in the `Sites` folder. The `Sites` folder will be created automatically if it does not already exist, and will contain the saved polygon files.

**Clearing the Project Area:**

To clear the polygon from the map canvas, do the following:

- **Ensure the Polygon is Selected:** Confirm that the polygon you wish to clear is active.

- **Click the Clear Button:** The polygon will be removed from the map canvas.

> Note: Clearing the polygon will only remove it from the map canvas. The .shp file saved in the Sites folder will remain intact and will not be deleted.

## Generating Reports

To generate a report based on the saved project areas, perform these steps:

- **Prepare Data:** Ensure that the relevant polygons are saved and any necessary data is up-to-date.

- **Generate Report:** Click on the  `Generate Report` button, to generate the report. The `Reports` folder will be created automatically if it does not already exist, and will contain the saved report files.
