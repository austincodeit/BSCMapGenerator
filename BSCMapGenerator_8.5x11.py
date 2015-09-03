# BSCMapGenerator 8.5 x 11 v2.1
# Generates two separate 8.5" x 11" map PDFs: one map for the property location, and one for the property structures.
# Created for Austin Code Department 9/19/2014 by J Clary.
#New to this version: ability to set scale of each map or use defaults

import arcpy

workspace = "G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC_Maps\\AutoLayerFiles.gdb"
arcpy.env.workspace = workspace
arcpy.env.overwritOutput = True #overwrite existing files
mxd = arcpy.mapping.MapDocument("G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\BSC_Template_AutoGenerate_8.5x11_v2.mxd")
df = arcpy.mapping.ListDataFrames(mxd)[0] # address location data frame and turn on select layers
location = arcpy.GetParameterAsText(0)
location = location.upper() #convert to uppercase
caseNumber = arcpy.GetParameterAsText(1)
userName = arcpy.GetParameterAsText(2)
date = time.strftime("%m/%d/%Y")  #added to map
expression = "FULL_STREET_NAME LIKE '" + location + "%'" #this is an SQL expression and can be modified as necessary
expression2 = "OBJECTID LIKE '%'"
arcpy.AddMessage("Query = " + expression)
visibleStructuresLayers = ["TRANSPORTATION.street_segment","Structures","Subject Property","Parcels","Lakes"]
visibleLocationLayers = ["TRANSPORTATION.street_segment","Subject Tract","Parcels","Lakes"]
visibleRoadMapLayers = ["Subject Tract","Subject Property","Lakes","Basemap","OpenStreetMap"]

locationMapScale = arcpy.GetParameterAsText(3) #default 2000
roadMapScale = arcpy.GetParameterAsText(4) #default 5500
structureMultiplier = float(arcpy.GetParameterAsText(5)) # default 1.1 (110% of parcel size)

#-----------REFRESH TEMPLATE------------------
arcpy.AddMessage("Refreshing template...")
arcpy.Delete_management("Subject Tract")  #removes instances from memory (not from map)
arcpy.Delete_management("Subject Property")

for lyr in arcpy.mapping.ListLayers(mxd, "", df): #set visibility and remove older layers
	lyr.visible = False
	if lyr.name == "Subject Tract": 
			arcpy.mapping.RemoveLayer(df, lyr)
	if lyr.name == "Subject Property":
		arcpy.mapping.RemoveLayer(df, lyr)
	if lyr.name in visibleLocationLayers:
		lyr.visible = True

mxd.activeView = "PAGE_LAYOUT"#pan to location and refresh layout
arcpy.RefreshActiveView() #update view

lyr = arcpy.mapping.ListLayers(mxd, "LOCATION.address_point", df)[0]
srcLyr = arcpy.mapping.ListLayers(mxd, "source_symbology", df)[0]
parcels = arcpy.mapping.ListLayers(mxd, "Parcels", df)[0]
structureLayer = arcpy.mapping.ListLayers(mxd, "Structures", df)[0]
arcpy.SelectLayerByAttribute_management(lyr,"NEW_SELECTION",expression) # search address points and select location
#-------------------------ERROR CHECKING------------------------
results = arcpy.GetCount_management(lyr) #return number of features selected
featureCount = int(results.getOutput(0)) #extract result as integer
if featureCount > 1:
	arcpy.AddMessage("!------Multiple addresses found! Please refine query------!")
	sys.exit()
if featureCount == 0:
	arcpy.AddMessage("!------No address found! Please refine query------!")
	sys.exit()
for row in arcpy.SearchCursor(lyr):#retrieve address of selected feature
	selectedAddress = row.FULL_STREET_NAME  #this variable used later for legend
	arcpy.AddMessage("Selected address is ---> " + selectedAddress +" <---") #print address name
