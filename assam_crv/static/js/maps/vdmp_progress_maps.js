var map;

// document.addEventListener('DOMContentLoaded',async ()=>{
//      // Center on Assam (approximate coordinates)
//   const assamCenter = ol.proj.fromLonLat([92.9376, 26.2006]);

//   // Google Maps-like tile source (CartoDB Positron or OSM alternative)
//   const googleLikeLayer = new ol.layer.Tile({
//     title: 'Google-like Base Map',
//     // source: new ol.source.XYZ({
//     //   url: 'http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga',
     
//     // })
//   });

//   // Assam Boundary Vector Layer (sample GeoJSON - you must replace the `url` with your actual GeoJSON file or data)
//   const assamBoundaryLayer = new ol.layer.Vector({
//   title: 'Assam Boundary',
//   source: new ol.source.Vector({
//     url: "/static/temp_Map_data/assam.geojson",
//     format: new ol.format.GeoJSON()
//   }),
//   style: new ol.style.Style({
//     stroke: new ol.style.Stroke({
//       color: 'block',
//       width: 2
//     }),
//     // fill: new ol.style.Fill({
//     //   color: 'rgba(255, 0, 0, 0.1)'
//     // })
//   })
// });

// //   console.log("-------Control -----------",control,ol)
//   // Map initialization
  
//    map = new ol.Map({
    
//     target: 'VDMP_progress_page_map',
//     layers: [
//       googleLikeLayer,
//       assamBoundaryLayer
//     ],
//     view: new ol.View({
//       center: assamCenter,
//       zoom: 7
//     }),

//     // controls: Control.defaults().extend([
//     //   new ol.control.Zoom()
//     // ])
//   });
//   console.log("-------map -----------", map)
// })