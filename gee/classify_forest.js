// ============================================================
// FOREST CARBON MRV: KAKUM NATIONAL PARK, GHANA
// Google Earth Engine (JavaScript). Pixel + classification half
// of the pipeline; exports a classified GeoTIFF that the Python
// package (../) reads for carbon accounting and uncertainty.
//
// MANUAL STEP REQUIRED: this script needs two hand-drawn geometry
// layers, created in the Code Editor before running:
//   forest     (FeatureCollection, property class = 1)  ~40 points
//   nonforest  (FeatureCollection, property class = 0)  ~40 points
// Place them across the scene; include points inside any tree-crop
// plantation as nonforest. Seeded split (42) makes results reproduce.
// ============================================================

// --- 1. Area of interest ---
var kakum = ee.Geometry.Point([-1.38, 5.35]);
Map.centerObject(kakum, 11);

// --- 2. Clean 2023 Sentinel-2 composite ---
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(kakum)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));
var composite = s2.median();
Map.addLayer(composite, {bands: ['B4','B3','B2'], min: 0, max: 3000}, 'Kakum 2023 (true colour)');
print('Images used:', s2.size());

// --- 3. NDVI ---
var ndvi = composite.normalizedDifference(['B8','B4']).rename('NDVI');
Map.addLayer(ndvi, {min: 0, max: 0.9, palette: ['brown','yellow','lightgreen','darkgreen']}, 'NDVI 2023');

// --- 4. Bands the classifier may use ---
var bands = ['B2','B3','B4','B8','B11','B12'];

// --- 5. Sample training points + reproducible 70/30 split ---
var sampled = composite.select(bands).sampleRegions({
  collection: forest.merge(nonforest),
  properties: ['class'],
  scale: 10
}).randomColumn('rnd', 42);          // seed 42 = same split every run
var trainSet = sampled.filter(ee.Filter.lt('rnd', 0.7));
var testSet  = sampled.filter(ee.Filter.gte('rnd', 0.7));

// --- 6. Train Random Forest ---
var classifier = ee.Classifier.smileRandomForest(50).train({
  features: trainSet,
  classProperty: 'class',
  inputProperties: bands
});

// --- 7. Accuracy assessment ---
var validation = testSet.classify(classifier);
var confusionMatrix = validation.errorMatrix('class', 'classification');
print('Confusion Matrix:', confusionMatrix);
print('Overall Accuracy:', confusionMatrix.accuracy());

// --- 8. Classify the whole composite ---
var classified = composite.select(bands).classify(classifier);
var classVis = {min: 0, max: 1, palette: ['tan','darkgreen']};
Map.addLayer(classified, classVis, 'Forest / Non-forest 2023');

// --- 9. Official Kakum boundary (WDPA) ---
var wdpa = ee.FeatureCollection('WCMC/WDPA/current/polygons');
var kakumPark = wdpa.filter(ee.Filter.eq('NAME', 'Kakum'));
print('Features matched:', kakumPark.size());
print('Matched park(s):', kakumPark.aggregate_array('NAME'));
var outline = ee.Image().byte().paint({featureCollection: kakumPark, color: 1, width: 2});
Map.addLayer(outline, {palette: ['red']}, 'Kakum boundary');
print('Polygon area (ha):', kakumPark.geometry().area().divide(10000));

// --- 10. Forest area inside the park (GEE-side check) ---
var kakumClassified = classified.clip(kakumPark);
Map.addLayer(kakumClassified, classVis, 'Classified (Kakum only)');
var pixelArea = ee.Image.pixelArea();
var areaStats = classified.eq(1).multiply(pixelArea).rename('forest_m2')
  .addBands(classified.eq(0).multiply(pixelArea).rename('nonforest_m2'))
  .reduceRegion({reducer: ee.Reducer.sum(), geometry: kakumPark.geometry(), scale: 10, maxPixels: 1e9});
var forestHa    = ee.Number(areaStats.get('forest_m2')).divide(10000);
var nonForestHa = ee.Number(areaStats.get('nonforest_m2')).divide(10000);
print('Forest area (ha):', forestHa);
print('Non-forest area (ha):', nonForestHa);
print('Total inside boundary (ha):', forestHa.add(nonForestHa));

// --- 11. Emission factor: hectares -> carbon -> CO2e (Tier 1 sanity check) ---
var AGB = 310, CF = 0.47, CO2 = 44/12, R = 0.24;   // IPCC Tier 1 defaults
var agCO2ePerHa = AGB * CF * CO2;
print('Above-ground CO2e per ha (tCO2e/ha):', agCO2ePerHa);
print('TOTAL above-ground stock (tCO2e):', forestHa.multiply(agCO2ePerHa));
var totCO2ePerHa = AGB * (1 + R) * CF * CO2;
print('CO2e per ha incl. roots (tCO2e/ha):', totCO2ePerHa);
print('TOTAL stock incl. roots (tCO2e):', forestHa.multiply(totCO2ePerHa));

// --- 12. EXPORT: classified raster for the Python workflow ---
// UTM 30N (EPSG:32630) -> every pixel is exactly 10 m x 10 m, so
// Python computes area as (forest pixel count) x 100 m^2, no distortion.
Export.image.toDrive({
  image: classified.clip(kakumPark).toByte(),   // 1 = forest, 0 = non-forest
  description: 'kakum_classified',
  folder: 'kakum_mrv',
  fileNamePrefix: 'kakum_classified',
  region: kakumPark.geometry(),
  scale: 10,
  crs: 'EPSG:32630',
  maxPixels: 1e9
});