#----------------------------------------------------------------------
arcpy.AddMessage("Selecting corresponding parcel in location map...")
arcpy.SelectLayerByLocation_management(parcels, "INTERSECT", lyr) #select parcel that intersects with address point
arcpy.AddMessage("Creating location map feature layer...")
arcpy.MakeFeatureLayer_management(parcels, "Subject Property") # generate a feature layer and...
addLayer = arcpy.mapping.Layer("Subject Property") #pass it as a layer...
arcpy.mapping.AddLayer(df,addLayer, "AUTO_ARRANGE")  #to the AddLayer() function
newLyr = arcpy.mapping.ListLayers(mxd, "Subject Property", df)[0]
arcpy.AddMessage("Updating feature symbology...")
arcpy.mapping.UpdateLayer(df, newLyr, srcLyr, True) #apply symbology to new layer
arcpy.mapping.MoveLayer(df, structureLayer, newLyr, "AFTER") #set the drawing order
#----------Update Layout and Export----------|
arcpy.AddMessage("Updating map text...")
mainText = "This product is for informational purposes and may not have been prepared for or be suitable for legal, engineering, or surveying purposes. It does not represent an on-the-ground survey and represents only the approximate relative location of property boundaries. This product has been produced by the Austin Code Department for the sole purpose of geographic reference. No warranty is made by the City of Austin regarding specific accuracy or completeness.	Produced by " + userName + " for the Austin Code Department - " + date
titleText = "CASE#: " + str(caseNumber) + "\r\nLOCATION: " + str(selectedAddress).title()

for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):#update the text boxes
	if elm.name == "Text_1":
		elm.text = mainText	
	if elm.name == "Title_1":
		elm.text = titleText
	if elm.name == "Frame":
		elm.text = "Location Map"	

arcpy.AddMessage("Updating map extents and clearing selections...")
mxd.activeView = "PAGE_LAYOUT"#pan to location and refresh layout
df.extent = parcels.getSelectedExtent()
df.scale = locationMapScale 
arcpy.SelectLayerByAttribute_management(parcels, "CLEAR_SELECTION")
arcpy.RefreshActiveView() #update view
arcpy.AddMessage("Exporting G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\AutoGenerate Maps\\BSC Case " + caseNumber + " - " + selectedAddress + "- Location.pdf")
arcpy.mapping.ExportToPDF(mxd, "G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\AutoGenerate Maps\\BSC Case " + caseNumber + " - " + selectedAddress + "- Location.pdf")

#-------------"Road Map"---------------|
arcpy.AddMessage("Creating 'road map'...")

for lyr in arcpy.mapping.ListLayers(mxd, "", df): #set visibility
	lyr.visible = False
	if lyr.name in visibleRoadMapLayers:
		lyr.visible = True

df.scale = roadMapScale  #zoom out a little

arcpy.RefreshActiveView() #update view

for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):#update the text boxes
	if elm.name == "Frame":
		elm.text = "Road Map"	

arcpy.AddMessage("Exporting G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\AutoGenerate Maps\\BSC Case " + caseNumber + " - " + selectedAddress + "- Road Map.pdf")
arcpy.mapping.ExportToPDF(mxd, "G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\AutoGenerate Maps\\BSC Case " + caseNumber + " - " + selectedAddress + "- Road Map.pdf")

#-------------Structures Map---------------|
arcpy.AddMessage("Generating structures map...")

newLyr = arcpy.mapping.ListLayers(mxd, "Subject Property", df)[0]
arcpy.mapping.MoveLayer(df, parcels, newLyr, "AFTER") #set the drawing order		

layers = arcpy.mapping.ListLayers(mxd, "", df) 
for layer in layers:	
	 layer.visible = False
	 if layer.name in visibleStructuresLayers:
		layer.visible = True

arcpy.RefreshTOC()

arcpy.SelectLayerByAttribute_management(newLyr, "NEW_SELECTION", expression2)		#select all features in new layer (there's only one)

df.extent = newLyr.getSelectedExtent() #get extent and pan to parcel
df.scale =df.scale * structureMultiplier # default 1.1 (110% of parcel size)

for elm in arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT"):#update the text boxes
	if elm.name == "Frame":
		elm.text = "Structures Map"	

for layer in layers:	
	 if layer.name in visibleStructuresLayers:
		layer.visible = True

arcpy.RefreshTOC()
arcpy.RefreshActiveView() #update view
mxd.activeView = "PAGE_LAYOUT"#pan to location and refresh layout
arcpy.SelectLayerByAttribute_management(newLyr, "CLEAR_SELECTION")
arcpy.AddMessage("Exporting G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\AutoGenerate Maps\\BSC Case " + caseNumber + " - " + selectedAddress + "- Structures.pdf")
arcpy.mapping.ExportToPDF(mxd, "G:\\Code Enforcement\\CC GIS Operations\\Operations\\BSC Maps\\AutoGenerate Maps\\BSC Case " + caseNumber + " - " + selectedAddress + "- Structures.pdf")
