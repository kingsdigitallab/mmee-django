var search_map = function(L, g_map_image_size, on_map_created) {
    // This 'class' encapsulates a leaflet map on the search web page

    // ns is a dictionary for all public methods
    var ns = {};
    
    function init() {
        // constructor
        ns.cluster_group = null;
        ns.map = create_leaflet_map();
    }

    function create_leaflet_map() {
        var centre = (window.initial_query.geo.split(',')).map(function(v) {return parseFloat(v);});
        var ret = L.map('map-leaflet').setView([centre[0], centre[1]], centre[2]);
        L.control.locate().addTo(ret);

        // Create tilelayer and add to map
        L.tileLayer("http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.png").addTo(ret);
        
        return ret;
        /*            
        function init_click_map_to_interact(map) {
            // map.scrollWheelZoom.disable();
            // map.once('focus', function() {
            //     map.scrollWheelZoom.enable();
            // });
        }
        init_click_map_to_interact(ret);
        */
    }
    
    ns.resize_map = function() {
        // redraw map after any chnage in size
        $(window).trigger('resize');
    };

    ns.redraw_map = function() {
        ns.map.invalidateSize();
    };

    function on_click_marker(e) {
        // ajax-load an image in a popup for the map marker the user has just clicked on  
        var marker = e.target;
        var content = '<a href="/photos/'+marker.id+'">Loading image...</a>';
        marker.setPopupContent(content);
        var req = $.getJSON('/api/1.0/photos/', {'id': marker.id, 'imgspecs': 'height-'+g_map_image_size});
        req.done(function(res) {
            content = '<a class="map-img" href="/photos/'+marker.id+'">'+res.data[0].attributes.image+'</a>';
            marker.setPopupContent(content);
        });
    }
    
    ns.fit_bounds = function(bounds) {
        ns.map.fitBounds(bounds);
    };

    ns.replace_markers = function(photos, reframe) {
        //  if reframe = 1: reframe the map around the set of markers
        var markers = {};
        var has_markers = false;
        photos.map(function(p) {
            var pa = p.attributes;
            if (pa.location) {
                // TODO: expensive to set content and event for thousands of markers
                var marker = L.marker(pa.location).bindPopup('loading...');
                marker.id = p.id;
                marker.on('click', on_click_marker);
                markers[p.id] = marker;
                has_markers = true;
            }
        });
        if (has_markers) {
            if (!ns.cluster_group) {
                ns.cluster_group = L.markerClusterGroup();
            }
            ns.map.addLayer(ns.cluster_group);
            ns.cluster_group.clearLayers();
            ns.cluster_group.addLayers(Object.values(markers));
        }
        
        if (on_map_created) {
            on_map_created();
        }
        ns.resize_map();

        if (has_markers && reframe) {
            ns.map.fitBounds(ns.cluster_group.getBounds());
        }
    };

    init();

    return ns;
};
